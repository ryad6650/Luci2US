import pytest

from s2us_filter import S2USFilter
from ui.filtres.filter_editor import FilterEditor


def _mk() -> S2USFilter:
    return S2USFilter(
        name="Demo",
        enabled=True,
        sets={"Violent": True, "Swift": True},
        slots={}, grades={}, stars={}, main_stats={},
        ancient_type="",
        sub_requirements={}, min_values={},
        innate_required={},
    )


def test_editor_instantiates(qapp):
    e = FilterEditor()
    assert e is not None


def test_load_filter_sets_name_and_enabled(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    assert e._name_edit.text() == "Demo"
    assert e._enabled_check.isChecked() is True


def test_load_filter_unchecked_when_disabled(qapp):
    e = FilterEditor()
    f = _mk()
    f.enabled = False
    e.load_filter(f)
    assert e._enabled_check.isChecked() is False


def test_current_filter_roundtrip_header(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    e._name_edit.setText("Changed")
    e._enabled_check.setChecked(False)
    f = e.current_filter()
    assert f.name == "Changed"
    assert f.enabled is False


def test_sets_grid_has_all_23_sets(qapp):
    from PySide6.QtWidgets import QCheckBox
    e = FilterEditor()
    e.load_filter(_mk())
    checks = [c for c in e._sets_frame.findChildren(QCheckBox)]
    assert len(checks) == 23


def test_load_sets_populates_checkboxes(qapp):
    from PySide6.QtWidgets import QCheckBox
    e = FilterEditor()
    e.load_filter(_mk())
    checks = {c.text(): c for c in e._sets_frame.findChildren(QCheckBox)}
    assert checks["Violent"].isChecked() is True
    assert checks["Swift"].isChecked() is True
    assert checks["Fatal"].isChecked() is False


def test_current_filter_reads_sets(qapp):
    from PySide6.QtWidgets import QCheckBox
    e = FilterEditor()
    e.load_filter(_mk())
    checks = {c.text(): c for c in e._sets_frame.findChildren(QCheckBox)}
    checks["Fatal"].setChecked(True)
    f = e.current_filter()
    assert f.sets.get("Fatal") is True
    assert f.sets.get("Violent") is True


def test_level_slider_sync_with_filter(qapp):
    e = FilterEditor()
    f = _mk()
    f.level = 4
    e.load_filter(f)
    assert e._level_slider.value() == 4
    e._level_slider.setValue(2)
    assert e.current_filter().level == 2


def test_rarity_checkboxes_load_and_save(qapp):
    e = FilterEditor()
    f = _mk()
    f.grades = {"Rare": False, "Hero": True, "Legend": True}
    e.load_filter(f)
    assert e._rar_hero.isChecked() and e._rar_legend.isChecked()
    assert not e._rar_rare.isChecked()
    e._rar_rare.setChecked(True)
    g = e.current_filter()
    assert g.grades["Rare"] is True and g.grades["Hero"] is True


def test_slot_grid_2x3(qapp):
    e = FilterEditor()
    f = _mk()
    f.slots = {f"Slot{i}": (i in (2, 4, 6)) for i in range(1, 7)}
    e.load_filter(f)
    for i in range(1, 7):
        cb = e._slot_checks[i]
        assert cb.isChecked() == (i in (2, 4, 6))


def test_stars_checkboxes(qapp):
    e = FilterEditor()
    f = _mk()
    f.stars = {"FiveStars": True, "SixStars": True}
    e.load_filter(f)
    assert e._star5.isChecked() and e._star6.isChecked()
    e._star5.setChecked(False)
    assert e.current_filter().stars["FiveStars"] is False


def test_ancient_radio_tristate(qapp):
    e = FilterEditor()
    f = _mk()
    f.ancient_type = "Ancient"
    e.load_filter(f)
    assert e._ancient_group.checkedId() == 1
    f.ancient_type = "NotAncient"
    e.load_filter(f)
    assert e._ancient_group.checkedId() == 2
    f.ancient_type = ""
    e.load_filter(f)
    assert e._ancient_group.checkedId() == 0


def test_main_stats_grid(qapp):
    e = FilterEditor()
    f = _mk()
    f.main_stats = {"MainSPD": True, "MainATK": True}
    e.load_filter(f)
    assert e._main_checks["MainSPD"].isChecked()
    assert e._main_checks["MainATK"].isChecked()
    assert not e._main_checks["MainHP"].isChecked()


def test_innate_grid_roundtrip(qapp):
    e = FilterEditor()
    f = _mk()
    f.innate_required = {"SPD": True, "CR": True}
    e.load_filter(f)
    assert e._innate_checks["SPD"].isChecked()
    assert e._innate_checks["CR"].isChecked()
    e._innate_checks["CD"].setChecked(True)
    g = e.current_filter()
    assert g.innate_required.get("CD") is True
