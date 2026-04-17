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
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            f"<b style='color:{theme.COLOR_GOLD}'>SWOP</b> -<br>"
            f"<b style='color:{theme.COLOR_GOLD}'>S2US</b> -"
        )
        self._eff_label.setTextFormat(Qt.TextFormat.RichText)
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
