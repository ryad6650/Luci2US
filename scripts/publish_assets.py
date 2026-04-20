"""Package ``assets/monsters`` + ``assets/monsters_hd`` into a zip and upload it
to a new GitHub Release so the app can fetch it via ``assets/asset_sync.py``.

Usage::

    python scripts/publish_assets.py v2

Prereqs: ``gh`` CLI installed and authenticated on the ``ryad6650/Luci2US``
repo. After a successful upload, bump ``REQUIRED_VERSION`` in
``assets/asset_sync.py`` to match, then commit + push.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
BUNDLE_DIRS = ("monsters", "monsters_hd")
BUNDLE_NAME = "luci2us_assets.zip"


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("version", help='Version label, e.g. "v2".')
    ap.add_argument(
        "--skip-upload",
        action="store_true",
        help="Build the zip locally without calling gh (useful to inspect size).",
    )
    return ap.parse_args()


def build_zip(zip_path: Path) -> int:
    files: list[Path] = []
    for name in BUNDLE_DIRS:
        base = ASSETS / name
        if not base.exists():
            sys.exit(f"Missing source dir: {base}")
        files.extend(p for p in base.rglob("*") if p.is_file())

    print(f"Zipping {len(files)} files from {BUNDLE_DIRS}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for i, f in enumerate(files, 1):
            z.write(f, f.relative_to(ASSETS))
            if i % 200 == 0:
                print(f"  {i}/{len(files)}")
    return zip_path.stat().st_size


def upload_release(version: str, zip_path: Path) -> None:
    tag = f"assets-{version}"
    title = f"Assets {version}"
    notes = f"Bundle ressources lourdes (monstres + HD). Sync via assets/asset_sync.py."
    cmd = [
        "gh", "release", "create", tag, str(zip_path),
        "--title", title,
        "--notes", notes,
    ]
    print(f"Creating release {tag}...")
    subprocess.run(cmd, check=True)


def mark_local_version(version: str) -> None:
    # Skip download on this machine: the bundle we just uploaded already matches disk.
    (ASSETS / ".asset_version").write_text(version, encoding="utf-8")


def main() -> None:
    args = parse_args()
    zip_path = ROOT / BUNDLE_NAME

    size = build_zip(zip_path)
    print(f"Built {zip_path.name}: {size / 1024 / 1024:.1f} MB")

    if args.skip_upload:
        print("--skip-upload set, stopping here.")
        return

    upload_release(args.version, zip_path)
    mark_local_version(args.version)
    zip_path.unlink(missing_ok=True)

    print()
    print("Next steps:")
    print(f"  1. Edit assets/asset_sync.py -> REQUIRED_VERSION = \"{args.version}\"")
    print(f"  2. git commit -am 'chore(assets): bump REQUIRED_VERSION to {args.version}'")
    print(f"  3. git push")


if __name__ == "__main__":
    main()
