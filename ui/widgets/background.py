"""Luci2US background — variation D (magenta warm-dark).

Paints two radial gradients over the deep brown-black base to match
design_handoff_scan/variation-d.jsx:
    radial-gradient(ellipse at 12% 0%,   #3a1624 0%, #0d0907 50%)
    radial-gradient(ellipse at 100% 100%, #2a1018 0%, #0d0907 55%)
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

        # Base fill
        p.fillRect(r, QColor(theme.D.BG))

        # Top-left radial (magenta plum)
        radius_a = max(w, h) * 0.85
        g1 = QRadialGradient(w * 0.12, 0.0, radius_a)
        c1 = QColor(theme.D.BG_GRAD_HI)
        c1.setAlpha(230)
        g1.setColorAt(0.0, c1)
        g1.setColorAt(0.50, QColor(theme.D.BG))
        g1.setColorAt(1.0, QColor(theme.D.BG))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(g1))
        p.drawRect(QRectF(r))

        # Bottom-right radial (burgundy)
        radius_b = max(w, h) * 0.95
        g2 = QRadialGradient(float(w), float(h), radius_b)
        c2 = QColor(theme.D.BG_GRAD_LO)
        c2.setAlpha(210)
        g2.setColorAt(0.0, c2)
        g2.setColorAt(0.55, QColor(0, 0, 0, 0))
        g2.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(g2))
        p.drawRect(QRectF(r))
        p.end()
