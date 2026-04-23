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

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from models import Monster, Rune
from swlens import rl_score
from ui import theme
G = theme.D
from ui.monsters.elements import ELEMENTS, element_key, hex_alpha, make_star_pixmap
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
        return float(rl_score(rune).total)
    except Exception:
        return None


def _monster_efficiency(mon: Monster) -> float:
    effs = [e for e in (_rune_efficiency(r) for r in mon.equipped_runes) if e is not None]
    return sum(effs) / len(effs) if effs else 0.0


def _equipped_count(mon: Monster) -> int:
    return len(mon.equipped_runes)


# ── Pill toggle button ────────────────────────────────────────────────────
class _PillButton(QPushButton):
    """Shared pill used by status/element filters."""

    def __init__(self, key: str, label: str, kind: str = "default", parent=None) -> None:
        super().__init__(label, parent)
        self.key = key
        self._kind = kind
        self._el_color: str | None = None
        # WA_StyledBackground forces QSS to fully control the button's paint,
        # otherwise the native Windows style leaks a square frame on QPushButton
        # even when border-radius is set — causing pills to look rectangular.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(28)
        self._apply(False)

    def set_element_color(self, color: str) -> None:
        self._el_color = color
        self._apply(self.isChecked())

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply(active)

    def _apply(self, active: bool) -> None:
        if self._kind == "element" and active and self._el_color:
            bg = hex_alpha(self._el_color, "22")
            fg = self._el_color
            border = hex_alpha(self._el_color, "80")
        elif active:
            bg = G.ACCENT_DIM
            fg = G.ACCENT
            border = G.ACCENT
        else:
            bg = "rgba(0,0,0,0.25)"
            if self._kind == "element":
                fg = G.FG_MUTE
            elif self._kind == "star":
                fg = G.ACCENT   # star pills use the accent colour
            else:
                fg = G.FG_DIM
            border = G.BORDER

        self.setStyleSheet(
            f"""
            QPushButton {{
                background:{bg}; color:{fg};
                border:1px solid {border}; border-radius:14px;
                padding:2px 12px;
                font-family:'{G.FONT_UI}';
                font-size:11px; font-weight:600;
            }}
            QPushButton:hover {{
                background:{G.ACCENT_DIM}; color:{G.ACCENT};
                border:1px solid {G.ACCENT};
            }}
            """
        )


# ── Main page ─────────────────────────────────────────────────────────────
class MonstersPage(QWidget):
    """Public API preserved: `apply_profile(profile, saved_at)`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"MonstersPage {{ color:{G.FG}; }}")

        # ── State ─────────────────────────────────────────────────
        self._all_monsters: list[Monster] = []
        self._filtered: list[Monster] = []
        self._view: str = "grid"               # 'grid' | 'table'
        self._sort_by: str = "efficiency"
        self._filter_element: str | None = None   # element key ('fire', ...)
        self._filter_equipped: str = "all"     # 'all' | 'equipped' | 'empty'
        self._filter_stars: set[int] = set()   # {1..6}, empty = no filter
        self._search: str = ""
        self._selected: Monster | None = None

        self._eff_cache: dict[int, float] = {}       # id(Monster) -> eff avg
        self._equipped_cache: dict[int, int] = {}

        self._grid_cards: list[MonsterCard] = []
        self._row_widgets: list[MonsterTableRow] = []

        self._detail_modal: MonsterDetailModal | None = None

        # ── Layout skeleton ──────────────────────────────────────
        # Root is H-split so the side panel (Infos Générales) spans the
        # FULL height of the page, from title-bar to bottom.
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        left_col = QWidget()
        left_lay = QVBoxLayout(left_col)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        left_lay.addWidget(self._build_header())
        left_lay.addWidget(self._h_separator())
        left_lay.addWidget(self._build_toolbar())

        # List area (grid/table) below the toolbar
        body = QWidget()
        body_lay = QHBoxLayout(body)
        # No right margin so the grid extends up to the side-panel separator.
        body_lay.setContentsMargins(24, 4, 0, 16)
        body_lay.setSpacing(0)

        self._list_area = QScrollArea()
        self._list_area.setWidgetResizable(True)
        self._list_area.setFrameShape(QFrame.Shape.NoFrame)
        # Transparent viewport so the page's brown background shows through
        # behind the monster cards.
        self._list_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._list_area.viewport().setAutoFillBackground(False)
        self._list_area.setStyleSheet(
            f"""
            QScrollArea, QScrollArea > QWidget > QWidget {{ background:transparent; }}
            QScrollBar:vertical {{ width:6px; background:transparent; margin:6px; }}
            QScrollBar::handle:vertical {{
                background:rgba(240,104,154,0.40); border-radius:3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            """
        )

        # Two swap-able inner widgets: grid and table. We just switch which
        # one the scroll area owns.
        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(6)
        self._grid_layout.setVerticalSpacing(6)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._table_widget = QFrame()
        self._table_widget.setObjectName("MonsterTable")
        self._table_widget.setStyleSheet(
            f"""
            #MonsterTable {{
                background:{G.PANEL};
                border:1px solid {G.BORDER};
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

        left_lay.addWidget(body, 1)
        outer.addWidget(left_col, 1)

        # Vertical separator between list area and side panel
        outer.addWidget(self._v_separator())

        self._side_panel = MonsterSidePanel()
        self._side_panel.open_detail_clicked.connect(self._open_detail)
        # Full height: panel spans from title bar to bottom of the page.
        outer.addWidget(self._side_panel)

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
        """Header mirrors `monstres sw.png`: big 'Monstres' title on the left,
        inline Filter/Sort/Search controls on the right."""
        header = QWidget()
        lay = QHBoxLayout(header)
        lay.setContentsMargins(24, 18, 24, 10)
        lay.setSpacing(14)

        title = QLabel("Monstres")
        title.setStyleSheet(
            f"color:{G.FG}; font-family:'{G.FONT_UI}';"
            f"font-size:22px; font-weight:700; letter-spacing:-0.3px;"
        )
        lay.addWidget(title, 0, Qt.AlignmentFlag.AlignVCenter)

        self._counter = QLabel("")
        self._counter.setTextFormat(Qt.TextFormat.RichText)
        self._counter.setStyleSheet(
            f"color:{G.FG_DIM}; font-family:'{G.FONT_UI}';"
            f"font-size:11px; padding-left:10px;"
        )
        lay.addWidget(self._counter, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch(1)

        # Equipped combo ("Filter ▼" in maquette)
        self._equipped_combo = QComboBox()
        for key, label in (("all", "Filtrer"), ("equipped", "Runés"), ("empty", "Vides")):
            self._equipped_combo.addItem(label, userData=key)
        self._equipped_combo.setCurrentIndex(0)
        self._equipped_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._equipped_combo.setStyleSheet(self._combo_qss())
        self._equipped_combo.currentIndexChanged.connect(self._on_equipped_changed)
        lay.addWidget(self._equipped_combo, 0, Qt.AlignmentFlag.AlignVCenter)

        # Sort combo
        self._sort_combo = QComboBox()
        for key, label in SORT_LABELS.items():
            self._sort_combo.addItem(label, userData=key)
        self._sort_combo.setCurrentIndex(0)
        self._sort_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sort_combo.setStyleSheet(self._combo_qss())
        self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        lay.addWidget(self._sort_combo, 0, Qt.AlignmentFlag.AlignVCenter)

        # Search (inline, compact)
        search_wrap = QFrame()
        search_wrap.setObjectName("SearchBox")
        search_wrap.setStyleSheet(
            f"""
            #SearchBox {{
                background: rgba(0,0,0,0.20);
                border: 1px solid {G.BORDER};
                border-radius: 6px;
            }}
            """
        )
        sl = QHBoxLayout(search_wrap)
        sl.setContentsMargins(10, 4, 10, 4)
        sl.setSpacing(6)
        loupe = QLabel("⌕")
        loupe.setStyleSheet(f"color:{G.FG_MUTE}; font-size:13px;")
        sl.addWidget(loupe, 0, Qt.AlignmentFlag.AlignVCenter)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Rechercher…")
        self._search_input.setFixedWidth(180)
        self._search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background:transparent; border:none;
                color:{G.FG}; font-family:'{G.FONT_UI}';
                font-size:11px; selection-background-color:{G.ACCENT_DIM};
            }}
            """
        )
        self._search_input.textChanged.connect(self._on_search_changed)
        sl.addWidget(self._search_input, 1)
        lay.addStretch(1)
        lay.addWidget(search_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        return header

    def _combo_qss(self) -> str:
        return (
            f"QComboBox {{"
            f"  background: rgba(0,0,0,0.20); border: 1px solid {G.BORDER};"
            f"  border-radius: 6px; color: {G.FG};"
            f"  font-family:'{G.FONT_UI}'; font-size:11px;"
            f"  padding: 4px 24px 4px 10px; min-height: 18px;"
            f"}}"
            f"QComboBox::drop-down {{ border:none; width: 18px; }}"
            f"QComboBox QAbstractItemView {{"
            f"  background:{G.PANEL}; color:{G.FG}; border:1px solid {G.BORDER};"
            f"  selection-background-color:{G.ACCENT_DIM};"
            f"  selection-color:{G.ACCENT}; outline:0;"
            f"}}"
        )

    def _on_equipped_changed(self, _idx: int) -> None:
        key = self._equipped_combo.currentData() or "all"
        self._filter_equipped = key
        self._refilter()

    def _h_separator(self) -> QFrame:
        """Thin horizontal line between header block and toolbar."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.NoFrame)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{G.BORDER}; border:none;")
        return line

    def _v_separator(self) -> QFrame:
        """Thin vertical line between list area and side panel."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.NoFrame)
        line.setFixedWidth(1)
        line.setStyleSheet(f"background:{G.BORDER}; border:none;")
        return line

    # ── Toolbar build ─────────────────────────────────────────────────
    def _build_toolbar(self) -> QWidget:
        """Toolbar mirrors `monstres sw.png`:
        - "Élément" label then a row of individual rounded element pills
        - "Étoiles" label then a row of individual rounded star pills
        Each pill is an independent rounded card — no segmented container.
        """
        bar = QWidget()
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(24, 6, 24, 10)
        outer.setSpacing(10)

        # ── Row 1: Element + Star Rating (labels above) ─────────────
        el_col = QVBoxLayout()
        el_col.setSpacing(4)
        el_col.addWidget(self._section_label("Élément"))
        el_row = QHBoxLayout()
        el_row.setContentsMargins(0, 0, 0, 0)
        el_row.setSpacing(6)

        self._element_btns: dict[str | None, _PillButton] = {}
        all_btn = _PillButton("", "All", kind="default")
        all_btn.setFixedHeight(28)
        all_btn.clicked.connect(lambda: self._set_element(None))
        self._element_btns[None] = all_btn
        all_btn.set_active(True)
        el_row.addWidget(all_btn)

        for key, meta in ELEMENTS.items():
            b = _PillButton(key, meta.label, kind="element")
            b.setFixedHeight(28)
            b.set_element_color(meta.color)
            icon_path = theme.asset_element_icon(key)
            b.setIcon(QIcon(icon_path))
            b.setIconSize(QSize(16, 16))
            b.clicked.connect(lambda _c=False, k=key: self._toggle_element(k))
            el_row.addWidget(b)
            self._element_btns[key] = b
        el_row.addStretch(1)
        el_col.addLayout(el_row)

        star_col = QVBoxLayout()
        star_col.setSpacing(4)
        star_col.addWidget(self._section_label("Étoiles"))
        star_row = QHBoxLayout()
        star_row.setContentsMargins(0, 0, 0, 0)
        star_row.setSpacing(6)

        self._star_btns: dict[int, _PillButton] = {}
        # Vector star icon (crisp at all DPIs — the text ★ glyph looked pixelated).
        star_icon = QIcon(make_star_pixmap(14, QColor(G.ACCENT)))
        # Maquette shows 1, 2, 3, 4, 6 — no 5★ pill.
        for n in (1, 2, 3, 4, 6):
            b = _PillButton(str(n), f"  {n}", kind="star")
            b.setIcon(star_icon)
            b.setIconSize(QSize(14, 14))
            b.setFixedHeight(28)
            b.clicked.connect(lambda _c=False, s=n: self._toggle_star(s))
            star_row.addWidget(b)
            self._star_btns[n] = b
        star_row.addStretch(1)
        star_col.addLayout(star_row)

        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(24)
        row1.addLayout(el_col, 1)
        row1.addLayout(star_col, 0)
        outer.addLayout(row1)

        return bar

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color:{G.FG_DIM}; font-family:'{G.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:0.4px;"
        )
        return lbl

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
        # mirror to combo if mounted
        combo = getattr(self, "_equipped_combo", None)
        if combo is not None:
            for i in range(combo.count()):
                if combo.itemData(i) == key:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(i)
                    combo.blockSignals(False)
                    break
        self._refilter()

    def _toggle_star(self, star: int) -> None:
        if star in self._filter_stars:
            self._filter_stars.discard(star)
        else:
            self._filter_stars.add(star)
        for n, b in self._star_btns.items():
            b.set_active(n in self._filter_stars)
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
            if self._filter_stars and int(m.stars) not in self._filter_stars:
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
            f"<span style='color:{G.FG}; font-family:\"{G.FONT_MONO}\";'>"
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
            cols = max(1, (self._list_area.viewport().width() or 900) // 76)
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
            cols = max(1, (self._list_area.viewport().width() or 900) // 76)
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
