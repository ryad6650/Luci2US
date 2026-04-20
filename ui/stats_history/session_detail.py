"""Vue detail d'une session : breadcrumb + mini-charts Verdict/Grade + table des runes."""
from __future__ import annotations

import json
import sqlite3

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from history_db import get_runes_by_session
from ui import theme
from ui.stats_history.charts import GradeBarChart, StackedBarChart
from ui.stats_history.session_list import format_duration


_COLS = ["Set", "Slot", "Etoiles", "Grade", "Main", "Eff", "Verdict"]


class SessionDetail(QWidget):
    back_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        # --- Breadcrumb ---
        crumb = QHBoxLayout()
        crumb.setSpacing(8)
        self._back_btn = QPushButton("< Retour")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{theme.COLOR_BRONZE};"
            f" border:none; font-size:13px; font-weight:600; padding:4px 8px; }}"
            f"QPushButton:hover {{ color:{theme.COLOR_EMBER}; }}"
        )
        self._back_btn.clicked.connect(self.back_clicked.emit)
        crumb.addWidget(self._back_btn)

        self._crumb = QLabel("Historique /")
        self._crumb.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:13px;"
        )
        crumb.addWidget(self._crumb)
        crumb.addStretch()
        outer.addLayout(crumb)

        # --- Header compact (date + duree + compteurs) ---
        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background:rgba(26,15,7,0.8);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 10, 14, 10)
        h_lay.setSpacing(16)

        self._title_lbl = QLabel("")
        self._title_lbl.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:15px; font-weight:700;"
        )
        h_lay.addWidget(self._title_lbl)
        h_lay.addStretch()

        self._meta_lbl = QLabel("")
        self._meta_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:12px;"
        )
        h_lay.addWidget(self._meta_lbl)

        outer.addWidget(header)

        # --- Mini-charts (row horizontal) ---
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        self._verdict_chart = StackedBarChart()
        self._grade_chart = GradeBarChart()
        for chart in (self._verdict_chart, self._grade_chart):
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background:rgba(26,15,7,0.7);"
                f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
            )
            inner = QVBoxLayout(card)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(chart)
            charts_row.addWidget(card, 1)

        outer.addLayout(charts_row)

        # --- Table des runes ---
        self._table = QTableWidget(0, len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setStyleSheet(
            f"QTableWidget {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" gridline-color:{theme.COLOR_BORDER_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; font-size:11px; }}"
            f"QHeaderView::section {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" padding:4px; font-size:11px; font-weight:700; }}"
        )
        outer.addWidget(self._table, 1)

    def load_session(self, conn: sqlite3.Connection, session_id: int) -> None:
        """Charge le header + charts + table pour la session donnee."""
        session_row = conn.execute(
            "SELECT id, start_time, end_time, dungeon, total, keep, sell "
            "FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if session_row is None:
            self._title_lbl.setText("Session introuvable")
            self._meta_lbl.setText("")
            self._crumb.setText("Historique /")
            self._verdict_chart.set_counts({})
            self._grade_chart.set_counts({})
            self._table.setRowCount(0)
            return

        session = dict(session_row)

        # Header
        start = session.get("start_time") or ""
        date_str = start.replace("T", " ")[:16]
        dungeon = session.get("dungeon") or "\u2014"
        self._title_lbl.setText(f"{dungeon} \u2014 {date_str}")
        self._crumb.setText(f"Historique / {dungeon}")

        duration = format_duration(session.get("start_time"), session.get("end_time"))
        self._meta_lbl.setText(
            f"Scan {session.get('total', 0)} \u00b7 "
            f"Keep {session.get('keep', 0)} \u00b7 "
            f"Sell {session.get('sell', 0)} \u00b7 "
            f"Duree {duration}"
        )

        # Runes
        runes = get_runes_by_session(conn, session_id)

        verdict_counts: dict[str, int] = {}
        grade_counts: dict[str, int] = {}
        for r in runes:
            verdict_counts[r["verdict"]] = verdict_counts.get(r["verdict"], 0) + 1
            grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1
        self._verdict_chart.set_counts(verdict_counts)
        self._grade_chart.set_counts(grade_counts)

        self._populate_table(runes)

    def _populate_table(self, runes: list[dict]) -> None:
        self._table.setRowCount(0)
        for r in runes:
            row = self._table.rowCount()
            self._table.insertRow(row)

            score = r.get("score")
            eff_text = f"{float(score):.1f}" if score is not None else "\u2014"

            cells = [
                r.get("set", ""),
                str(r.get("slot", "")),
                str(r.get("stars", "")),
                r.get("grade", ""),
                r.get("main_stat", ""),
                eff_text,
                r.get("verdict", ""),
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Couleur verdict
                if col == 6:
                    if val == "KEEP":
                        item.setForeground(QColor(theme.COLOR_KEEP))
                    elif val == "SELL":
                        item.setForeground(QColor(theme.COLOR_SELL))
                    elif val == "POWER-UP":
                        item.setForeground(QColor(theme.COLOR_POWERUP))
                self._table.setItem(row, col, item)
