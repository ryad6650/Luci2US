"""Luci2US background — Dark Slate (gris-bleu très foncé).

Fond uniforme #1a1d24 + dégradés subtils haut-gauche / bas-droite
pour apporter un léger relief sans partir dans les tons chauds.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget

from ui import theme


class BackgroundPane(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        w = r.width()
        h = r.height()

        # Base fill — Dark Slate
        p.fillRect(r, QColor(theme.D.BG))

        # Top-left radial (slight lift)
        radius_a = max(w, h) * 0.85
        g1 = QRadialGradient(w * 0.12, 0.0, radius_a)
        c1 = QColor(theme.D.BG_GRAD_HI)
        c1.setAlpha(170)
        g1.setColorAt(0.0, c1)
        g1.setColorAt(0.50, QColor(theme.D.BG))
        g1.setColorAt(1.0, QColor(theme.D.BG))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g1))
        p.drawRect(QRectF(r))

        # Bottom-right subtle radial
        radius_b = max(w, h) * 0.95
        g2 = QRadialGradient(float(w), float(h), radius_b)
        c2 = QColor(theme.D.BG_GRAD_LO)
        c2.setAlpha(140)
        g2.setColorAt(0.0, c2)
        g2.setColorAt(0.55, QColor(0, 0, 0, 0))
        g2.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(g2))
        p.drawRect(QRectF(r))
        p.end()
