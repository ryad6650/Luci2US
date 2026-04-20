"""Barre de periode partagee (Aujourd'hui / 7j / 30j / Tout) + helper compute_period_range."""
from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

from ui import theme

PERIOD_TODAY = "today"
PERIOD_7D = "7d"
PERIOD_30D = "30d"
PERIOD_ALL = "all"


def compute_period_range(
    key: str, *, now: datetime | None = None
) -> tuple[str, str]:
    """Retourne (start_iso, end_iso) format 'YYYY-MM-DD HH:MM:SS' pour la cle donnee.

    Cle inconnue -> equivalent PERIOD_ALL (debut = 2000-01-01).
    """
    if now is None:
        now = datetime.now()
    end = now.strftime("%Y-%m-%d 23:59:59")

    if key == PERIOD_TODAY:
        start = now.strftime("%Y-%m-%d 00:00:00")
    elif key == PERIOD_7D:
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
    elif key == PERIOD_30D:
        start = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    else:
        start = "2000-01-01 00:00:00"
    return start, end


class PeriodBar(QWidget):
    """4 boutons radio-like avec style bronze/or. Emet period_changed(key)."""

    period_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current = PERIOD_ALL

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addStretch()

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self._btn_today = self._make_btn("Aujourd'hui", PERIOD_TODAY)
        self._btn_7d = self._make_btn("7j", PERIOD_7D)
        self._btn_30d = self._make_btn("30j", PERIOD_30D)
        self._btn_all = self._make_btn("Tout", PERIOD_ALL)

        for btn in (self._btn_today, self._btn_7d, self._btn_30d, self._btn_all):
            lay.addWidget(btn)
            self._group.addButton(btn)

        self._btn_all.setChecked(True)

    def _make_btn(self, label: str, period_key: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_SUB};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:4px 12px;"
            f" font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ color:{theme.COLOR_GOLD}; }}"
            f"QPushButton:checked {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD}; border:1px solid {theme.COLOR_BRONZE}; }}"
        )
        btn.clicked.connect(lambda _checked=False, k=period_key: self._on_clicked(k))
        return btn

    def _on_clicked(self, key: str) -> None:
        if self._current == key:
            return
        self._current = key
        self.period_changed.emit(key)

    def current_period(self) -> str:
        return self._current
