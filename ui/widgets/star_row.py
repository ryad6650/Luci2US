"""★ row placed above a rune card icon — matches .rc-stars in v13."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ui import theme


class StarRow(QLabel):
    def __init__(self, count: int = 6, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("★" * count)
        self.setStyleSheet(
            f"color:#f8c040; font-size:9px; letter-spacing:-1.4px;"
            f"background:transparent;"
        )
