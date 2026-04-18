"""Scan page: header + counters + history + last/best + selection + upgrades."""
from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel

from models import Rune, Verdict
from ui import theme
from ui.scan.counters_bar import CountersBar
from ui.scan.header_bar import HeaderBar
from ui.scan.history_list import HistoryList
from ui.scan.rune_card import RuneCard, RuneCardStatus
from ui.scan.selection_card import SelectionCard
from ui.scan.upgrade_list import UpgradeList
from ui.scan.verdict_bar import VerdictBar, VerdictKind


_DECISION_TO_STATUS = {
    "KEEP": (RuneCardStatus.KEEP, VerdictKind.KEEP),
    "SELL": (RuneCardStatus.SELL, VerdictKind.SELL),
    "PWR-UP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
    "POWERUP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
    "POWER-UP": (RuneCardStatus.POWERUP, VerdictKind.POWERUP),
}


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
        f"text-transform:uppercase; letter-spacing:1.5px; font-weight:600;"
    )
    return lbl


class ScanPage(QWidget):
    start_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._counts = {"total": 0, "kept": 0, "sold": 0}
        self._best_score: float = -1.0
        self._started_at: float | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick_time)

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

        # Row 0: section labels
        main_grid.addWidget(_section_label("Historique"),    0, 0)
        main_grid.addWidget(_section_label("Derniere rune"), 0, 1)
        main_grid.addWidget(_section_label("Meilleure rune"), 0, 2)

        # Row 1-2: history (2 rows tall on left), last/best cards + verdicts
        self._history = HistoryList()
        self._history.item_clicked.connect(self._on_history_clicked)
        main_grid.addWidget(self._history, 1, 0, 2, 1)

        self._last_card = RuneCard(RuneCardStatus.KEEP)
        self._last_verdict = VerdictBar()
        main_grid.addWidget(self._last_card,    1, 1)
        main_grid.addWidget(self._last_verdict, 2, 1, Qt.AlignmentFlag.AlignTop)

        self._best_card = RuneCard(RuneCardStatus.POWERUP)
        self._best_verdict = VerdictBar()
        main_grid.addWidget(self._best_card,    1, 2)
        main_grid.addWidget(self._best_verdict, 2, 2, Qt.AlignmentFlag.AlignTop)

        # Row 3: second section labels (Selection spans col 0+1, Upgrades col 2)
        main_grid.addWidget(_section_label("Selection"),       3, 0, 1, 2)
        main_grid.addWidget(_section_label("En amelioration"), 3, 2)

        # Row 4: selection card (spans col 0+1) + upgrade list (col 2)
        self._selection = SelectionCard()
        main_grid.addWidget(self._selection, 4, 0, 1, 2)

        self._upgrades = UpgradeList()
        main_grid.addWidget(self._upgrades, 4, 2)

        main_grid.setColumnMinimumWidth(0, theme.SIZE_HISTORY_W)
        main_grid.setColumnStretch(1, 1)
        main_grid.setColumnStretch(2, 1)
        outer.addLayout(main_grid)
        outer.addStretch()

    def set_active(self, active: bool) -> None:
        self._header.set_active(active)
        if active:
            self._started_at = time.monotonic()
            self._counters.update_time(0)
            self._timer.start()
        else:
            self._timer.stop()

    def _tick_time(self) -> None:
        if self._started_at is None:
            return
        self._counters.update_time(int(time.monotonic() - self._started_at))

    def _on_history_clicked(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple, s2us: tuple, set_bonus: str,
    ) -> None:
        self._selection.set_selection(rune, verdict, mana, swop, s2us, set_bonus)

    def on_rune(self, rune: Rune, verdict: Verdict, mana: int,
                swop: tuple[float, float], s2us: tuple[float, float],
                set_bonus: str = "") -> None:
        self._counts["total"] += 1
        if verdict.decision == "KEEP":
            self._counts["kept"] += 1
        elif verdict.decision == "SELL":
            self._counts["sold"] += 1
        self._counters.update_counts(**self._counts)

        self._history.add(rune, verdict, mana, swop, s2us, set_bonus)

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

    def on_rune_upgraded(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple[float, float], s2us: tuple[float, float],
        set_bonus: str = "",
    ) -> None:
        self._upgrades.upsert(rune, verdict)
