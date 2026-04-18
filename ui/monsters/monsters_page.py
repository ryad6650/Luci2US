"""Monstres tab - QStackedWidget interne (liste/detail)."""
from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ui.monsters.monster_detail import MonsterDetail
from ui.monsters.monster_list import MonsterList


class MonstersPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._stack = QStackedWidget()
        self._list = MonsterList()
        self._detail = MonsterDetail()
        self._stack.addWidget(self._list)
        self._stack.addWidget(self._detail)
        lay.addWidget(self._stack)

        self._list.monster_clicked.connect(self._on_monster_clicked)
        self._detail.back_clicked.connect(self._on_back)

    def apply_profile(self, profile: dict, saved_at) -> None:
        monsters = profile.get("monsters", [])
        self._list.set_monsters(monsters)
        self._stack.setCurrentIndex(0)

    def _on_monster_clicked(self, monster) -> None:
        self._detail.set_monster(monster)
        self._stack.setCurrentIndex(1)

    def _on_back(self) -> None:
        self._stack.setCurrentIndex(0)
