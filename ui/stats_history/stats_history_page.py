"""Page Stats & Historique : toolbar periode partagee + QTabWidget (Stats / Historique)."""
from __future__ import annotations

import os
import sqlite3

from PySide6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from history_db import init_db
from ui import theme
from ui.stats_history.history_view import HistoryView
from ui.stats_history.period_bar import PeriodBar, compute_period_range
from ui.stats_history.stats_view import StatsView


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "history.db")


class StatsHistoryPage(QWidget):
    def __init__(
        self, parent: QWidget | None = None, db_path: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._conn: sqlite3.Connection = init_db(db_path or _DEFAULT_DB_PATH)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # --- Header (titre + barre periode) ---
        header = QHBoxLayout()
        header.setSpacing(12)

        title = QLabel("Stats & Historique")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:20px; font-weight:700; letter-spacing:0.5px;"
        )
        header.addWidget(title)
        header.addStretch()

        self._period_bar = PeriodBar()
        self._period_bar.period_changed.connect(self._on_period_changed)
        header.addWidget(self._period_bar)

        outer.addLayout(header)

        # --- QTabWidget (Stats / Historique) ---
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            f"QTabWidget::pane {{ border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" background:{theme.COLOR_BG_FRAME}; }}"
            f"QTabBar::tab {{ background:{theme.COLOR_BG_GRAD_LO};"
            f" color:{theme.COLOR_TEXT_SUB}; padding:8px 24px;"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" font-size:12px; font-weight:600; }}"
            f"QTabBar::tab:selected {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD}; }}"
        )

        self._stats_view = StatsView()
        self._history_view = HistoryView()
        self._tabs.addTab(self._stats_view, "Stats")
        self._tabs.addTab(self._history_view, "Historique")
        outer.addWidget(self._tabs, 1)

        # Refresh initial avec periode par defaut (ALL)
        self._dispatch_refresh()

    def _on_period_changed(self, _key: str) -> None:
        self._dispatch_refresh()

    def _dispatch_refresh(self) -> None:
        start, end = compute_period_range(self._period_bar.current_period())
        self._stats_view.refresh(self._conn, start, end)
        self._history_view.refresh(self._conn, start, end)
