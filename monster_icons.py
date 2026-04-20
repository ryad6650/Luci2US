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
_HD_DIR = _ROOT / "assets" / "monsters_hd"
_MAP_FILE = _CACHE_DIR / "_icon_map.json"
_BESTIARY_FILE = _ROOT / "bestiary.json"
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


def _fetch_all_monsters() -> list[dict]:
    """Fetch every page of the Swarfarm monsters endpoint."""
    url: str | None = _SWARFARM_API
    all_monsters: list[dict] = []
    while url:
        data = _fetch_page(url)
        all_monsters.extend(data.get("results", []))
        url = data.get("next")
    return all_monsters


def _write_bestiary(all_monsters: list[dict]) -> None:
    """Write bestiary.json at project root for profile_loader to read."""
    entries = []
    for entry in all_monsters:
        com2us_id = entry.get("com2us_id")
        name = entry.get("name")
        if not com2us_id or not name:
            continue
        element = entry.get("element")
        awakens_to = entry.get("awakens_to")
        entries.append({
            "com2us_id": int(com2us_id),
            "name": name,
            "element": element,
            "awakens_to": awakens_to,
        })
    with open(_BESTIARY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)


def _download_icons(on_progress: Callable[[int, int], None] | None = None) -> None:
    """Download all monster icons from SWARFARM API (paginated) and refresh bestiary."""
    global _icon_map
    _ensure_dirs()

    new_map: dict[int, str] = {}
    all_monsters = _fetch_all_monsters()

    # Always refresh the bestiary (names) so profile_loader can resolve IDs
    _write_bestiary(all_monsters)

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


def _download_bestiary() -> None:
    """Fetch only names from Swarfarm and write bestiary.json (no images)."""
    all_monsters = _fetch_all_monsters()
    _write_bestiary(all_monsters)


def is_cache_populated() -> bool:
    """True if the icon cache directory exists and has a map file."""
    return _MAP_FILE.is_file()


def is_bestiary_available() -> bool:
    """True if bestiary.json (names) exists at project root."""
    return _BESTIARY_FILE.is_file()


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


def download_bestiary_async(
    on_done: Callable[[], None] | None = None,
) -> None:
    """Fetch only Swarfarm monster names (fast, no images) in background."""

    def _worker() -> None:
        try:
            _download_bestiary()
        except Exception:
            pass
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
        hd_path = _HD_DIR / filename
        if hd_path.is_file():
            return hd_path
        path = _CACHE_DIR / filename
        if path.is_file():
            return path
    return _PLACEHOLDER


# In-memory name map loaded lazily from bestiary.json
_name_map: dict[int, str] = {}
_names_loaded = False


def _load_names() -> None:
    """Load monster names from bestiary.json on demand."""
    global _name_map, _names_loaded
    if _names_loaded and _name_map:
        return
    if not _BESTIARY_FILE.is_file():
        _names_loaded = True
        return
    try:
        with open(_BESTIARY_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        _names_loaded = True
        return
    new_map: dict[int, str] = {}
    for entry in data:
        mid = entry.get("com2us_id") or entry.get("unit_master_id")
        name = entry.get("name")
        if mid and name:
            new_map[int(mid)] = name
    _name_map = new_map
    _names_loaded = True


def invalidate_names_cache() -> None:
    """Force the name map to be re-read from bestiary.json on next lookup."""
    global _name_map, _names_loaded
    _name_map = {}
    _names_loaded = False


def get_monster_name(unit_master_id: int) -> str | None:
    """Return the Swarfarm name for a monster id, or None if unknown."""
    _load_names()
    return _name_map.get(unit_master_id)
