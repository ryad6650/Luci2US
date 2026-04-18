"""Liste des monstres : barre filtres (Task 3) + lignes scrollables."""
from __future__ import annotations

from PySide6.QtCore import Qt, QMetaObject, Q_ARG, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

import monster_icons
from models import Monster
from s2us_filter import calculate_efficiency_s2us
from ui import theme


def _rune_eff(rune) -> float | None:
    if rune.swex_efficiency is not None:
        return float(rune.swex_efficiency)
    try:
        return float(calculate_efficiency_s2us(rune))
    except Exception:
        return None


def _avg_efficiency(monster: Monster) -> float:
    effs = [e for e in (_rune_eff(r) for r in monster.equipped_runes) if e is not None]
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
        try:
            icon_path = monster_icons.get_monster_icon(monster.unit_master_id)
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self._icon.setPixmap(pix.scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass
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

        # --- Barre de filtres ---
        filters = QHBoxLayout()
        filters.setSpacing(10)

        self._element_combo = QComboBox()
        self._element_combo.addItems(["Tous", "Eau", "Feu", "Vent", "Lumiere", "Tenebres"])
        self._element_combo.setFixedWidth(120)
        self._element_combo.currentTextChanged.connect(self._refresh_visible)
        filters.addWidget(QLabel("Element :"))
        filters.addWidget(self._element_combo)

        self._stars_combo = QComboBox()
        self._stars_combo.addItems([">=1", ">=2", ">=3", ">=4", ">=5", ">=6"])
        self._stars_combo.setCurrentText(">=1")
        self._stars_combo.setFixedWidth(80)
        self._stars_combo.currentTextChanged.connect(self._refresh_visible)
        filters.addWidget(QLabel("Etoiles :"))
        filters.addWidget(self._stars_combo)

        self._name_search = QLineEdit()
        self._name_search.setPlaceholderText("Rechercher par nom...")
        self._name_search.textChanged.connect(self._refresh_visible)
        filters.addWidget(self._name_search, 1)

        self._refresh_btn = QPushButton("Refresh icones & noms Swarfarm")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._on_refresh_icons)
        filters.addWidget(self._refresh_btn)

        outer.addLayout(filters)

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
        self._all_monsters = list(monsters)
        self._refresh_visible()

    def _refresh_visible(self) -> None:
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        elem = self._element_combo.currentText()
        min_stars = int(self._stars_combo.currentText().lstrip(">="))
        name_query = self._name_search.text().strip().lower()

        filtered = []
        for mon in self._all_monsters:
            if elem != "Tous" and mon.element != elem:
                continue
            if mon.stars < min_stars:
                continue
            if name_query and name_query not in mon.name.lower():
                continue
            filtered.append(mon)

        stretch_index = self._rows_layout.count() - 1
        for monster in filtered:
            row = _MonsterRow(monster)
            row.clicked.connect(self.monster_clicked.emit)
            self._rows.append(row)
            self._rows_layout.insertWidget(stretch_index, row)
            stretch_index += 1

    def _on_refresh_icons(self) -> None:
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("Telechargement... 0%")

        def on_progress(done: int, total: int) -> None:
            if total <= 0:
                return
            pct = int(done * 100 / total)
            QMetaObject.invokeMethod(
                self, "_set_refresh_progress",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(int, pct), Q_ARG(int, done), Q_ARG(int, total),
            )

        def on_done() -> None:
            QMetaObject.invokeMethod(
                self, "_on_refresh_done",
                Qt.ConnectionType.QueuedConnection,
            )

        monster_icons.download_icons_async(on_progress=on_progress, on_done=on_done)

    @Slot(int, int, int)
    def _set_refresh_progress(self, pct: int, done: int, total: int) -> None:
        self._refresh_btn.setText(f"Telechargement... {pct}% ({done}/{total})")

    @Slot()
    def _on_refresh_done(self) -> None:
        self._refresh_btn.setEnabled(True)
        self._refresh_btn.setText("Refresh icones & noms Swarfarm")
        monster_icons.invalidate_names_cache()
        self._refresh_visible()
