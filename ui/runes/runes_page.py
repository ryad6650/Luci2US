"""Runes tab orchestration (filter bar + table on left, detail panel on right)."""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from models import Rune
from ui.runes.rune_detail_panel import RuneDetailPanel
from ui.runes.rune_filter_bar import RuneFilterBar
from ui.runes.rune_table import RuneTable


class RunesPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)

        self._filter_bar = RuneFilterBar()
        left_lay.addWidget(self._filter_bar)

        self._table = RuneTable()
        left_lay.addWidget(self._table, 1)

        root.addWidget(left, 1)

        self._detail = RuneDetailPanel()
        root.addWidget(self._detail)

        self._all_runes: list[Rune] = []
        self._equipped_index: dict = {}

        self._filter_bar.changed.connect(self._refilter)
        self._table.rune_selected.connect(self._on_rune_selected)

    # -- public API ------------------------------------------------------

    def apply_profile(self, profile: dict, saved_at) -> None:
        self._all_runes = list(profile.get("runes", []))
        self._equipped_index = {}
        for monster in profile.get("monsters", []):
            for rune in getattr(monster, "equipped_runes", []):
                key = rune.rune_id if rune.rune_id is not None else id(rune)
                self._equipped_index[key] = monster.name

        # Reset filters (blockSignals keeps us from calling _refilter N times).
        self._filter_bar.blockSignals(True)
        self._filter_bar.reset_to_defaults()
        self._filter_bar.blockSignals(False)
        self._refilter()
        self._detail.clear()

    # -- internals -------------------------------------------------------

    def _refilter(self) -> None:
        fb = self._filter_bar
        sets = fb.selected_sets()
        slots = fb.selected_slots()
        stars = fb.selected_stars()
        grades = fb.selected_grades()
        focus = fb.focus_stat()
        mode = fb.score_mode()
        threshold = fb.score_threshold()

        filtered: list[Rune] = []
        for r in self._all_runes:
            if r.set not in sets:
                continue
            if r.slot not in slots:
                continue
            if r.stars not in stars:
                continue
            if r.grade not in grades:
                continue
            if focus and not any(s.type == focus for s in r.substats):
                continue
            score = r.swex_efficiency if mode == "Eff" else r.swex_max_efficiency
            if threshold > 0 and (score is None or score < threshold):
                continue
            filtered.append(r)

        self._table.set_runes(filtered, self._equipped_index, focus_stat=focus)

    def _on_rune_selected(self, rune: Rune) -> None:
        key = rune.rune_id if rune.rune_id is not None else id(rune)
        self._detail.set_rune(rune, equipped_on=self._equipped_index.get(key))
