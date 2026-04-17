"""Thin quality bar: fill = value / theoretical_max, color from threshold zone.

Zones (fill color) — same scale applies to any metric via (value, max, thresholds):
  value < zones[0]           -> red
  zones[0] <= value < zones[1]-> yellow
  zones[1] <= value < zones[2]-> green
  value >= zones[2]          -> gold
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtWidgets import QWidget

from ui import theme


# Bar-fill ceilings calibrated on realistic top-tier 6* Legend +12 rolls
# (not grinded-perfect theoretical). A rune hitting 100% bar = excellent.
MAX_SCORE = 300.0
MAX_SWOP  = 150.0
MAX_S2US  = 250.0

# Zone thresholds (value units, NOT percent of max):
#   [red->yellow, yellow->green, green->gold]
ZONES_SCORE = (100.0, 150.0, 200.0)
ZONES_SWOP  = (80.0, 100.0, 120.0)
ZONES_S2US  = (100.0, 140.0, 180.0)


def _zone_color(value: float, zones: tuple[float, float, float]) -> str:
    if value < zones[0]:
        return theme.COLOR_SELL
    if value < zones[1]:
        return theme.COLOR_POWERUP
    if value < zones[2]:
        return theme.COLOR_KEEP
    return theme.COLOR_GOLD


class QualityBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(5)
        self.setMinimumWidth(80)
        self._ratio = 0.0
        self._color = QColor(theme.COLOR_SELL)

    def set_value(self, value: float, max_value: float,
                  zones: tuple[float, float, float]) -> None:
        self._ratio = max(0.0, min(1.0, value / max_value)) if max_value > 0 else 0.0
        self._color = QColor(_zone_color(value, zones))
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        track = QColor(theme.COLOR_BORDER_FRAME)
        track.setAlpha(90)
        p.setBrush(QBrush(track))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(r, 2, 2)

        w = int(r.width() * self._ratio)
        if w > 0:
            fill_rect = r.adjusted(0, 0, -(r.width() - w), 0)
            p.setBrush(QBrush(self._color))
            p.drawRoundedRect(fill_rect, 2, 2)
