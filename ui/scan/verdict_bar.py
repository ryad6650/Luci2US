"""Verdict card under each rune-card: badge + Score + SWOP + S2US + quality bars."""
from __future__ import annotations
from enum import Enum

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
)

from ui import theme
from ui.widgets.quality_bar import (
    QualityBar, MAX_SCORE, MAX_SWOP, MAX_S2US,
    ZONES_SCORE, ZONES_SWOP, ZONES_S2US,
)


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


class VerdictBar(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._kind = VerdictKind.KEEP

        outer = QHBoxLayout(self)
        outer.setContentsMargins(14, 11, 14, 11)
        outer.setSpacing(12)

        self._badge = QLabel("KEEP")
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)

        eff_box = QWidget()
        eff_lay = QVBoxLayout(eff_box)
        eff_lay.setContentsMargins(0, 0, 0, 0)
        eff_lay.setSpacing(3)

        # Row 1: Score + bar
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
            f"color:{theme.COLOR_GOLD}; font-size:12px; font-weight:700;"
        )
        srl.addWidget(self._score_label)
        srl.addStretch()
        eff_lay.addWidget(score_row)
        self._score_bar = QualityBar()
        eff_lay.addWidget(self._score_bar)

        # Row 2: SWOP label + bar
        self._swop_label = QLabel(
            f"<b style='color:{theme.COLOR_GOLD}'>SWOP</b> -"
        )
        self._swop_label.setTextFormat(Qt.TextFormat.RichText)
        self._swop_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
        )
        eff_lay.addWidget(self._swop_label)
        self._swop_bar = QualityBar()
        eff_lay.addWidget(self._swop_bar)

        # Row 3: S2US label + bar
        self._s2us_label = QLabel(
            f"<b style='color:{theme.COLOR_GOLD}'>S2US</b> -"
        )
        self._s2us_label.setTextFormat(Qt.TextFormat.RichText)
        self._s2us_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
        )
        eff_lay.addWidget(self._s2us_label)
        self._s2us_bar = QualityBar()
        eff_lay.addWidget(self._s2us_bar)

        outer.addWidget(eff_box, 1)

        self._repaint_style()

    def _repaint_style(self) -> None:
        bg, fg = _COLORS[self._kind]
        self.setStyleSheet(
            f"""
            VerdictBar {{
                background: rgba(26,15,7,0.9);
                border:1px solid {bg};
                border-radius:7px;
            }}
            """
        )
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(18)
        glow.setOffset(0, 0)
        c = QColor(bg)
        c.setAlpha(100)
        glow.setColor(c)
        self.setGraphicsEffect(glow)

        self._badge.setText(_LABELS[self._kind])
        self._badge.setStyleSheet(
            f"background:{bg}; color:{fg}; font-weight:900;"
            f"font-size:11px; padding:4px 10px; border-radius:3px; letter-spacing:1px;"
        )

    def update_verdict(self, kind: VerdictKind, score: int,
                       swop: tuple[float, float], s2us: tuple[float, float]) -> None:
        self._kind = kind
        self._score_label.setText(f"Score {score}")
        self._score_bar.set_value(float(score), MAX_SCORE, ZONES_SCORE)

        self._swop_label.setText(
            f"<b style='color:{theme.COLOR_GOLD}'>SWOP</b> {swop[0]:.1f}% "
            f"<span style='color:{theme.COLOR_TEXT_DIM}'>(max {swop[1]:.1f}%)</span>"
        )
        self._swop_bar.set_value(swop[0], MAX_SWOP, ZONES_SWOP)

        self._s2us_label.setText(
            f"<b style='color:{theme.COLOR_GOLD}'>S2US</b> {s2us[0]:.1f}% "
            f"<span style='color:{theme.COLOR_TEXT_DIM}'>(max {s2us[1]:.1f}%)</span>"
        )
        self._s2us_bar.set_value(s2us[0], MAX_S2US, ZONES_S2US)

        self._repaint_style()
