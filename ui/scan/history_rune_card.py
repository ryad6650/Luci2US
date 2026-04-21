"""Mini-carte rune affichee dans la grille 2x3 de ScanHistoryPanel.

API :
    card = HistoryRuneCard(rune, verdict)
    card.clicked.connect(callback)
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from models import Rune, Verdict
from ui import theme


GREEN = "#4ADE80"
RED = "#F87171"

_STAT_FR = {
    "ATQ": "ATK", "ATQ%": "ATK%", "DEF": "DEF", "DEF%": "DEF%",
    "PV": "PV", "PV%": "PV%", "VIT": "VIT",
    "CC": "TX CRIT", "DC": "DEG CRIT", "RES": "RES", "PRE": "PRE",
}


def _summary_line(rune: Rune) -> str:
    if rune.substats:
        s = rune.substats[0]
        label = _STAT_FR.get(s.type, s.type)
        v = int(s.value + (s.grind_value or 0.0))
        return f"{label}+{v}"
    ms = rune.main_stat
    return f"{_STAT_FR.get(ms.type, ms.type)}+{int(ms.value)}"


class HistoryRuneCard(QFrame):
    clicked = Signal(object, object)

    def __init__(self, rune: Rune, verdict: Verdict, parent=None) -> None:
        super().__init__(parent)
        self._rune = rune
        self._verdict = verdict
        self.setObjectName("HistoryRuneCard")
        self.setStyleSheet(
            """
            #HistoryRuneCard {
                background: transparent;
                border: none;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(4)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        self._icon = QLabel()
        self._icon.setFixedSize(24, 24)
        self._icon.setScaledContents(True)
        set_key = (rune.set or "").lower()
        asset = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "assets", "swarfarm", "runes", f"{set_key}.png",
        ))
        if os.path.isfile(asset):
            self._icon.setPixmap(QPixmap(asset))
        header.addWidget(self._icon)

        self._name = QLabel(f"{(rune.set or '').upper()} (+{rune.level})")
        self._name.setStyleSheet(
            f"color: {theme.D.FG}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 12px; font-weight: 800;"
        )
        header.addWidget(self._name, 1)
        root.addLayout(header)

        self._summary = QLabel(_summary_line(rune))
        self._summary.setStyleSheet(
            f"color: {theme.D.FG_DIM}; background: transparent;"
            f"font-family: '{theme.D.FONT_MONO}'; font-size: 11px;"
        )
        root.addWidget(self._summary)

        keep = (verdict.decision or "").upper() in ("KEEP", "POWER-UP")
        color = GREEN if keep else RED
        label = "Garder" if keep else "Vendre"
        self._verdict_btn = QPushButton(label)
        self._verdict_btn.setFixedHeight(22)
        self._verdict_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none; border-radius: 11px;
                padding: 0 10px;
                font-family: '{theme.D.FONT_UI}';
                font-size: 10px; font-weight: 800;
            }}
            """
        )
        self._verdict_btn.clicked.connect(
            lambda: self.clicked.emit(self._rune, self._verdict)
        )
        root.addWidget(self._verdict_btn, 0, Qt.AlignmentFlag.AlignLeft)
