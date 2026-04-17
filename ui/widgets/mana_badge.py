"""Mana value badge: mana.png icon + integer value, pill background."""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from ui import theme


class ManaBadge(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"background:{theme.COLOR_MANA_BG}; color:{theme.COLOR_TEXT_SUB};"
            f"border:1px solid {theme.COLOR_MANA_BORDER}; border-radius:3px;"
            f"font-size:10px; font-weight:600;"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 2, 8, 2)
        lay.setSpacing(4)

        icon = QLabel()
        icon.setFixedSize(QSize(theme.SIZE_MANA_ICON, theme.SIZE_MANA_ICON))
        icon.setPixmap(QPixmap(theme.asset_icon("mana")))
        icon.setScaledContents(True)
        lay.addWidget(icon)

        self._value_label = QLabel("0")
        self._value_label.setAlignment(Qt.AlignVCenter)
        lay.addWidget(self._value_label)

    def set_value(self, v: int) -> None:
        self._value_label.setText(str(v))
