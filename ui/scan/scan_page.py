"""Scan page: header + counters + history + last-rune card + best-rune card."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel

from models import Rune, Verdict
from ui import theme
from ui.scan.counters_bar import CountersBar
from ui.scan.header_bar import HeaderBar
from ui.scan.history_list import HistoryList
from ui.scan.rune_card import RuneCard, RuneCardStatus
from ui.scan.verdict_bar import VerdictBar, VerdictKind


_DECISION_TO_STATUS = {
    "KEEP": (RuneCardStatus.KEEP, VerdictKind.KEEP),
    "SELL": (RuneCardStatus.SELL, VerdictKind.SELL),
    "PWR-UP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
    "POWERUP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
}


class ScanPage(QWidget):
    start_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._counts = {"total": 0, "kept": 0, "sold": 0, "pwrup": 0}
        self._best_score: float = -1.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        self._header = HeaderBar()
        self._header.start_clicked.connect(self.start_requested.emit)
        outer.addWidget(self._header)

        self._counters = CountersBar()
        outer.addWidget(self._counters)

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(14)
        main_grid.setVerticalSpacing(6)

        for col, text in enumerate(["Historique", "Derniere rune", "Meilleure rune"]):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
                f"text-transform:uppercase; letter-spacing:1.5px; font-weight:600;"
            )
            main_grid.addWidget(lbl, 0, col)

        self._history = HistoryList()
        main_grid.addWidget(self._history, 1, 0, 3, 1, Qt.AlignmentFlag.AlignTop)

        self._last_card = RuneCard(RuneCardStatus.KEEP)
        self._last_verdict = VerdictBar()
        main_grid.addWidget(self._last_card, 1, 1)
        main_grid.addWidget(self._last_verdict, 2, 1, Qt.AlignmentFlag.AlignTop)

        self._best_card = RuneCard(RuneCardStatus.POWERUP)
        self._best_verdict = VerdictBar()
        main_grid.addWidget(self._best_card, 1, 2)
        main_grid.addWidget(self._best_verdict, 2, 2, Qt.AlignmentFlag.AlignTop)

        main_grid.setColumnMinimumWidth(0, theme.SIZE_HISTORY_W)
        main_grid.setColumnStretch(1, 1)
        main_grid.setColumnStretch(2, 1)
        outer.addLayout(main_grid)
        outer.addStretch()

    def set_active(self, active: bool) -> None:
        self._header.set_active(active)

    def on_rune(self, rune: Rune, verdict: Verdict, mana: int,
                swop: tuple[float, float], s2us: tuple[float, float],
                set_bonus: str = "") -> None:
        self._counts["total"] += 1
        if verdict.decision == "KEEP":
            self._counts["kept"] += 1
        elif verdict.decision == "SELL":
            self._counts["sold"] += 1
        elif verdict.decision in ("PWR-UP", "POWERUP"):
            self._counts["pwrup"] += 1
        self._counters.update_counts(**self._counts)

        self._history.add(rune, verdict)

        status, vkind = _DECISION_TO_STATUS.get(
            verdict.decision, (RuneCardStatus.SELL, VerdictKind.SELL)
        )
        self._last_card.set_status(status)
        self._last_card.update_rune(rune, mana=mana, set_bonus_text=set_bonus)
        self._last_verdict.update_verdict(vkind, int(verdict.score or 0), swop, s2us)

        if verdict.score is not None and verdict.score > self._best_score:
            self._best_score = verdict.score
            self._best_card.set_status(status)
            self._best_card.update_rune(rune, mana=mana, set_bonus_text=set_bonus)
            self._best_verdict.update_verdict(vkind, int(verdict.score), swop, s2us)
