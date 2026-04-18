"""Stub temporaire - sera complete en Task 6-7."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout


class MonsterDetail(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        QVBoxLayout(self)

    def set_monster(self, monster) -> None:
        self._monster = monster
