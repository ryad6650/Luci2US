"""Central theme constants + asset path helpers for Luci2US PySide6 UI.

Two palettes cohabit here:
- legacy "Rune Forge" gold/bronze (COLOR_*) — used by older components.
- design-handoff_scan "variation D" magenta/warm-brown (D.*) — used by
  the redesigned Scan shell (title bar, sidebar, scan page).
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
SIZE_APP_MIN_H      = 900
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


# ── Design tokens (variation D — magenta warm-dark) ──────────────────────
# Mirror of design_handoff_scan/variation-d.jsx + README.md tokens.
# Use these for the new Scan shell; keep legacy COLOR_* for older widgets.
class D:
    # Base background — Dark Slate (gris-bleu très foncé, cf. maquette Scan)
    BG          = "#1a1d24"
    BG_GRAD_HI  = "#232730"   # radial 12% 0%
    BG_GRAD_LO  = "#1f232c"   # radial 100% 100%

    # Panels — un cran plus clair que le fond pour la carte glass.
    PANEL       = "#232730"                       # cards
    PANEL_2     = "rgba(40, 46, 58, 0.70)"        # inner panels
    PANEL_FLAT  = "#232730"                       # fallback solid
    STAT_BG     = "rgba(255, 255, 255, 0.04)"    # session stat cell
    BORDER      = "rgba(255, 255, 255, 0.08)"
    BORDER_STR  = "rgba(255, 255, 255, 0.14)"
    SIDEBAR_BG  = "#15171c"
    TITLEBAR_BG = "#15171c"

    # Text
    FG          = "#f5ecef"
    FG_DIM      = "#c2a7af"
    FG_MUTE     = "#7a6168"

    # Accent rose magenta
    ACCENT      = "#f0689a"
    ACCENT_2    = "#d93d7a"
    ACCENT_DIM  = "rgba(240, 104, 154, 0.14)"
    ACCENT_BG   = "rgba(240, 104, 154, 0.08)"

    # Semantic
    OK          = "#5dd39e"   # keep (green)
    ERR         = "#ef6461"   # sell (red)
    WARN        = "#f4c05a"
    INFO        = "#9dd9ff"

    # Typography
    FONT_UI     = "Inter"
    FONT_MONO   = "JetBrains Mono"

    # Shell sizes
    TITLEBAR_H  = 36
    SIDEBAR_W   = 188


# Colours by rune set (for RuneGlyph placeholder tint + header accents).
# Keys are the French set names used on models.Rune.set.
SETS_COLOR: dict[str, str] = {
    "Violent":       "#b892ff",
    "Will":          "#9dd9ff",
    "Rapide":        "#5dd1e8",   # Swift
    "Desespoir":     "#7d7287",   # Despair
    "Rage":          "#e86161",
    "Fatal":         "#f4a74a",
    "Energie":       "#f0c949",   # Energy
    "Lame":          "#e86161",   # Blade
    "Concentration": "#ffb4a2",   # Focus
    "Garde":         "#7ea6ff",   # Guard
    "Endurance":     "#b0a896",   # Endure
    "Vengeance":     "#e8a0c4",
    "Nemesis":       "#c09dff",
    "Vampire":       "#b8425a",
    "Destruction":   "#ff8a5a",
    "Combat":        "#f0b070",
    "Determination": "#a0c8a0",
    "Amelioration":  "#e8c488",
    "Precision":     "#8eb4ff",
    "Tolerance":     "#b0d48a",
    "Intangible":    "#c0c0d8",
    "Sceau":         "#d8b0ff",
    "Bouclier":      "#8ad0d0",
}


def set_color(set_fr: str) -> str:
    """Return the accent colour for a rune set (French name) — falls back to ACCENT."""
    return SETS_COLOR.get(set_fr, D.ACCENT)
