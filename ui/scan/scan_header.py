"""Scan page header: LIVE FEED eyebrow + h1 + Farming pill."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui import theme


class _StatusDot(QLabel):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(8, 8)
        self._color = color
        self._opacity = 1.0
        self._refresh()
        self._anim = QPropertyAnimation(self, b"pulse")
        self._anim.setDuration(1400)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.45)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)

    def set_color(self, color: str) -> None:
        self._color = color
        self._refresh()

    def set_pulsing(self, on: bool) -> None:
        if on:
            self._anim.start()
        else:
            self._anim.stop()
            self._opacity = 1.0
            self._refresh()

    def _refresh(self) -> None:
        c = QColor(self._color)
        self.setStyleSheet(
            f"background: rgba({c.red()},{c.green()},{c.blue()},{self._opacity});"
            f"border-radius:4px;"
        )

    def get_pulse(self) -> float:
        return self._opacity

    def set_pulse(self, v: float) -> None:
        self._opacity = max(0.0, min(1.0, v))
        self._refresh()

    pulse = Property(float, get_pulse, set_pulse)


class ScanHeader(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        # ── left: eyebrow + h1 ──
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(4)

        self._eyebrow = QLabel("LIVE FEED")
        self._eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:1.5px;"
        )
        ll.addWidget(self._eyebrow)

        self._title = QLabel("Le bot tourne. Je t'affiche tout ce qui tombe.")
        self._title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:24px; font-weight:600; letter-spacing:-0.5px;"
        )
        ll.addWidget(self._title)
        lay.addWidget(left, 1)

        # ── status pill ──
        self._pill = QFrame()
        self._pill.setObjectName("StatusPill")
        pl = QHBoxLayout(self._pill)
        pl.setContentsMargins(14, 6, 14, 6)
        pl.setSpacing(10)
        self._dot = _StatusDot(theme.D.FG_MUTE)
        pl.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)
        self._pill_label = QLabel("Paused")
        self._pill_label.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
        )
        pl.addWidget(self._pill_label, 0, Qt.AlignmentFlag.AlignVCenter)
        self._uptime = QLabel("\u00B7 00:00:00")
        self._uptime.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        pl.addWidget(self._uptime, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self._pill, 0, Qt.AlignmentFlag.AlignVCenter)

        self._apply_state()

    def set_active(self, active: bool) -> None:
        self._active = bool(active)
        self._apply_state()

    def update_time(self, seconds: int) -> None:
        h, r = divmod(max(0, int(seconds)), 3600)
        m, s = divmod(r, 60)
        self._uptime.setText(f"\u00B7 {h:02d}:{m:02d}:{s:02d}")

    def _apply_state(self) -> None:
        if self._active:
            color = theme.D.OK
            label = "Farming"
            pill_bg = "rgba(93,211,158,0.10)"
            pill_border = "rgba(93,211,158,0.25)"
        else:
            color = theme.D.FG_MUTE
            label = "Paused"
            pill_bg = "rgba(122,97,104,0.12)"
            pill_border = "rgba(122,97,104,0.22)"

        self._pill.setStyleSheet(
            f"""
            #StatusPill {{
                background:{pill_bg}; border:1px solid {pill_border};
                border-radius:999px;
            }}
            """
        )
        self._pill_label.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
        )
        self._pill_label.setText(label)
        self._dot.set_color(color)
        self._dot.set_pulsing(self._active)
