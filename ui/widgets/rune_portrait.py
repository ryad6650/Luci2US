"""Portrait de rune — QLabel image-ready.

Affiche une image de rune via QPixmap + setScaledContents(True).
En attendant l'asset, un dégradé orange placeholder est peint via QSS avec
une bordure dorée et des coins arrondis.

    portrait = RunePortrait(size=100)
    portrait.set_pixmap(QPixmap("assets/swarfarm/runes/violent.png"))

Un overlay "+12" (niveau) peut être activé via `show_level(True, "+12")`.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


GOLD_BORDER = "#e8b040"
GOLD_SOFT = "#ffd07a"

_DEFAULT_GRADIENT = ("#f5a430", "#d97a1b", "#8c4610")

_RARITY_GRADIENT = {
    "Legendaire": ("#f5c16e", "#c98a2a", "#5c3a10"),
    "Heroique":   ("#ED8DED", "#9f4ca0", "#3f1a42"),
    "Rare":       ("#5aa0d8", "#2e6a9c", "#14304e"),
    "Magique":    ("#8ec44a", "#4e8825", "#1f3a0f"),
    "Normal":     ("#9a9aa2", "#5a5a62", "#262630"),
}


class RunePortrait(QFrame):
    def __init__(
        self,
        size: int = 100,
        border_color: str | None = None,
        rarity: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._size = size
        self._border_color = border_color or GOLD_BORDER
        self._gradient = _RARITY_GRADIENT.get(rarity, _DEFAULT_GRADIENT)
        self.setObjectName("RunePortrait")
        self.setFixedSize(size, size)
        self._apply_placeholder_style()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._image = QLabel(self)
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setScaledContents(True)
        self._image.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(self._image)

    def set_border_color(self, color: str) -> None:
        self._border_color = color
        if self._image.pixmap() is None or self._image.pixmap().isNull():
            self._apply_placeholder_style()
        else:
            self._apply_image_style()

    def set_rarity(self, rarity: str | None) -> None:
        self._gradient = _RARITY_GRADIENT.get(rarity, _DEFAULT_GRADIENT)
        if self._image.pixmap() is None or self._image.pixmap().isNull():
            self._apply_placeholder_style()
        else:
            self._apply_image_style()

    def _apply_placeholder_style(self) -> None:
        s0, s1, s2 = self._gradient
        self.setStyleSheet(
            f"""
            #RunePortrait {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {s0},
                    stop:0.55 {s1},
                    stop:1 {s2}
                );
                border: 3px solid {self._border_color};
                border-radius: 16px;
            }}
            """
        )

    def _apply_image_style(self) -> None:
        s0, s1, s2 = self._gradient
        self.setStyleSheet(
            f"""
            #RunePortrait {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {s0},
                    stop:0.55 {s1},
                    stop:1 {s2}
                );
                border: 3px solid {self._border_color};
                border-radius: 16px;
            }}
            """
        )

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """Injecter l'image finale de rune une fois l'asset disponible."""
        if pixmap is None or pixmap.isNull():
            self._image.clear()
            self._apply_placeholder_style()
            return
        self._image.setPixmap(pixmap)
        self._apply_image_style()


class RunePortraitWithLevel(QFrame):
    """Portrait + pastille de niveau dorée (style mockup '+12')."""

    def __init__(
        self,
        size: int = 100,
        level: str = "+12",
        border_color: str | None = None,
        rarity: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._portrait = RunePortrait(size=size, border_color=border_color, rarity=rarity)
        lay.addWidget(self._portrait, 0, Qt.AlignmentFlag.AlignHCenter)

        self._level = QLabel(level)
        self._level.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._level.setFixedWidth(size - 12)
        self._level.setStyleSheet(
            f"color:{GOLD_SOFT}; background: rgba(245, 164, 48, 0.14);"
            f"border: 1px solid rgba(245, 164, 48, 0.55);"
            f"border-radius: 9px; padding: 2px 0px;"
            f"font-family: 'JetBrains Mono'; font-size: 12px; font-weight: 800;"
        )
        lay.addWidget(self._level, 0, Qt.AlignmentFlag.AlignHCenter)

    def set_level(self, level: str) -> None:
        self._level.setText(level)

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        self._portrait.set_pixmap(pixmap)
