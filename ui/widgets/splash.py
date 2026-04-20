"""Frameless splash shown at startup: transparent Luci2US logo + rounded progress bar.

Emits ``finished`` when the bar reaches 100%; the caller then shows the main window.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui import theme

_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets",
    "logo_luci2us.png",
)


class _RoundedProgressBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._value = 0.0
        self.setFixedHeight(14)

    def set_value(self, v: float) -> None:
        v = 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)
        if v == self._value:
            return
        self._value = v
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2

        track = QPainterPath()
        track.addRoundedRect(rect, radius, radius)
        p.fillPath(track, QColor(0, 0, 0, 28))

        if self._value <= 0.0:
            return
        fill_w = rect.width() * self._value
        min_w = rect.height()
        if fill_w < min_w:
            fill_w = min_w
        fill_rect = QRectF(rect.x(), rect.y(), fill_w, rect.height())
        fill_path = QPainterPath()
        fill_path.addRoundedRect(fill_rect, radius, radius)
        grad = QLinearGradient(rect.x(), 0, rect.x() + rect.width(), 0)
        grad.setColorAt(0.0, QColor(theme.D.ACCENT))
        grad.setColorAt(1.0, QColor(theme.D.ACCENT_2))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(fill_path, QBrush(grad))


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self, duration_ms: int = 1800, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setAutoFillBackground(False)

        self._duration_ms = max(400, int(duration_ms))
        self._elapsed_ms = 0
        self._tick_ms = 16
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_tick)
        self._emitted = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(24)

        self._logo = QLabel()
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(_LOGO_PATH)
        if not pix.isNull():
            scaled = pix.scaledToWidth(
                560,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._logo.setPixmap(scaled)
        else:
            self._logo.setText("Luci2US")
            self._logo.setStyleSheet(
                f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
                "font-size:36px; font-weight:700;"
            )
        lay.addWidget(self._logo, 0, Qt.AlignmentFlag.AlignHCenter)

        self._bar = _RoundedProgressBar(self)
        self._bar.setFixedWidth(480)
        lay.addWidget(self._bar, 0, Qt.AlignmentFlag.AlignHCenter)

        self.resize(640, 400)
        self._center_on_screen()

    def start(self) -> None:
        self.show()
        self.raise_()
        self._elapsed_ms = 0
        self._bar.set_value(0.0)
        self._emitted = False
        self._timer.start(self._tick_ms)

    def _on_tick(self) -> None:
        self._elapsed_ms += self._tick_ms
        ratio = self._elapsed_ms / self._duration_ms
        if ratio >= 1.0:
            self._bar.set_value(1.0)
            self._timer.stop()
            if not self._emitted:
                self._emitted = True
                self.finished.emit()
            self.close()
            return
        self._bar.set_value(_ease_out_cubic(ratio))

    def _center_on_screen(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2
        self.move(x, y)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        p.fillRect(self.rect(), Qt.GlobalColor.transparent)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._strip_windows_chrome()

    def _strip_windows_chrome(self) -> None:
        import sys
        if sys.platform != "win32":
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            dwmapi = ctypes.windll.dwmapi
            # Disable non-client rendering (DWM frame/outline).
            policy = ctypes.c_int(1)  # DWMNCRP_DISABLED
            dwmapi.DwmSetWindowAttribute(
                hwnd, 2, ctypes.byref(policy), ctypes.sizeof(policy),
            )
            # Force square corners on Win11 so no rounded chrome is drawn.
            corner = ctypes.c_int(1)  # DWMWCP_DONOTROUND
            dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner),
            )
        except Exception:
            pass


def _ease_out_cubic(t: float) -> float:
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return 1.0 - (1.0 - t) ** 3
