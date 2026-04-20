"""Remove the white background from 'Logo + Luci2US.png' and save as assets/logo_luci2us.png."""
from __future__ import annotations

import os

from PIL import Image

SRC = os.path.join(os.path.dirname(__file__), "..", "Logo + Luci2US.png")
DST = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_luci2us.png")


def strip_white(img: Image.Image) -> Image.Image:
    """Convert white background to transparent and unmultiply edges to kill the white halo."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    lo, hi = 8, 40
    span = hi - lo
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            d = 255 - min(r, g, b)
            if d <= lo:
                px[x, y] = (0, 0, 0, 0)
                continue
            if d >= hi:
                px[x, y] = (r, g, b, a)
                continue
            new_a = int(round((d - lo) / span * 255))
            an = new_a / 255.0
            nr = int(round(255 + (r - 255) / an))
            ng = int(round(255 + (g - 255) / an))
            nb = int(round(255 + (b - 255) / an))
            nr = 0 if nr < 0 else (255 if nr > 255 else nr)
            ng = 0 if ng < 0 else (255 if ng > 255 else ng)
            nb = 0 if nb < 0 else (255 if nb > 255 else nb)
            px[x, y] = (nr, ng, nb, min(a, new_a))
    return img


def main() -> None:
    src = os.path.abspath(SRC)
    dst = os.path.abspath(DST)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    img = Image.open(src)
    out = strip_white(img)
    out.save(dst, "PNG")
    print(f"Saved -> {dst} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    main()
