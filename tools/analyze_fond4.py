"""Mesure precise des 4 cadres visibles dans fond_1.png."""
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
lum = (0.299 * R + 0.587 * G + 0.114 * B).astype(int)


def r(x, y, w, h):
    return (round(x / W, 3), round(y / H, 3), round(w / W, 3), round(h / H, 3))


def peaks_1d(profile: np.ndarray, threshold: int) -> list[tuple[int, int]]:
    peaks = []
    in_pk = False
    start = 0
    for i, v in enumerate(profile):
        if v > threshold and not in_pk:
            in_pk = True
            start = i
        elif v <= threshold and in_pk:
            in_pk = False
            peaks.append((start, i - 1))
    if in_pk:
        peaks.append((start, len(profile) - 1))
    return peaks


# ═══════════════════════════════════════════════════════════════════════════
# 1. RECO : bord rose saturé (R>>G)
# ═══════════════════════════════════════════════════════════════════════════
print("═══ 1. RECO (cadre rose bas) ═══")
# Masque rose strict (bordure neon)
pink = (R > 160) & (R - G > 40) & (B > 100) & (R - B > 0)
# Clip zone plausible
pink_c = pink.copy()
pink_c[:440, :] = False   # au-dessus du cadre
pink_c[735:, :] = False   # sous l'image (bordure bas)
pink_c[:, :180] = False
pink_c[:, 1120:] = False

rows = pink_c.sum(axis=1)
cols = pink_c.sum(axis=0)
# Seuils adaptés pour extérieur du cadre
rys = np.where(rows > 10)[0]
cxs = np.where(cols > 10)[0]
if len(rys) and len(cxs):
    x0, x1 = cxs.min(), cxs.max()
    y0, y1 = rys.min(), rys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"  RECO px=({x0},{y0},{w},{h})  ratio={r(x0,y0,w,h)}")

# ═══════════════════════════════════════════════════════════════════════════
# 2. HISTORY : grille 2x3. Detection par scan en gradient vertical
# ═══════════════════════════════════════════════════════════════════════════
print("\n═══ 2. HISTORY (grille 2x3) ═══")
# On se restreint a la zone haut-droite (hors pentagramme)
hist_mask = (lum > 42) & (lum < 120)  # cadres subtils mais pas trop brillants
hist_mask[:, :1080] = False
hist_mask[:, 1385:] = False
hist_mask[:55, :] = False
hist_mask[545:, :] = False

rows = hist_mask.sum(axis=1)
cols = hist_mask.sum(axis=0)
rys = np.where(rows > 30)[0]
cxs = np.where(cols > 30)[0]
if len(rys) and len(cxs):
    x0, x1 = cxs.min(), cxs.max()
    y0, y1 = rys.min(), rys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"  HISTORY englobant px=({x0},{y0},{w},{h})  ratio={r(x0,y0,w,h)}")

# Identifier les colonnes verticales de séparation (peu de pixels lumineux)
print("\n  Détection colonnes (peu de pixels -> bords vertical) :")
col_profile = hist_mask[55:540, 1080:1385].sum(axis=0)
# Inverse : on cherche les minima (espaces vides entre cells)
# Les cells sont pleines, les bords sont rares
# Au lieu : lum>42 donne les "bords" des cellules, regardons pics
print(f"    Col profile (x=1080..1385): min={col_profile.min()} max={col_profile.max()}")
print(f"    Pics forts (>{int(col_profile.max()*0.6)}):")
strong = peaks_1d(col_profile, int(col_profile.max() * 0.6))
for a, b in strong[:10]:
    print(f"      x={a+1080}..{b+1080} (ratio {(a+1080)/W:.3f}..{(b+1080)/W:.3f})")

# Scan rows
print("\n  Détection lignes (y) :")
row_profile = hist_mask[55:540, 1080:1385].sum(axis=1)
strong_y = peaks_1d(row_profile, int(row_profile.max() * 0.6))
for a, b in strong_y[:10]:
    print(f"      y={a+55}..{b+55} (ratio {(a+55)/H:.3f}..{(b+55)/H:.3f})")

# Approche alternative : detecter les 6 cellules via remplissage gris sombre
print("\n  Cellules (intérieur sombre uniforme 20<lum<42) :")
cell_mask = (lum > 20) & (lum < 42)
cell_mask[:, :1080] = False
cell_mask[:, 1385:] = False
cell_mask[:55, :] = False
cell_mask[545:, :] = False
rows = cell_mask.sum(axis=1)
cols = cell_mask.sum(axis=0)
rys = np.where(rows > 30)[0]
cxs = np.where(cols > 20)[0]
if len(rys) and len(cxs):
    x0, x1 = cxs.min(), cxs.max()
    y0, y1 = rys.min(), rys.max()
    print(f"    cell-zone englobant px=({x0},{y0},{x1-x0},{y1-y0})  ratio={r(x0,y0,x1-x0,y1-y0)}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. UPGRADE : card bas-droit
# ═══════════════════════════════════════════════════════════════════════════
print("\n═══ 3. UPGRADE (card bas-droit) ═══")
# Cyan subtil (bordure halo bleue autour de la card)
cy = (B > 130) & (B - R > 20) & (G > 100)
cy[:, :1080] = False
cy[:555, :] = False
cy[760:, :] = False
cy[:, 1385:] = False
rows = cy.sum(axis=1)
cols = cy.sum(axis=0)
rys = np.where(rows > 3)[0]
cxs = np.where(cols > 3)[0]
if len(rys) and len(cxs):
    x0, x1 = cxs.min(), cxs.max()
    y0, y1 = rys.min(), rys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"  UPGRADE cyan px=({x0},{y0},{w},{h})  ratio={r(x0,y0,w,h)}")

# Bord brightness
up = (lum > 45) & (lum < 150)
up[:, :1080] = False
up[:555, :] = False
up[760:, :] = False
up[:, 1385:] = False
rows = up.sum(axis=1)
cols = up.sum(axis=0)
rys = np.where(rows > 20)[0]
cxs = np.where(cols > 20)[0]
if len(rys) and len(cxs):
    x0, x1 = cxs.min(), cxs.max()
    y0, y1 = rys.min(), rys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"  UPGRADE lum  px=({x0},{y0},{w},{h})  ratio={r(x0,y0,w,h)}")

# ═══════════════════════════════════════════════════════════════════════════
# 4. SCAN_BTN : zone sous le pentagramme, centrée horizontalement sur lui
# ═══════════════════════════════════════════════════════════════════════════
print("\n═══ 4. SCAN_BTN (sous pentagramme) ═══")
gold = (R > 200) & (G > 160) & (B < 140)
ys, xs = np.where(gold)
if len(xs):
    gx0, gx1 = xs.min(), xs.max()
    gy1 = ys.max()
    cx = (gx0 + gx1) // 2
    print(f"  Pentagramme: x={gx0}..{gx1} (cx={cx}, ratio {cx/W:.3f})  bas_y={gy1} (ratio {gy1/H:.3f})")
    # Zone scan btn : sous pentagramme, centrée, avant RECO (y<540)
    # Prop : larg 260, hauteur 50, centré sur cx, y juste au-dessus de RECO
    btn_w = 260
    btn_h = 50
    btn_x = cx - btn_w // 2
    btn_y = gy1 - 20  # chevauche un peu le bas du pentagramme (au niveau "WAY" runes)
    print(f"  SCAN_BTN proposé px=({btn_x},{btn_y},{btn_w},{btn_h})  ratio={r(btn_x,btn_y,btn_w,btn_h)}")

# ═══════════════════════════════════════════════════════════════════════════
# 5. CAPSULE gauche (l'"onglet" à gauche)
# ═══════════════════════════════════════════════════════════════════════════
print("\n═══ 5. CAPSULE gauche (onglet bouton gauche) ═══")
cap = (lum > 40).copy()
cap[:, 310:] = False
cap[:100, :] = False
cap[260:, :] = False
rows = cap.sum(axis=1)
cols = cap.sum(axis=0)
rys = np.where(rows > 15)[0]
cxs = np.where(cols > 15)[0]
if len(rys) and len(cxs):
    x0, x1 = cxs.min(), cxs.max()
    y0, y1 = rys.min(), rys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"  CAPSULE px=({x0},{y0},{w},{h})  ratio={r(x0,y0,w,h)}")
