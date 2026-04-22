"""Profil utilisateur affiche dans la capsule haut-gauche du fond_2.png.

Contenu : pastille avatar + nom + niveau, aligne horizontalement.
Conçu pour rester compact dans la zone _Z_PROFILE (156x34).

API :
    pill.set_profile(name, level, avatar_path=None)
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ui import theme


class ProfilePill(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ProfilePill")
        self.setStyleSheet(theme.transparent_frame_stylesheet("ProfilePill"))

        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 2, 8, 2)
        lay.setSpacing(6)

        self._avatar = QLabel()
        self._avatar.setFixedSize(20, 20)
        self._avatar.setStyleSheet(
            "background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,"
            " fx:0.5, fy:0.5, stop:0 #ff8ab5, stop:1 #d93d7a);"
            "border: 1px solid rgba(255,255,255,0.35); border-radius: 10px;"
        )
        lay.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        self._name = QLabel("Luci2US")
        self._name.setStyleSheet(
            f"color: {theme.D.FG}; background: transparent;"
            f"font-family: '{theme.SW.FONT_UI}';"
            f"font-size: 9px; font-weight: 700; letter-spacing: 0.3px;"
        )
        lay.addWidget(self._name, 0, Qt.AlignmentFlag.AlignVCenter)

        self._level = QLabel("LV 1")
        self._level.setStyleSheet(
            f"color: {theme.D.ACCENT}; background: transparent;"
            f"font-family: '{theme.SW.FONT_MONO}';"
            f"font-size: 8px; font-weight: 700;"
        )
        lay.addStretch(1)
        lay.addWidget(self._level, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_profile(self, name: str, level: int, avatar_path: str | None = None) -> None:
        self._name.setText(name or "")
        self._level.setText(f"LV {int(level)}")
        if avatar_path:
            pix = QPixmap(avatar_path)
            if not pix.isNull():
                self._avatar.setPixmap(pix.scaled(
                    26, 26,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
                self._avatar.setStyleSheet(
                    "border: 1px solid rgba(255,255,255,0.35); border-radius: 13px;"
                )
