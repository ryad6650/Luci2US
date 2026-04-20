"""Left sidebar — 188px, magenta accent, LIVE dot on the active Scan tab.

Layout matches design_handoff_scan/variation-d.jsx Sidebar component:
- WORKSPACE eyebrow
- 7 nav items (Scan, Filtres, Runes, Monsters, Stats & Historique, Profils, Paramètres)
- user block at the bottom with a magenta-gradient avatar

The active item gets a magenta-tinted background; the Scan item also
shows a pulsing LIVE dot when the bot is running.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, Property
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui import theme


NAV_ITEMS: list[tuple[str, str, str | None]] = [
    ("scan",          "Scan",                 None),   # LIVE dot handled separately
    ("filters",       "Filtres",              None),
    ("runes",         "Runes",                "1.2k"),
    ("monsters",      "Monstres",             None),
    ("stats_history", "Stats & Historique",   None),
    ("profile",       "Profils",              None),
    ("settings",      "Parametres",           None),
]


_ICON = {
    "scan":          "\u25CE",   # ◎
    "filters":       "\u2261",   # ≡
    "runes":         "\u2726",   # ✦
    "monsters":      "\u2618",   # ☘
    "stats_history": "\u2630",   # ☰
    "profile":       "\u25CB",   # ○
    "settings":      "\u2699",   # ⚙
}


class _LiveDot(QLabel):
    """Magenta pulsing dot — opacity 1.0 → 0.35 → 1.0 every 1.6s."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self._opacity = 1.0
        self._refresh()
        self._anim = QPropertyAnimation(self, b"pulse")
        self._anim.setDuration(1600)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.35)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.start()

    def _refresh(self) -> None:
        a = int(255 * self._opacity)
        c = QColor(theme.D.ACCENT)
        c.setAlpha(a)
        self.setStyleSheet(
            f"background:rgba({c.red()},{c.green()},{c.blue()},{self._opacity});"
            f"border-radius:4px;"
        )

    def get_pulse(self) -> float:
        return self._opacity

    def set_pulse(self, v: float) -> None:
        self._opacity = max(0.0, min(1.0, v))
        self._refresh()

    pulse = Property(float, get_pulse, set_pulse)


class _NavButton(QPushButton):
    def __init__(self, key: str, label: str, badge: str | None, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self._badge_text = badge
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(10)

        self._icon = QLabel(_ICON.get(key, "\u2022"))
        self._icon.setFixedWidth(16)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(label)
        lay.addWidget(self._label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._badge: QLabel | _LiveDot | None = None
        self._live_wrap: QWidget | None = None
        if key == "scan":
            self._live_wrap = QWidget()
            lw = QHBoxLayout(self._live_wrap)
            lw.setContentsMargins(0, 0, 0, 0)
            lw.setSpacing(4)
            dot = _LiveDot()
            live_txt = QLabel("LIVE")
            live_txt.setStyleSheet(
                f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:10px; font-weight:700; letter-spacing:0.5px;"
            )
            lw.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            lw.addWidget(live_txt, 0, Qt.AlignmentFlag.AlignVCenter)
            self._live_wrap.hide()
            lay.addWidget(self._live_wrap, 0, Qt.AlignmentFlag.AlignVCenter)
        elif badge:
            b = QLabel(badge)
            b.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:10px; padding:2px 6px; border-radius:4px;"
                f"background:rgba(122,97,104,0.22);"
            )
            lay.addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)
            self._badge = b

        self._apply_style(active=False)

    def set_live(self, live: bool) -> None:
        if self._live_wrap is not None:
            self._live_wrap.setVisible(live)

    def _apply_style(self, active: bool) -> None:
        fg = theme.D.FG if active else theme.D.FG_MUTE
        icon_fg = theme.D.ACCENT if active else theme.D.FG_MUTE
        bg = theme.D.ACCENT_DIM if active else "transparent"
        weight = 600 if active else 500
        self.setStyleSheet(
            f"""
            _NavButton {{
                text-align:left; background:{bg}; border:none;
                border-radius:6px;
            }}
            _NavButton:hover {{ background:rgba(255,255,255,0.04); }}
            """
        )
        self._label.setStyleSheet(
            f"color:{fg}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:{weight};"
        )
        self._icon.setStyleSheet(
            f"color:{icon_fg}; font-size:14px;"
        )

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply_style(active)


class Sidebar(QFrame):
    nav_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(theme.D.SIDEBAR_W)
        self.setStyleSheet(
            f"""
            #Sidebar {{
                background:{theme.D.SIDEBAR_BG};
                border-right:1px solid {theme.D.BORDER};
            }}
            """
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        eyebrow = QLabel("WORKSPACE")
        eyebrow.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:600; letter-spacing:1.5px;"
            f"padding:18px 14px 10px;"
        )
        lay.addWidget(eyebrow)

        nav_wrap = QWidget()
        nav_lay = QVBoxLayout(nav_wrap)
        nav_lay.setContentsMargins(8, 0, 8, 0)
        nav_lay.setSpacing(2)
        self._buttons: dict[str, _NavButton] = {}
        for key, label, badge in NAV_ITEMS:
            b = _NavButton(key, label, badge)
            b.clicked.connect(lambda _c=False, k=key: self._on_click(k))
            nav_lay.addWidget(b)
            self._buttons[key] = b
        lay.addWidget(nav_wrap)
        lay.addStretch(1)

        # ── user block ──
        user = QFrame()
        user.setObjectName("UserBlock")
        user.setStyleSheet(
            f"""
            #UserBlock {{
                background:rgba(255,255,255,0.04); border-radius:8px;
            }}
            """
        )
        ul = QHBoxLayout(user)
        ul.setContentsMargins(10, 10, 10, 10)
        ul.setSpacing(10)

        avatar = QLabel("AZ")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f" stop:0 {theme.D.ACCENT}, stop:1 {theme.D.ACCENT_2});"
            f" color:#0b0b0f; font-weight:700; font-size:12px;"
            f" border-radius:14px;"
        )
        ul.addWidget(avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        user_col = QWidget()
        ucl = QVBoxLayout(user_col)
        ucl.setContentsMargins(0, 0, 0, 0)
        ucl.setSpacing(1)
        name = QLabel("ArtheZ")
        name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; font-weight:600;"
        )
        region = QLabel("global \u00B7 47")
        region.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:10px;"
        )
        ucl.addWidget(name)
        ucl.addWidget(region)
        ul.addWidget(user_col, 1)

        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(10, 0, 10, 10)
        wl.addWidget(user)
        lay.addWidget(wrap)

        self.set_active("scan")

    def _on_click(self, key: str) -> None:
        self.set_active(key)
        self.nav_changed.emit(key)

    def set_active(self, key: str) -> None:
        for k, b in self._buttons.items():
            b.set_active(k == key)

    def set_live(self, live: bool) -> None:
        """Toggle LIVE dot on the Scan nav item."""
        scan_btn = self._buttons.get("scan")
        if scan_btn is not None:
            scan_btn.set_live(live)
