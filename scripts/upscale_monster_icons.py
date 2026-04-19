"""Upscale cached monster icons (100x100) to HD (400x400) with Real-ESRGAN.

Usage: `python scripts/upscale_monster_icons.py`

Requires the standalone Real-ESRGAN ncnn-vulkan binary at
`tools/realesrgan/realesrgan-ncnn-vulkan.exe` (download:
https://github.com/xinntao/Real-ESRGAN/releases).

Only processes icons missing from assets/monsters_hd/, so re-running
after download_icons_async() just covers the new monsters.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "monsters"
DST = ROOT / "assets" / "monsters_hd"
EXE = ROOT / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
MODEL = "realesrgan-x4plus-anime"


def main() -> int:
    if not EXE.is_file():
        print(f"ERROR: Real-ESRGAN binary not found at {EXE}", file=sys.stderr)
        print("Download from https://github.com/xinntao/Real-ESRGAN/releases "
              "and extract into tools/realesrgan/", file=sys.stderr)
        return 2

    DST.mkdir(parents=True, exist_ok=True)
    todo = [p for p in SRC.glob("unit_icon_*.png") if not (DST / p.name).is_file()]
    if not todo:
        print("Nothing to do — every icon already has an HD version.")
        return 0

    print(f"Upscaling {len(todo)} icons → {DST}")
    with tempfile.TemporaryDirectory() as staging:
        stage = Path(staging)
        for p in todo:
            (stage / p.name).write_bytes(p.read_bytes())
        cmd = [
            str(EXE),
            "-i", str(stage),
            "-o", str(DST),
            "-n", MODEL,
            "-s", "4",
            "-f", "png",
        ]
        result = subprocess.run(cmd, cwd=EXE.parent)
        if result.returncode != 0:
            print("Real-ESRGAN returned non-zero exit code.", file=sys.stderr)
            return result.returncode

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
