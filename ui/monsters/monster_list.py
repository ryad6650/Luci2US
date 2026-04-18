"""Stub temporaire - sera complete en Task 2."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout


class MonsterList(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list = []
        QVBoxLayout(self)

    def set_monsters(self, monsters: list) -> None:
        self._rows = list(monsters)
