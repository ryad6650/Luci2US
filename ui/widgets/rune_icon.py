"""Simple rune icon: just the set logo centered in a fixed-size square."""
from __future__ import annotations
import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

from ui import theme


class RuneIcon(QWidget):
    def __init__(self, size: int = theme.SIZE_RUNE_ICON_HIST, parent=None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(QSize(size, size))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setScaledContents(True)
        layout.addWidget(self._label)

    def set_logo(self, set_fr: str) -> None:
        path = theme.asset_set_logo(theme.set_asset_name(set_fr))
        if os.path.isfile(path):
            self._label.setPixmap(QPixmap(path))
        else:
            self._label.clear()
