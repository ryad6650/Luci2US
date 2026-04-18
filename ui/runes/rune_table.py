"""Rune list table (QTableWidget wrapper).

Columns: Set, SL, Main, <one column per substat type>, Eff, Max, Equipee.
Click-to-sort on any column. Each substat column sorts numerically by the
rune's value+grind for that stat (empty for runes that don't have it).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from models import Rune, STATS_FR
from ui import theme


SUBSTAT_COLUMNS: list[str] = list(STATS_FR)  # 11 stats in display order

COL_SET = 0
COL_SLOT = 1
COL_MAIN = 2
SUBSTAT_COL_START = 3
SUBSTAT_COL_END = SUBSTAT_COL_START + len(SUBSTAT_COLUMNS)  # exclusive
COL_EFF = SUBSTAT_COL_END
COL_MAX = COL_EFF + 1
COL_EQUIPPED = COL_MAX + 1
COLUMN_COUNT = COL_EQUIPPED + 1


def _substat_col(stat: str) -> int:
    return SUBSTAT_COL_START + SUBSTAT_COLUMNS.index(stat)


def _format_main(rune: Rune) -> str:
    ms = rune.main_stat
    if ms is None:
        return "-"
    return f"{ms.type}+{int(ms.value)}"


def _substat_cell(rune: Rune, stat: str) -> tuple[float, str]:
    """Return (sort_value, display) for this rune's column of `stat`.

    - sort_value = value+grind (float("-inf") if the rune doesn't have the stat).
    - display: "" if absent; "12" if no grind; "12+5" if grinded.
    """
    for s in rune.substats:
        if s.type == stat:
            v = int(s.value)
            g = int(s.grind_value)
            total = float(s.value + s.grind_value)
            return (total, f"{v}+{g}" if g else f"{v}")
    return (float("-inf"), "")


class _NumericItem(QTableWidgetItem):
    def __lt__(self, other: object) -> bool:
        try:
            a = self.data(Qt.ItemDataRole.UserRole)
            b = other.data(Qt.ItemDataRole.UserRole)  # type: ignore[attr-defined]
            if a is None:
                a = float("-inf")
            if b is None:
                b = float("-inf")
            return float(a) < float(b)
        except Exception:
            return super().__lt__(other)  # type: ignore[misc]


class _EquippedItem(QTableWidgetItem):
    """Alphabetic sort with dash (unequipped) pushed to the end."""

    def __lt__(self, other: object) -> bool:
        a = self.text()
        b = other.text()  # type: ignore[attr-defined]
        a_dash = (a == "\u2014" or not a)
        b_dash = (b == "\u2014" or not b)
        if a_dash and not b_dash:
            return False
        if b_dash and not a_dash:
            return True
        return a.lower() < b.lower()


def _text_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


class RuneTable(QWidget):
    rune_selected = Signal(object)  # emits Rune

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, COLUMN_COUNT, self)

        headers = ["Set", "SL", "Main"] + SUBSTAT_COLUMNS + ["Eff", "Max", "\u00c9quip\u00e9e"]
        self._table.setHorizontalHeaderLabels(headers)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            f"QTableWidget {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" gridline-color:{theme.COLOR_BORDER_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" alternate-background-color:#180e07; font-size:12px; }}"
            f"QHeaderView::section {{ background:{theme.COLOR_BG_GRAD_HI};"
            f" color:{theme.COLOR_GOLD}; border:none; padding:4px;"
            f" border-bottom:1px solid {theme.COLOR_BORDER_FRAME}; font-weight:600; }}"
            f"QTableWidget::item:selected {{ background:{theme.COLOR_MANA_BG};"
            f" color:{theme.COLOR_TEXT_MAIN}; }}"
        )
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(COL_SET, 110)
        self._table.setColumnWidth(COL_SLOT, 40)
        self._table.setColumnWidth(COL_MAIN, 105)
        for stat in SUBSTAT_COLUMNS:
            self._table.setColumnWidth(_substat_col(stat), 52)
        self._table.setColumnWidth(COL_EFF, 55)
        self._table.setColumnWidth(COL_MAX, 55)
        self._table.setColumnWidth(COL_EQUIPPED, 130)

        self._table.itemSelectionChanged.connect(self._on_selection)

        outer.addWidget(self._table)

        self._rows: list[Rune] = []
        self._focus_stat: str | None = None

    # -- public API ------------------------------------------------------

    def set_runes(
        self,
        runes: list[Rune],
        equipped_index: dict,
        focus_stat: str | None = None,
    ) -> None:
        self._table.setSortingEnabled(False)
        self._table.clearSelection()
        self._table.setRowCount(0)
        self._rows = list(runes)
        self._focus_stat = focus_stat

        for row, rune in enumerate(self._rows):
            self._table.insertRow(row)
            self._fill_row(row, rune, equipped_index)

        self._table.setSortingEnabled(True)
        if focus_stat and focus_stat in SUBSTAT_COLUMNS:
            self._table.sortItems(_substat_col(focus_stat), Qt.SortOrder.DescendingOrder)
        else:
            self._table.sortItems(COL_EFF, Qt.SortOrder.DescendingOrder)

    def selected_rune(self) -> Rune | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, COL_SET)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole + 1)

    # -- internals -------------------------------------------------------

    def _fill_row(self, row: int, rune: Rune, equipped_index: dict) -> None:
        # Column 0 : Set (text + icon)
        set_item = _text_item(rune.set)
        set_item.setData(Qt.ItemDataRole.UserRole + 1, rune)
        try:
            from ui.theme import asset_set_logo, set_asset_name
            from PySide6.QtGui import QIcon
            pix = QPixmap(asset_set_logo(set_asset_name(rune.set)))
            if not pix.isNull():
                set_item.setIcon(QIcon(pix))
        except Exception:
            pass
        self._table.setItem(row, COL_SET, set_item)

        # Column 1 : Slot
        slot_item = _NumericItem()
        slot_item.setFlags(slot_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        slot_item.setText(str(rune.slot))
        slot_item.setData(Qt.ItemDataRole.UserRole, float(rune.slot))
        slot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._table.setItem(row, COL_SLOT, slot_item)

        # Column 2 : Main
        self._table.setItem(row, COL_MAIN, _text_item(_format_main(rune)))

        # One column per substat
        for stat in SUBSTAT_COLUMNS:
            value, display = _substat_cell(rune, stat)
            item = _NumericItem()
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setText(display)
            item.setData(Qt.ItemDataRole.UserRole, value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, _substat_col(stat), item)

        # Eff
        eff = rune.swex_efficiency
        item = _NumericItem()
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if eff is None:
            item.setText("")
            item.setData(Qt.ItemDataRole.UserRole, float("-inf"))
        else:
            item.setText(f"{eff:.0f}")
            item.setData(Qt.ItemDataRole.UserRole, float(eff))
        self._table.setItem(row, COL_EFF, item)

        # Max
        mx = rune.swex_max_efficiency
        item = _NumericItem()
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if mx is None:
            item.setText("")
            item.setData(Qt.ItemDataRole.UserRole, float("-inf"))
        else:
            item.setText(f"{mx:.0f}")
            item.setData(Qt.ItemDataRole.UserRole, float(mx))
        self._table.setItem(row, COL_MAX, item)

        # Equipped
        key = rune.rune_id if rune.rune_id is not None else id(rune)
        monster_name = equipped_index.get(key)
        self._table.setItem(
            row, COL_EQUIPPED, _EquippedItem(monster_name if monster_name else "\u2014")
        )

    def _on_selection(self) -> None:
        rune = self.selected_rune()
        if rune is not None:
            self.rune_selected.emit(rune)
