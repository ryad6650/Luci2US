"""Scrollable vertical list of HistoryItem - newest on top, capped to MAX items."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout

from models import Rune, Verdict
from ui import theme
from ui.scan.history_item import HistoryItem


MAX_ITEMS = 50


class HistoryList(QScrollArea):
    item_clicked = Signal(object, object, int, tuple, tuple, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFixedWidth(theme.SIZE_HISTORY_W)
        self.setMinimumHeight(theme.SIZE_HISTORY_MAX_H)
        self.setMaximumHeight(theme.SIZE_HISTORY_MAX_H)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"""
            QScrollArea {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(45,31,20,0.85), stop:1 rgba(26,15,7,0.9));
                border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:5px;
            }}
            QScrollBar:vertical {{ width:5px; background:#1a0f07; }}
            QScrollBar::handle:vertical {{ background:#5a3d1f; border-radius:3px; }}
            """
        )

        self._content = QWidget()
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(6, 6, 6, 6)
        self._lay.setSpacing(0)
        self._lay.addStretch()
        self.setWidget(self._content)

    def add(
        self, rune: Rune, verdict: Verdict,
        mana: int = 0, swop: tuple[float, float] = (0.0, 0.0),
        s2us: tuple[float, float] = (0.0, 0.0), set_bonus: str = "",
    ) -> None:
        item = HistoryItem(rune, verdict, mana, swop, s2us, set_bonus)
        item.clicked.connect(self.item_clicked)
        self._lay.insertWidget(0, item)
        while self._lay.count() - 1 > MAX_ITEMS:
            old = self._lay.takeAt(self._lay.count() - 2)
            if old and old.widget():
                old.widget().deleteLater()

    def clear(self) -> None:
        while self._lay.count() > 1:
            old = self._lay.takeAt(0)
            if old and old.widget():
                old.widget().deleteLater()
