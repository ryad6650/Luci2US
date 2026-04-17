"""Bot state indicator — dot + label. Green pulsing when active, grey when idle."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from ui import theme


class _Dot(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(14, 14)
        self._opacity = 1.0
        self._color = QColor(theme.COLOR_KEEP)

    def set_color(self, hex_color: str) -> None:
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(self._color)
        c.setAlphaF(self._opacity)
        p.setBrush(QBrush(c))
        p.setPen(Qt.NoPen)
        p.drawEllipse(2, 2, 9, 9)

    def get_opacity(self) -> float:
        return self._opacity

    def set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    opacity = Property(float, get_opacity, set_opacity)


class StateIndicator(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._dot = _Dot()
        self._label = QLabel("INACTIF")
        self._label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:12px; font-weight:600; letter-spacing:.5px;"
        )

        lay.addWidget(self._dot)
        lay.addWidget(self._label)
        lay.addStretch()

        self._anim = QPropertyAnimation(self._dot, b"opacity")
        self._anim.setDuration(1200)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.4)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self._dot.set_color(theme.COLOR_KEEP)
            self._label.setText("ACTIF")
            self._label.setStyleSheet(
                f"color:{theme.COLOR_KEEP}; font-size:12px; font-weight:600; letter-spacing:.5px;"
            )
            self._anim.start()
        else:
            self._anim.stop()
            self._dot.set_color(theme.COLOR_TEXT_DIM)
            self._dot.set_opacity(1.0)
            self._label.setText("INACTIF")
            self._label.setStyleSheet(
                f"color:{theme.COLOR_TEXT_DIM}; font-size:12px; font-weight:600; letter-spacing:.5px;"
            )
