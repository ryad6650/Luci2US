"""Monsters page — collection browser + detail modal.

High-level layout (design_handoff_monsters/monsters.jsx):
    Header      (eyebrow "COLLECTION" + title + counter + grid/table toggle)
    Toolbar     (search + element chips + status chips + sort combo)
    Body split  (scrolling list | MonsterSidePanel 300px)

Selecting a card/row updates the side panel. The side panel's CTA opens
`MonsterDetailModal`. The page keeps the `apply_profile(profile, saved_at)`
contract so main_window can feed it like the other pages.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from models import Monster, Rune
from s2us_filter import calculate_efficiency_s2us
from ui import theme
from ui.monsters.elements import ELEMENTS, element_key, hex_alpha
from ui.monsters.monster_card import (
    MonsterCard, MonsterTableHeader, MonsterTableRow,
)
from ui.monsters.monster_detail_modal import MonsterDetailModal
from ui.monsters.monster_detail.skills_tab import Skill
from ui.monsters.monster_side_panel import MonsterSidePanel


SORT_LABELS = {
    "efficiency": "Efficacité",
    "stars":      "Étoiles",
    "level":      "Niveau",
    "name":       "Nom",
    "element":    "Élément",
}


def _rune_efficiency(rune: Rune) -> float | None:
    if rune is None:
        return None
    if rune.swex_efficiency is not None:
        return float(rune.swex_efficiency)
    try:
        return float(calculate_efficiency_s2us(rune))
    except Exception:
        return None


def _monster_efficiency(mon: Monster) -> float:
    effs = [e for e in (_rune_efficiency(r) for r in mon.equipped_runes) if e is not None]
    return sum(effs) / len(effs) if effs else 0.0


def _equipped_count(mon: Monster) -> int:
    return len(mon.equipped_runes)


# ── Pill toggle button ────────────────────────────────────────────────────
class _PillButton(QPushButton):
    """Shared pill used by Grid/Table toggle and status/element filters."""

    def __init__(self, key: str, label: str, kind: str = "default", parent=None) -> None:
        super().__init__(label, parent)
        self.key = key
        self._kind = kind
        self._el_color: str | None = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(26)
        self._apply(False)

    def set_element_color(self, color: str) -> None:
        self._el_color = color
        self._apply(self.isChecked())

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply(active)

    def _apply(self, active: bool) -> None:
        if self._kind == "view" and active:
            # Grid/Table toggle — active is filled magenta, black text.
            self.setStyleSheet(
                f"""
                QPushButton {{
                    background:{theme.D.ACCENT}; color:{theme.D.BG};
                    border:none; border-radius:999px;
                    padding:0 14px;
                    font-family:'{theme.D.FONT_UI}';
                    font-size:11px; font-weight:600;
                }}
                """
            )
            return

        if self._kind == "element" and active and self._el_color:
            bg = hex_alpha(self._el_color, "22")
            fg = self._el_color
        elif active:
            bg = theme.D.ACCENT_DIM
            fg = theme.D.ACCENT
        else:
            bg = "transparent"
            fg = theme.D.FG_DIM if self._kind != "element" else theme.D.FG_MUTE

        self.setStyleSheet(
            f"""
            QPushButton {{
                background:{bg}; color:{fg};
                border:none; border-radius:999px;
                padding:0 11px;
                font-family:'{theme.D.FONT_UI}';
                font-size:11px; font-weight:600;
            }}
            QPushButton:hover {{ background:{theme.D.ACCENT_DIM}; color:{theme.D.ACCENT}; }}
            """
        )


class _PillGroup(QFrame):
    """Rounded background holding pill buttons — matches the handoff segmented control."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PillGroup")
        self.setStyleSheet(
            f"""
            #PillGroup {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 999px;
            }}
            """
        )
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(3, 3, 3, 3)
        self._lay.setSpacing(2)

    def add(self, widget: QPushButton) -> None:
        self._lay.addWidget(widget)


# ── Main page ─────────────────────────────────────────────────────────────
class MonstersPage(QWidget):
    """Public API preserved: `apply_profile(profile, saved_at)`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"MonstersPage {{ background: transparent; color:{theme.D.FG}; }}"
        )

        # ── State ─────────────────────────────────────────────────
        self._all_monsters: list[Monster] = []
        self._filtered: list[Monster] = []
        self._view: str = "grid"               # 'grid' | 'table'
        self._sort_by: str = "efficiency"
        self._filter_element: str | None = None   # element key ('fire', ...)
        self._filter_equipped: str = "all"     # 'all' | 'equipped' | 'empty'
        self._search: str = ""
        self._selected: Monster | None = None

        self._eff_cache: dict[int, float] = {}       # id(Monster) -> eff avg
        self._equipped_cache: dict[int, int] = {}

        self._grid_cards: list[MonsterCard] = []
        self._row_widgets: list[MonsterTableRow] = []

        self._detail_modal: MonsterDetailModal | None = None

        # ── Layout skeleton ──────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_toolbar())

        # Body split: list + side panel
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(28, 0, 28, 20)
        body_lay.setSpacing(16)

        self._list_area = QScrollArea()
        self._list_area.setWidgetResizable(True)
        self._list_area.setFrameShape(QFrame.Shape.NoFrame)
        self._list_area.setStyleSheet(
            """
            QScrollArea { background:transparent; }
            QScrollBar:vertical { width:6px; background:transparent; margin:6px; }
            QScrollBar::handle:vertical {
                background:rgba(240,104,154,0.25); border-radius:3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
            """
        )

        # Two swap-able inner widgets: grid and table. We just switch which
        # one the scroll area owns.
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(12)
        self._grid_layout.setVerticalSpacing(12)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._table_widget = QFrame()
        self._table_widget.setObjectName("MonsterTable")
        self._table_widget.setStyleSheet(
            f"""
            #MonsterTable {{
                background:{theme.D.PANEL};
                border:1px solid {theme.D.BORDER};
                border-radius:12px;
            }}
            """
        )
        tl = QVBoxLayout(self._table_widget)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)
        self._table_header = MonsterTableHeader()
        tl.addWidget(self._table_header)
        self._table_rows_wrap = QWidget()
        self._table_rows_layout = QVBoxLayout(self._table_rows_wrap)
        self._table_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._table_rows_layout.setSpacing(0)
        tl.addWidget(self._table_rows_wrap)

        self._list_area.setWidget(self._grid_widget)
        body_lay.addWidget(self._list_area, 1)

        self._side_panel = MonsterSidePanel()
        self._side_panel.open_detail_clicked.connect(self._open_detail)
        body_lay.addWidget(self._side_panel, 0, Qt.AlignmentFlag.AlignTop)

        outer.addWidget(body, 1)

        # Debounce the search input by 150ms (handoff recommends it).
        self._search_timer = QTimer(self)
        self._search_timer.setInterval(150)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._refilter)

        # ── Provide a test-accessibility proxy for the list.
        # The old UI exposed `_list._rows` — keep a similar shim so existing
        # integration tests that poke at row counts still have something to
        # look at.
        self._list = _RowsProxy(self)

    # ── Header build ──────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        header = QWidget()
        lay = QHBoxLayout(header)
        lay.setContentsMargins(28, 22, 28, 14)
        lay.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(3)
        eyebrow = QLabel("COLLECTION")
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:1.5px;"
        )
        left.addWidget(eyebrow)

        title = QLabel("Monstres")
        title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:24px; font-weight:600; letter-spacing:-0.5px;"
        )
        left.addWidget(title)

        self._counter = QLabel("")
        self._counter.setTextFormat(Qt.TextFormat.RichText)
        self._counter.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px;"
        )
        left.addWidget(self._counter)
        lay.addLayout(left, 1)

        # Grid/Table toggle
        toggle_group = _PillGroup()
        self._view_btns: dict[str, _PillButton] = {}
        self._view_group = QButtonGroup(self)
        self._view_group.setExclusive(True)
        for key, label in (("grid", "Grille"), ("table", "Tableau")):
            b = _PillButton(key, label, kind="view")
            b.clicked.connect(lambda _c=False, k=key: self._set_view(k))
            toggle_group.add(b)
            self._view_btns[key] = b
            self._view_group.addButton(b)
        self._view_btns["grid"].set_active(True)
        lay.addWidget(toggle_group, 0, Qt.AlignmentFlag.AlignBottom)

        return header

    # ── Toolbar build ─────────────────────────────────────────────────
    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(28, 0, 28, 14)
        lay.setSpacing(10)

        # Search
        search_wrap = QFrame()
        search_wrap.setObjectName("SearchBox")
        search_wrap.setStyleSheet(
            f"""
            #SearchBox {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 8px;
            }}
            """
        )
        sl = QHBoxLayout(search_wrap)
        sl.setContentsMargins(12, 7, 12, 7)
        sl.setSpacing(8)
        loupe = QLabel("⌕")
        loupe.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-size:14px;"
        )
        sl.addWidget(loupe, 0, Qt.AlignmentFlag.AlignVCenter)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Rechercher un monstre…")
        self._search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background:transparent; border:none;
                color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';
                font-size:12px; selection-background-color:{theme.D.ACCENT_DIM};
            }}
            """
        )
        self._search_input.textChanged.connect(self._on_search_changed)
        sl.addWidget(self._search_input, 1)
        search_wrap.setMinimumWidth(240)
        lay.addWidget(search_wrap)

        # Element filter chips
        el_group = _PillGroup()
        self._element_btns: dict[str | None, _PillButton] = {}
        all_btn = _PillButton("", "Tous", kind="default")
        all_btn.clicked.connect(lambda: self._set_element(None))
        el_group.add(all_btn)
        self._element_btns[None] = all_btn
        all_btn.set_active(True)
        for key, meta in ELEMENTS.items():
            b = _PillButton(key, meta.label, kind="element")
            b.set_element_color(meta.color)
            b.clicked.connect(lambda _c=False, k=key: self._toggle_element(k))
            el_group.add(b)
            self._element_btns[key] = b
        lay.addWidget(el_group)

        # Equipped filter chips
        eq_group = _PillGroup()
        self._equipped_btns: dict[str, _PillButton] = {}
        for key, label in (("all", "Tous"), ("equipped", "Runés"), ("empty", "Vides")):
            b = _PillButton(key, label, kind="default")
            b.clicked.connect(lambda _c=False, k=key: self._set_equipped(k))
            eq_group.add(b)
            self._equipped_btns[key] = b
        self._equipped_btns["all"].set_active(True)
        lay.addWidget(eq_group)

        lay.addStretch(1)

        # Sort
        sort_lbl = QLabel("Trier :")
        sort_lbl.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}'; font-size:11px;"
        )
        lay.addWidget(sort_lbl)

        self._sort_combo = QComboBox()
        for key, label in SORT_LABELS.items():
            self._sort_combo.addItem(label, userData=key)
        self._sort_combo.setCurrentIndex(0)
        self._sort_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sort_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 8px;
                color: {theme.D.FG};
                font-family:'{theme.D.FONT_UI}'; font-size:12px;
                padding: 5px 28px 5px 10px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{ border:none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: #1a0f14;
                color: {theme.D.FG};
                border: 1px solid {theme.D.BORDER};
                selection-background-color: {theme.D.ACCENT_DIM};
                selection-color: {theme.D.ACCENT};
                outline: 0;
            }}
            """
        )
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        lay.addWidget(self._sort_combo)

        return bar

    # ── Public API ────────────────────────────────────────────────────
    def apply_profile(self, profile: dict, saved_at) -> None:
        self._all_monsters = list(profile.get("monsters", []))
        self._eff_cache.clear()
        self._equipped_cache.clear()
        for m in self._all_monsters:
            self._eff_cache[id(m)] = _monster_efficiency(m)
            self._equipped_cache[id(m)] = _equipped_count(m)
        self._selected = None
        self._refilter()

    # ── State setters ─────────────────────────────────────────────────
    def _set_view(self, view: str) -> None:
        if view == self._view:
            return
        self._view = view
        for k, b in self._view_btns.items():
            b.set_active(k == view)
        self._rebuild_list()

    def _set_element(self, key: str | None) -> None:
        self._filter_element = key
        for k, b in self._element_btns.items():
            b.set_active(k == key)
        self._refilter()

    def _toggle_element(self, key: str) -> None:
        """Click the already-active chip → back to 'Tous'."""
        if self._filter_element == key:
            self._set_element(None)
        else:
            self._set_element(key)

    def _set_equipped(self, key: str) -> None:
        self._filter_equipped = key
        for k, b in self._equipped_btns.items():
            b.set_active(k == key)
        self._refilter()

    def _on_search_changed(self, text: str) -> None:
        self._search = text.strip().lower()
        self._search_timer.start()

    def _on_sort_changed(self, _idx: int) -> None:
        self._sort_by = self._sort_combo.currentData() or "efficiency"
        self._refilter()

    # ── Filtering / sorting ───────────────────────────────────────────
    def _refilter(self) -> None:
        monsters = []
        for m in self._all_monsters:
            eq = self._equipped_cache.get(id(m), 0) > 0
            if self._filter_element:
                if element_key(m.element) != self._filter_element:
                    continue
            if self._filter_equipped == "equipped" and not eq:
                continue
            if self._filter_equipped == "empty" and eq:
                continue
            if self._search and self._search not in m.name.lower():
                continue
            monsters.append(m)

        sort_key = {
            "name":       lambda m: m.name.lower(),
            "element":    lambda m: element_key(m.element),
            "stars":      lambda m: (-int(m.stars), -int(m.level)),
            "level":      lambda m: -int(m.level),
            "efficiency": lambda m: -self._eff_cache.get(id(m), 0.0),
        }[self._sort_by]
        monsters.sort(key=sort_key)
        self._filtered = monsters

        self._update_counter()
        self._rebuild_list()
        # Keep current selection if still visible; otherwise pick the first.
        if not any(m is self._selected for m in monsters):
            self._selected = monsters[0] if monsters else None
        self._update_side_panel()
        self._update_row_selection()

    def _update_counter(self) -> None:
        total = len(self._all_monsters)
        shown = len(self._filtered)
        nat6 = sum(1 for m in self._all_monsters if m.stars >= 6)
        self._counter.setText(
            f"<span style='color:{theme.D.FG}; font-family:\"{theme.D.FONT_MONO}\";'>"
            f"{shown}</span> sur {total} · {nat6} nat 6★"
        )

    # ── List rebuild ──────────────────────────────────────────────────
    def _rebuild_list(self) -> None:
        # Clear existing widgets
        for c in self._grid_cards:
            c.setParent(None)
            c.deleteLater()
        self._grid_cards.clear()
        for r in self._row_widgets:
            r.setParent(None)
            r.deleteLater()
        self._row_widgets.clear()
        while self._grid_layout.count():
            it = self._grid_layout.takeAt(0)
            # items are widgets above; layout is empty now.

        if self._view == "grid":
            if self._list_area.widget() is not self._grid_widget:
                self._list_area.takeWidget()
                self._list_area.setWidget(self._grid_widget)
            cols = max(1, min(5, (self._list_area.viewport().width() or 900) // 232))
            self._grid_cols = cols
            for idx, m in enumerate(self._filtered):
                card = MonsterCard(
                    m,
                    self._eff_cache.get(id(m), 0.0),
                    self._equipped_cache.get(id(m), 0),
                )
                card.clicked.connect(self._on_monster_clicked)
                row, col = divmod(idx, cols)
                self._grid_layout.addWidget(card, row, col)
                self._grid_cards.append(card)
            # Fill remaining columns with stretch items so cards don't bloat.
            for c in range(cols):
                self._grid_layout.setColumnStretch(c, 1)
        else:
            if self._list_area.widget() is not self._table_widget:
                self._list_area.takeWidget()
                self._list_area.setWidget(self._table_widget)
            for m in self._filtered:
                row = MonsterTableRow(
                    m,
                    self._eff_cache.get(id(m), 0.0),
                    self._equipped_cache.get(id(m), 0),
                )
                row.clicked.connect(self._on_monster_clicked)
                self._table_rows_layout.addWidget(row)
                self._row_widgets.append(row)

    def resizeEvent(self, e) -> None:  # noqa: N802
        super().resizeEvent(e)
        # Reflow grid columns on resize, but only when the column count
        # actually changes — otherwise rebuilding thrashes layout every pixel.
        if self._view == "grid" and self._grid_cards:
            cols = max(1, min(5, (self._list_area.viewport().width() or 900) // 232))
            if cols != getattr(self, "_grid_cols", cols):
                self._rebuild_list()

    # ── Selection / modal ─────────────────────────────────────────────
    def _on_monster_clicked(self, monster: Monster) -> None:
        self._selected = monster
        self._update_side_panel()
        self._update_row_selection()

    def _update_side_panel(self) -> None:
        if self._selected is None:
            self._side_panel.set_monster(None, 0.0, 0)
            return
        self._side_panel.set_monster(
            self._selected,
            self._eff_cache.get(id(self._selected), 0.0),
            self._equipped_cache.get(id(self._selected), 0),
            base_stats=self._estimate_base_stats(self._selected),
        )

    def _update_row_selection(self) -> None:
        for c in self._grid_cards:
            c.set_selected(c.monster is self._selected)
        for r in self._row_widgets:
            r.set_selected(r.monster is self._selected)

    def _open_detail(self, monster: Monster) -> None:
        if self._detail_modal is None:
            self._detail_modal = MonsterDetailModal(self.window())
        runes: list[Rune | None] = [None] * 6
        effs: list[float | None] = [None] * 6
        for r in monster.equipped_runes:
            slot = int(r.slot)
            if 1 <= slot <= 6:
                runes[slot - 1] = r
                effs[slot - 1] = _rune_efficiency(r)
        base = self._estimate_base_stats(monster)
        total = self._estimate_total_stats(monster, base)
        self._detail_modal.load(
            monster=monster,
            runes=runes,
            rune_effs=effs,
            base_stats=base,
            total_stats=total,
            skills=[],   # no skill data plumbed yet
            passive=None,
            analysis=self._build_analysis_text(monster, runes, effs, total),
        )
        self._detail_modal.show()
        self._detail_modal.raise_()

    # ── Placeholders for unplumbed data ───────────────────────────────
    def _estimate_base_stats(self, monster: Monster) -> dict[str, int]:
        """Rough base stats so the layout renders until the backend is plumbed."""
        seed = (int(monster.unit_master_id) or abs(hash(monster.name))) & 0xFFFF
        return {
            "HP":    10800 + (seed * 37) % 2000,
            "ATK":   680 + (seed * 13) % 300,
            "DEF":   540 + (seed * 17) % 250,
            "SPD":   101,
            "CRI R": 15,
            "CRI D": 50,
            "RES":   15,
            "ACC":   0,
        }

    def _estimate_total_stats(self, monster: Monster, base: dict[str, int]) -> dict[str, int]:
        equipped = sum(1 for r in monster.equipped_runes if r is not None)
        if equipped == 0:
            return dict(base)
        seed = (int(monster.unit_master_id) or abs(hash(monster.name))) & 0xFFFF
        total = {}
        for i, key in enumerate(("HP", "ATK", "DEF", "SPD", "CRI R", "CRI D", "RES", "ACC")):
            boost = 1.0 + ((seed + i) % 5) * 0.12
            extra = 20 + (seed % 20) if key == "SPD" else 0
            total[key] = int(base[key] * boost) + extra
        return total

    def _build_analysis_text(
        self, monster: Monster, runes: list[Rune | None],
        effs: list[float | None], total: dict[str, int],
    ) -> str:
        equipped = sum(1 for r in runes if r is not None)
        avg = sum(e for e in effs if e is not None) / max(1, equipped) if equipped else 0
        if equipped == 0:
            return "Aucune rune équipée — équipe des runes pour voir une analyse."
        pieces = [
            f"{equipped}/6 runes équipées, efficacité moyenne {avg:.1f}%."
        ]
        if total.get("SPD", 0) >= 150:
            pieces.append("SPD élevée, bon pour les rôles tempo.")
        if total.get("ACC", 0) < 45:
            pieces.append("ACC insuffisante pour de l'endgame (viser ≥ 55%).")
        return " ".join(pieces)


class _RowsProxy:
    """Legacy accessor used by tests: `page._list._rows` returns either grid
    cards or table rows, whichever is currently rendered."""

    def __init__(self, page: "MonstersPage") -> None:
        self._page = page

    @property
    def _rows(self) -> list:
        if self._page._view == "grid":
            return list(self._page._grid_cards)
        return list(self._page._row_widgets)
