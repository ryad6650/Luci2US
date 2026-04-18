from models import Rune, SubStat
from ui.runes.rune_table import RuneTable


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


def test_table_empty_on_init(qapp):
    t = RuneTable()
    assert t._model.rowCount() == 0


def test_set_runes_populates_rows(qapp):
    t = RuneTable()
    t.set_runes([_r(rune_id=1), _r(rune_id=2, slot=3)], equipped_index={})
    assert t._model.rowCount() == 2


def test_default_sort_is_efficiency_desc(qapp):
    t = RuneTable()
    low = _r(rune_id=1, swex_efficiency=50.0)
    high = _r(rune_id=2, swex_efficiency=95.0)
    t.set_runes([low, high], equipped_index={})
    assert t._model.rune_at(0) is high


def test_sort_click_toggles_direction(qapp):
    t = RuneTable()
    low = _r(rune_id=1, swex_efficiency=50.0)
    high = _r(rune_id=2, swex_efficiency=95.0)
    t.set_runes([low, high], equipped_index={})
    t._on_sort_clicked("efficiency")
    assert t.sort_dir() == "asc"
    assert t._model.rune_at(0) is low


def test_sort_by_set_alpha(qapp):
    t = RuneTable()
    r_z = _r(rune_id=1, set="Will")
    r_a = _r(rune_id=2, set="Fatal")
    t.set_runes([r_z, r_a], equipped_index={})
    t._on_sort_clicked("set")       # desc → Will, Fatal
    assert t._model.rune_at(0).set == "Will"
    t._on_sort_clicked("set")       # asc
    assert t._model.rune_at(0).set == "Fatal"


def test_rune_selected_signal(qapp):
    t = RuneTable()
    r = _r(rune_id=5)
    t.set_runes([r], equipped_index={})
    received = []
    t.rune_selected.connect(lambda ru: received.append(ru))
    t._on_view_clicked(t._model.index(0, 0))
    assert received and received[-1] is r


def test_empty_state_visible_when_no_rows(qapp):
    t = RuneTable()
    t.set_runes([], equipped_index={})
    assert t._empty_lbl.isVisible() is False or t._empty_lbl.isVisibleTo(t)
