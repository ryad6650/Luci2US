"""History panel — 2-column grid of HistoryItem + filter chips.

Design variation D:
- header: "HISTORIQUE" + "N runes · session HH:MM" + filter chips (Tout/Nouvelle/Amelioree/Reroll)
- body:   scrollable QGridLayout, newest prepended, 2 columns, gap 8
"""
from __future__ import annotations
import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from models import Rune, Verdict
from ui import theme
from ui.scan.history_item import HistoryItem, TYPE_NEW, TYPE_UPGRADE, TYPE_REROLL


MAX_ITEMS = 80

FILTERS = [
    ("all",     "Tout"),
    ("new",     "Nouvelle"),
    ("upgrade", "Amelioree"),
    ("reroll",  "Reroll"),
]
_FILTER_TO_KIND = {
    "new":     TYPE_NEW,
    "upgrade": TYPE_UPGRADE,
    "reroll":  TYPE_REROLL,
}


class _FilterChip(QPushButton):
    def __init__(self, key: str, label: str, parent=None) -> None:
        super().__init__(label, parent)
        self._key = key
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(26)
        self._apply(False)

    @property
    def key(self) -> str:
        return self._key

    def _apply(self, active: bool) -> None:
        bg = theme.D.ACCENT_DIM if active else "transparent"
        fg = theme.D.ACCENT if active else theme.D.FG_MUTE
        self.setStyleSheet(
            f"""
            QPushButton {{
                padding:0 12px; border:none; border-radius:999px;
                background:{bg}; color:{fg};
                font-family:'{theme.D.FONT_UI}'; font-size:11px; font-weight:500;
            }}
            QPushButton:hover {{ background:{theme.D.ACCENT_DIM}; color:{theme.D.ACCENT}; }}
            """
        )

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply(active)


class HistoryList(QFrame):
    item_clicked = Signal(object, object, int, tuple, tuple, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("HistoryList")
        self.setStyleSheet(
            f"""
            #HistoryList {{
                background:{theme.D.PANEL};
                border:1px solid {theme.D.BORDER};
                border-radius:14px;
            }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── header ──
        header = QFrame()
        header.setObjectName("HistoryHeader")
        header.setStyleSheet(
            f"""
            #HistoryHeader {{
                background:transparent;
                border-bottom:1px solid {theme.D.BORDER};
            }}
            """
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(22, 16, 22, 16)
        hl.setSpacing(10)

        title = QLabel("HISTORIQUE")
        title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; font-weight:700; letter-spacing:1.2px;"
        )
        hl.addWidget(title, 0, Qt.AlignmentFlag.AlignVCenter)

        self._meta = QLabel("0 runes \u00B7 session 00:00")
        self._meta.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        hl.addWidget(self._meta, 0, Qt.AlignmentFlag.AlignVCenter)
        hl.addStretch(1)

        self._chips: dict[str, _FilterChip] = {}
        for key, label in FILTERS:
            chip = _FilterChip(key, label)
            chip.clicked.connect(lambda _c=False, k=key: self._on_filter(k))
            hl.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
            self._chips[key] = chip
        self._chips["all"].set_active(True)
        self._active_filter = "all"

        outer.addWidget(header)

        # ── scrollable grid ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            """
            QScrollArea { background:transparent; }
            QScrollBar:vertical { width:6px; background:transparent; margin:6px; }
            QScrollBar::handle:vertical {
                background:rgba(240,104,154,0.25); border-radius:3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
            """
        )

        self._content = QWidget()
        self._grid = QGridLayout(self._content)
        self._grid.setContentsMargins(14, 14, 14, 14)
        self._grid.setHorizontalSpacing(8)
        self._grid.setVerticalSpacing(8)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1)
        self._content.setStyleSheet("background:transparent;")
        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll, 1)

        self._items: list[HistoryItem] = []
        self._session_start = time.monotonic()

        self._ago_timer = QTimer(self)
        self._ago_timer.setInterval(5000)
        self._ago_timer.timeout.connect(self._refresh_agos)
        self._ago_timer.start()

    def set_session_start(self, monotonic_ts: float) -> None:
        self._session_start = monotonic_ts
        self._update_meta()

    def _refresh_agos(self) -> None:
        for it in self._items:
            it.refresh_ago()
        self._update_meta()

    def _update_meta(self) -> None:
        seconds = int(max(0, time.monotonic() - self._session_start))
        h, r = divmod(seconds, 3600)
        m = r // 60
        stamp = f"{h:02d}:{m:02d}" if h else f"00:{m:02d}"
        self._meta.setText(f"{len(self._items)} runes \u00B7 session {stamp}")

    def add(
        self, rune: Rune, verdict: Verdict, kind: str = TYPE_NEW,
        mana: int = 0, swop: tuple[float, float] = (0.0, 0.0),
        s2us: tuple[float, float] = (0.0, 0.0), set_bonus: str = "",
    ) -> None:
        item = HistoryItem(
            rune, verdict, kind=kind,
            mana=mana, swop=swop, s2us=s2us, set_bonus=set_bonus,
        )
        item.clicked.connect(self.item_clicked)
        self._items.insert(0, item)
        while len(self._items) > MAX_ITEMS:
            old = self._items.pop()
            old.setParent(None)
            old.deleteLater()
        self._relayout()
        self._update_meta()

    def clear(self) -> None:
        for it in self._items:
            it.setParent(None)
            it.deleteLater()
        self._items.clear()
        self._relayout()
        self._update_meta()

    def _on_filter(self, key: str) -> None:
        self._active_filter = key
        for k, chip in self._chips.items():
            chip.set_active(k == key)
        self._relayout()

    def _relayout(self) -> None:
        # Detach every item from the grid (they stay parented to self._content).
        while self._grid.count():
            self._grid.takeAt(0)

        target = self._active_filter
        col = 0
        row = 0
        for item in self._items:
            matches = (
                target == "all"
                or item.kind == _FILTER_TO_KIND.get(target, TYPE_NEW)
            )
            if not matches:
                item.hide()
                continue
            if item.parent() is not self._content:
                item.setParent(self._content)
            item.show()
            self._grid.addWidget(item, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        self._grid.setRowStretch(row + 1, 1)
