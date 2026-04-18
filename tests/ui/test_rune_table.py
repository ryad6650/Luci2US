from PySide6.QtCore import Qt

from models import Rune, SubStat
from ui.runes.rune_table import (
    COLUMN_COUNT, COL_EFF, COL_EQUIPPED, RuneTable, SUBSTAT_COLUMNS,
    _substat_col,
)


def _r(**kw) -> Rune:
    defaults = dict(
        set="Violent", slot=2, stars=6, grade="Heroique", level=12,
        main_stat=SubStat(type="VIT", value=39, grind_value=0),
        prefix=None, substats=[
            SubStat(type="CC", value=9, grind_value=0),
            SubStat(type="VIT", value=6, grind_value=2),
        ],
        swex_efficiency=90.0, swex_max_efficiency=100.0, rune_id=1,
    )
    defaults.update(kw)
    return Rune(**defaults)


def test_table_has_expected_columns(qapp):
    t = RuneTable()
    assert t._table.columnCount() == COLUMN_COUNT
    # 11 substat columns between Main and Eff
    for stat in SUBSTAT_COLUMNS:
        header = t._table.horizontalHeaderItem(_substat_col(stat)).text()
        assert header == stat


def test_set_runes_populates(qapp):
    t = RuneTable()
    runes = [_r(rune_id=1), _r(rune_id=2, slot=3)]
    t.set_runes(runes, equipped_index={})
    assert t._table.rowCount() == 2


def test_substat_cell_shows_value_and_grind(qapp):
    t = RuneTable()
    t.set_runes([_r()], equipped_index={})
    # VIT: 6 base + 2 grind
    item = t._table.item(0, _substat_col("VIT"))
    assert item.text() == "6+2"
    # CC: 9 base, no grind
    item = t._table.item(0, _substat_col("CC"))
    assert item.text() == "9"
    # ATQ: rune doesn't have this stat
    item = t._table.item(0, _substat_col("ATQ"))
    assert item.text() == ""


def test_substat_cells_sort_numerically(qapp):
    t = RuneTable()
    r_low = _r(rune_id=1, substats=[SubStat(type="VIT", value=5)])
    r_high = _r(rune_id=2, substats=[SubStat(type="VIT", value=20)])
    t.set_runes([r_low, r_high], equipped_index={})
    t._table.sortItems(_substat_col("VIT"), Qt.SortOrder.DescendingOrder)
    first_set = t._table.item(0, 0).data(Qt.ItemDataRole.UserRole + 1)
    assert first_set is r_high


def test_missing_substat_sorts_to_bottom(qapp):
    t = RuneTable()
    r_with = _r(rune_id=1, substats=[SubStat(type="VIT", value=10)])
    r_without = _r(rune_id=2, substats=[SubStat(type="CC", value=5)])
    t.set_runes([r_with, r_without], equipped_index={})
    t._table.sortItems(_substat_col("VIT"), Qt.SortOrder.DescendingOrder)
    first_set = t._table.item(0, 0).data(Qt.ItemDataRole.UserRole + 1)
    assert first_set is r_with


def test_equipped_column_uses_index(qapp):
    t = RuneTable()
    r = _r(rune_id=42)
    t.set_runes([r], equipped_index={42: "Lushen"})
    row_item = t._table.item(0, COL_EQUIPPED)
    assert row_item.text() == "Lushen"


def test_equipped_column_dash_when_not_equipped(qapp):
    t = RuneTable()
    r = _r(rune_id=42)
    t.set_runes([r], equipped_index={})
    row_item = t._table.item(0, COL_EQUIPPED)
    assert row_item.text() == "\u2014"


def test_missing_efficiency_is_empty(qapp):
    t = RuneTable()
    r = _r(rune_id=1, swex_efficiency=None)
    t.set_runes([r], equipped_index={})
    item = t._table.item(0, COL_EFF)
    assert item.text() == ""


def test_focus_mode_sorts_by_focus_stat(qapp):
    t = RuneTable()
    r_low = _r(rune_id=1, substats=[SubStat(type="VIT", value=5)])
    r_high = _r(rune_id=2, substats=[SubStat(type="VIT", value=20)])
    t.set_runes([r_low, r_high], equipped_index={}, focus_stat="VIT")
    first_set = t._table.item(0, 0).data(Qt.ItemDataRole.UserRole + 1)
    assert first_set is r_high


def test_rune_selected_signal(qapp):
    t = RuneTable()
    r = _r(rune_id=5)
    t.set_runes([r], equipped_index={})
    received = []
    t.rune_selected.connect(lambda ru: received.append(ru))
    t._table.selectRow(0)
    assert received and received[-1] is r
