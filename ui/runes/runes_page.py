"""Page Runes — gestionnaire d'inventaire visuel.

Layout :
    Header          (eyebrow "INVENTAIRE" + titre "Gestionnaire de Runes")
    RuneFilterBar   (recherche + combos + slots + tri)
    RuneGridView    (FlowLayout paginé de RuneCardWidget)

Actions :
    lock_toggled    → toggle volatile dans `self._locked_ids` (non persisté)
    edit_clicked    → non implémenté pour l'instant (bouton désactivé)
    upgrade_clicked → inerte (l'ancien RuneTesterModal a été supprimé avec
                      le retrait de la paradigme filtres S2US)

API publique pour `main_window` :
    runes_page.apply_profile(profile, saved_at)
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from models import Rune
from swlens import rl_score
from ui import theme
from ui.runes.rune_filter_bar import RuneFilterBar
from ui.runes.rune_grid_view import RuneGridView


def _eff(rune: Rune) -> float:
    if rune.swex_efficiency is not None:
        return float(rune.swex_efficiency)
    try:
        return float(rl_score(rune).total)
    except Exception:
        return 0.0


class RunesPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"RunesPage {{ background: transparent; color: {theme.D.FG}; }}"
        )

        self._all_runes: list[Rune] = []
        self._equipped_index: dict = {}
        self._locked_ids: set = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())

        self._filter_bar = RuneFilterBar()
        self._filter_bar.changed.connect(self._refilter)
        outer.addWidget(self._filter_bar)

        self._grid = RuneGridView()
        self._grid.lock_toggled.connect(self._toggle_lock)
        self._grid.edit_clicked.connect(self._on_edit)
        outer.addWidget(self._grid, 1)

    # ── Header ────────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        header = QWidget()
        lay = QVBoxLayout(header)
        lay.setContentsMargins(28, 22, 28, 12)
        lay.setSpacing(3)

        eyebrow = QLabel("INVENTAIRE")
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:1.5px;"
        )
        lay.addWidget(eyebrow)

        title = QLabel("Gestionnaire de Runes")
        title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:24px; font-weight:600; letter-spacing:-0.5px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(title)
        return header

    # ── Public API ────────────────────────────────────────────────────
    def apply_profile(self, profile: dict, saved_at) -> None:
        self._all_runes = list(profile.get("runes", []))
        self._equipped_index = {}
        for monster in profile.get("monsters", []):
            for rune in getattr(monster, "equipped_runes", []):
                key = rune.rune_id if rune.rune_id is not None else id(rune)
                self._equipped_index[key] = monster.name

        self._locked_ids.clear()

        sets_present = sorted({r.set for r in self._all_runes})
        self._filter_bar.blockSignals(True)
        self._filter_bar.populate_sets(sets_present)
        self._filter_bar.reset_to_defaults()
        self._filter_bar.blockSignals(False)

        self._refilter()

    # ── Filtering & sorting ───────────────────────────────────────────
    def _refilter(self) -> None:
        fb = self._filter_bar
        set_f = fb.filter_set()
        slot_f = fb.filter_slot()
        rarity_f = fb.filter_rarity()
        stars_f = fb.filter_stars()
        level_min = fb.filter_level_min()
        main_f = fb.filter_main_stat()
        search = fb.search_text()

        filtered: list[Rune] = []
        for r in self._all_runes:
            if set_f and r.set != set_f:
                continue
            if slot_f is not None and r.slot != slot_f:
                continue
            if rarity_f and r.grade != rarity_f:
                continue
            if stars_f is not None and r.stars != stars_f:
                continue
            if r.level < level_min:
                continue
            if main_f and (r.main_stat is None or r.main_stat.type != main_f):
                continue
            if search:
                key = r.rune_id if r.rune_id is not None else id(r)
                equipped_on = self._equipped_index.get(key, "")
                blob = f"{r.set} {equipped_on}".lower()
                if search not in blob:
                    continue
            filtered.append(r)

        if fb.sort_key() == "level":
            filtered.sort(key=lambda r: (r.level, _eff(r)), reverse=True)
        else:
            filtered.sort(key=lambda r: _eff(r), reverse=True)

        self._grid.set_runes(
            filtered, self._equipped_index, self._locked_ids,
            total_in_profile=len(self._all_runes),
        )

    # ── Actions ───────────────────────────────────────────────────────
    def _toggle_lock(self, rune: Rune) -> None:
        key = rune.rune_id if rune.rune_id is not None else id(rune)
        if key in self._locked_ids:
            self._locked_ids.discard(key)
        else:
            self._locked_ids.add(key)

    def _on_edit(self, rune: Rune) -> None:
        # Placeholder : bouton désactivé dans la carte, ce slot est inerte.
        return

    # ── Accessors (utile aux tests) ───────────────────────────────────
    @property
    def locked_ids(self) -> set:
        return self._locked_ids
