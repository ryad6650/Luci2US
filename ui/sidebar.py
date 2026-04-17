"""Left sidebar - logo + nav items (Scan, Filtres, Runes, Monstres, Stats & Historique, Profils, Parametres)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from ui import theme


NAV_ITEMS = [
    ("scan",          "\u25C9  Scan"),
    ("filters",       "\u25A3  Filtres"),
    ("runes",         "\u2726  Runes"),
    ("monsters",      "\u2618  Monstres"),
    ("stats_history", "\u2261  Stats & Historique"),
    ("profile",       "\u25CE  Profils"),
    ("settings",      "\u2699  Parametres"),
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

        logo = QLabel(
            "Luci2US<br>"
            "<span style='font-size:9px;color:#8b6a3d;letter-spacing:3px;font-weight:400'>SW RUNE BOT</span>"
        )
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:22px; font-style:italic; font-weight:700; letter-spacing:0.5px;"
            f"padding:6px 0 22px; border-bottom:1px solid {theme.COLOR_SIDEBAR_BORDER};"
        )
        lay.addWidget(logo)
        lay.addSpacing(14)

        self._buttons: dict[str, QPushButton] = {}
        for key, label in NAV_ITEMS:
            b = QPushButton(label)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
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
