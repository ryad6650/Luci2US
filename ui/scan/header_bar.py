"""Header row: Start button + state indicator."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout

from ui.widgets.glow_button import GlowButton
from ui.widgets.state_indicator import StateIndicator


class HeaderBar(QWidget):
    start_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        self._btn = GlowButton("\u25b6 START")
        self._btn.clicked.connect(self.start_clicked.emit)
        lay.addWidget(self._btn)

        self._state = StateIndicator()
        lay.addWidget(self._state)
        lay.addStretch()

    def set_active(self, active: bool) -> None:
        self._state.set_active(active)
        self._btn.setText("\u25a0 STOP" if active else "\u25b6 START")
