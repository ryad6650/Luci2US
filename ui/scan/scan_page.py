"""Scan page — live dashboard (design_handoff_scan / variation D).

Layout:
    ScanHeader       (live feed, Farming/Paused pill)
    SessionStats     (4 glass counter cards)
    LastRuneCard | UpgradeRuneCard      (grid 1.2fr / 1fr)
    HistoryList      (2-col grid, scrollable)

Public API preserved from the previous implementation so scan_controller /
main_window / tests don't need to change:
    - set_active(bool)
    - on_rune(rune, verdict, mana, swop, s2us, set_bonus)
    - on_rune_upgraded(rune, verdict, mana, swop, s2us, set_bonus)
"""
from __future__ import annotations
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from models import Rune, Verdict
from ui import theme
from ui.scan.history_item import TYPE_NEW, TYPE_UPGRADE
from ui.scan.history_list import HistoryList
from ui.scan.last_rune_card import LastRuneCard
from ui.scan.scan_header import ScanHeader
from ui.scan.session_stats import SessionStats
from ui.scan.upgrade_rune_card import UpgradeRuneCard


class ScanPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"ScanPage {{ background: transparent; color: {theme.D.FG}; }}"
        )

        self._total = 0
        self._kept = 0
        self._sold = 0
        self._eff_sum = 0.0
        self._started_at: float | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick_time)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        self._header = ScanHeader()
        outer.addWidget(self._header)

        self._stats = SessionStats()
        outer.addWidget(self._stats)

        # ── hero row: last rune (1.2fr) + upgrade (1fr) ──
        hero = QWidget()
        hero_grid = QGridLayout(hero)
        hero_grid.setContentsMargins(0, 0, 0, 0)
        hero_grid.setHorizontalSpacing(18)
        hero_grid.setColumnStretch(0, 12)
        hero_grid.setColumnStretch(1, 10)

        self._last_card = LastRuneCard()
        self._upgrade_card = UpgradeRuneCard()
        hero_grid.addWidget(self._last_card, 0, 0)
        hero_grid.addWidget(self._upgrade_card, 0, 1)
        outer.addWidget(hero)

        self._history = HistoryList()
        self._history.item_clicked.connect(self._on_history_clicked)
        outer.addWidget(self._history, 1)

    # ── public API ─────────────────────────────────────────────────────
    def set_active(self, active: bool) -> None:
        self._header.set_active(active)
        if active:
            self._reset_session()
            self._started_at = time.monotonic()
            self._history.set_session_start(self._started_at)
            self._timer.start()
            self._tick_time()
        else:
            self._timer.stop()

    def _reset_session(self) -> None:
        """Wipe counters, feed and hero cards on each new scan session."""
        self._total = 0
        self._kept = 0
        self._sold = 0
        self._eff_sum = 0.0
        self._stats.update_counts(total=0, kept=0, sold=0, avg_eff=0.0)
        self._history.clear()
        self._last_card.set_empty()
        self._upgrade_card.set_empty()

    def on_rune(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple[float, float], s2us: tuple[float, float],
        set_bonus: str = "",
    ) -> None:
        self._total += 1
        eff = float(verdict.score or 0.0)
        if verdict.decision == "KEEP":
            self._kept += 1
        elif verdict.decision == "SELL":
            self._sold += 1
        self._eff_sum += eff

        self._stats.update_counts(
            total=self._total, kept=self._kept, sold=self._sold,
            avg_eff=self._eff_sum / self._total if self._total else 0.0,
        )

        self._last_card.update_rune(rune, verdict)
        self._history.add(
            rune, verdict, kind=TYPE_NEW,
            mana=mana, swop=swop, s2us=s2us, set_bonus=set_bonus,
        )

    def on_rune_upgraded(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple[float, float], s2us: tuple[float, float],
        set_bonus: str = "",
    ) -> None:
        self._upgrade_card.update_rune(rune, verdict)
        self._history.add(
            rune, verdict, kind=TYPE_UPGRADE,
            mana=mana, swop=swop, s2us=s2us, set_bonus=set_bonus,
        )

    # ── internals ──────────────────────────────────────────────────────
    def _tick_time(self) -> None:
        if self._started_at is None:
            return
        self._header.update_time(int(time.monotonic() - self._started_at))

    def _on_history_clicked(
        self, rune: Rune, verdict: Verdict, _mana: int,
        _swop: tuple, _s2us: tuple, _set_bonus: str,
    ) -> None:
        # Clicking an item re-plays it into the Last-rune hero card.
        self._last_card.update_rune(rune, verdict)
