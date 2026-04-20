"""Hexagonal rune placeholder — matches design_handoff_runes.

Two sizes: mini (28×28 for table rows) and big (88×88 for the detail side panel
and 56 for the simulation modal header). Flat polygon with an accent stroke +
translucent fill for mini; radial gradient for big. Slot number centred, a
tiny gold star bades the hex when grade ≥ 6.

Swap for real Swarfarm icons when assets are available — replace `paintEvent`
with a QPixmap draw.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import (
    QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from ui import theme


def _hex_polygon_mini(w: float, h: float) -> QPolygonF:
    # Matches "16,2 28,9 28,23 16,30 4,23 4,9" on a 32×32 viewBox.
    return QPolygonF([
        QPointF(w * 0.50, h * 0.0625),
        QPointF(w * 0.875, h * 0.28125),
        QPointF(w * 0.875, h * 0.71875),
        QPointF(w * 0.50, h * 0.9375),
        QPointF(w * 0.125, h * 0.71875),
        QPointF(w * 0.125, h * 0.28125),
    ])


def _hex_polygon_big(w: float, h: float) -> QPolygonF:
    # Matches "32,4 56,18 56,46 32,60 8,46 8,18" on a 64×64 viewBox.
    return QPolygonF([
        QPointF(w * 0.50, h * 0.0625),
        QPointF(w * 0.875, h * 0.28125),
        QPointF(w * 0.875, h * 0.71875),
        QPointF(w * 0.50, h * 0.9375),
        QPointF(w * 0.125, h * 0.71875),
        QPointF(w * 0.125, h * 0.28125),
    ])


def paint_hex_mini(
    painter: QPainter, rect: QRectF, slot: int, grade: int, color: QColor,
) -> None:
    """Paint a mini hex directly into `rect` on an existing QPainter.

    Shared by RuneHexMini.paintEvent and the rune-table delegate so the
    virtualised table can draw the same glyph without instantiating a widget
    per row.
    """
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(rect.topLeft())

    w, h = rect.width(), rect.height()
    s = min(w, h)
    poly = _hex_polygon_mini(s, s)

    fill = QColor(color)
    fill.setAlpha(int(0.13 * 255))
    painter.setBrush(QBrush(fill))
    pen = QPen(color)
    pen.setWidthF(1.2)
    painter.setPen(pen)
    painter.drawPolygon(poly)

    f = QFont(theme.D.FONT_MONO)
    f.setBold(True)
    f.setPixelSize(max(9, int(s * 0.36)))
    painter.setFont(f)
    painter.setPen(color)
    painter.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, str(int(slot)))

    if int(grade) >= 6:
        sf = QFont(theme.D.FONT_UI)
        sf.setPixelSize(max(7, int(s * 0.34)))
        sf.setBold(True)
        painter.setFont(sf)
        painter.setPen(QColor("#f5c16e"))
        painter.drawText(
            QRectF(s * 0.55, -s * 0.04, s * 0.5, s * 0.5),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            "★",
        )
    painter.restore()


class RuneHexMini(QWidget):
    """28×28 hexagon with a centred slot number and optional 6★ badge."""

    def __init__(
        self, slot: int = 1, grade: int = 6, color: str | None = None,
        size: int = 28, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._slot = int(slot)
        self._grade = int(grade)
        self._color = QColor(color or theme.D.ACCENT)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_values(self, slot: int, grade: int, color: str | None = None) -> None:
        self._slot = int(slot)
        self._grade = int(grade)
        if color is not None:
            self._color = QColor(color)
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._size, self._size)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        s = float(self._size)
        paint_hex_mini(p, QRectF(0, 0, s, s), self._slot, self._grade, self._color)
        p.end()


class RuneHexBig(QWidget):
    """Larger hex with a radial-gradient fill and a row of stars top-right."""

    def __init__(
        self, slot: int = 1, grade: int = 6, color: str | None = None,
        size: int = 88, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._slot = int(slot)
        self._grade = int(grade)
        self._color = QColor(color or theme.D.ACCENT)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_values(self, slot: int, grade: int, color: str | None = None) -> None:
        self._slot = int(slot)
        self._grade = int(grade)
        if color is not None:
            self._color = QColor(color)
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._size, self._size)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = float(self._size)
        poly = _hex_polygon_big(s, s)

        # Radial-gradient fill
        grad = QRadialGradient(QPointF(s * 0.5, s * 0.35), s * 0.6)
        inner = QColor(self._color)
        inner.setAlpha(int(0.40 * 255))
        outer = QColor(self._color)
        outer.setAlpha(int(0.08 * 255))
        grad.setColorAt(0.0, inner)
        grad.setColorAt(1.0, outer)
        p.setBrush(QBrush(grad))

        pen = QPen(self._color)
        pen.setWidthF(1.8)
        p.setPen(pen)
        p.drawPolygon(poly)

        # Slot number
        f = QFont(theme.D.FONT_MONO)
        f.setBold(True)
        f.setPixelSize(max(14, int(s * 0.32)))
        p.setFont(f)
        p.setPen(QColor(self._color))
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, str(self._slot))

        # Stars row top-right — one per grade
        if self._grade > 0:
            star_font = QFont(theme.D.FONT_UI)
            star_font.setPixelSize(max(8, int(s * 0.12)))
            star_font.setBold(True)
            p.setFont(star_font)
            p.setPen(QColor("#f5c16e"))
            txt = "★" * int(self._grade)
            # Position it in a strip at the top-right corner.
            p.drawText(
                QRectF(s * 0.55, -s * 0.06, s * 0.55, s * 0.22),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                txt,
            )
        p.end()
