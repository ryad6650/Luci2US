"""Large rune card: title, 6-star row + icon, main stat, grade + mana, subs, set bonus."""
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
    "Legendaire": ("Legendaire", theme.COLOR_GRADE_LEGEND, theme.COLOR_GRADE_LEGEND_B),
    "Heroique":   ("Heroique",  theme.COLOR_GRADE_HERO,   theme.COLOR_GRADE_HERO_B),
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

        self._title = QLabel("-")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        iw_lay.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignHCenter)
        grid.addWidget(icon_wrap, 0, 0)

        self._main = QLabel("-")
        self._main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:17px; font-weight:600;"
        )
        grid.addWidget(self._main, 0, 1)
        grid.setColumnStretch(1, 1)

        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(3)
        rlay.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._grade = QLabel("-")
        rlay.addWidget(self._grade, 0, Qt.AlignmentFlag.AlignRight)
        self._mana = ManaBadge()
        rlay.addWidget(self._mana, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(right, 0, 2)

        outer.addWidget(body)

        subs_box = QWidget()
        sl = QVBoxLayout(subs_box)
        sl.setContentsMargins(2, 3, 2, 6)
        sl.setSpacing(3)
        self._sub_labels: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel("-")
            lbl.setStyleSheet(f"color:{theme.COLOR_TEXT_SUB}; font-size:11px;")
            sl.addWidget(lbl)
            self._sub_labels.append(lbl)
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
            f"font-weight:700; font-size:10px; padding:1px 9px; border-radius:3px;"
        )

        for i, lbl in enumerate(self._sub_labels):
            if i < len(rune.substats):
                lbl.setText(_sub_line(rune.substats[i]))
            else:
                lbl.setText("")

        self._setbonus.setText(set_bonus_text)
