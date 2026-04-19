"""Sous-onglet Stats : grille 2x2 de 4 cartes (Verdict / Grade / Sessions-jour / Top runes)."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QFrame, QGridLayout, QVBoxLayout, QWidget

from ui import theme
from ui.stats_history.charts import (
    GradeBarChart, StackedBarChart, TimelineBarChart, TopRunesList,
)


def _card_frame() -> QFrame:
    """Cartouche bronze/or qui encadre un chart."""
    card = QFrame()
    card.setStyleSheet(
        f"QFrame {{ background:rgba(26,15,7,0.7);"
        f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
    )
    return card


class StatsView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 12, 0, 0)
        outer.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)

        # 4 cartes (row, col)
        self._verdict_chart = StackedBarChart()
        self._grade_chart = GradeBarChart()
        self._timeline_chart = TimelineBarChart()
        self._top_runes = TopRunesList()

        placements = [
            (self._verdict_chart, 0, 0),
            (self._grade_chart, 0, 1),
            (self._timeline_chart, 1, 0),
            (self._top_runes, 1, 1),
        ]
        for widget, row, col in placements:
            card = _card_frame()
            inner = QVBoxLayout(card)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(widget)
            grid.addWidget(card, row, col)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid, 1)

    def refresh(self, conn: sqlite3.Connection, start: str, end: str) -> None:
        # Recupere toutes les runes de la periode (avec session pour timeline)
        runes = conn.execute(
            'SELECT r."set", r.slot, r.stars, r.grade, r.verdict, '
            "       r.main_stat, r.score "
            "FROM runes r JOIN sessions s ON r.session_id = s.id "
            "WHERE s.start_time >= ? AND s.start_time <= ? "
            "ORDER BY r.id",
            (start, end),
        ).fetchall()
        runes = [dict(r) for r in runes]

        sessions = conn.execute(
            "SELECT start_time FROM sessions "
            "WHERE start_time >= ? AND start_time <= ?",
            (start, end),
        ).fetchall()
        sessions = [dict(s) for s in sessions]

        # Agreger verdicts
        verdict_counts: dict[str, int] = {}
        for r in runes:
            v = r["verdict"]
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
        self._verdict_chart.set_counts(verdict_counts)

        # Agreger grades
        grade_counts: dict[str, int] = {}
        for r in runes:
            g = r["grade"]
            grade_counts[g] = grade_counts.get(g, 0) + 1
        self._grade_chart.set_counts(grade_counts)

        # Timeline sessions/jour
        self._timeline_chart.set_sessions(sessions)

        # Top runes
        self._top_runes.set_runes(runes)
