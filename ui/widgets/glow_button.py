"""Start button — bronze gradient + pulsing glow (B4 direction from v13)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect

from ui import theme


class GlowButton(QPushButton):
    def __init__(self, label: str = "START", parent=None) -> None:
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.COLOR_BRONZE},
                    stop:1 {theme.COLOR_BRONZE_DARK}
                );
                color:#fff3d0;
                font-weight:800; font-size:13px; letter-spacing:1.5px;
                padding:10px 26px;
                border:1px solid {theme.COLOR_BRONZE_LIGHT};
                border-radius:6px;
            }}
            QPushButton:hover {{ background: {theme.COLOR_BRONZE_LIGHT}; }}
            QPushButton:pressed {{ padding-top:11px; padding-bottom:9px; }}
            """
        )

        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(18)
        self._glow.setOffset(0, 0)
        self._glow.setColor(QColor(245, 160, 48, 90))
        self.setGraphicsEffect(self._glow)

        self._anim = QPropertyAnimation(self._glow, b"blurRadius")
        self._anim.setDuration(2200)
        self._anim.setStartValue(18)
        self._anim.setKeyValueAt(0.5, 26)
        self._anim.setEndValue(18)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.start()
