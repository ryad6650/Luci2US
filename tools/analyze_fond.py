"""Analyse des cadres dessinés dans assets/swarfarm/scan_bg/fond_1.png.

Strategie :
1. Charger l'image + passer en numpy (H, W, 4).
2. Detecter pixels "roses/magenta" -> cadre RECO + capsule gauche.
3. Detecter pixels "bleus cyan" -> grille HISTORY + card UPGRADE.
4. Pour chaque masque, extraire les bounding boxes des composantes connexes.
5. Identifier le cercle magique central (zone doree) pour la zone SCAN_BTN.
"""
from __future__ import annotations
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = os.path.join(ROOT, "assets", "swarfarm", "scan_bg", "fond_1.png")

im = Image.open(IMG).convert("RGBA")
W, H = im.size
print(f"Image: {W}x{H}")
arr = np.asarray(im)
R, G, B, A = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

# ── Masques de couleur ──────────────────────────────────────────────────────
# Rose/magenta : R fort, B moyen, G faible
mask_pink = (R > 180) & (G < 140) & (B > 100) & (B < 220)
# Bleu cyan (cadres history + upgrade) : B fort, G moyen, R faible
mask_cyan = (B > 140) & (G > 120) & (R < 130)
# Or/jaune (pentagramme central)
mask_gold = (R > 200) & (G > 160) & (B < 140)


def component_bboxes(mask: np.ndarray, min_pixels: int = 50) -> list[tuple[int, int, int, int, int]]:
    """BFS componantes connexes → (x, y, w, h, npix). Stack‑safe."""
    visited = np.zeros_like(mask, dtype=bool)
    boxes: list[tuple[int, int, int, int, int]] = []
    ys, xs = np.where(mask & ~visited)
    for i in range(len(ys)):
        sy, sx = ys[i], xs[i]
        if visited[sy, sx]:
            continue
        stack = [(sy, sx)]
        pts: list[tuple[int, int]] = []
        while stack:
            y, x = stack.pop()
            if y < 0 or y >= mask.shape[0] or x < 0 or x >= mask.shape[1]:
                continue
            if visited[y, x] or not mask[y, x]:
                continue
            visited[y, x] = True
            pts.append((y, x))
            stack.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
        if len(pts) < min_pixels:
            continue
        ys_c = [p[0] for p in pts]
        xs_c = [p[1] for p in pts]
        y0, y1 = min(ys_c), max(ys_c)
        x0, x1 = min(xs_c), max(xs_c)
        boxes.append((x0, y0, x1 - x0 + 1, y1 - y0 + 1, len(pts)))
    return boxes


def fmt(name: str, x: int, y: int, w: int, h: int) -> None:
    rx, ry, rw, rh = x / W, y / H, w / W, h / H
    print(
        f"  {name:20s} px=({x:4d},{y:4d},{w:4d},{h:4d})  "
        f"ratio=({rx:.3f},{ry:.3f},{rw:.3f},{rh:.3f})"
    )


# ── Regroupe par zone (bbox englobant + pixels) ─────────────────────────────
print("\n== ROSE/MAGENTA (cadre reco + capsule gauche) ==")
pink_boxes = sorted(component_bboxes(mask_pink, 200), key=lambda b: -b[4])[:10]
for i, (x, y, w, h, n) in enumerate(pink_boxes):
    fmt(f"rose#{i} ({n}px)", x, y, w, h)

print("\n== CYAN/BLEU (cadres history + upgrade) ==")
cyan_boxes = sorted(component_bboxes(mask_cyan, 150), key=lambda b: -b[4])[:20]
for i, (x, y, w, h, n) in enumerate(cyan_boxes):
    fmt(f"cyan#{i} ({n}px)", x, y, w, h)

# ── Bounding box global des pixels or (pentagramme central) ────────────────
print("\n== OR (cercle magique central) ==")
gold_ys, gold_xs = np.where(mask_gold)
if len(gold_xs):
    gx0, gy0, gx1, gy1 = gold_xs.min(), gold_ys.min(), gold_xs.max(), gold_ys.max()
    fmt("pentagramme", gx0, gy0, gx1 - gx0, gy1 - gy0)
    cx = (gx0 + gx1) // 2
    cy = (gy0 + gy1) // 2
    print(f"  centre ({cx}, {cy})  ratio_centre=({cx/W:.3f}, {cy/H:.3f})")

# ── Bounding box global rose (pour _Z_RECO) ────────────────────────────────
if pink_boxes:
    xs_min = min(b[0] for b in pink_boxes)
    ys_min = min(b[1] for b in pink_boxes)
    xs_max = max(b[0] + b[2] for b in pink_boxes)
    ys_max = max(b[1] + b[3] for b in pink_boxes)
    print("\n== ROSE englobant global ==")
    fmt("reco_all", xs_min, ys_min, xs_max - xs_min, ys_max - ys_min)

# ── Bounding box global cyan (pour _Z_HISTORY + _Z_UPGRADE) ────────────────
if cyan_boxes:
    # On sépare history (haut, y<500) et upgrade (bas, y>500)
    hist = [b for b in cyan_boxes if b[1] < 500]
    upg = [b for b in cyan_boxes if b[1] >= 500]
    if hist:
        hx0 = min(b[0] for b in hist)
        hy0 = min(b[1] for b in hist)
        hx1 = max(b[0] + b[2] for b in hist)
        hy1 = max(b[1] + b[3] for b in hist)
        print("\n== CYAN history englobant ==")
        fmt("history_all", hx0, hy0, hx1 - hx0, hy1 - hy0)
    if upg:
        ux0 = min(b[0] for b in upg)
        uy0 = min(b[1] for b in upg)
        ux1 = max(b[0] + b[2] for b in upg)
        uy1 = max(b[1] + b[3] for b in upg)
        print("\n== CYAN upgrade englobant ==")
        fmt("upgrade_all", ux0, uy0, ux1 - ux0, uy1 - uy0)
