"""KEEP / SELL / PWR tag badge — matches .hist-tag in v13."""
from __future__ import annotations
from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from ui import theme


class TagKind(Enum):
    KEEP = "keep"
    SELL = "sell"
    POWERUP = "powerup"


_LABELS = {TagKind.KEEP: "KEEP", TagKind.SELL: "SELL", TagKind.POWERUP: "PWR"}


class TagBadge(QLabel):
    def __init__(self, kind: TagKind, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_kind(kind)

    def set_kind(self, kind: TagKind) -> None:
        self._kind = kind
        self.setText(_LABELS[kind])
        bg = {
            TagKind.KEEP: theme.COLOR_KEEP,
            TagKind.SELL: theme.COLOR_SELL,
            TagKind.POWERUP: theme.COLOR_POWERUP,
        }[kind]
        fg = "#1a0f07" if kind != TagKind.SELL else "#fff"
        self.setStyleSheet(
            f"background:{bg}; color:{fg};"
            f"font-size:9px; font-weight:800; letter-spacing:.5px;"
            f"padding:3px 6px; border-radius:3px;"
        )
