"""Barre de filtres pour la page Runes — recherche texte + combos + slots.

Contrôles (maquette "Rune page.png") :
  - QLineEdit de recherche (matche sur `rune.set` + nom du monstre équipé).
  - QComboBox "Type" (dynamique — sets présents dans le profil).
  - Pills "Emplacement" 1-6 (toggle : re-click sur actif → déselection).
  - QComboBox "Rareté" (Legendaire / Heroique / Rare / Magique / Normal).
  - QComboBox "Étoiles" (6★ / 5★).
  - QComboBox "Amélioration" (+0 / +3 / +6 / +9 / +12 / +15 — seuil minimum).
  - QComboBox "Stat Principale" (ATQ, ATQ%, DEF, DEF%, PV, PV%, VIT, CC, DC, RES, PRE).
  - Groupe radio "Tri" (Niveau+Élevé | Score).

Toute modification émet `changed()` ; la page parente re-filtre.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QVBoxLayout, QWidget,
)

from models import STATS_FR
from ui import theme


_RARITIES = [("Tous", None), ("Légendaire", "Legendaire"), ("Héroïque", "Heroique"),
             ("Rare", "Rare"), ("Magique", "Magique"), ("Normal", "Normal")]
_STARS = [("Toutes", None), ("6★", 6), ("5★", 5), ("4★", 4), ("3★", 3), ("2★", 2), ("1★", 1)]
_LEVELS = [("Tous", 0), ("+0", 0), ("+3", 3), ("+6", 6), ("+9", 9), ("+12", 12), ("+15", 15)]


_COMBO_QSS = f"""
QComboBox {{
    background: rgba(255,255,255,0.04);
    color: {theme.D.FG};
    border: 1px solid {theme.D.BORDER};
    border-radius: 8px;
    padding: 4px 24px 4px 10px;
    min-height: 22px;
    font-family: '{theme.D.FONT_UI}';
    font-size: 12px; font-weight: 600;
}}
QComboBox:hover {{ border: 1px solid {theme.D.ACCENT}aa; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: #1a1d24;
    color: {theme.D.FG};
    border: 1px solid {theme.D.BORDER_STR};
    selection-background-color: {theme.D.ACCENT_DIM};
    selection-color: {theme.D.ACCENT};
    outline: 0;
}}
"""


class _SlotPill(QPushButton):
    """Pill 1-6 pour le filtre slot."""

    def __init__(self, label: str, key: int | None) -> None:
        super().__init__(label)
        self.key = key
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(28, 24)
        self._apply(False)

    def set_active(self, on: bool) -> None:
        self.setChecked(on)
        self._apply(on)

    def _apply(self, on: bool) -> None:
        if on:
            bg, fg, border = theme.D.ACCENT_DIM, theme.D.ACCENT, theme.D.ACCENT
        else:
            bg, fg, border = "transparent", theme.D.FG_DIM, theme.D.BORDER_STR
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {bg}; color: {fg};
                border: 1px solid {border}; border-radius: 12px;
                font-family: '{theme.D.FONT_UI}';
                font-size: 11px; font-weight: 700;
            }}
            QPushButton:hover {{ color: {theme.D.FG}; }}
            """
        )


class RuneFilterBar(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._filter_set: str | None = None
        self._filter_slot: int | None = None
        self._filter_rarity: str | None = None
        self._filter_stars: int | None = None
        self._filter_level_min: int = 0
        self._filter_main_stat: str | None = None
        self._filter_search: str = ""
        self._sort_key: str = "score"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 14, 28, 14)
        outer.setSpacing(8)

        # Row 1 : recherche
        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(8)
        lbl_search = QLabel("Barre de Recherche")
        lbl_search.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:0.8px;"
        )
        lbl_search.setFixedWidth(150)
        search_row.addWidget(lbl_search)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher des Runes...")
        self._search.setClearButtonEnabled(True)
        self._search.setStyleSheet(
            f"""
            QLineEdit {{
                background: rgba(255,255,255,0.04);
                color: {theme.D.FG};
                border: 1px solid {theme.D.BORDER};
                border-radius: 8px; padding: 5px 10px;
                font-family: '{theme.D.FONT_UI}'; font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {theme.D.ACCENT}aa; }}
            """
        )
        self._search.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search, 1)
        outer.addLayout(search_row)

        # Row 2 : filtres principaux
        row_a = QHBoxLayout()
        row_a.setContentsMargins(0, 0, 0, 0)
        row_a.setSpacing(14)

        self._set_combo = self._make_combo([("Tous les sets", None)])
        self._set_combo.currentIndexChanged.connect(self._on_set_changed)
        row_a.addLayout(self._labeled("Type", self._set_combo))

        slot_wrap = QFrame()
        slot_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        slot_lay = QHBoxLayout(slot_wrap)
        slot_lay.setContentsMargins(0, 0, 0, 0)
        slot_lay.setSpacing(4)
        self._slot_btns: dict[int, _SlotPill] = {}
        for n in range(1, 7):
            pill = _SlotPill(str(n), n)
            pill.clicked.connect(lambda _c=False, k=n: self._set_slot(k))
            slot_lay.addWidget(pill)
            self._slot_btns[n] = pill
        row_a.addLayout(self._labeled("Emplacement", slot_wrap))

        self._rarity_combo = self._make_combo(_RARITIES)
        self._rarity_combo.currentIndexChanged.connect(self._on_rarity_changed)
        row_a.addLayout(self._labeled("Rareté", self._rarity_combo))

        self._stars_combo = self._make_combo(_STARS)
        self._stars_combo.currentIndexChanged.connect(self._on_stars_changed)
        row_a.addLayout(self._labeled("Étoiles", self._stars_combo))

        row_a.addStretch(1)
        outer.addLayout(row_a)

        # Row 3 : amélioration + main stat + tri
        row_b = QHBoxLayout()
        row_b.setContentsMargins(0, 0, 0, 0)
        row_b.setSpacing(14)

        self._level_combo = self._make_combo(_LEVELS)
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        row_b.addLayout(self._labeled("Amélioration", self._level_combo))

        self._main_combo = self._make_combo(
            [("Toutes", None)] + [(s, s) for s in STATS_FR]
        )
        self._main_combo.currentIndexChanged.connect(self._on_main_changed)
        row_b.addLayout(self._labeled("Stats Principales", self._main_combo))

        row_b.addStretch(1)

        sort_wrap = QFrame()
        sort_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        sort_lay = QHBoxLayout(sort_wrap)
        sort_lay.setContentsMargins(0, 0, 0, 0)
        sort_lay.setSpacing(12)

        self._sort_group = QButtonGroup(self)
        self._sort_group.setExclusive(True)
        radio_qss = f"""
            QRadioButton {{ color:{theme.D.FG_DIM};
                background: transparent; spacing: 6px;
                font-family:'{theme.D.FONT_UI}'; font-size: 11px; font-weight: 600; }}
            QRadioButton::indicator {{
                width: 12px; height: 12px;
                border: 1.5px solid {theme.D.BORDER_STR};
                background: transparent; border-radius: 6px; }}
            QRadioButton::indicator:checked {{
                background: {theme.D.ACCENT};
                border: 1.5px solid {theme.D.ACCENT}; }}
            QRadioButton:hover {{ color: {theme.D.FG}; }}
        """
        self._rb_level = QRadioButton("Niveau + Élevé")
        self._rb_level.setStyleSheet(radio_qss)
        self._rb_score = QRadioButton("Score")
        self._rb_score.setStyleSheet(radio_qss)
        self._rb_score.setChecked(True)
        self._sort_group.addButton(self._rb_level)
        self._sort_group.addButton(self._rb_score)
        self._rb_level.toggled.connect(self._on_sort_changed)
        self._rb_score.toggled.connect(self._on_sort_changed)
        sort_lay.addWidget(self._rb_level)
        sort_lay.addWidget(self._rb_score)
        row_b.addLayout(self._labeled("Tri", sort_wrap))

        outer.addLayout(row_b)

    # ── Helpers de construction ───────────────────────────────────────
    def _make_combo(self, items: list[tuple[str, object]]) -> QComboBox:
        cb = QComboBox()
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.setMinimumWidth(130)
        for label, key in items:
            cb.addItem(label, userData=key)
        cb.setStyleSheet(_COMBO_QSS)
        return cb

    def _labeled(self, label: str, widget: QWidget) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:0.8px;"
        )
        col.addWidget(lbl)
        col.addWidget(widget)
        return col

    # ── Public API (lecture d'état) ───────────────────────────────────
    def search_text(self) -> str:
        return self._filter_search

    def filter_set(self) -> str | None:
        return self._filter_set

    def filter_slot(self) -> int | None:
        return self._filter_slot

    def filter_rarity(self) -> str | None:
        return self._filter_rarity

    def filter_stars(self) -> int | None:
        return self._filter_stars

    def filter_level_min(self) -> int:
        return self._filter_level_min

    def filter_main_stat(self) -> str | None:
        return self._filter_main_stat

    def sort_key(self) -> str:
        return self._sort_key

    # ── Public API (mutation) ─────────────────────────────────────────
    def populate_sets(self, sets_in_profile: list[str]) -> None:
        self._set_combo.blockSignals(True)
        self._set_combo.clear()
        self._set_combo.addItem("Tous les sets", userData=None)
        for s in sorted(sets_in_profile):
            self._set_combo.addItem(s, userData=s)
        self._set_combo.setCurrentIndex(0)
        self._set_combo.blockSignals(False)
        self._filter_set = None

    def reset_to_defaults(self) -> None:
        self.blockSignals(True)
        self._set_combo.setCurrentIndex(0)
        self._rarity_combo.setCurrentIndex(0)
        self._stars_combo.setCurrentIndex(0)
        self._level_combo.setCurrentIndex(0)
        self._main_combo.setCurrentIndex(0)
        self._search.clear()
        for n, btn in self._slot_btns.items():
            btn.set_active(False)
        self._rb_score.setChecked(True)
        self._filter_set = None
        self._filter_slot = None
        self._filter_rarity = None
        self._filter_stars = None
        self._filter_level_min = 0
        self._filter_main_stat = None
        self._filter_search = ""
        self._sort_key = "score"
        self.blockSignals(False)
        self.changed.emit()

    # ── Slots ─────────────────────────────────────────────────────────
    def _on_search_changed(self, txt: str) -> None:
        self._filter_search = txt.strip().lower()
        self.changed.emit()

    def _on_set_changed(self, _idx: int) -> None:
        self._filter_set = self._set_combo.currentData()
        self.changed.emit()

    def _set_slot(self, key: int) -> None:
        if self._filter_slot == key:
            self._filter_slot = None
        else:
            self._filter_slot = key
        for n, btn in self._slot_btns.items():
            btn.set_active(n == self._filter_slot)
        self.changed.emit()

    def _on_rarity_changed(self, _idx: int) -> None:
        self._filter_rarity = self._rarity_combo.currentData()
        self.changed.emit()

    def _on_stars_changed(self, _idx: int) -> None:
        self._filter_stars = self._stars_combo.currentData()
        self.changed.emit()

    def _on_level_changed(self, _idx: int) -> None:
        val = self._level_combo.currentData()
        self._filter_level_min = int(val) if val is not None else 0
        self.changed.emit()

    def _on_main_changed(self, _idx: int) -> None:
        self._filter_main_stat = self._main_combo.currentData()
        self.changed.emit()

    def _on_sort_changed(self, _checked: bool) -> None:
        self._sort_key = "level" if self._rb_level.isChecked() else "score"
        self.changed.emit()
