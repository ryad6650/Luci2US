"""Jauge circulaire (anneau de progression) — utilisee par le panneau
recommandation optimiseur pour EFFI S2US / EFFI SWOP.

API :
    g = CircularGauge(label="EFFI S2US", color="#ff5ac8", size=72)
    g.set_value(0.32)  # 0.0 -> 1.0 ; affiche "32%" au centre
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui import theme


class _RingWidget(QWidget):
    def __init__(self, color: str, size: int, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = QColor(color)
        self._value = 0.0

    def set_value(self, v: float) -> None:
        self._value = max(0.0, min(1.0, float(v)))
        self.update()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        side = min(self.width(), self.height())
        stroke = max(4, side // 9)
        rect = QRectF(
            stroke / 2, stroke / 2,
            side - stroke, side - stroke,
        )
        pen_bg = QPen(QColor(255, 255, 255, 40))
        pen_bg.setWidthF(stroke)
        pen_bg.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.setPen(pen_bg)
        p.drawArc(rect, 0, 360 * 16)
        pen_fg = QPen(self._color)
        pen_fg.setWidthF(stroke)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_fg)
        span = int(-360 * 16 * self._value)
        p.drawArc(rect, 90 * 16, span)
        p.end()


class CircularGauge(QWidget):
    def __init__(
        self, label: str, color: str, size: int = 72, parent=None,
    ) -> None:
        super().__init__(parent)
        self._label_text = label
        self._color = color
        self._size = size
        self._value_v = 0.0

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ring_host = QWidget()
        ring_lay = QVBoxLayout(ring_host)
        ring_lay.setContentsMargins(0, 0, 0, 0)
        self._ring = _RingWidget(color, size)
        ring_lay.addWidget(self._ring, 0, Qt.AlignmentFlag.AlignCenter)

        self._value_label = QLabel("0%", ring_host)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setStyleSheet(
            f"color: white; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: {max(11, size // 5)}px; font-weight: 800;"
        )
        self._value_label.setGeometry(0, 0, size, size)
        self._value_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._value_label.raise_()
        lay.addWidget(ring_host)

        self._text_label = QLabel(label)
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setStyleSheet(
            f"color: {theme.D.FG_DIM}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 11px; font-weight: 700; letter-spacing: 1.2px;"
        )
        lay.addWidget(self._text_label)

    def value(self) -> float:
        return self._value_v

    def label(self) -> str:
        return self._label_text

    def set_value(self, v: float) -> None:
        self._value_v = max(0.0, min(1.0, float(v)))
        self._ring.set_value(self._value_v)
        self._value_label.setText(f"{int(round(self._value_v * 100))}%")
