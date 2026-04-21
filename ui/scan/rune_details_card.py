"""Carte de details rune — affichee a droite du hologramme dans la maquette.

Contient :
    RAGE RUNE (+12)
    TYPE : 6* | CLASSE : HEROIQUE

    [STAT PRINCIPALE]
    TX CRIT +23%

    PV +10%       [===== Growth]
    ATK +10%      [===== Growth]
    VIT +9        [=====  Speed]
    TX CRIT +9%   [====== Growth]

API :
    card.set_rune(rune)
    card.show_empty_state()
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

from models import Rune, SubStat
from ui import theme


GOLD = "#ffd07a"
MAGENTA = "#ff5ac8"

_STAT_FR = {
    "ATQ": "ATK", "ATQ%": "ATK", "DEF": "DEF", "DEF%": "DEF",
    "PV": "PV", "PV%": "PV", "VIT": "VIT",
    "CC": "TX CRIT", "DC": "DEG CRIT", "RES": "RES", "PRE": "PRE",
}

_STAT_COLOR = {
    "PV": "#4ADE80", "PV%": "#4ADE80",
    "ATQ": "#f59e42", "ATQ%": "#f59e42",
    "DEF": "#60a5fa", "DEF%": "#60a5fa",
    "VIT": "#60a5fa",
    "CC": "#4ADE80", "DC": "#a78bfa",
    "RES": "#a78bfa", "PRE": "#f59e42",
}


def _fmt_stat(stat: SubStat) -> str:
    label = _STAT_FR.get(stat.type, stat.type)
    value = int(stat.value + (stat.grind_value or 0.0))
    suffix = "%" if stat.type.endswith("%") or stat.type in ("CC", "DC", "RES", "PRE") else ""
    return f"{label} +{value}{suffix}"


class _GrowthRow(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(8)

        self._label = QLabel("")
        self._label.setStyleSheet(
            f"color: {theme.D.FG}; background: transparent;"
            f"font-family: '{theme.D.FONT_MONO}';"
            f"font-size: 13px; font-weight: 600;"
        )
        self._label.setMinimumWidth(120)
        lay.addWidget(self._label, 0)

        self._bar = QProgressBar()
        self._bar.setFixedHeight(6)
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        lay.addWidget(self._bar, 1)

    def set_stat(self, stat: SubStat) -> None:
        self._label.setText(_fmt_stat(stat))
        color = _STAT_COLOR.get(stat.type, "#60a5fa")
        pct = min(100, int(stat.value + (stat.grind_value or 0.0)))
        self._bar.setValue(pct)
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 0.08);
                border: none; border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
            """
        )


class RuneDetailsCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("RuneDetailsCard")
        self.setStyleSheet(
            f"""
            #RuneDetailsCard {{
                background: rgba(18, 22, 32, 0.72);
                border: 1px solid {theme.D.BORDER};
                border-radius: 16px;
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(8)

        self._title = QLabel("")
        self._title.setStyleSheet(
            f"color: {GOLD}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 22px; font-weight: 900; letter-spacing: 1px;"
        )
        root.addWidget(self._title)

        self._type_line = QLabel("")
        self._type_line.setStyleSheet(
            f"color: {theme.D.FG_DIM}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}'; font-size: 13px;"
        )
        root.addWidget(self._type_line)

        root.addSpacing(6)

        self._main_badge = QLabel("[STAT PRINCIPALE]")
        self._main_badge.setStyleSheet(
            f"color: {MAGENTA}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 11px; font-weight: 800; letter-spacing: 1.5px;"
        )
        root.addWidget(self._main_badge)

        self._main_stat = QLabel("")
        self._main_stat.setStyleSheet(
            f"color: white; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 26px; font-weight: 900;"
        )
        root.addWidget(self._main_stat)

        root.addSpacing(8)

        self._sub_rows: list[_GrowthRow] = []
        for _ in range(4):
            row = _GrowthRow()
            self._sub_rows.append(row)
            root.addWidget(row)

        root.addStretch(1)

        self._empty_hint = QLabel("En attente d'une rune scannee...")
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.setStyleSheet(
            f"color: {theme.D.FG_MUTE}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 13px; font-style: italic;"
        )
        root.addWidget(self._empty_hint)

        self.show_empty_state()

    def show_empty_state(self) -> None:
        self._title.setText("")
        self._type_line.setText("")
        self._main_badge.setVisible(False)
        self._main_stat.setText("")
        for row in self._sub_rows:
            row.setVisible(False)
        self._empty_hint.setVisible(True)

    def set_rune(self, rune: Rune) -> None:
        set_fr = (rune.set or "").upper()
        grade_fr = (rune.grade or "").upper()
        self._title.setText(f"{set_fr} RUNE (+{rune.level})")
        self._type_line.setText(f"TYPE : {rune.stars}\u2605 | CLASSE : {grade_fr}")
        self._main_badge.setVisible(True)
        self._main_stat.setText(_fmt_stat(rune.main_stat))
        for i, row in enumerate(self._sub_rows):
            if i < len(rune.substats):
                row.set_stat(rune.substats[i])
                row.setVisible(True)
            else:
                row.setVisible(False)
        self._empty_hint.setVisible(False)
