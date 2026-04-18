from models import Monster, Rune, SubStat
from ui.runes.runes_page import RunesPage


def _r(rune_id: int, slot: int = 2, stars: int = 6, grade: str = "Heroique",
       set_name: str = "Violent", substats=None, eff: float | None = 90.0) -> Rune:
    return Rune(
        set=set_name, slot=slot, stars=stars, grade=grade, level=12,
        main_stat=SubStat(type="VIT", value=39, grind_value=0),
        prefix=None,
        substats=substats if substats is not None else [
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
    assert p._table._table.rowCount() == 2


def test_apply_profile_builds_equipped_index(qapp):
    p = RunesPage()
    r = _r(42)
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, equipped_runes=[r])
    # Inventory includes the equipped rune (profile_loader merges both)
    p.apply_profile({"runes": [r], "monsters": [mon]}, saved_at=0.0)
    assert p._equipped_index.get(42) == "Lushen"


def test_apply_profile_resets_filter_defaults(qapp):
    p = RunesPage()
    p._filter_bar._score_slider.setValue(80)
    p.apply_profile({"runes": [], "monsters": []}, saved_at=0.0)
    assert p._filter_bar.score_threshold() == 0


def test_selection_updates_detail_panel(qapp):
    p = RunesPage()
    r = _r(42)
    p.apply_profile({"runes": [r], "monsters": []}, saved_at=0.0)
    p._on_rune_selected(r)
    assert p._detail._current is r


def test_filter_by_set(qapp):
    p = RunesPage()
    p.apply_profile({
        "runes": [_r(1, set_name="Violent"), _r(2, set_name="Rapide")],
        "monsters": [],
    }, saved_at=0.0)
    p._filter_bar._set.set_selected(["Violent"])
    assert p._table._table.rowCount() == 1


def test_focus_filter_removes_runes_without_stat(qapp):
    p = RunesPage()
    r_with = _r(1, substats=[SubStat(type="VIT", value=10)])
    r_without = _r(2, substats=[SubStat(type="CC", value=5)])
    p.apply_profile({"runes": [r_with, r_without], "monsters": []}, saved_at=0.0)
    p._filter_bar._focus.setCurrentText("VIT")
    assert p._table._table.rowCount() == 1


def test_score_threshold_filters(qapp):
    p = RunesPage()
    low = _r(1, eff=50.0)
    high = _r(2, eff=95.0)
    p.apply_profile({"runes": [low, high], "monsters": []}, saved_at=0.0)
    p._filter_bar._score_slider.setValue(80)
    assert p._table._table.rowCount() == 1


def test_new_profile_clears_detail(qapp):
    p = RunesPage()
    r = _r(1)
    p.apply_profile({"runes": [r], "monsters": []}, saved_at=0.0)
    p._on_rune_selected(r)
    p.apply_profile({"runes": [], "monsters": []}, saved_at=0.0)
    assert p._detail._current is None
