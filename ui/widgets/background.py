"""Rune Forge background: radial gradients, runic circles, animated embers."""
from __future__ import annotations
import random

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, Property
from PySide6.QtGui import QPainter, QRadialGradient, QLinearGradient, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


class _Ember(QWidget):
    """Single floating amber dot."""
    def __init__(self, size: int, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._offset = 0.0

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(245, 160, 48, 200)
        p.setBrush(QBrush(c))
        p.setPen(Qt.NoPen)
        p.drawEllipse(self.rect())

    def get_offset(self) -> float:
        return self._offset

    def set_offset(self, v: float) -> None:
        self._offset = v
        self.move(self.x(), self._base_y + int(v))

    offset = Property(float, get_offset, set_offset)


# Ember seeds (relative position %, size px, delay ms, duration ms)
EMBER_SEEDS = [
    (8, 12, 3, 0, 8000), (22, 35, 2, 2000, 9000), (12, 58, 4, 4000, 6000),
    (42, 18, 2, 1000, 10000), (38, 68, 3, 3000, 8000), (62, 25, 2, 5000, 7000),
    (72, 52, 4, 2000, 9000), (58, 78, 3, 6000, 6000),
    (86, 14, 2, 4000, 8000), (92, 45, 3, 1000, 10000),
]


class BackgroundPane(QWidget):
    """The tab background — draws gradients/circles in paintEvent, hosts embers as children."""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._embers: list[_Ember] = []
        self._anims: list[QPropertyAnimation] = []
        for _ in EMBER_SEEDS:
            e = _Ember(1, self)
            self._embers.append(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        w, h = self.width(), self.height()
        for ember, (px, py, size, delay, dur) in zip(self._embers, EMBER_SEEDS):
            ember.setFixedSize(size, size)
            x = int(w * px / 100)
            y = int(h * py / 100)
            ember._base_y = y
            ember.move(x, y)
        # (Re)start animations once on first resize
        if not self._anims:
            for ember, (_, _, _, delay, dur) in zip(self._embers, EMBER_SEEDS):
                a = QPropertyAnimation(ember, b"offset")
                a.setStartValue(0.0)
                a.setKeyValueAt(0.5, -20.0)
                a.setEndValue(0.0)
                a.setDuration(dur)
                a.setLoopCount(-1)
                a.setEasingCurve(QEasingCurve.InOutSine)
                a.start()
                self._anims.append(a)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        # Linear base
        g = QLinearGradient(0, 0, 0, r.height())
        g.setColorAt(0.0, QColor("#1a0f07"))
        g.setColorAt(1.0, QColor("#120a05"))
        p.fillRect(r, QBrush(g))

        # Radial gold (top-left)
        rg1 = QRadialGradient(r.width() * 0.18, r.height() * 0.28, r.width() * 0.45)
        rg1.setColorAt(0.0, QColor(232, 176, 64, 23))
        rg1.setColorAt(1.0, Qt.transparent)
        p.fillRect(r, QBrush(rg1))

        # Radial orange (bottom-right)
        rg2 = QRadialGradient(r.width() * 0.82, r.height() * 0.78, r.width() * 0.50)
        rg2.setColorAt(0.0, QColor(200, 80, 40, 28))
        rg2.setColorAt(1.0, Qt.transparent)
        p.fillRect(r, QBrush(rg2))

        # Circles
        pen = QPen(QColor(232, 176, 64, 31))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(-80, -80, 280, 280))

        pen2 = QPen(QColor(200, 80, 40, 26))
        pen2.setWidth(1)
        p.setPen(pen2)
        p.drawEllipse(QRectF(r.width() - 220, r.height() - 220, 320, 320))

        # Runic symbols (Elder Futhark) — big translucent glyphs, mirror v13 .rune-sym
        p.setFont(QFont("Georgia", 90, QFont.Bold))
        p.setPen(QColor(232, 176, 64, 10))
        p.drawText(20, 110, "\u16DF")      # ᛟ (Othala) top-left
        p.setPen(QColor(200, 80, 40, 13))
        p.drawText(r.width() - 130, r.height() - 20, "\u16B1")  # ᚱ (Raido) bottom-right
