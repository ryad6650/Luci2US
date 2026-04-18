"""Panel showing runes the user is manually powering up (+3/+6/+9/+12).

Keyed by a synthetic identity (set, slot, stars, grade, main_stat.type) since
Rune has no stable id. Re-upgrades of the same rune update the existing entry
in-place (level and score bumped), keeping the list deduplicated.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
)

from models import Rune, Verdict
from ui import theme
from ui.widgets.rune_icon import RuneIcon


MAX_ITEMS = 30


def _rune_key(rune: Rune) -> tuple:
    return (rune.set, rune.slot, rune.stars, rune.grade, rune.main_stat.type)


class _UpgradeItem(QFrame):
    def __init__(self, rune: Rune, verdict: Verdict, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"_UpgradeItem {{ background:rgba(245,160,48,0.06);"
            f"border:1px solid {theme.COLOR_POWERUP}; border-radius:5px; }}"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(7, 5, 9, 5)
        lay.setSpacing(8)

        self._icon = RuneIcon(size=theme.SIZE_RUNE_ICON_HIST)
        self._icon.set_logo(rune.set)
        lay.addWidget(self._icon)

        text_box = QWidget()
        tl = QVBoxLayout(text_box)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(1)
        self._name = QLabel()
        self._name.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:11px; font-weight:600;"
        )
        tl.addWidget(self._name)
        self._sub = QLabel()
        self._sub.setTextFormat(Qt.TextFormat.RichText)
        self._sub.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
        )
        tl.addWidget(self._sub)
        lay.addWidget(text_box, 1)

        self._score = QLabel()
        self._score.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:11px; font-weight:700;"
        )
        lay.addWidget(self._score, 0, Qt.AlignmentFlag.AlignVCenter)

        self.update_values(rune, verdict)

    def update_values(self, rune: Rune, verdict: Verdict) -> None:
        self._name.setText(f"{rune.set} ({rune.slot})")
        self._sub.setText(
            f"<span style='color:{theme.COLOR_POWERUP};font-weight:700'>+{rune.level}</span>"
            f" &middot; {rune.grade}"
        )
        self._score.setText(f"Score {int(verdict.score or 0)}")


class UpgradeList(QScrollArea):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setMinimumHeight(220)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"""
            QScrollArea {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(45,31,20,0.85), stop:1 rgba(26,15,7,0.9));
                border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:7px;
            }}
            QScrollBar:vertical {{ width:5px; background:#1a0f07; }}
            QScrollBar::handle:vertical {{ background:#5a3d1f; border-radius:3px; }}
            """
        )

        self._content = QWidget()
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(8, 8, 8, 8)
        self._lay.setSpacing(5)
        self._empty = QLabel("Aucune rune en amelioration")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-style:italic; padding:24px;"
        )
        self._lay.addWidget(self._empty)
        self._lay.addStretch()
        self.setWidget(self._content)

        self._items: dict[tuple, _UpgradeItem] = {}

    def upsert(self, rune: Rune, verdict: Verdict) -> None:
        self._empty.hide()
        key = _rune_key(rune)
        existing = self._items.get(key)
        if existing is not None:
            existing.update_values(rune, verdict)
            self._lay.removeWidget(existing)
            self._lay.insertWidget(0, existing)
            return

        item = _UpgradeItem(rune, verdict)
        self._items[key] = item
        self._lay.insertWidget(0, item)

        while len(self._items) > MAX_ITEMS:
            oldest_key = next(iter(self._items))
            old = self._items.pop(oldest_key)
            self._lay.removeWidget(old)
            old.deleteLater()

    def clear(self) -> None:
        for item in self._items.values():
            self._lay.removeWidget(item)
            item.deleteLater()
        self._items.clear()
        self._empty.show()
