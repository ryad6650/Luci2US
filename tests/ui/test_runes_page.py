from models import Monster, Rune, SubStat
from ui.runes.runes_page import RunesPage


def _r(rune_id: int, slot: int = 2, stars: int = 6, grade: str = "Heroique",
       set_name: str = "Violent", level: int = 12, eff: float | None = 90.0) -> Rune:
    return Rune(
        set=set_name, slot=slot, stars=stars, grade=grade, level=level,
        main_stat=SubStat(type="VIT", value=39, grind_value=0),
        prefix=None,
        substats=[
            SubStat(type="CC", value=9, grind_value=0),
            SubStat(type="VIT", value=6, grind_value=2),
        ],
        swex_efficiency=eff, swex_max_efficiency=100.0,
        rune_id=rune_id,
    )


def test_page_instantiates(qapp):
    p = RunesPage()
    assert p is not None


def test_apply_profile_populates_table(qapp):
    p = RunesPage()
    runes = [_r(1), _r(2, slot=3)]
    p.apply_profile({"runes": runes, "monsters": []}, saved_at=0.0)
    assert p._table._model.rowCount() == 2


def test_apply_profile_builds_equipped_index(qapp):
    p = RunesPage()
    r = _r(42)
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, equipped_runes=[r])
    p.apply_profile({"runes": [r], "monsters": [mon]}, saved_at=0.0)
    assert p._equipped_index.get(42) == "Lushen"


def test_apply_profile_resets_filter_defaults(qapp):
    p = RunesPage()
    p._filter_bar._level_slider.setValue(12)
    p.apply_profile({"runes": [], "monsters": []}, saved_at=0.0)
    assert p._filter_bar.filter_level_min() == 0


def test_selection_updates_detail_panel(qapp):
    p = RunesPage()
    r = _r(42)
    p.apply_profile({"runes": [r], "monsters": []}, saved_at=0.0)
    p._on_rune_selected(r)
    assert p._detail._current is r


def test_filter_by_slot(qapp):
    p = RunesPage()
    p.apply_profile({
        "runes": [_r(1, slot=2), _r(2, slot=3)],
        "monsters": [],
    }, saved_at=0.0)
    p._filter_bar._slot_btns[2].click()
    assert p._table._model.rowCount() == 1


def test_filter_by_rarity(qapp):
    p = RunesPage()
    p.apply_profile({
        "runes": [_r(1, grade="Heroique"), _r(2, grade="Legendaire")],
        "monsters": [],
    }, saved_at=0.0)
    p._filter_bar._rarity_btns["Legendaire"].click()
    assert p._table._model.rowCount() == 1


def test_level_slider_filters_low_levels(qapp):
    p = RunesPage()
    low = _r(1, level=3)
    high = _r(2, level=15)
    p.apply_profile({"runes": [low, high], "monsters": []}, saved_at=0.0)
    p._filter_bar._level_slider.setValue(12)
    assert p._table._model.rowCount() == 1


def test_equipped_filter_keeps_only_equipped(qapp):
    p = RunesPage()
    eq = _r(1)
    free = _r(2)
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, equipped_runes=[eq])
    p.apply_profile({"runes": [eq, free], "monsters": [mon]}, saved_at=0.0)
    p._filter_bar._equipped_btns["equipped"].click()
    assert p._table._model.rowCount() == 1


def test_new_profile_clears_detail(qapp):
    p = RunesPage()
    r = _r(1)
    p.apply_profile({"runes": [r], "monsters": []}, saved_at=0.0)
    p._on_rune_selected(r)
    p.apply_profile({"runes": [], "monsters": []}, saved_at=0.0)
    assert p._detail._current is None
