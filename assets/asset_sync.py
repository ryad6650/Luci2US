"""Download + extract the heavy asset bundle (monsters + HD icons) on demand.

Heavy assets are hosted as a zip on GitHub Releases (tag ``assets-vN``) rather
than committed to git. At startup the app calls :func:`ensure_assets`; if the
local ``.asset_version`` matches :data:`REQUIRED_VERSION` it returns instantly.
Otherwise the bundle is downloaded, extracted into ``assets/``, and the version
marker is written last (so a crashed download never pretends to be complete).
"""
from __future__ import annotations

import os
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

# Bump when you publish a new bundle via scripts/publish_assets.py
REQUIRED_VERSION = "v1"

_REPO = "ryad6650/Luci2US"
_BUNDLE_NAME = "luci2us_assets.zip"

ASSETS_DIR = Path(__file__).resolve().parent
VERSION_FILE = ASSETS_DIR / ".asset_version"

ProgressCb = Callable[[float, str], None]


def release_url(version: str = REQUIRED_VERSION) -> str:
    return f"https://github.com/{_REPO}/releases/download/assets-{version}/{_BUNDLE_NAME}"


def current_version() -> Optional[str]:
    if not VERSION_FILE.exists():
        return None
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def is_up_to_date() -> bool:
    return current_version() == REQUIRED_VERSION


def ensure_assets(progress: Optional[ProgressCb] = None) -> None:
    if is_up_to_date():
        return

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_zip = ASSETS_DIR / f"_{_BUNDLE_NAME}.part"
    final_zip = ASSETS_DIR / f"_{_BUNDLE_NAME}"

    _download(release_url(), tmp_zip, progress)
    tmp_zip.replace(final_zip)
    try:
        _extract(final_zip, ASSETS_DIR, progress)
    finally:
        final_zip.unlink(missing_ok=True)

    VERSION_FILE.write_text(REQUIRED_VERSION, encoding="utf-8")


def _download(url: str, dest: Path, progress: Optional[ProgressCb]) -> None:
    if progress:
        progress(0.0, f"Connexion à GitHub Releases ({REQUIRED_VERSION})...")
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            chunk = 1024 * 256
            with dest.open("wb") as f:
                while True:
                    buf = resp.read(chunk)
                    if not buf:
                        break
                    f.write(buf)
                    downloaded += len(buf)
                    if progress and total:
                        ratio = min(downloaded / total, 1.0) * 0.9
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        progress(
                            ratio,
                            f"Téléchargement... {mb_done:.0f} / {mb_total:.0f} Mo",
                        )
    except (urllib.error.URLError, TimeoutError) as e:
        dest.unlink(missing_ok=True)
        raise AssetSyncError(f"Téléchargement impossible: {e}") from e


def _extract(zip_path: Path, target_dir: Path, progress: Optional[ProgressCb]) -> None:
    if progress:
        progress(0.9, "Extraction des ressources...")
    with zipfile.ZipFile(zip_path) as z:
        members = z.namelist()
        total = max(len(members), 1)
        for i, name in enumerate(members):
            z.extract(name, target_dir)
            if progress and i % 50 == 0:
                ratio = 0.9 + (i / total) * 0.1
                progress(min(ratio, 0.999), f"Extraction... {i}/{total} fichiers")


class AssetSyncError(RuntimeError):
    """Raised when the asset bundle cannot be downloaded or extracted."""


__all__ = [
    "REQUIRED_VERSION",
    "AssetSyncError",
    "current_version",
    "ensure_assets",
    "is_up_to_date",
    "release_url",
]
