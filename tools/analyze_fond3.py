"""Analyse v3 : détection par edge/gradient + crop d'inspection."""
from __future__ import annotations
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = os.path.join(ROOT, "assets", "swarfarm", "scan_bg", "fond_1.png")
TOOLS = os.path.dirname(os.path.abspath(__file__))

im = Image.open(IMG).convert("RGBA")
W, H = im.size
arr = np.asarray(im)
R, G, B = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)
lum = (0.299 * R + 0.587 * G + 0.114 * B).astype(int)


def ratios(x, y, w, h):
    return (round(x / W, 3), round(y / H, 3), round(w / W, 3), round(h / H, 3))


def bbox_from_gradient(x0, x1, y0, y1, luminance_min: int = 45) -> tuple[int, int, int, int]:
    """Dans la fenetre, seuiller sur luminance puis tight bbox."""
    sub = lum[y0:y1, x0:x1]
    mask = sub > luminance_min
    rows = mask.sum(axis=1)
    cols = mask.sum(axis=0)
    rys = np.where(rows > 5)[0]
    cxs = np.where(cols > 5)[0]
    if len(rys) == 0 or len(cxs) == 0:
        return None
    return (x0 + cxs.min(), y0 + rys.min(),
            cxs.max() - cxs.min() + 1, rys.max() - rys.min() + 1)


# ── Crops de zones d'inspection ─────────────────────────────────────────────
crops = {
    "hist": (1020, 0, 1408, 560),
    "reco": (180, 440, 1120, 760),
    "upgrade": (1020, 500, 1408, 768),
    "capsule": (0, 100, 310, 260),
}
for name, (x0, y0, x1, y1) in crops.items():
    out = os.path.join(TOOLS, f"_crop_{name}.png")
    im.crop((x0, y0, x1, y1)).save(out)
    print(f"crop {name}: {x0},{y0}..{x1},{y1}  -> {out}")


def show(name, bb):
    if bb is None:
        print(f"  {name}: None")
        return
    x, y, w, h = bb
    rx, ry, rw, rh = ratios(x, y, w, h)
    print(f"  {name:16s} px=({x:4d},{y:4d},{w:4d},{h:4d})  ratio=({rx},{ry},{rw},{rh})")


# ── RECO : masque pink + bright, large tolérance ────────────────────────────
print("\n== RECO (pink, y>440) ==")
pink_loose = ((R > 150) & (R - G > 30)) | ((R > 190) & (G < 180) & (B > 120))
sub_mask = pink_loose.copy()
sub_mask[:440, :] = False
sub_mask[:, :180] = False
sub_mask[:, 1120:] = False
rows = sub_mask.sum(axis=1)
cols = sub_mask.sum(axis=0)
rys = np.where(rows > 3)[0]
cxs = np.where(cols > 3)[0]
if len(rys) and len(cxs):
    show("reco_loose", (cxs.min(), rys.min(), cxs.max()-cxs.min()+1, rys.max()-rys.min()+1))

# ── HISTORY : détection par bord clair (luminance) sur x>1020, y<500 ───────
print("\n== HISTORY (lum>45, x>1020, y<500) ==")
sub_h = (lum > 45).copy()
sub_h[:, :1020] = False
sub_h[500:, :] = False
# exclure pentagramme pixels (qui débordent)
rows = sub_h.sum(axis=1)
cols = sub_h.sum(axis=0)
rys = np.where(rows > 10)[0]
cxs = np.where(cols > 10)[0]
if len(rys) and len(cxs):
    show("hist_lum", (cxs.min(), rys.min(), cxs.max()-cxs.min()+1, rys.max()-rys.min()+1))

# Detection des cellules dans HISTORY : scan par y
print("\n  Profil vertical HISTORY (somme colonne x=1030..1380) :")
col_profile = (lum[:500, 1030:1380] > 45).sum(axis=1)
# Trouver les pics (lignes de cadre horizontal)
from itertools import groupby
peaks_y = []
threshold = 30
in_peak = False
start = 0
for y in range(len(col_profile)):
    if col_profile[y] > threshold and not in_peak:
        in_peak = True
        start = y
    elif col_profile[y] <= threshold and in_peak:
        in_peak = False
        peaks_y.append((start, y - 1))
if in_peak:
    peaks_y.append((start, len(col_profile) - 1))
for i, (a, b) in enumerate(peaks_y[:15]):
    print(f"    pic y#{i}: {a}..{b} (ratio {a/H:.3f}..{b/H:.3f})")

# Detection des cellules dans HISTORY : scan par x
print("\n  Profil horizontal HISTORY (somme ligne y=30..490) :")
row_profile = (lum[30:490, 1000:1408] > 45).sum(axis=0)
peaks_x = []
threshold = 30
in_peak = False
start = 0
for x in range(len(row_profile)):
    if row_profile[x] > threshold and not in_peak:
        in_peak = True
        start = x
    elif row_profile[x] <= threshold and in_peak:
        in_peak = False
        peaks_x.append((start + 1000, x - 1 + 1000))
if in_peak:
    peaks_x.append((start + 1000, len(row_profile) - 1 + 1000))
for i, (a, b) in enumerate(peaks_x[:15]):
    print(f"    pic x#{i}: {a}..{b} (ratio {a/W:.3f}..{b/W:.3f})")

# ── CAPSULE gauche : détection par bord clair ───────────────────────────────
print("\n== CAPSULE GAUCHE (lum>50, x<310, y 100..260) ==")
sub_c = (lum > 50).copy()
sub_c[:, 310:] = False
sub_c[:100, :] = False
sub_c[260:, :] = False
rows = sub_c.sum(axis=1)
cols = sub_c.sum(axis=0)
rys = np.where(rows > 3)[0]
cxs = np.where(cols > 3)[0]
if len(rys) and len(cxs):
    show("capsule_lum", (cxs.min(), rys.min(), cxs.max()-cxs.min()+1, rys.max()-rys.min()+1))
