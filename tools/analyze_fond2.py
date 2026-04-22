"""Analyse v2 de fond_1.png par projection ligne/colonne."""
from __future__ import annotations
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = os.path.join(ROOT, "assets", "swarfarm", "scan_bg", "fond_1.png")

im = Image.open(IMG).convert("RGBA")
W, H = im.size
arr = np.asarray(im)
R, G, B = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)

# ── Masques plus larges ─────────────────────────────────────────────────────
# Rose/magenta — pour cadre RECO : R fort et R > G
pink = (R > 170) & (R - G > 50) & (B > 90)
# Cyan/turquoise — cards HISTORY/UPGRADE (cadre néon subtil). B>R, B>G-20.
cyan_frame = (B > 150) & (B - R > 30) & (G > 120) & (G < 230)
# Or/jaune — pentagramme
gold = (R > 200) & (G > 160) & (B < 140)


def tight_bbox(mask: np.ndarray, x0: int = 0, x1: int | None = None,
               y0: int = 0, y1: int | None = None,
               min_row: int = 3, min_col: int = 3) -> tuple[int, int, int, int] | None:
    """Bbox du masque clipé, en gardant seulement lignes/colonnes avec >=min pixels."""
    x1 = x1 if x1 is not None else W
    y1 = y1 if y1 is not None else H
    sub = mask[y0:y1, x0:x1]
    rows = sub.sum(axis=1)
    cols = sub.sum(axis=0)
    rys = np.where(rows >= min_row)[0]
    cxs = np.where(cols >= min_col)[0]
    if len(rys) == 0 or len(cxs) == 0:
        return None
    return (x0 + cxs.min(), y0 + rys.min(),
            cxs.max() - cxs.min() + 1, rys.max() - rys.min() + 1)


def ratios(x: int, y: int, w: int, h: int) -> tuple[float, float, float, float]:
    return (round(x / W, 3), round(y / H, 3), round(w / W, 3), round(h / H, 3))


def show(name: str, bb):
    if bb is None:
        print(f"  {name}: AUCUN")
        return
    x, y, w, h = bb
    rx, ry, rw, rh = ratios(x, y, w, h)
    print(f"  {name:18s} px=({x:4d},{y:4d},{w:4d},{h:4d})  "
          f"ratio=({rx},{ry},{rw},{rh})")

print(f"Image: {W}x{H}\n")

# 1. RECO (cadre rose bas). Chercher sur y>450 toute la largeur.
print("== RECO (rose, y>440) ==")
bb = tight_bbox(pink, y0=440, min_row=15, min_col=15)
show("RECO bbox", bb)

# 2. HISTORY (grille 2x3 haut-droit). Zone x>1000, y<500.
print("\n== HISTORY (cyan, x>1000, y<500) ==")
bb = tight_bbox(cyan_frame, x0=1000, y0=0, y1=500, min_row=2, min_col=2)
show("HISTORY bbox", bb)

# 3. UPGRADE (card bas-droit). x>1000, y>500.
print("\n== UPGRADE (cyan, x>1000, y>500) ==")
bb = tight_bbox(cyan_frame, x0=1000, y0=500, min_row=2, min_col=2)
show("UPGRADE bbox", bb)

# 4. PENTAGRAMME (or)
print("\n== PENTAGRAMME (or) ==")
bb = tight_bbox(gold, min_row=4, min_col=4)
show("pentagramme", bb)
if bb:
    cx = bb[0] + bb[2] // 2
    print(f"  centre_x={cx} ratio={cx/W:.3f}   bas_pentagramme_y={bb[1]+bb[3]} ratio={(bb[1]+bb[3])/H:.3f}")

# 5. Capsule gauche (possible scan button). Zone x<300.
print("\n== CAPSULE GAUCHE (rose/blanc, x<300) ==")
# Essayons une détection plus large : pixels "pinkish" ou "gris clair encadre"
light_pink = (R > 160) & (R - G > 20) & (B > 100)
bb = tight_bbox(light_pink, x0=0, x1=300, y0=50, y1=250, min_row=2, min_col=2)
show("CAPSULE bbox", bb)

# 6. Mesure détaillée de la grille HISTORY (chaque cellule)
print("\n== HISTORY : détection colonnes/lignes de cellules ==")
cyan_hist = cyan_frame.copy()
cyan_hist[:, :1000] = False
cyan_hist[500:, :] = False
cols_sum = cyan_hist.sum(axis=0)
rows_sum = cyan_hist.sum(axis=1)
print("  Top 12 x avec forte densité (cadres verticaux) :")
top_x = np.argsort(cols_sum)[-40:][::-1]
top_x = sorted([int(x) for x in top_x if cols_sum[x] > 0])
# Grouper en clusters (pics adjacents)
clusters_x = []
cur = []
for x in top_x:
    if not cur or x - cur[-1] <= 4:
        cur.append(x)
    else:
        clusters_x.append(cur)
        cur = [x]
if cur:
    clusters_x.append(cur)
for c in clusters_x:
    print(f"    x cluster {c[0]}..{c[-1]}  ratio_x0={c[0]/W:.3f}  ratio_x1={c[-1]/W:.3f}")

print("  Top 12 y avec forte densité (cadres horizontaux) :")
top_y = np.argsort(rows_sum)[-40:][::-1]
top_y = sorted([int(y) for y in top_y if rows_sum[y] > 0])
clusters_y = []
cur = []
for y in top_y:
    if not cur or y - cur[-1] <= 4:
        cur.append(y)
    else:
        clusters_y.append(cur)
        cur = [y]
if cur:
    clusters_y.append(cur)
for c in clusters_y:
    print(f"    y cluster {c[0]}..{c[-1]}  ratio_y0={c[0]/H:.3f}  ratio_y1={c[-1]/H:.3f}")
