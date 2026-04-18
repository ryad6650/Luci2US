"""Liste des monstres : barre filtres (Task 3) + lignes scrollables."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from models import Monster
from ui import theme


def _avg_efficiency(monster: Monster) -> float:
    effs = [r.swex_efficiency for r in monster.equipped_runes if r.swex_efficiency is not None]
    if not effs:
        return 0.0
    return sum(effs) / len(effs)


class _MonsterRow(QFrame):
    clicked = Signal(object)

    def __init__(self, monster: Monster, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._monster = monster
        self._eff_avg = _avg_efficiency(monster)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"_MonsterRow {{ background:rgba(26,15,7,0.6);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:4px; }}"
            f"_MonsterRow:hover {{ background:rgba(198,112,50,0.2);"
            f" border:1px solid {theme.COLOR_BRONZE}; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(14)

        self._icon = QLabel()
        self._icon.setFixedSize(48, 48)
        self._icon.setStyleSheet(
            f"background:{theme.COLOR_BG_FRAME};"
            f"border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:3px;"
        )
        row.addWidget(self._icon)

        name = QLabel(monster.name)
        name.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:14px; font-weight:700;"
        )
        row.addWidget(name, 1)

        stars = QLabel(f"{'\u2605' * monster.stars} ({monster.stars})")
        stars.setStyleSheet(f"color:{theme.COLOR_GOLD_TITLE}; font-size:12px;")
        row.addWidget(stars)

        level = QLabel(f"L{monster.level}")
        level.setStyleSheet(f"color:{theme.COLOR_TEXT_MAIN}; font-size:12px;")
        row.addWidget(level)

        element = QLabel(monster.element)
        element.setStyleSheet(f"color:{theme.COLOR_BRONZE_LIGHT}; font-size:12px;")
        row.addWidget(element)

        eff = QLabel(f"Eff moyenne {self._eff_avg:.1f}%")
        eff.setStyleSheet(f"color:{theme.COLOR_KEEP}; font-size:12px; font-weight:600;")
        row.addWidget(eff)

        chevron = QLabel("\u25B6")
        chevron.setStyleSheet(f"color:{theme.COLOR_BRONZE}; font-size:14px;")
        row.addWidget(chevron)

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._monster)
        super().mousePressEvent(ev)


class MonsterList(QWidget):
    monster_clicked = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._rows: list[_MonsterRow] = []
        self._all_monsters: list[Monster] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(8)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        self._rows_layout.addStretch()

        self._scroll.setWidget(self._rows_container)
        outer.addWidget(self._scroll)

    def set_monsters(self, monsters: list[Monster]) -> None:
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()
        self._all_monsters = list(monsters)

        stretch_index = self._rows_layout.count() - 1
        for monster in monsters:
            row = _MonsterRow(monster)
            row.clicked.connect(self.monster_clicked.emit)
            self._rows.append(row)
            self._rows_layout.insertWidget(stretch_index, row)
            stretch_index += 1
