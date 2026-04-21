"""One-shot: crop image_19.png (sidebar excluded) to produce the ScanPage fond.

image_19.png is 1408x768 with the sidebar baked in at x=0..256.
We keep only x=256..1408 (1152x768) so the Qt Sidebar widget can render
independently to the left of the ScanPage.
"""
from __future__ import annotations
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "image_19.png")
DST = os.path.join(ROOT, "assets", "swarfarm", "scan_bg", "fond_v19.png")

SIDEBAR_PX = 256  # measured: transition from sidebar bg to scan bg


def main() -> None:
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    crop = im.crop((SIDEBAR_PX, 0, w, h))
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    crop.save(DST)
    print(f"Saved {DST} ({crop.size[0]}x{crop.size[1]})")


if __name__ == "__main__":
    main()
