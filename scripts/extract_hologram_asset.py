"""One-shot : extrait l'hologramme rune depuis `scan 2.png`.

La maquette `scan 2.png` contient l'hologramme (hexagramme rose + piedestal)
dans le quart centre-gauche. Ce script extrait la zone et sauvegarde un PNG
avec fond transparent pour overlay sur le cercle magique.

Usage : python scripts/extract_hologram_asset.py
"""
from __future__ import annotations

import os
from PIL import Image

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scan 2.png")
DST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "scan_ui", "hologram_rune.png",
)

# Zone mesuree sur scan 2.png — ratios (x0, y0, x1, y1) relatifs a l'image entiere.
RATIO_BOX = (0.235, 0.160, 0.485, 0.570)


def main() -> None:
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    rx0, ry0, rx1, ry1 = RATIO_BOX
    box = (int(w * rx0), int(h * ry0), int(w * rx1), int(h * ry1))
    crop = im.crop(box)
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    crop.save(DST)
    print(f"Saved {DST} ({crop.size[0]}x{crop.size[1]})")


if __name__ == "__main__":
    main()
