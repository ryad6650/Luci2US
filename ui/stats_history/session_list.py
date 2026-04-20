"""Liste scrollable des sessions. Chaque ligne est cliquable."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ui import theme


def format_duration(start: str | None, end: str | None) -> str:
    if not start or not end:
        return "\u2014"
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        s = start.replace("T", " ")[:19]
        e = end.replace("T", " ")[:19]
        delta = datetime.strptime(e, fmt) - datetime.strptime(s, fmt)
        total_sec = int(delta.total_seconds())
        if total_sec < 0:
            return "\u2014"
        h, rem = divmod(total_sec, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h{m:02d}m"
        return f"{m}m{s:02d}s"
    except (ValueError, TypeError):
        return "\u2014"


class _SessionRow(QFrame):
    clicked = Signal(int)

    def __init__(self, session: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session_id = int(session["id"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"_SessionRow {{ background:rgba(26,15,7,0.6);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
            f"_SessionRow:hover {{ background:rgba(198,112,50,0.2);"
            f" border:1px solid {theme.COLOR_BRONZE}; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        start = str(session.get("start_time") or "")
        date_str = start.replace("T", " ")[:16] if start else "\u2014"

        date_lbl = QLabel(date_str)
        date_lbl.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:12px; font-weight:600;"
        )
        date_lbl.setMinimumWidth(130)
        row.addWidget(date_lbl)

        dungeon = session.get("dungeon") or "\u2014"
        dungeon_lbl = QLabel(dungeon)
        dungeon_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:12px;"
        )
        dungeon_lbl.setMinimumWidth(140)
        row.addWidget(dungeon_lbl)

        duration = format_duration(session.get("start_time"), session.get("end_time"))
        dur_lbl = QLabel(duration)
        dur_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:12px;"
        )
        dur_lbl.setMinimumWidth(60)
        row.addWidget(dur_lbl)

        row.addStretch()

        # Compteurs colores
        for label, value, color in (
            ("Scan", session.get("total", 0), theme.COLOR_TEXT_MAIN),
            ("Keep", session.get("keep", 0), theme.COLOR_KEEP),
            ("Sell", session.get("sell", 0), theme.COLOR_SELL),
            ("PwrUp", session.get("power_up", 0), theme.COLOR_POWERUP),
        ):
            lbl = QLabel(f"{label} {value}")
            lbl.setStyleSheet(
                f"color:{color}; font-size:11px; font-weight:600;"
            )
            row.addWidget(lbl)

        avg = session.get("avg_score")
        if avg is None:
            eff_text = "Eff \u2014"
        else:
            eff_text = f"Eff {float(avg):.1f}"
        eff_lbl = QLabel(eff_text)
        eff_lbl.setStyleSheet(
            f"color:{theme.COLOR_BRONZE_LIGHT}; font-size:12px; font-weight:700;"
        )
        eff_lbl.setMinimumWidth(80)
        row.addWidget(eff_lbl)

        chevron = QLabel("\u25B6")  # ▶
        chevron.setStyleSheet(f"color:{theme.COLOR_BRONZE}; font-size:12px;")
        row.addWidget(chevron)

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._session_id)
        super().mousePressEvent(ev)


class SessionList(QWidget):
    session_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[_SessionRow] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._lay = QVBoxLayout(self._container)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(4)
        self._lay.addStretch()

        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll)

        self._empty = QLabel("Aucune session pour cette periode.")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:13px; font-style:italic;"
            f" padding:24px;"
        )
        outer.addWidget(self._empty)
        self._empty.setVisible(True)

    def set_sessions(self, sessions: list[dict]) -> None:
        # Purge rows
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        # Empty state
        self._empty.setVisible(not sessions)
        self._scroll.setVisible(bool(sessions))

        stretch_index = self._lay.count() - 1
        for session in sessions:
            row = _SessionRow(session)
            row.clicked.connect(self.session_clicked.emit)
            self._rows.append(row)
            self._lay.insertWidget(stretch_index, row)
            stretch_index += 1
