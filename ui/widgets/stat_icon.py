"""Small QPainter-rendered icons for the Scan session-stats cards.

A rune-shaped hexagon with an optional inner glyph — check (Keep),
cross (Sell) or a 4-point sparkle (Efficacy). Tinted by the card accent
colour, matches the 38x38 box the SessionStats cards allocate.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QWidget


OVERLAY_NONE    = "none"
OVERLAY_CHECK   = "check"
OVERLAY_CROSS   = "cross"
OVERLAY_SPARKLE = "sparkle"


def _hex_polygon(w: float, h: float) -> QPolygonF:
    return QPolygonF([
        QPointF(w * 0.50, 0.0),
        QPointF(w,        h * 0.25),
        QPointF(w,        h * 0.75),
        QPointF(w * 0.50, h),
        QPointF(0.0,      h * 0.75),
        QPointF(0.0,      h * 0.25),
    ])


class StatIcon(QWidget):
    """Hexagonal rune silhouette + optional glyph overlay."""

    def __init__(
        self, size: int = 22, color: str = "#f0689a",
        overlay: str = OVERLAY_NONE, parent=None,
    ) -> None:
        super().__init__(parent)
        self._size = size
        self._color = QColor(color)
        self._overlay = overlay
        self.setFixedSize(size, size)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = float(self._size)
        h = float(self._size)

        # Hex silhouette — filled (tinted accent at ~35% alpha), with a
        # stronger outline for the "empty rune" rune-look.
        poly = _hex_polygon(w, h)
        fill = QColor(self._color)
        fill.setAlpha(70)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill))
        p.drawPolygon(poly)

        pen = QPen(QColor(self._color))
        pen.setWidthF(max(1.3, w * 0.07))
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPolygon(poly)

        if self._overlay == OVERLAY_CHECK:
            self._draw_check(p, w, h)
        elif self._overlay == OVERLAY_CROSS:
            self._draw_cross(p, w, h)
        elif self._overlay == OVERLAY_SPARKLE:
            self._draw_sparkle(p, w, h)

        p.end()

    def _draw_check(self, p: QPainter, w: float, h: float) -> None:
        pen = QPen(QColor(self._color))
        pen.setWidthF(max(1.6, w * 0.10))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        path = QPainterPath()
        path.moveTo(w * 0.30, h * 0.52)
        path.lineTo(w * 0.46, h * 0.66)
        path.lineTo(w * 0.72, h * 0.38)
        p.drawPath(path)

    def _draw_cross(self, p: QPainter, w: float, h: float) -> None:
        pen = QPen(QColor(self._color))
        pen.setWidthF(max(1.6, w * 0.10))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(w * 0.33, h * 0.37), QPointF(w * 0.67, h * 0.63))
        p.drawLine(QPointF(w * 0.67, h * 0.37), QPointF(w * 0.33, h * 0.63))

    def _draw_sparkle(self, p: QPainter, w: float, h: float) -> None:
        # Four-point star
        cx, cy = w * 0.5, h * 0.5
        arm = w * 0.22
        pen = QPen(QColor(self._color))
        pen.setWidthF(max(1.4, w * 0.08))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))
        p.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
