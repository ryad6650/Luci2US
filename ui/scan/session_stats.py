"""Session stats row — 4 glass cards (Runes obtenues / Gardées / Vendues / Efficacité)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui import theme
from ui.widgets.stat_icon import (
    StatIcon, OVERLAY_NONE, OVERLAY_CHECK, OVERLAY_CROSS, OVERLAY_SPARKLE,
)


class _StatCard(QFrame):
    def __init__(
        self, label: str, accent: str, overlay: str,
        value: str = "0", unit: str = "", parent=None,
    ) -> None:
        super().__init__(parent)
        self._accent = accent
        self.setObjectName("StatCard")
        self.setStyleSheet(
            f"""
            #StatCard {{
                background: {theme.D.STAT_BG};
                border: 1px solid {theme.D.BORDER};
                border-radius: 12px;
            }}
            """
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(14)

        icon = StatIcon(size=32, color=accent, overlay=overlay)
        row.addWidget(icon, 0, Qt.AlignmentFlag.AlignVCenter)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(3)

        self._label = QLabel(label)
        self._label.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:600; letter-spacing:1.2px;"
        )
        rl.addWidget(self._label)

        val_row = QWidget()
        vrl = QHBoxLayout(val_row)
        vrl.setContentsMargins(0, 0, 0, 0)
        vrl.setSpacing(5)
        self._value = QLabel(value)
        self._value.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:20px; font-weight:600; letter-spacing:-0.4px;"
        )
        vrl.addWidget(self._value, 0, Qt.AlignmentFlag.AlignBottom)
        self._unit = QLabel(unit)
        self._unit.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        vrl.addWidget(self._unit, 0, Qt.AlignmentFlag.AlignBottom)
        vrl.addStretch()
        rl.addWidget(val_row)

        row.addWidget(right, 1)

    def set_value(self, value: str, unit: str | None = None) -> None:
        self._value.setText(value)
        if unit is not None:
            self._unit.setText(unit)


class SessionStats(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self._obtained = _StatCard("Runes obtenues", theme.D.ACCENT, OVERLAY_NONE,    "0", "session")
        self._kept     = _StatCard("Gardees",         theme.D.OK,     OVERLAY_CHECK,   "0", "sur 0")
        self._sold     = _StatCard("Vendues",         theme.D.ERR,    OVERLAY_CROSS,   "0", "auto")
        self._eff      = _StatCard("Efficacite moy.", theme.D.INFO,   OVERLAY_SPARKLE, "0.0", "%")

        for c in (self._obtained, self._kept, self._sold, self._eff):
            lay.addWidget(c, 1)

    def update_counts(self, total: int, kept: int, sold: int, avg_eff: float) -> None:
        self._obtained.set_value(str(total), "session")
        self._kept.set_value(str(kept), f"sur {total}")
        self._sold.set_value(str(sold), "auto")
        self._eff.set_value(f"{avg_eff:.1f}", "%")
