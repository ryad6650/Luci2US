"""Hexagonal rune placeholder — QWidget painted via QPainter.

Design-handoff_scan "variation D": clipPath hex polygon, gradient fill tinted
by the rune set colour, slot number centered, grade stars underneath.

Swap for real Swarfarm artwork (QPixmap) once the user uploads them.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPolygonF
from PySide6.QtWidgets import QWidget


def _hex_polygon(w: float, h: float) -> QPolygonF:
    return QPolygonF([
        QPointF(w * 0.50, 0.0),
        QPointF(w,        h * 0.25),
        QPointF(w,        h * 0.75),
        QPointF(w * 0.50, h),
        QPointF(0.0,      h * 0.75),
        QPointF(0.0,      h * 0.25),
    ])


class RuneGlyph(QWidget):
    def __init__(
        self, size: int = 56, grade: int = 6, slot: int = 2,
        color: str = "#f0689a", parent=None,
    ) -> None:
        super().__init__(parent)
        self._size = size
        self._grade = grade
        self._slot = slot
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def set_values(self, grade: int, slot: int, color: str) -> None:
        self._grade = grade
        self._slot = slot
        self._color = QColor(color)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self._size)
        h = float(self._size)

        path = QPainterPath()
        path.addPolygon(_hex_polygon(w, h))
        path.closeSubpath()

        grad = QLinearGradient(0, 0, w * 0.85, h * 0.85)
        top = QColor(self._color)
        bot = QColor(self._color)
        bot.setAlpha(135)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bot)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        # Slot number (centre)
        p.setPen(QColor("#0b0b10"))
        slot_font = QFont("JetBrains Mono", int(self._size * 0.28))
        slot_font.setWeight(QFont.Weight.Bold)
        p.setFont(slot_font)
        slot_rect = QRectF(0, 0, w, h * 0.85)
        p.drawText(slot_rect, Qt.AlignmentFlag.AlignCenter, str(self._slot))

        # Stars (bottom)
        stars_txt = "\u2605" * max(0, min(6, self._grade))
        stars_txt = stars_txt[:3]  # room for 3 max on a 38px glyph
        star_font = QFont("JetBrains Mono", int(self._size * 0.12))
        star_font.setWeight(QFont.Weight.Bold)
        p.setFont(star_font)
        sc = QColor("#0b0b10")
        sc.setAlpha(180)
        p.setPen(sc)
        star_rect = QRectF(0, h * 0.68, w, h * 0.25)
        p.drawText(star_rect, Qt.AlignmentFlag.AlignCenter, stars_txt)

        p.end()
