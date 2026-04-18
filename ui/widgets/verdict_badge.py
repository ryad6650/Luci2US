"""VerdictBadge — pill with KEEP / SELL icon + label.

Design-handoff variant D: auto-decides from efficiency (>= 70 → KEEP).
Four sizes (sm/md/lg/xl) matching the JSX sizing table.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ui import theme


_SIZES = {
    "sm": {"pad": (4, 8),   "fs": 10, "gap": 6},
    "md": {"pad": (6, 10),  "fs": 11, "gap": 6},
    "lg": {"pad": (9, 16),  "fs": 13, "gap": 8},
    "xl": {"pad": (12, 20), "fs": 15, "gap": 10},
}


class VerdictBadge(QFrame):
    def __init__(self, size: str = "md", parent=None) -> None:
        super().__init__(parent)
        self._size = size if size in _SIZES else "md"
        self._keep: bool = True

        lay = QHBoxLayout(self)
        sz = _SIZES[self._size]
        lay.setContentsMargins(sz["pad"][1], sz["pad"][0], sz["pad"][1], sz["pad"][0])
        lay.setSpacing(sz["gap"])

        self._icon = QLabel()
        self._label = QLabel("KEEP")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self._label, 0, Qt.AlignmentFlag.AlignVCenter)

        self._apply_style()

    def set_keep(self, keep: bool) -> None:
        self._keep = bool(keep)
        self._apply_style()

    def set_efficiency(self, efficiency: float) -> None:
        self.set_keep(efficiency >= 70.0)

    def _apply_style(self) -> None:
        sz = _SIZES[self._size]
        color = theme.D.OK if self._keep else theme.D.ERR
        label = "KEEP" if self._keep else "SELL"
        # Mimic the React glyph icons with unicode.
        icon_char = "\u2706" if self._keep else "\u29C9"

        self.setStyleSheet(
            f"""
            VerdictBadge {{
                background: {color}26;
                border: 1.5px solid {color}55;
                border-radius: 999px;
            }}
            """
        )
        self._icon.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:{sz['fs'] + 2}px; font-weight:700;"
        )
        self._icon.setText(icon_char)
        self._label.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:{sz['fs']}px; font-weight:700; letter-spacing:1px;"
        )
        self._label.setText(label)
