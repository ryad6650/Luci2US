"""Composite panel shown when the user clicks a history item.

Stacks a RuneCard + VerdictBar identical to 'Derniere rune'. Holds an
internal rune-key so a re-click on the same item toggles the panel off.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from models import Rune, Verdict
from ui import theme
from ui.scan.rune_card import RuneCard, RuneCardStatus
from ui.scan.verdict_bar import VerdictBar, VerdictKind


_DECISION_TO_STATUS = {
    "KEEP": (RuneCardStatus.KEEP, VerdictKind.KEEP),
    "SELL": (RuneCardStatus.SELL, VerdictKind.SELL),
    "PWR-UP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
    "POWERUP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
    "POWER-UP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
}


def _rune_key(rune: Rune) -> tuple:
    return (rune.set, rune.slot, rune.stars, rune.grade, rune.main_stat.type, rune.level)


class SelectionCard(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self._card = RuneCard(RuneCardStatus.KEEP)
        self._verdict = VerdictBar()
        lay.addWidget(self._card)
        lay.addWidget(self._verdict, 0, Qt.AlignmentFlag.AlignTop)

        self._empty = QLabel("Clique sur un item de l'historique pour l'afficher ici")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        self._empty.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-style:italic;"
            f"border:1px dashed {theme.COLOR_BORDER_FRAME}; border-radius:7px;"
            f"padding:36px 16px; background:rgba(26,15,7,0.4);"
        )
        lay.addWidget(self._empty)

        self._current_key: tuple | None = None
        self._show_empty()

    def _show_empty(self) -> None:
        self._card.hide()
        self._verdict.hide()
        self._empty.show()
        self._current_key = None

    def _show_rune(self) -> None:
        self._empty.hide()
        self._card.show()
        self._verdict.show()

    def set_selection(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple[float, float], s2us: tuple[float, float],
        set_bonus: str = "",
    ) -> None:
        """Display rune+verdict. Re-selecting the same entry clears the panel."""
        key = _rune_key(rune)
        if self._current_key == key:
            self._show_empty()
            return

        status, vkind = _DECISION_TO_STATUS.get(
            verdict.decision, (RuneCardStatus.SELL, VerdictKind.SELL)
        )
        self._card.set_status(status)
        self._card.update_rune(rune, mana=mana, set_bonus_text=set_bonus)
        self._verdict.update_verdict(vkind, int(verdict.score or 0), swop, s2us)
        self._current_key = key
        self._show_rune()
