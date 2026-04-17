"""Download swarfarm set logos + mana.png + rune.png into assets/swarfarm/.

Run once after checkout: `python scripts/fetch_swarfarm_assets.py`
"""
from __future__ import annotations
import os
import sys
import urllib.request

BASE = "https://raw.githubusercontent.com/swarfarm/swarfarm/master/herders/static/herders/images"
ROOT = os.path.join(os.path.dirname(__file__), "..", "assets", "swarfarm")

# Filenames match the SETS_EN list in models.py, lowercased
SET_LOGOS = [
    "violent", "will", "swift", "despair", "rage", "fatal",
    "energy", "blade", "focus", "guard", "endure",
    "revenge", "nemesis", "vampire", "destroy", "fight",
    "determination", "enhance", "accuracy", "tolerance",
    "intangible", "seal", "shield",
]


def download(url: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        print(f"  skip (exists): {dst}")
        return
    print(f"  GET {url}")
    with urllib.request.urlopen(url) as r, open(dst, "wb") as f:
        f.write(r.read())


def main() -> int:
    for s in SET_LOGOS:
        download(f"{BASE}/runes/{s}.png", os.path.join(ROOT, "runes", f"{s}.png"))
    download(f"{BASE}/items/mana.png", os.path.join(ROOT, "icons", "mana.png"))
    download(f"{BASE}/icons/rune.png", os.path.join(ROOT, "icons", "rune.png"))
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
