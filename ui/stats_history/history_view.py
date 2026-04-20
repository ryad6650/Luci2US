"""Sous-onglet Historique : QStackedWidget interne (liste sessions / detail session)."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from history_db import get_sessions_with_stats
from ui.stats_history.session_detail import SessionDetail
from ui.stats_history.session_list import SessionList


class HistoryView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._conn: sqlite3.Connection | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 12, 0, 0)
        outer.setSpacing(0)

        self._stack = QStackedWidget()
        self._list = SessionList()
        self._detail = SessionDetail()
        self._stack.addWidget(self._list)
        self._stack.addWidget(self._detail)
        outer.addWidget(self._stack)

        self._list.session_clicked.connect(self._on_session_clicked)
        self._detail.back_clicked.connect(self._on_back)

    def refresh(self, conn: sqlite3.Connection, start: str, end: str) -> None:
        self._conn = conn
        sessions = get_sessions_with_stats(conn, start=start, end=end)
        self._list.set_sessions(sessions)
        self._stack.setCurrentIndex(0)  # revient a la liste a chaque refresh

    def _on_session_clicked(self, session_id: int) -> None:
        self._stack.setCurrentIndex(1)
        if self._conn is None:
            return
        self._detail.load_session(self._conn, session_id)

    def _on_back(self) -> None:
        self._stack.setCurrentIndex(0)
