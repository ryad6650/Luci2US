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


def test_apply_profile_populates_grid(qapp):
    p = RunesPage()
    runes = [_r(1), _r(2, slot=3)]
    p.apply_profile({"runes": runes, "monsters": []}, saved_at=0.0)
    assert len(p._grid._runes) == 2


def test_apply_profile_builds_equipped_index(qapp):
    p = RunesPage()
    r = _r(42)
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, equipped_runes=[r])
    p.apply_profile({"runes": [r], "monsters": [mon]}, saved_at=0.0)
    assert p._equipped_index.get(42) == "Lushen"


def test_apply_profile_resets_filters(qapp):
    p = RunesPage()
    p._filter_bar._rarity_combo.setCurrentIndex(
        p._filter_bar._rarity_combo.findData("Legendaire"),
    )
    p.apply_profile({"runes": [], "monsters": []}, saved_at=0.0)
    assert p._filter_bar.filter_rarity() is None


def test_filter_by_slot(qapp):
    p = RunesPage()
    p.apply_profile({
        "runes": [_r(1, slot=2), _r(2, slot=3)],
        "monsters": [],
    }, saved_at=0.0)
    p._filter_bar._slot_btns[2].click()
    assert len(p._grid._runes) == 1


def test_filter_by_rarity(qapp):
    p = RunesPage()
    p.apply_profile({
        "runes": [_r(1, grade="Heroique"), _r(2, grade="Legendaire")],
        "monsters": [],
    }, saved_at=0.0)
    idx = p._filter_bar._rarity_combo.findData("Legendaire")
    p._filter_bar._rarity_combo.setCurrentIndex(idx)
    assert len(p._grid._runes) == 1


def test_level_combo_filters_low_levels(qapp):
    p = RunesPage()
    low = _r(1, level=3)
    high = _r(2, level=15)
    p.apply_profile({"runes": [low, high], "monsters": []}, saved_at=0.0)
    idx = p._filter_bar._level_combo.findData(12)
    p._filter_bar._level_combo.setCurrentIndex(idx)
    assert len(p._grid._runes) == 1


def test_search_filters_by_set(qapp):
    p = RunesPage()
    p.apply_profile({
        "runes": [_r(1, set_name="Violent"), _r(2, set_name="Rapide")],
        "monsters": [],
    }, saved_at=0.0)
    p._filter_bar._search.setText("Viole")
    assert len(p._grid._runes) == 1
    assert p._grid._runes[0].set == "Violent"


def test_sort_by_level_desc(qapp):
    p = RunesPage()
    r_low = _r(1, level=6, eff=80.0)
    r_high = _r(2, level=15, eff=50.0)
    p.apply_profile({"runes": [r_low, r_high], "monsters": []}, saved_at=0.0)
    p._filter_bar._rb_level.setChecked(True)
    assert p._grid._runes[0].level == 15


def test_sort_by_score_desc(qapp):
    p = RunesPage()
    r_low = _r(1, eff=40.0)
    r_high = _r(2, eff=95.0)
    p.apply_profile({"runes": [r_low, r_high], "monsters": []}, saved_at=0.0)
    # Score est le défaut
    assert p._grid._runes[0].rune_id == 2


def test_toggle_lock_updates_locked_ids(qapp):
    p = RunesPage()
    r = _r(7)
    p.apply_profile({"runes": [r], "monsters": []}, saved_at=0.0)
    p._toggle_lock(r)
    assert 7 in p.locked_ids
    p._toggle_lock(r)
    assert 7 not in p.locked_ids


