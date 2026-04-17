"""Central theme constants + asset path helpers for Luci2US PySide6 UI.

Mirror of scan-page-v13.html CSS values. If a value is changed here it
must match v13 or the reverse. v13 is the source of truth.
"""
from __future__ import annotations
import os
from models import SET_FR_TO_EN

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ASSETS = os.path.join(_ROOT, "assets", "swarfarm")

# ── Colors (hex, matches CSS) ────────────────────────────────────────────
COLOR_BG_APP        = "#0a0604"
COLOR_BG_FRAME      = "#120a05"
COLOR_BORDER_FRAME  = "#5a3d1f"
COLOR_BG_GRAD_HI    = "#1a0f07"
COLOR_BG_GRAD_LO    = "#120a05"
COLOR_SIDEBAR_BORDER = "#3d2818"

COLOR_GOLD          = "#e8c96a"
COLOR_GOLD_TITLE    = "#e8b040"
COLOR_BRONZE        = "#c67032"
COLOR_BRONZE_DARK   = "#8b4a1f"
COLOR_BRONZE_LIGHT  = "#e8a050"
COLOR_EMBER         = "#f5a030"

COLOR_TEXT_MAIN     = "#f0e6d0"
COLOR_TEXT_SUB      = "#ddd0b8"
COLOR_TEXT_DIM      = "#9ca3af"
COLOR_TEXT_SET      = "#9cc848"

COLOR_KEEP          = "#8ec44a"
COLOR_POWERUP       = "#f5a030"
COLOR_SELL          = "#d84a3a"

COLOR_MANA_BG       = "#5a2e14"
COLOR_MANA_BORDER   = "#7d3e1a"
COLOR_GRADE_LEGEND  = "#a05a2a"
COLOR_GRADE_LEGEND_B = "#c06838"
COLOR_GRADE_HERO    = "#8a3aab"
COLOR_GRADE_HERO_B  = "#d06cff"

# ── Sizes ────────────────────────────────────────────────────────────────
SIZE_SIDEBAR_W      = 170
SIZE_HISTORY_W      = 230
SIZE_HISTORY_MAX_H  = 470
SIZE_APP_MAX_W      = 1200
SIZE_APP_MIN_H      = 620
SIZE_RUNE_ICON_HIST = 36
SIZE_RUNE_ICON_CARD = 62
SIZE_SCORE_ICON     = 14
SIZE_MANA_ICON      = 12
SIZE_NAV_ICON       = 18

# ── Font stack ───────────────────────────────────────────────────────────
FONT_UI    = "Segoe UI"
FONT_TITLE = "Georgia"

# ── Asset helpers ────────────────────────────────────────────────────────
def asset_set_logo(name_en: str) -> str:
    """Given an English set name (e.g. 'violent'), return its PNG path."""
    return os.path.join(_ASSETS, "runes", f"{name_en.lower()}.png")


def asset_icon(name: str) -> str:
    """'mana' | 'rune' -> absolute path."""
    return os.path.join(_ASSETS, "icons", f"{name}.png")


def set_asset_name(set_fr: str) -> str:
    """Map a French set name from models.SET_FR_TO_EN to its asset filename (lowercase English)."""
    en = SET_FR_TO_EN.get(set_fr, set_fr)
    return en.lower()
