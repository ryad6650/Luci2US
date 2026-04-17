# Scan Page Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a PySide6 Scan page pixel-perfect-matching `scan-page-v13.html`, replacing the existing `auto_tab.py` customtkinter panel, while keeping all bot logic (`evaluator_chain`, `s2us_filter`, `auto_mode`) untouched.

**Architecture:** A new `ui/` package hosts a standalone PySide6 entry point (`scan_app.py`) that opens a `QMainWindow` with a sidebar + Scan page. The Scan page is composed of small, testable widgets (rune icons, history items, rune cards, verdict bars). A `ScanController` bridges the existing `AutoMode` + `EvaluatorChain` (which run on a worker thread) to Qt signals consumed by the view. Swarfarm assets (set logos, mana, score-rune) are bundled locally via a one-shot fetch script.

**Tech Stack:** PySide6 (Qt 6), pytest-qt, Python 3.11+, existing models (`Rune`, `Verdict`, `AutoMode`, `State`).

**Spec :** `docs/superpowers/specs/2026-04-17-scan-page-redesign.md`
**Référence visuelle autoritaire :** `.superpowers/brainstorm/1160-1776439696/content/scan-page-v13.html`

---

## File Structure

### Create
```
ui/
├── __init__.py
├── theme.py                      # Colors, sizes, font stacks, asset paths
├── main_window.py                # QMainWindow with sidebar + content stack
├── sidebar.py                    # Left nav (logo + nav items)
├── widgets/
│   ├── __init__.py
│   ├── background.py             # Paints radial gradient + rune circles + ember animation
│   ├── glow_button.py            # B4 Start button (gradient + pulsing glow)
│   ├── state_indicator.py        # Active/idle dot with pulse
│   ├── rune_icon.py              # Set logo centered in card (36 or 62)
│   ├── mana_badge.py             # Mana icon + value
│   ├── star_row.py               # ★★★★★★ stars
│   └── tag_badge.py              # KEEP / SELL / PWR tag
├── scan/
│   ├── __init__.py
│   ├── scan_page.py              # Orchestrator — receives rune/verdict, dispatches
│   ├── header_bar.py             # Start button + state indicator
│   ├── counters_bar.py           # 4 compteurs (total, kept, sold, pwrup)
│   ├── history_item.py           # One row of history
│   ├── history_list.py           # QScrollArea of history items
│   ├── rune_card.py              # Rune card (title, body, subs, set bonus)
│   └── verdict_bar.py            # KEEP/PWR/SELL badge + Score/SWOP/S2US
└── controllers/
    ├── __init__.py
    └── scan_controller.py        # Bridges AutoMode threads -> Qt signals

scripts/
└── fetch_swarfarm_assets.py      # Download swarfarm set logos + mana.png + rune.png

assets/swarfarm/                   # Populated by fetch script (gitignored or committed)
├── runes/                        # {violent,swift,...}.png (23 sets)
└── icons/                        # mana.png, rune.png

scan_app.py                        # PySide6 entrypoint (separate from app.py CTk)

tests/ui/
├── __init__.py
├── conftest.py                   # pytest-qt fixtures
├── test_theme.py
├── test_rune_icon.py
├── test_mana_badge.py
├── test_tag_badge.py
├── test_history_item.py
├── test_counters_bar.py
├── test_verdict_bar.py
├── test_rune_card.py
├── test_scan_page.py
└── test_scan_controller.py
```

### Modify
- `requirements.txt` — add `PySide6>=6.6`, `pytest-qt>=4.2`
- `.gitignore` — add `assets/swarfarm/` (populated by script, not versioned)

### Untouched
- `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `swex_bridge.py`, `models.py`, `history_db.py`, `powerup_simulator.py`, `profile_loader.py`
- `app.py`, `auto_tab.py`, `profile_tab.py`, `settings_tab.py`, `history_tab.py`, `stats_tab.py` (current CTk app continues to work in parallel)

---

### Task 1: Setup dependencies and package skeleton

**Files:**
- Modify: `requirements.txt`
- Create: `ui/__init__.py`, `ui/widgets/__init__.py`, `ui/scan/__init__.py`, `ui/controllers/__init__.py`
- Create: `tests/ui/__init__.py`, `tests/ui/conftest.py`
- Modify: `.gitignore`

- [ ] **Step 1: Add deps to `requirements.txt`**

Append:
```
PySide6>=6.6
pytest-qt>=4.2
```

- [ ] **Step 2: Install**

Run: `pip install -r requirements.txt`
Expected: PySide6 and pytest-qt installed without errors.

- [ ] **Step 3: Create empty package files**

`ui/__init__.py`, `ui/widgets/__init__.py`, `ui/scan/__init__.py`, `ui/controllers/__init__.py`, `tests/ui/__init__.py` — all empty.

- [ ] **Step 4: Write `tests/ui/conftest.py`**

```python
"""Shared pytest-qt fixtures for UI tests."""
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app
```

- [ ] **Step 5: Update `.gitignore`**

Append:
```
assets/swarfarm/
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt ui/ tests/ui/__init__.py tests/ui/conftest.py .gitignore
git commit -m "feat(ui): scaffold PySide6 package + pytest-qt"
```

---

### Task 2: Fetch swarfarm assets

**Files:**
- Create: `scripts/fetch_swarfarm_assets.py`

- [ ] **Step 1: Write the fetch script**

```python
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
```

- [ ] **Step 2: Run the script**

Run: `python scripts/fetch_swarfarm_assets.py`
Expected: `assets/swarfarm/runes/*.png` (23 files) + `assets/swarfarm/icons/{mana,rune}.png` downloaded.

- [ ] **Step 3: Verify count**

Run: `ls assets/swarfarm/runes | wc -l && ls assets/swarfarm/icons`
Expected: `23` and `mana.png rune.png`.

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch_swarfarm_assets.py
git commit -m "feat(ui): asset fetch script for swarfarm logos"
```

---

### Task 3: Theme constants

**Files:**
- Create: `ui/theme.py`
- Create: `tests/ui/test_theme.py`

- [ ] **Step 1: Write the failing test**

```python
import os
from ui import theme


def test_colors_exposed():
    assert theme.COLOR_GOLD == "#e8c96a"
    assert theme.COLOR_BRONZE == "#c67032"
    assert theme.COLOR_KEEP == "#8ec44a"
    assert theme.COLOR_POWERUP == "#f5a030"
    assert theme.COLOR_SELL == "#d84a3a"


def test_asset_paths_resolve():
    assert os.path.isfile(theme.asset_set_logo("violent"))
    assert os.path.isfile(theme.asset_icon("mana"))
    assert os.path.isfile(theme.asset_icon("rune"))


def test_set_fr_to_asset_name():
    # i18n maps "Violent" (FR) -> "violent.png" filename
    assert theme.set_asset_name("Violent") == "violent"
    assert theme.set_asset_name("Rapide") == "swift"
    assert theme.set_asset_name("Endurance") == "endure"
```

- [ ] **Step 2: Run the test — expect FAIL**

Run: `pytest tests/ui/test_theme.py -v`
Expected: FAIL (module ui.theme not found).

- [ ] **Step 3: Implement `ui/theme.py`**

```python
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
```

- [ ] **Step 4: Run the test — expect PASS**

Run: `pytest tests/ui/test_theme.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ui/theme.py tests/ui/test_theme.py
git commit -m "feat(ui): theme constants + asset path helpers"
```

---

### Task 4: RuneIcon widget

**Files:**
- Create: `ui/widgets/rune_icon.py`
- Create: `tests/ui/test_rune_icon.py`

- [ ] **Step 1: Write the failing test**

```python
import os
import pytest
from PySide6.QtCore import QSize
from ui.widgets.rune_icon import RuneIcon
from ui import theme


def test_default_size_history(qapp):
    w = RuneIcon(size=theme.SIZE_RUNE_ICON_HIST)
    assert w.size() == QSize(36, 36)


def test_set_logo_loads_pixmap(qapp, tmp_path):
    w = RuneIcon(size=36)
    w.set_logo("Violent")  # FR name -> resolves to violent.png
    assert not w._label.pixmap().isNull()


def test_set_logo_unknown_falls_back_to_blank(qapp):
    w = RuneIcon(size=36)
    w.set_logo("NonExistent")
    # No crash; pixmap may be null but widget is intact
    assert w.isVisible() is False  # not yet shown
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_rune_icon.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `ui/widgets/rune_icon.py`**

```python
"""Simple rune icon: just the set logo centered in a fixed-size square."""
from __future__ import annotations
import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

from ui import theme


class RuneIcon(QWidget):
    def __init__(self, size: int = theme.SIZE_RUNE_ICON_HIST, parent=None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(QSize(size, size))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setScaledContents(True)
        layout.addWidget(self._label)

    def set_logo(self, set_fr: str) -> None:
        path = theme.asset_set_logo(theme.set_asset_name(set_fr))
        if os.path.isfile(path):
            self._label.setPixmap(QPixmap(path))
        else:
            self._label.clear()
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_rune_icon.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ui/widgets/rune_icon.py tests/ui/test_rune_icon.py
git commit -m "feat(ui): RuneIcon widget (set logo in fixed square)"
```

---

### Task 5: ManaBadge widget

**Files:**
- Create: `ui/widgets/mana_badge.py`
- Create: `tests/ui/test_mana_badge.py`

- [ ] **Step 1: Write the failing test**

```python
from ui.widgets.mana_badge import ManaBadge


def test_initial_value(qapp):
    w = ManaBadge()
    assert w._value_label.text() == "0"


def test_set_value(qapp):
    w = ManaBadge()
    w.set_value(65)
    assert w._value_label.text() == "65"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_mana_badge.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `ui/widgets/mana_badge.py`**

```python
"""Mana value badge: mana.png icon + integer value, pill background."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from ui import theme


class ManaBadge(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background:{theme.COLOR_MANA_BG}; color:{theme.COLOR_TEXT_SUB};"
            f"border:1px solid {theme.COLOR_MANA_BORDER}; border-radius:3px;"
            f"font-size:10px; font-weight:600;"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 8, 2)
        lay.setSpacing(4)

        icon = QLabel()
        icon.setFixedSize(QSize(theme.SIZE_MANA_ICON, theme.SIZE_MANA_ICON))
        icon.setPixmap(QPixmap(theme.asset_icon("mana")))
        icon.setScaledContents(True)
        lay.addWidget(icon)

        self._value_label = QLabel("0")
        self._value_label.setAlignment(Qt.AlignVCenter)
        lay.addWidget(self._value_label)

    def set_value(self, v: int) -> None:
        self._value_label.setText(str(v))
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_mana_badge.py -v`
Expected: 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ui/widgets/mana_badge.py tests/ui/test_mana_badge.py
git commit -m "feat(ui): ManaBadge widget"
```

---

### Task 6: TagBadge widget

**Files:**
- Create: `ui/widgets/tag_badge.py`
- Create: `tests/ui/test_tag_badge.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from ui.widgets.tag_badge import TagBadge, TagKind


@pytest.mark.parametrize("kind,expected", [
    (TagKind.KEEP, "KEEP"),
    (TagKind.SELL, "SELL"),
    (TagKind.POWERUP, "PWR"),
])
def test_label_text(qapp, kind, expected):
    w = TagBadge(kind)
    assert w.text() == expected


def test_change_kind(qapp):
    w = TagBadge(TagKind.KEEP)
    w.set_kind(TagKind.SELL)
    assert w.text() == "SELL"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_tag_badge.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `ui/widgets/tag_badge.py`**

```python
"""KEEP / SELL / PWR tag badge — matches .hist-tag in v13."""
from __future__ import annotations
from enum import Enum

from PySide6.QtWidgets import QLabel

from ui import theme


class TagKind(Enum):
    KEEP = "keep"
    SELL = "sell"
    POWERUP = "powerup"


_LABELS = {TagKind.KEEP: "KEEP", TagKind.SELL: "SELL", TagKind.POWERUP: "PWR"}


class TagBadge(QLabel):
    def __init__(self, kind: TagKind, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(0x0004)  # Qt.AlignCenter fallback for static
        self.set_kind(kind)

    def set_kind(self, kind: TagKind) -> None:
        self._kind = kind
        self.setText(_LABELS[kind])
        bg = {
            TagKind.KEEP: theme.COLOR_KEEP,
            TagKind.SELL: theme.COLOR_SELL,
            TagKind.POWERUP: theme.COLOR_POWERUP,
        }[kind]
        fg = "#1a0f07" if kind != TagKind.SELL else "#fff"
        self.setStyleSheet(
            f"background:{bg}; color:{fg};"
            f"font-size:9px; font-weight:800; letter-spacing:.5px;"
            f"padding:3px 6px; border-radius:3px;"
        )
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_tag_badge.py -v`
Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ui/widgets/tag_badge.py tests/ui/test_tag_badge.py
git commit -m "feat(ui): TagBadge (KEEP/SELL/PWR)"
```

---

### Task 7: StarRow widget

**Files:**
- Create: `ui/widgets/star_row.py`

- [ ] **Step 1: Implement directly (trivial)**

```python
"""★ row placed above a rune card icon — matches .rc-stars in v13."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ui import theme


class StarRow(QLabel):
    def __init__(self, count: int = 6, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("★" * count)
        self.setStyleSheet(
            f"color:#f8c040; font-size:9px; letter-spacing:-1.4px;"
            f"background:transparent;"
        )
```

- [ ] **Step 2: Commit**

```bash
git add ui/widgets/star_row.py
git commit -m "feat(ui): StarRow widget"
```

---

### Task 8: StateIndicator (green pulse)

**Files:**
- Create: `ui/widgets/state_indicator.py`
- Create: `tests/ui/test_state_indicator.py`

- [ ] **Step 1: Write the failing test**

```python
from ui.widgets.state_indicator import StateIndicator


def test_default_label(qapp):
    w = StateIndicator()
    assert w._label.text().upper() == "INACTIF"


def test_set_active(qapp):
    w = StateIndicator()
    w.set_active(True)
    assert w._label.text().upper() == "ACTIF"
    assert w._active is True


def test_set_inactive(qapp):
    w = StateIndicator()
    w.set_active(True)
    w.set_active(False)
    assert w._active is False
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_state_indicator.py -v`

- [ ] **Step 3: Implement `ui/widgets/state_indicator.py`**

```python
"""Bot state indicator — dot + label. Green pulsing when active, grey when idle."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from ui import theme


class _Dot(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(14, 14)
        self._opacity = 1.0
        self._color = QColor(theme.COLOR_KEEP)

    def set_color(self, hex_color: str) -> None:
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(QBrush(c))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, 9, 9)

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    opacity = Property(float, get_opacity, set_opacity)


class StateIndicator(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._dot = _Dot()
        self._label = QLabel("INACTIF")
        self._label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:12px; font-weight:600; letter-spacing:.5px;"
        )

        lay.addWidget(self._dot)
        lay.addWidget(self._label)
        lay.addStretch()

        self._anim = QPropertyAnimation(self._dot, b"opacity")
        self._anim.setDuration(1200)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.4)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self._dot.set_color(theme.COLOR_KEEP)
            self._label.setText("ACTIF")
            self._label.setStyleSheet(
                f"color:{theme.COLOR_KEEP}; font-size:12px; font-weight:600; letter-spacing:.5px;"
            )
            self._anim.start()
        else:
            self._anim.stop()
            self._dot.set_color(theme.COLOR_TEXT_DIM)
            self._dot.set_opacity(1.0)
            self._label.setText("INACTIF")
            self._label.setStyleSheet(
                f"color:{theme.COLOR_TEXT_DIM}; font-size:12px; font-weight:600; letter-spacing:.5px;"
            )
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_state_indicator.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ui/widgets/state_indicator.py tests/ui/test_state_indicator.py
git commit -m "feat(ui): StateIndicator with pulsing dot"
```

---

### Task 9: GlowButton (Start B4)

**Files:**
- Create: `ui/widgets/glow_button.py`

- [ ] **Step 1: Implement**

```python
"""Start button — bronze gradient + pulsing glow (B4 direction from v13)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect

from ui import theme


class GlowButton(QPushButton):
    def __init__(self, label: str = "START", parent=None) -> None:
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.COLOR_BRONZE},
                    stop:1 {theme.COLOR_BRONZE_DARK}
                );
                color:#fff3d0;
                font-weight:800; font-size:13px; letter-spacing:1.5px;
                padding:10px 26px;
                border:1px solid {theme.COLOR_BRONZE_LIGHT};
                border-radius:6px;
            }}
            QPushButton:hover {{ background: {theme.COLOR_BRONZE_LIGHT}; }}
            QPushButton:pressed {{ padding-top:11px; padding-bottom:9px; }}
            """
        )

        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(18)
        self._glow.setOffset(0, 0)
        self._glow.setColor(QColor(245, 160, 48, 90))
        self.setGraphicsEffect(self._glow)

        self._anim = QPropertyAnimation(self._glow, b"blurRadius")
        self._anim.setDuration(2200)
        self._anim.setStartValue(18)
        self._anim.setKeyValueAt(0.5, 26)
        self._anim.setEndValue(18)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.start()
```

- [ ] **Step 2: Commit**

```bash
git add ui/widgets/glow_button.py
git commit -m "feat(ui): GlowButton with pulsing shadow (Start B4)"
```

---

### Task 10: Background widget (gradient + circles + embers)

**Files:**
- Create: `ui/widgets/background.py`

- [ ] **Step 1: Implement**

```python
"""Rune Forge background: radial gradients, runic circles, animated embers."""
from __future__ import annotations
import random

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, Property
from PySide6.QtGui import QPainter, QRadialGradient, QLinearGradient, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


class _Ember(QWidget):
    """Single floating amber dot."""
    def __init__(self, size: int, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._offset = 0.0

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(245, 160, 48, 200)
        p.setBrush(QBrush(c))
        p.setPen(Qt.NoPen)
        p.drawEllipse(self.rect())

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, v: float) -> None:
        self._offset = v
        self.move(self.x(), self._base_y + int(v))

    offset = Property(float, get_offset, set_offset)


# Ember seeds (relative position %, size px, delay ms, duration ms)
EMBER_SEEDS = [
    (8, 12, 3, 0, 8000), (22, 35, 2, 2000, 9000), (12, 58, 4, 4000, 6000),
    (42, 18, 2, 1000, 10000), (38, 68, 3, 3000, 8000), (62, 25, 2, 5000, 7000),
    (72, 52, 4, 2000, 9000), (58, 78, 3, 6000, 6000),
    (86, 14, 2, 4000, 8000), (92, 45, 3, 1000, 10000),
]


class BackgroundPane(QWidget):
    """The tab background — draws gradients/circles in paintEvent, hosts embers as children."""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._embers: list[_Ember] = []
        self._anims: list[QPropertyAnimation] = []
        for _ in EMBER_SEEDS:
            e = _Ember(1, self)
            self._embers.append(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        w, h = self.width(), self.height()
        for ember, (px, py, size, delay, dur) in zip(self._embers, EMBER_SEEDS):
            ember.setFixedSize(size, size)
            x = int(w * px / 100)
            y = int(h * py / 100)
            ember._base_y = y
            ember.move(x, y)
        # (Re)start animations once on first resize
        if not self._anims:
            for ember, (_, _, _, delay, dur) in zip(self._embers, EMBER_SEEDS):
                a = QPropertyAnimation(ember, b"offset")
                a.setStartValue(0.0)
                a.setKeyValueAt(0.5, -20.0)
                a.setEndValue(0.0)
                a.setDuration(dur)
                a.setLoopCount(-1)
                a.setEasingCurve(QEasingCurve.InOutSine)
                a.start()
                self._anims.append(a)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        # Linear base
        g = QLinearGradient(0, 0, 0, r.height())
        g.setColorAt(0.0, QColor("#1a0f07"))
        g.setColorAt(1.0, QColor("#120a05"))
        p.fillRect(r, QBrush(g))

        # Radial gold (top-left)
        rg1 = QRadialGradient(r.width() * 0.18, r.height() * 0.28, r.width() * 0.45)
        rg1.setColorAt(0.0, QColor(232, 176, 64, 23))
        rg1.setColorAt(1.0, Qt.transparent)
        p.fillRect(r, QBrush(rg1))

        # Radial orange (bottom-right)
        rg2 = QRadialGradient(r.width() * 0.82, r.height() * 0.78, r.width() * 0.50)
        rg2.setColorAt(0.0, QColor(200, 80, 40, 28))
        rg2.setColorAt(1.0, Qt.transparent)
        p.fillRect(r, QBrush(rg2))

        # Circles
        pen = QPen(QColor(232, 176, 64, 31))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(-80, -80, 280, 280))

        pen2 = QPen(QColor(200, 80, 40, 26))
        pen2.setWidth(1)
        p.setPen(pen2)
        p.drawEllipse(QRectF(r.width() - 220, r.height() - 220, 320, 320))

        # Runic symbols (big translucent glyphs)
        p.setFont(QFont("Georgia", 90, QFont.Bold))
        p.setPen(QColor(232, 176, 64, 10))
        p.drawText(30, 110, "Ж")
        p.setPen(QColor(200, 80, 40, 13))
        p.drawText(r.width() - 140, r.height() - 30, "§")
```

- [ ] **Step 2: Commit**

```bash
git add ui/widgets/background.py
git commit -m "feat(ui): BackgroundPane — gradients, circles, embers"
```

---

### Task 11: HistoryItem widget

**Files:**
- Create: `ui/scan/history_item.py`
- Create: `tests/ui/test_history_item.py`

- [ ] **Step 1: Write the failing test**

```python
from models import Rune, SubStat, Verdict
from ui.scan.history_item import HistoryItem
from ui.widgets.tag_badge import TagKind


def _make_rune() -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=9,
        main_stat=SubStat("VIT", 19),
        prefix=None, substats=[],
    )


def test_displays_set_and_level(qapp):
    r = _make_rune()
    v = Verdict(decision="KEEP", source="s2us", reason="")
    w = HistoryItem(r, v)
    assert "Violent" in w._name_label.text()
    assert "+9" in w._sub_label.text()


def test_tag_matches_verdict(qapp):
    r = _make_rune()
    v = Verdict(decision="SELL", source="s2us", reason="")
    w = HistoryItem(r, v)
    assert w._tag.text() == "SELL"


def test_tag_powerup(qapp):
    r = _make_rune()
    v = Verdict(decision="PWR-UP", source="s2us", reason="")
    w = HistoryItem(r, v)
    assert w._tag.text() == "PWR"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_history_item.py -v`

- [ ] **Step 3: Implement `ui/scan/history_item.py`**

```python
"""One history row: 36×36 rune icon · set name + level/stat · verdict tag."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout

from models import Rune, Verdict
from ui import theme
from ui.widgets.rune_icon import RuneIcon
from ui.widgets.tag_badge import TagBadge, TagKind


_VERDICT_TO_KIND = {
    "KEEP": TagKind.KEEP,
    "SELL": TagKind.SELL,
    "PWR-UP": TagKind.POWERUP,
    "POWERUP": TagKind.POWERUP,
}


def _main_stat_str(rune: Rune) -> str:
    ms = rune.main_stat
    suffix = "%" if ms.type.endswith("%") else ""
    return f"{ms.type.rstrip('%')} +{int(ms.value)}{suffix}"


class HistoryItem(QWidget):
    def __init__(self, rune: Rune, verdict: Verdict, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background:transparent; border-bottom:1px solid #2d1f14;"
        )

        grid = QGridLayout(self)
        grid.setContentsMargins(7, 6, 7, 6)
        grid.setHorizontalSpacing(8)
        grid.setColumnStretch(1, 1)

        icon = RuneIcon(size=theme.SIZE_RUNE_ICON_HIST)
        icon.set_logo(rune.set)
        grid.addWidget(icon, 0, 0, 2, 1)

        info_box = QWidget()
        info_lay = QVBoxLayout(info_box)
        info_lay.setContentsMargins(0, 0, 0, 0)
        info_lay.setSpacing(1)

        self._name_label = QLabel(f"{rune.set} ({rune.slot})")
        self._name_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:11px; font-weight:600;"
        )
        info_lay.addWidget(self._name_label)

        self._sub_label = QLabel(
            f"<span style='color:{theme.COLOR_GOLD};font-weight:600'>+{rune.level}</span>"
            f" · {_main_stat_str(rune)}"
        )
        self._sub_label.setTextFormat(Qt.RichText)
        self._sub_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
        )
        info_lay.addWidget(self._sub_label)

        grid.addWidget(info_box, 0, 1, 2, 1)

        kind = _VERDICT_TO_KIND.get(verdict.decision, TagKind.SELL)
        self._tag = TagBadge(kind)
        grid.addWidget(self._tag, 0, 2, 2, 1, Qt.AlignVCenter | Qt.AlignRight)
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_history_item.py -v`
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add ui/scan/history_item.py tests/ui/test_history_item.py
git commit -m "feat(ui): HistoryItem row"
```

---

### Task 12: HistoryList widget

**Files:**
- Create: `ui/scan/history_list.py`

- [ ] **Step 1: Implement**

```python
"""Scrollable vertical list of HistoryItem — newest on top, capped to MAX items."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout

from models import Rune, Verdict
from ui import theme
from ui.scan.history_item import HistoryItem


MAX_ITEMS = 50


class HistoryList(QScrollArea):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFixedWidth(theme.SIZE_HISTORY_W)
        self.setMaximumHeight(theme.SIZE_HISTORY_MAX_H)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"""
            QScrollArea {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(45,31,20,0.85), stop:1 rgba(26,15,7,0.9));
                border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:5px;
            }}
            QScrollBar:vertical {{ width:5px; background:#1a0f07; }}
            QScrollBar::handle:vertical {{ background:#5a3d1f; border-radius:3px; }}
            """
        )

        self._content = QWidget()
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(6, 6, 6, 6)
        self._lay.setSpacing(0)
        self._lay.addStretch()
        self.setWidget(self._content)

    def add(self, rune: Rune, verdict: Verdict) -> None:
        item = HistoryItem(rune, verdict)
        self._lay.insertWidget(0, item)
        # Cap: remove items above MAX (stretch is the last child)
        while self._lay.count() - 1 > MAX_ITEMS:
            old = self._lay.takeAt(self._lay.count() - 2)
            if old and old.widget():
                old.widget().deleteLater()

    def clear(self) -> None:
        while self._lay.count() > 1:  # keep the stretch
            old = self._lay.takeAt(0)
            if old and old.widget():
                old.widget().deleteLater()
```

- [ ] **Step 2: Commit**

```bash
git add ui/scan/history_list.py
git commit -m "feat(ui): HistoryList scroll area with cap"
```

---

### Task 13: CountersBar widget

**Files:**
- Create: `ui/scan/counters_bar.py`
- Create: `tests/ui/test_counters_bar.py`

- [ ] **Step 1: Write the failing test**

```python
from ui.scan.counters_bar import CountersBar


def test_initial_all_zero(qapp):
    w = CountersBar()
    assert w._total.text() == "0"
    assert w._kept.text() == "0"
    assert w._sold.text() == "0"
    assert w._pwr.text() == "0"


def test_update(qapp):
    w = CountersBar()
    w.update_counts(total=10, kept=4, sold=5, pwrup=1)
    assert w._total.text() == "10"
    assert w._kept.text() == "4"
    assert w._sold.text() == "5"
    assert w._pwr.text() == "1"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_counters_bar.py -v`

- [ ] **Step 3: Implement `ui/scan/counters_bar.py`**

```python
"""4-cell counters strip: Total · Kept · Sold · PwrUp."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame

from ui import theme


class _Cell(QWidget):
    def __init__(self, label: str, is_last: bool = False) -> None:
        super().__init__()
        self.setStyleSheet(
            f"background:transparent;"
            + ("" if is_last else f"border-right:1px solid #3d2818;")
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(3)

        k = QLabel(label)
        k.setAlignment(Qt.AlignCenter)
        k.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
            f"text-transform:uppercase; letter-spacing:1px;"
        )
        lay.addWidget(k)

        self.value = QLabel("0")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:20px; font-weight:700;"
        )
        lay.addWidget(self.value)


class CountersBar(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            CountersBar {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(45,31,20,0.85), stop:1 rgba(26,15,7,0.9));
                border:1px solid {theme.COLOR_BORDER_FRAME};
                border-radius:5px;
            }}
            """
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(0)

        cells = [
            _Cell("Total"), _Cell("Kept"), _Cell("Sold"),
            _Cell("PwrUp", is_last=True),
        ]
        for c in cells:
            lay.addWidget(c, 1)

        self._total, self._kept, self._sold, self._pwr = (c.value for c in cells)

    def update_counts(self, total: int, kept: int, sold: int, pwrup: int) -> None:
        self._total.setText(str(total))
        self._kept.setText(str(kept))
        self._sold.setText(str(sold))
        self._pwr.setText(str(pwrup))
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_counters_bar.py -v`

- [ ] **Step 5: Commit**

```bash
git add ui/scan/counters_bar.py tests/ui/test_counters_bar.py
git commit -m "feat(ui): CountersBar (4 cells)"
```

---

### Task 14: VerdictBar widget

**Files:**
- Create: `ui/scan/verdict_bar.py`
- Create: `tests/ui/test_verdict_bar.py`

- [ ] **Step 1: Write the failing test**

```python
from ui.scan.verdict_bar import VerdictBar, VerdictKind


def test_defaults(qapp):
    w = VerdictBar()
    assert w._badge.text() == "KEEP"
    assert "Score" in w._score_label.text()


def test_update(qapp):
    w = VerdictBar()
    w.update_verdict(
        kind=VerdictKind.POWERUP,
        score=184,
        swop=(84.1, 118.6),
        s2us=(108.2, 152.0),
    )
    assert w._badge.text() == "PWR-UP"
    assert "184" in w._score_label.text()
    assert "84.1" in w._eff_label.text()
    assert "108.2" in w._eff_label.text()
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_verdict_bar.py -v`

- [ ] **Step 3: Implement `ui/scan/verdict_bar.py`**

```python
"""Verdict bar under each rune-card: badge + Score + SWOP + S2US."""
from __future__ import annotations
from enum import Enum

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

from ui import theme


class VerdictKind(Enum):
    KEEP = "keep"
    POWERUP = "powerup"
    SELL = "sell"


_LABELS = {VerdictKind.KEEP: "KEEP", VerdictKind.POWERUP: "PWR-UP", VerdictKind.SELL: "SELL"}
_COLORS = {
    VerdictKind.KEEP: (theme.COLOR_KEEP, "#1a0f07"),
    VerdictKind.POWERUP: (theme.COLOR_POWERUP, "#1a0f07"),
    VerdictKind.SELL: (theme.COLOR_SELL, "#fff"),
}


class VerdictBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._kind = VerdictKind.KEEP

        outer = QHBoxLayout(self)
        outer.setContentsMargins(11, 8, 11, 8)
        outer.setSpacing(10)

        self._badge = QLabel("KEEP")
        self._badge.setAlignment(Qt.AlignCenter)
        outer.addWidget(self._badge)

        eff_box = QWidget()
        eff_lay = QVBoxLayout(eff_box)
        eff_lay.setContentsMargins(0, 0, 0, 0)
        eff_lay.setSpacing(2)

        score_row = QWidget()
        srl = QHBoxLayout(score_row)
        srl.setContentsMargins(0, 0, 0, 0)
        srl.setSpacing(6)
        icon = QLabel()
        icon.setFixedSize(QSize(theme.SIZE_SCORE_ICON, theme.SIZE_SCORE_ICON))
        icon.setPixmap(QPixmap(theme.asset_icon("rune")))
        icon.setScaledContents(True)
        srl.addWidget(icon)
        self._score_label = QLabel("Score 0")
        self._score_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:11px; font-weight:700;"
        )
        srl.addWidget(self._score_label)
        srl.addStretch()
        eff_lay.addWidget(score_row)

        self._eff_label = QLabel(
            f"<b style='color:{theme.COLOR_GOLD}'>SWOP</b> —<br>"
            f"<b style='color:{theme.COLOR_GOLD}'>S2US</b> —"
        )
        self._eff_label.setTextFormat(Qt.RichText)
        self._eff_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px; line-height:1.5;"
        )
        eff_lay.addWidget(self._eff_label)

        outer.addWidget(eff_box, 1)

        self._repaint_style()

    def _repaint_style(self) -> None:
        bg, fg = _COLORS[self._kind]
        self.setStyleSheet(
            f"""
            VerdictBar {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(45,31,20,0.85), stop:1 rgba(26,15,7,0.9));
                border:1px solid {bg};
                border-radius:5px;
            }}
            """
        )
        self._badge.setText(_LABELS[self._kind])
        self._badge.setStyleSheet(
            f"background:{bg}; color:{fg}; font-weight:900;"
            f"font-size:11px; padding:4px 10px; border-radius:3px; letter-spacing:1px;"
        )

    def update_verdict(self, kind: VerdictKind, score: int,
                       swop: tuple[float, float], s2us: tuple[float, float]) -> None:
        self._kind = kind
        self._score_label.setText(f"Score {score}")
        self._eff_label.setText(
            f"<b style='color:{theme.COLOR_GOLD}'>SWOP</b> {swop[0]:.1f}% (max {swop[1]:.1f}%)<br>"
            f"<b style='color:{theme.COLOR_GOLD}'>S2US</b> {s2us[0]:.1f}% (max {s2us[1]:.1f}%)"
        )
        self._repaint_style()
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_verdict_bar.py -v`

- [ ] **Step 5: Commit**

```bash
git add ui/scan/verdict_bar.py tests/ui/test_verdict_bar.py
git commit -m "feat(ui): VerdictBar with Score + SWOP + S2US"
```

---

### Task 15: RuneCard widget

**Files:**
- Create: `ui/scan/rune_card.py`
- Create: `tests/ui/test_rune_card.py`

- [ ] **Step 1: Write the failing test**

```python
from models import Rune, SubStat
from ui.scan.rune_card import RuneCard, RuneCardStatus


def _rune() -> Rune:
    return Rune(
        set="Endurance", slot=1, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("ATQ", 22),
        prefix=None,
        substats=[
            SubStat("PV%", 6), SubStat("ATQ%", 6),
            SubStat("VIT", 6), SubStat("PRE", 6),
        ],
    )


def test_update_populates_fields(qapp):
    w = RuneCard(status=RuneCardStatus.KEEP)
    w.update_rune(_rune(), mana=65)
    assert "Endurance" in w._title.text()
    assert "ATQ +22" in w._main.text()
    assert w._mana._value_label.text() == "65"
    assert len(w._sub_labels) == 4
    assert "PV +6%" in w._sub_labels[0].text()


def test_status_switch(qapp):
    w = RuneCard(status=RuneCardStatus.KEEP)
    w.set_status(RuneCardStatus.POWERUP)
    assert w._status == RuneCardStatus.POWERUP
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_rune_card.py -v`

- [ ] **Step 3: Implement `ui/scan/rune_card.py`**

```python
"""Large rune card: title, 6★ row + icon, main stat, grade + mana, subs, set bonus."""
from __future__ import annotations
from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
)

from models import Rune
from ui import theme
from ui.widgets.rune_icon import RuneIcon
from ui.widgets.mana_badge import ManaBadge
from ui.widgets.star_row import StarRow


class RuneCardStatus(Enum):
    KEEP = "keep"
    POWERUP = "powerup"
    SELL = "sell"


_STATUS_BORDER = {
    RuneCardStatus.KEEP: theme.COLOR_KEEP,
    RuneCardStatus.POWERUP: theme.COLOR_POWERUP,
    RuneCardStatus.SELL: theme.COLOR_SELL,
}


_GRADE_FR_TO_LABEL = {
    "Legendaire": ("Légendaire", theme.COLOR_GRADE_LEGEND, theme.COLOR_GRADE_LEGEND_B),
    "Heroique":   ("Héroïque",  theme.COLOR_GRADE_HERO,   theme.COLOR_GRADE_HERO_B),
    "Rare":       ("Rare",      "#2e6ea8", "#5aa0d8"),
    "Magique":    ("Magique",   "#2e8a2e", "#55c855"),
    "Normal":     ("Normal",    "#5a5a5a", "#7a7a7a"),
}


def _main_stat_line(r: Rune) -> str:
    suffix = "%" if r.main_stat.type.endswith("%") else ""
    return f"{r.main_stat.type.rstrip('%')} +{int(r.main_stat.value)}{suffix}"


def _sub_line(s) -> str:
    suffix = "%" if s.type.endswith("%") else ""
    return f"{s.type.rstrip('%')} +{int(s.value + (s.grind_value or 0))}{suffix}"


class RuneCard(QFrame):
    def __init__(self, status: RuneCardStatus = RuneCardStatus.KEEP, parent=None) -> None:
        super().__init__(parent)
        self._status = status

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 13, 18, 13)
        outer.setSpacing(6)

        self._title = QLabel("—")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-size:14px; font-weight:700;"
        )
        outer.addWidget(self._title)

        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)

        icon_wrap = QWidget()
        iw_lay = QVBoxLayout(icon_wrap)
        iw_lay.setContentsMargins(0, 0, 0, 0)
        iw_lay.setSpacing(0)
        self._stars = StarRow(6)
        iw_lay.addWidget(self._stars)
        self._icon = RuneIcon(size=theme.SIZE_RUNE_ICON_CARD)
        iw_lay.addWidget(self._icon, 0, Qt.AlignHCenter)
        grid.addWidget(icon_wrap, 0, 0)

        self._main = QLabel("—")
        self._main.setAlignment(Qt.AlignCenter)
        self._main.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:17px; font-weight:600;"
        )
        grid.addWidget(self._main, 0, 1)
        grid.setColumnStretch(1, 1)

        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(3)
        rlay.setAlignment(Qt.AlignRight)
        self._grade = QLabel("—")
        rlay.addWidget(self._grade, 0, Qt.AlignRight)
        self._mana = ManaBadge()
        rlay.addWidget(self._mana, 0, Qt.AlignRight)
        grid.addWidget(right, 0, 2)

        outer.addWidget(body)

        subs_box = QWidget()
        sl = QGridLayout(subs_box)
        sl.setContentsMargins(2, 3, 2, 6)
        sl.setHorizontalSpacing(12)
        self._sub_labels: list[QLabel] = []
        for i in range(4):
            l = QLabel("—")
            l.setStyleSheet(f"color:{theme.COLOR_TEXT_SUB}; font-size:11px;")
            sl.addWidget(l, i // 2, i % 2)
            self._sub_labels.append(l)
        outer.addWidget(subs_box)

        self._setbonus = QLabel("")
        self._setbonus.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SET}; font-size:11px; font-weight:500;"
            f"border-top:1px solid #2d1f14; padding-top:6px;"
        )
        outer.addWidget(self._setbonus)

        self._apply_style()

    def _apply_style(self) -> None:
        border = _STATUS_BORDER[self._status]
        self.setStyleSheet(
            f"""
            RuneCard {{
                background: rgba(26,15,7,0.9);
                border:1px solid {border};
                border-radius:7px;
            }}
            """
        )
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(18)
        glow.setOffset(0, 0)
        c = QColor(border)
        c.setAlpha(100)
        glow.setColor(c)
        self.setGraphicsEffect(glow)

    def set_status(self, status: RuneCardStatus) -> None:
        self._status = status
        self._apply_style()

    def update_rune(self, rune: Rune, mana: int, set_bonus_text: str = "") -> None:
        self._title.setText(f"Rune {rune.set} ({rune.slot})")
        self._icon.set_logo(rune.set)
        self._main.setText(_main_stat_line(rune))
        self._mana.set_value(mana)

        label, bg, border = _GRADE_FR_TO_LABEL.get(
            rune.grade, (rune.grade, theme.COLOR_GRADE_LEGEND, theme.COLOR_GRADE_LEGEND_B)
        )
        self._grade.setText(label)
        self._grade.setStyleSheet(
            f"background:{bg}; color:#f8e8c8; border:1px solid {border};"
            f"font-weight:700; font-size:10px; padding:3px 9px; border-radius:3px;"
        )

        for i, l in enumerate(self._sub_labels):
            if i < len(rune.substats):
                l.setText(_sub_line(rune.substats[i]))
            else:
                l.setText("")

        self._setbonus.setText(set_bonus_text)
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_rune_card.py -v`

- [ ] **Step 5: Commit**

```bash
git add ui/scan/rune_card.py tests/ui/test_rune_card.py
git commit -m "feat(ui): RuneCard widget"
```

---

### Task 16: HeaderBar (Start + StateIndicator)

**Files:**
- Create: `ui/scan/header_bar.py`

- [ ] **Step 1: Implement**

```python
"""Header row: Start button + state indicator."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout

from ui.widgets.glow_button import GlowButton
from ui.widgets.state_indicator import StateIndicator


class HeaderBar(QWidget):
    start_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        self._btn = GlowButton("▶ START")
        self._btn.clicked.connect(self.start_clicked.emit)
        lay.addWidget(self._btn)

        self._state = StateIndicator()
        lay.addWidget(self._state)
        lay.addStretch()

    def set_active(self, active: bool) -> None:
        self._state.set_active(active)
        self._btn.setText("■ STOP" if active else "▶ START")
```

- [ ] **Step 2: Commit**

```bash
git add ui/scan/header_bar.py
git commit -m "feat(ui): HeaderBar (Start + state)"
```

---

### Task 17: Sidebar widget

**Files:**
- Create: `ui/sidebar.py`

- [ ] **Step 1: Implement**

```python
"""Left sidebar — logo + nav items (Scan, Profil, Historique, Stats, Paramètres)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from ui import theme


NAV_ITEMS = [
    ("scan", "Scan"),
    ("profile", "Profil"),
    ("history", "Historique"),
    ("stats", "Stats"),
    ("settings", "Paramètres"),
]


class Sidebar(QWidget):
    nav_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(theme.SIZE_SIDEBAR_W)
        self.setStyleSheet(
            f"""
            Sidebar {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.COLOR_BG_GRAD_HI}, stop:1 {theme.COLOR_BG_GRAD_LO});
                border-right:1px solid {theme.COLOR_SIDEBAR_BORDER};
            }}
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 20, 12, 20)
        lay.setSpacing(4)

        logo = QLabel("LUCI2US<br><span style='font-size:9px;color:#8b6a3d;letter-spacing:3px;font-weight:400'>SW BOT</span>")
        logo.setTextFormat(Qt.RichText)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:20px; font-weight:800; letter-spacing:1px;"
            f"padding:6px 0 22px; border-bottom:1px solid {theme.COLOR_SIDEBAR_BORDER};"
        )
        lay.addWidget(logo)
        lay.addSpacing(14)

        self._buttons: dict[str, QPushButton] = {}
        for key, label in NAV_ITEMS:
            b = QPushButton(label)
            b.setCursor(Qt.PointingHandCursor)
            b.setCheckable(True)
            b.clicked.connect(lambda _checked, k=key: self._on_click(k))
            self._style_button(b, active=False)
            lay.addWidget(b)
            self._buttons[key] = b
        lay.addStretch()

        self.set_active("scan")

    def _style_button(self, b: QPushButton, active: bool) -> None:
        if active:
            b.setStyleSheet(
                f"""
                QPushButton {{
                    text-align:left; padding:10px 12px;
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(198,112,50,0.25), stop:1 transparent);
                    color:{theme.COLOR_GOLD};
                    border:none; border-left:3px solid {theme.COLOR_BRONZE};
                    border-radius:5px; font-size:12px; font-weight:600;
                }}
                """
            )
        else:
            b.setStyleSheet(
                f"""
                QPushButton {{
                    text-align:left; padding:10px 12px;
                    background:transparent; color:{theme.COLOR_TEXT_SUB};
                    border:none; border-left:3px solid transparent;
                    border-radius:5px; font-size:12px; font-weight:500;
                }}
                QPushButton:hover {{ background:rgba(232,201,106,0.06); color:{theme.COLOR_TEXT_MAIN}; }}
                """
            )

    def _on_click(self, key: str) -> None:
        self.set_active(key)
        self.nav_changed.emit(key)

    def set_active(self, key: str) -> None:
        for k, b in self._buttons.items():
            is_active = (k == key)
            b.setChecked(is_active)
            self._style_button(b, is_active)
```

- [ ] **Step 2: Commit**

```bash
git add ui/sidebar.py
git commit -m "feat(ui): Sidebar with nav"
```

---

### Task 18: ScanPage orchestrator

**Files:**
- Create: `ui/scan/scan_page.py`
- Create: `tests/ui/test_scan_page.py`

- [ ] **Step 1: Write the failing test**

```python
from models import Rune, SubStat, Verdict
from ui.scan.scan_page import ScanPage
from ui.scan.rune_card import RuneCardStatus


def _rune(set_name="Violent", decision="KEEP") -> tuple[Rune, Verdict]:
    r = Rune(
        set=set_name, slot=2, stars=6, grade="Heroique", level=9,
        main_stat=SubStat("VIT", 25), prefix=None,
        substats=[SubStat("PV%", 15), SubStat("CC", 9), SubStat("DC", 12), SubStat("PRE", 5)],
    )
    v = Verdict(decision=decision, source="s2us", reason="", score=215)
    return r, v


def test_on_rune_updates_last(qapp):
    page = ScanPage()
    r, v = _rune()
    page.on_rune(r, v, mana=65, swop=(98.3, 112.4), s2us=(127.4, 145.0))
    assert "Violent" in page._last_card._title.text()


def test_counters_increment(qapp):
    page = ScanPage()
    r, v = _rune(decision="KEEP")
    page.on_rune(r, v, mana=10, swop=(0,0), s2us=(0,0))
    r, v = _rune(decision="SELL")
    page.on_rune(r, v, mana=10, swop=(0,0), s2us=(0,0))
    assert page._counters._total.text() == "2"
    assert page._counters._kept.text() == "1"
    assert page._counters._sold.text() == "1"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_scan_page.py -v`

- [ ] **Step 3: Implement `ui/scan/scan_page.py`**

```python
"""Scan page: header + counters + history + last-rune card + best-rune card."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel

from models import Rune, Verdict
from ui import theme
from ui.scan.counters_bar import CountersBar
from ui.scan.header_bar import HeaderBar
from ui.scan.history_list import HistoryList
from ui.scan.rune_card import RuneCard, RuneCardStatus
from ui.scan.verdict_bar import VerdictBar, VerdictKind


_DECISION_TO_STATUS = {
    "KEEP": (RuneCardStatus.KEEP, VerdictKind.KEEP),
    "SELL": (RuneCardStatus.SELL, VerdictKind.SELL),
    "PWR-UP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
    "POWERUP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
}


class ScanPage(QWidget):
    start_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._counts = {"total": 0, "kept": 0, "sold": 0, "pwrup": 0}
        self._best_score: float = -1.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        self._header = HeaderBar()
        self._header.start_clicked.connect(self.start_requested.emit)
        outer.addWidget(self._header)

        self._counters = CountersBar()
        outer.addWidget(self._counters)

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(14)
        main_grid.setVerticalSpacing(6)

        # Labels above each column
        for col, text in enumerate(["Historique", "Dernière rune", "Meilleure rune"]):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
                f"text-transform:uppercase; letter-spacing:1.5px; font-weight:600;"
            )
            main_grid.addWidget(lbl, 0, col)

        self._history = HistoryList()
        main_grid.addWidget(self._history, 1, 0, 3, 1, Qt.AlignTop)

        self._last_card = RuneCard(RuneCardStatus.KEEP)
        self._last_verdict = VerdictBar()
        main_grid.addWidget(self._last_card, 1, 1)
        main_grid.addWidget(self._last_verdict, 2, 1, Qt.AlignTop)

        self._best_card = RuneCard(RuneCardStatus.POWERUP)
        self._best_verdict = VerdictBar()
        main_grid.addWidget(self._best_card, 1, 2)
        main_grid.addWidget(self._best_verdict, 2, 2, Qt.AlignTop)

        main_grid.setColumnMinimumWidth(0, theme.SIZE_HISTORY_W)
        main_grid.setColumnStretch(1, 1)
        main_grid.setColumnStretch(2, 1)
        outer.addLayout(main_grid)
        outer.addStretch()

    def set_active(self, active: bool) -> None:
        self._header.set_active(active)

    def on_rune(self, rune: Rune, verdict: Verdict, mana: int,
                swop: tuple[float, float], s2us: tuple[float, float],
                set_bonus: str = "") -> None:
        # Counters
        self._counts["total"] += 1
        if verdict.decision == "KEEP":
            self._counts["kept"] += 1
        elif verdict.decision == "SELL":
            self._counts["sold"] += 1
        elif verdict.decision in ("PWR-UP", "POWERUP"):
            self._counts["pwrup"] += 1
        self._counters.update_counts(**self._counts)

        # History
        self._history.add(rune, verdict)

        # Last rune card
        status, vkind = _DECISION_TO_STATUS.get(
            verdict.decision, (RuneCardStatus.SELL, VerdictKind.SELL)
        )
        self._last_card.set_status(status)
        self._last_card.update_rune(rune, mana=mana, set_bonus_text=set_bonus)
        self._last_verdict.update_verdict(vkind, int(verdict.score or 0), swop, s2us)

        # Best rune card (tracked by score)
        if verdict.score is not None and verdict.score > self._best_score:
            self._best_score = verdict.score
            self._best_card.set_status(status)
            self._best_card.update_rune(rune, mana=mana, set_bonus_text=set_bonus)
            self._best_verdict.update_verdict(vkind, int(verdict.score), swop, s2us)
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_scan_page.py -v`

- [ ] **Step 5: Commit**

```bash
git add ui/scan/scan_page.py tests/ui/test_scan_page.py
git commit -m "feat(ui): ScanPage orchestrator"
```

---

### Task 19: ScanController (bridge thread → Qt signals)

**Files:**
- Create: `ui/controllers/scan_controller.py`
- Create: `tests/ui/test_scan_controller.py`

- [ ] **Step 1: Write the failing test**

```python
from PySide6.QtCore import QCoreApplication
from models import Rune, SubStat, Verdict
from ui.controllers.scan_controller import ScanController


def test_emits_rune_evaluated(qapp, qtbot):
    ctrl = ScanController()
    r = Rune(set="Violent", slot=2, stars=6, grade="Heroique", level=9,
             main_stat=SubStat("VIT", 25), prefix=None, substats=[])
    v = Verdict(decision="KEEP", source="s2us", reason="", score=180)

    with qtbot.waitSignal(ctrl.rune_evaluated, timeout=500) as blocker:
        ctrl.push_from_worker(r, v, mana=50, swop=(85.0, 120.0), s2us=(120.0, 140.0))

    emitted = blocker.args
    assert emitted[0].set == "Violent"
    assert emitted[1].decision == "KEEP"
    assert emitted[2] == 50
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/ui/test_scan_controller.py -v`

- [ ] **Step 3: Implement `ui/controllers/scan_controller.py`**

```python
"""Bridge between the AutoMode worker thread and Qt signals.

The bot currently runs on its own thread (threading.Thread). Qt signals can be
emitted from any thread but will be queued to the receiver's thread when
connected with AutoConnection. This controller exposes one signal the view
connects to, and one push method the worker calls.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Qt

from models import Rune, Verdict


class ScanController(QObject):
    rune_evaluated = Signal(Rune, Verdict, int, tuple, tuple, str)
    state_changed = Signal(bool)  # True = active

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def push_from_worker(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple[float, float], s2us: tuple[float, float],
        set_bonus: str = "",
    ) -> None:
        """Called from the AutoMode worker thread. Emits queued signal to the UI thread."""
        self.rune_evaluated.emit(rune, verdict, mana, swop, s2us, set_bonus)

    def notify_state(self, active: bool) -> None:
        self.state_changed.emit(active)
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/ui/test_scan_controller.py -v`

- [ ] **Step 5: Commit**

```bash
git add ui/controllers/scan_controller.py tests/ui/test_scan_controller.py
git commit -m "feat(ui): ScanController (thread -> Qt signal bridge)"
```

---

### Task 20: MainWindow shell + entrypoint

**Files:**
- Create: `ui/main_window.py`
- Create: `scan_app.py`

- [ ] **Step 1: Implement `ui/main_window.py`**

```python
"""QMainWindow shell: sidebar + content stack. Only Scan is implemented; other
nav items show a placeholder."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel,
)

from ui import theme
from ui.sidebar import Sidebar
from ui.scan.scan_page import ScanPage
from ui.widgets.background import BackgroundPane


def _placeholder(text: str) -> QWidget:
    l = QLabel(text)
    l.setAlignment(Qt.AlignCenter)
    l.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:14px;")
    return l


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Luci2US")
        self.resize(1200, 720)
        self.setMinimumSize(1000, theme.SIZE_APP_MIN_H)
        self.setStyleSheet(f"QMainWindow {{ background:{theme.COLOR_BG_APP}; }}")

        root = QWidget()
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.nav_changed.connect(self._on_nav)
        root_lay.addWidget(self._sidebar)

        # Content area with background painter behind
        content = QWidget()
        content_lay = QHBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)

        bg = BackgroundPane()
        bg_lay = QHBoxLayout(bg)
        bg_lay.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        self.scan_page = ScanPage()
        self._stack.addWidget(self.scan_page)
        for name in ("Profil", "Historique", "Stats", "Paramètres"):
            self._stack.addWidget(_placeholder(f"{name} — à implémenter"))
        bg_lay.addWidget(self._stack)

        content_lay.addWidget(bg)
        root_lay.addWidget(content, 1)

        self.setCentralWidget(root)

    def _on_nav(self, key: str) -> None:
        index = {"scan": 0, "profile": 1, "history": 2, "stats": 3, "settings": 4}.get(key, 0)
        self._stack.setCurrentIndex(index)
```

- [ ] **Step 2: Implement `scan_app.py`**

```python
"""Standalone PySide6 entrypoint for the redesigned Scan page.

Run: `python scan_app.py`

The existing customtkinter app (`app.py`) continues to work untouched; this is
a parallel entrypoint while the migration is in progress.
"""
from __future__ import annotations
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Launch and visually diff against v13**

Run: `python scan_app.py`
Expected: window opens, sidebar visible, Scan page shows empty counters + empty history + two placeholder rune-cards.

Compare against `.superpowers/brainstorm/1160-1776439696/content/scan-page-v13.html` opened in a browser at the same window width. Adjust `ui/theme.py` / individual widgets if mismatches are found.

- [ ] **Step 4: Commit**

```bash
git add ui/main_window.py scan_app.py
git commit -m "feat(ui): MainWindow shell + scan_app entrypoint"
```

---

### Task 21: Wire ScanController into MainWindow + demo push

**Files:**
- Modify: `ui/main_window.py`
- Create: `scripts/demo_scan.py`

- [ ] **Step 1: Modify `ui/main_window.py` — add ScanController**

Add imports:
```python
from ui.controllers.scan_controller import ScanController
```

At the end of `MainWindow.__init__`, after `self.setCentralWidget(root)`, append:
```python
        self.controller = ScanController(self)
        self.controller.rune_evaluated.connect(
            self.scan_page.on_rune,
            type=Qt.QueuedConnection,
        )
        self.controller.state_changed.connect(
            self.scan_page.set_active,
            type=Qt.QueuedConnection,
        )
```

- [ ] **Step 2: Create `scripts/demo_scan.py`**

```python
"""Demo: feed the Scan page with fake runes every 2 seconds.

Run: `python scripts/demo_scan.py`

Proves the UI layer works end-to-end without booting SWEX.
"""
from __future__ import annotations
import random
import sys
import threading
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from models import Rune, SubStat, Verdict
from ui.main_window import MainWindow


SETS = ["Violent", "Rapide", "Fatal", "Rage", "Lame", "Desespoir", "Garde"]
SLOTS = [1, 2, 3, 4, 5, 6]
GRADES = ["Legendaire", "Heroique", "Rare", "Magique"]
MAINS = ["ATQ%", "DEF%", "PV%", "VIT", "CC", "DC"]


def fake_rune() -> Rune:
    return Rune(
        set=random.choice(SETS), slot=random.choice(SLOTS),
        stars=6, grade=random.choice(GRADES), level=random.randint(0, 15),
        main_stat=SubStat(random.choice(MAINS), random.randint(10, 30)),
        prefix=None,
        substats=[
            SubStat("PV%", random.randint(4, 10)),
            SubStat("ATQ%", random.randint(4, 10)),
            SubStat("VIT", random.randint(4, 10)),
            SubStat("CC", random.randint(4, 10)),
        ],
    )


def fake_verdict(score: float) -> Verdict:
    decision = "KEEP" if score >= 200 else "PWR-UP" if score >= 150 else "SELL"
    return Verdict(decision=decision, source="demo", reason="", score=score)


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    def tick() -> None:
        r = fake_rune()
        score = random.uniform(80, 250)
        v = fake_verdict(score)
        w.controller.push_from_worker(
            r, v, mana=random.randint(20, 100),
            swop=(random.uniform(60, 120), random.uniform(90, 150)),
            s2us=(random.uniform(80, 140), random.uniform(110, 160)),
        )

    t = QTimer()
    t.timeout.connect(tick)
    t.start(2000)
    w.controller.notify_state(True)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the demo**

Run: `python scripts/demo_scan.py`
Expected: window opens, every 2s a new rune enters the history, counters increment, last-rune card updates, best-rune card updates only when score rises.

- [ ] **Step 4: Commit**

```bash
git add ui/main_window.py scripts/demo_scan.py
git commit -m "feat(ui): wire ScanController + demo script"
```

---

### Task 22: Hook AutoMode worker to ScanController

**Files:**
- Modify: `scan_app.py`

- [ ] **Step 1: Update `scan_app.py` to boot the real worker**

Replace the body of `main()` with:

```python
def main() -> int:
    import json, os, copy
    from auto_mode import AutoMode
    from evaluator_chain import EvaluatorChain
    from swex_bridge import SwexBridge
    from s2us_filter import S2usFilter

    # Load config (same pattern as existing app.py)
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
    DEFAULT_CONFIG = {
        "db_path": "history.db", "lang": "FR",
        "swex": {
            "drops_dir": os.path.join(os.path.expanduser("~"),
                "AppData", "Local", "Programs", "sw-exporter", "rune-bot-drops"),
            "poll_interval": 0.5,
        },
        "s2us": {"filter_file": "", "artifact_eff_threshold": 70},
    }
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            on_disk = json.load(f)
        for k, v in on_disk.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    bridge = SwexBridge(cfg["swex"]["drops_dir"], cfg["swex"]["poll_interval"])
    chain = EvaluatorChain(s2us=S2usFilter(filter_file=cfg["s2us"]["filter_file"]))
    mode = AutoMode(bridge=bridge, evaluator=chain)

    def on_evaluated(rune, verdict) -> None:
        # Called from the worker thread. Push via controller (queued to UI thread).
        w.controller.push_from_worker(
            rune, verdict, mana=int(verdict.details.get("mana", 0)) if verdict.details else 0,
            swop=(verdict.details.get("swop_eff", 0), verdict.details.get("swop_max", 0)) if verdict.details else (0, 0),
            s2us=(verdict.details.get("s2us_eff", 0), verdict.details.get("s2us_max", 0)) if verdict.details else (0, 0),
            set_bonus=verdict.details.get("set_bonus", "") if verdict.details else "",
        )

    mode.on_evaluated = on_evaluated  # assumes AutoMode exposes this hook — verify
    w.controller.rune_evaluated.connect(
        w.scan_page.on_rune, type=Qt.QueuedConnection
    )

    w.scan_page.start_requested.connect(lambda: (mode.start(), w.controller.notify_state(True)))

    return app.exec()
```

- [ ] **Step 2: Verify AutoMode exposes `on_evaluated`**

Open `auto_mode.py`. Find where evaluation result is produced. If no `on_evaluated` callback exists, add one:
```python
# In AutoMode.__init__:
self.on_evaluated: Callable[[Rune, Verdict], None] | None = None
# After evaluating each rune:
if self.on_evaluated:
    self.on_evaluated(rune, verdict)
```
Commit this change with `feat(auto_mode): expose on_evaluated hook` before proceeding.

- [ ] **Step 3: Smoke test**

If SWEX is not running locally, the worker will idle silently — that's fine, the UI still opens.
If SWEX is running, dropping a rune should populate the UI.

- [ ] **Step 4: Commit**

```bash
git add scan_app.py
git commit -m "feat(ui): hook AutoMode into ScanPage via ScanController"
```

---

## Self-Review Notes

**Spec coverage:** every spec section maps to at least one task — theme (T3), sidebar (T17), header (T16+T8+T9), counters (T13), history (T11+T12), rune card (T15+T5+T7), verdict (T14), background (T10), data flow (T19+T22), tests scaffolding (T1).

**Asset management:** T2 fetches, `.gitignore` excludes, no runtime network dependency.

**Threading:** T19 uses `QueuedConnection` to cross the worker→UI thread boundary; T22 wires the AutoMode callback.

**Risk — pixel-perfect fidelity:** Qt StyleSheets don't support every CSS value identically (radial-gradient, box-shadow layering). T10 uses `paintEvent` for the background. If the rune-card glow or other shadow effects diverge from v13, paint them via `QGraphicsDropShadowEffect` (already done in T15) or switch to a custom `paintEvent`. Validate visually in T20/T21.

**Risk — AutoMode hook :** T22 assumes an `on_evaluated` callback that may not exist in the current `auto_mode.py`. Step 2 of T22 explicitly covers adding it before use.

**Out of scope (per spec §10):** other tabs remain CTk in `app.py`; this plan doesn't touch them.
