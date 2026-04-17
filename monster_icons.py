"""Monster icon downloader & cache for SWARFARM images."""

from __future__ import annotations

import json
import os
import threading
import urllib.request
from pathlib import Path
from typing import Callable

_ROOT = Path(__file__).parent
_CACHE_DIR = _ROOT / "assets" / "monsters"
_MAP_FILE = _CACHE_DIR / "_icon_map.json"
_SWARFARM_API = "https://swarfarm.com/api/v2/monsters/?format=json"
_SWARFARM_IMG = "https://swarfarm.com/static/herders/images/monsters/"
_PLACEHOLDER = _ROOT / "assets" / "placeholder.png"

# In-memory map: unit_master_id (int) -> local filename
_icon_map: dict[int, str] = {}
_loaded = False


def _ensure_dirs() -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_map() -> None:
    global _icon_map, _loaded
    if _loaded:
        return
    if _MAP_FILE.is_file():
        with open(_MAP_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        _icon_map = {int(k): v for k, v in raw.items()}
    _loaded = True


def _save_map() -> None:
    with open(_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in _icon_map.items()}, f)


def _fetch_page(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Luci2US/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_icons(on_progress: Callable[[int, int], None] | None = None) -> None:
    """Download all monster icons from SWARFARM API (paginated)."""
    global _icon_map
    _ensure_dirs()

    new_map: dict[int, str] = {}
    url: str | None = _SWARFARM_API
    all_monsters: list[dict] = []

    # Fetch all pages
    while url:
        data = _fetch_page(url)
        results = data.get("results", [])
        all_monsters.extend(results)
        url = data.get("next")

    total = len(all_monsters)
    downloaded = 0

    for entry in all_monsters:
        com2us_id = entry.get("com2us_id")
        image_filename = entry.get("image_filename")
        if not com2us_id or not image_filename:
            continue

        local_name = image_filename
        local_path = _CACHE_DIR / local_name
        new_map[int(com2us_id)] = local_name

        # Skip if already downloaded
        if local_path.is_file():
            downloaded += 1
            if on_progress:
                on_progress(downloaded, total)
            continue

        img_url = _SWARFARM_IMG + image_filename
        try:
            req = urllib.request.Request(
                img_url, headers={"User-Agent": "Luci2US/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                local_path.write_bytes(resp.read())
        except Exception:
            pass  # skip failed downloads silently

        downloaded += 1
        if on_progress:
            on_progress(downloaded, total)

    _icon_map = new_map
    _save_map()


def is_cache_populated() -> bool:
    """True if the icon cache directory exists and has a map file."""
    return _MAP_FILE.is_file()


def download_icons_async(
    on_progress: Callable[[int, int], None] | None = None,
    on_done: Callable[[], None] | None = None,
) -> None:
    """Download icons in a background thread."""

    def _worker() -> None:
        try:
            _download_icons(on_progress=on_progress)
        finally:
            if on_done:
                on_done()

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def get_monster_icon(unit_master_id: int) -> Path:
    """Return the path to the local icon PNG for a monster.

    Returns a placeholder path if the icon is not cached.
    """
    _load_map()
    filename = _icon_map.get(unit_master_id)
    if filename:
        path = _CACHE_DIR / filename
        if path.is_file():
            return path
    return _PLACEHOLDER
