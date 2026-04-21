"""Overlay hologramme rune — affiche l'asset hologram_rune.png sur la zone
centrale du cercle magique du fond. Version v2 : image statique, pas
d'animation. Le cercle magique est dessine dans `Fond 1.png` et reste
visible en arriere-plan.

API :
    visual.show_hologram()     # affiche l'hologramme
    visual.show_empty_state()  # masque + message d'attente
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QStackedLayout, QWidget

from ui import theme


_ASSET = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "assets", "scan_ui", "hologram_rune.png",
))


class HolographicRuneVisual(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QStackedLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self._image = QLabel()
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setScaledContents(False)
        self._pix = QPixmap(_ASSET)
        lay.addWidget(self._image)

        self._hint = QLabel("En attente de scan...")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setStyleSheet(
            f"color: {theme.D.FG_MUTE}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 14px; font-style: italic;"
        )
        lay.addWidget(self._hint)

        self.show_empty_state()

    def resizeEvent(self, e) -> None:  # noqa: N802
        super().resizeEvent(e)
        if not self._pix.isNull():
            scaled = self._pix.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image.setPixmap(scaled)

    def show_hologram(self) -> None:
        self._image.setVisible(True)
        self._hint.setVisible(False)

    def show_empty_state(self) -> None:
        self._image.setVisible(False)
        self._hint.setVisible(True)
