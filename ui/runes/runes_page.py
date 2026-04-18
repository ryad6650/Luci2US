"""Runes page — inventory browser (design_handoff_runes).

Layout (top→bottom, inside main content column):
    Header        (eyebrow "INVENTAIRE" + title "Runes" + live counters)
    Toolbar       (set dropdown + slot/grade/rarity pills + level slider + equipped pills)
    Body split    (table card in the middle | RuneDetailPanel 320px fixed on the right)

The CTA in the side panel opens SimuEquipModal; candidates are placeholder
until the backend is wired.

Public API preserved: `apply_profile(profile, saved_at)`.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models import Rune
from ui import theme
from ui.runes.rune_detail_panel import RuneDetailPanel
from ui.runes.rune_filter_bar import RuneFilterBar
from ui.runes.rune_simu_modal import SimuCandidate, SimuEquipModal
from ui.runes.rune_table import RuneTable


class RunesPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"RunesPage {{ background: transparent; color:{theme.D.FG}; }}"
        )

        # ── State ────────────────────────────────────────────────
        self._all_runes: list[Rune] = []
        self._equipped_index: dict = {}
        self._monsters: list = []
        self._selected: Rune | None = None
        self._simu_modal: SimuEquipModal | None = None

        # ── Layout skeleton ──────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())

        self._filter_bar = RuneFilterBar()
        self._filter_bar.changed.connect(self._refilter)
        outer.addWidget(self._filter_bar)

        # Body split
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(28, 0, 28, 20)
        body_lay.setSpacing(16)

        self._table = RuneTable()
        self._table.rune_selected.connect(self._on_rune_selected)
        body_lay.addWidget(self._table, 1)

        self._detail = RuneDetailPanel()
        self._detail.simulate_clicked.connect(self._open_simu_modal)
        body_lay.addWidget(self._detail, 0)

        outer.addWidget(body, 1)

    # ── Header build ──────────────────────────────────────────────
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

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        title = QLabel("Runes")
        title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:24px; font-weight:600; letter-spacing:-0.5px;"
        )
        row.addWidget(title, 0, Qt.AlignmentFlag.AlignBottom)

        self._counter = QLabel("")
        self._counter.setTextFormat(Qt.TextFormat.RichText)
        self._counter.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12.5px;"
        )
        row.addWidget(self._counter, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)

        row_wrap = QWidget()
        row_wrap.setLayout(row)
        lay.addWidget(row_wrap)
        return header

    # ── Public API ────────────────────────────────────────────────
    def apply_profile(self, profile: dict, saved_at) -> None:
        self._all_runes = list(profile.get("runes", []))
        self._monsters = list(profile.get("monsters", []))
        self._equipped_index = {}
        for monster in self._monsters:
            for rune in getattr(monster, "equipped_runes", []):
                key = rune.rune_id if rune.rune_id is not None else id(rune)
                self._equipped_index[key] = monster.name

        sets_present = sorted({r.set for r in self._all_runes})
        self._filter_bar.blockSignals(True)
        self._filter_bar.populate_sets(sets_present)
        self._filter_bar.reset_to_defaults()
        self._filter_bar.blockSignals(False)

        self._selected = None
        self._refilter()
        self._detail.clear()

    # ── Filtering ─────────────────────────────────────────────────
    def _refilter(self) -> None:
        fb = self._filter_bar
        set_filter = fb.filter_set()
        slot_filter = fb.filter_slot()
        stars_filter = fb.filter_stars()
        rarity_filter = fb.filter_rarity()
        level_min = fb.filter_level_min()
        equipped_mode = fb.filter_equipped()

        filtered: list[Rune] = []
        for r in self._all_runes:
            if set_filter and r.set != set_filter:
                continue
            if slot_filter is not None and r.slot != slot_filter:
                continue
            if stars_filter is not None and r.stars != stars_filter:
                continue
            if rarity_filter is not None and r.grade != rarity_filter:
                continue
            if r.level < level_min:
                continue
            key = r.rune_id if r.rune_id is not None else id(r)
            is_equipped = key in self._equipped_index
            if equipped_mode == "equipped" and not is_equipped:
                continue
            if equipped_mode == "free" and is_equipped:
                continue
            filtered.append(r)

        self._table.set_runes(filtered, self._equipped_index)
        self._update_counter(len(filtered))

        # Keep current selection if still visible, otherwise pick first.
        if self._selected is None or self._selected not in filtered:
            self._selected = filtered[0] if filtered else None
        if self._selected is not None:
            self._table.set_selected_rune(self._selected)
            key = self._selected.rune_id if self._selected.rune_id is not None else id(self._selected)
            self._detail.set_rune(self._selected, self._equipped_index.get(key))
        else:
            self._detail.clear()

    def _update_counter(self, shown: int) -> None:
        total = len(self._all_runes)
        plus15 = sum(1 for r in self._all_runes if r.level >= 15)
        free = sum(
            1 for r in self._all_runes
            if (r.rune_id if r.rune_id is not None else id(r)) not in self._equipped_index
        )
        mono = theme.D.FONT_MONO
        fg = theme.D.FG
        mute = theme.D.FG_MUTE
        self._counter.setText(
            f"<span style='color:{fg}; font-family:\"{mono}\";'>{shown}</span>"
            f" <span style='color:{mute};'>sur {total}</span>"
            f" <span style='color:{mute};'>·</span> "
            f"<span style='color:{fg}; font-family:\"{mono}\";'>{plus15}</span> +15 "
            f"<span style='color:{mute};'>·</span> "
            f"<span style='color:{fg}; font-family:\"{mono}\";'>{free}</span> libres"
        )

    # ── Selection ─────────────────────────────────────────────────
    def _on_rune_selected(self, rune: Rune) -> None:
        self._selected = rune
        key = rune.rune_id if rune.rune_id is not None else id(rune)
        self._detail.set_rune(rune, self._equipped_index.get(key))

    # ── Simulation ────────────────────────────────────────────────
    def _open_simu_modal(self, rune: Rune) -> None:
        if self._simu_modal is None:
            self._simu_modal = SimuEquipModal(self.window())
            self._simu_modal.equip_confirmed.connect(self._on_equip_confirmed)
        candidates = self._build_candidates(rune)
        self._simu_modal.load(rune, candidates)
        self._simu_modal.resize(self.window().size() if self.window() else self.size())
        self._simu_modal.exec()

    def _build_candidates(self, rune: Rune) -> list[SimuCandidate]:
        """Placeholder candidates until a real compatibility/eff engine is wired.

        Picks up to five monsters from the profile and fakes a delta around the
        rune's efficiency. The UI should render correctly once a real scorer
        replaces this function.
        """
        out: list[SimuCandidate] = []
        base = rune.swex_efficiency if rune.swex_efficiency is not None else 70.0
        for i, mon in enumerate(self._monsters[:5]):
            current = 55.0 + i * 4.0
            delta = (3.5 + i * 1.3) * (1 if i % 2 == 0 else -1)
            out.append(SimuCandidate(
                name=mon.name,
                stars=int(getattr(mon, "stars", 6)),
                level=int(getattr(mon, "level", 40)),
                current_eff=current,
                delta=delta,
            ))
        return out

    def _on_equip_confirmed(self, candidate: SimuCandidate) -> None:
        # Backend hook — the actual move/persist lives elsewhere. For now the
        # modal closes itself and the page leaves state untouched.
        return
