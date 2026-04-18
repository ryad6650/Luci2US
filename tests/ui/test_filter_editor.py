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


def test_sub_rows_created_for_every_stat_key(qapp):
    from s2us_filter import _STAT_KEYS
    e = FilterEditor()
    e.load_filter(_mk())
    for key in _STAT_KEYS:
        assert key in e._sub_rows


def test_sub_state_button_cycles_ignored_mandatory_optional(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    row = e._sub_rows["SPD"]
    assert row.state == 0
    row.state_btn.click()
    assert row.state == 1
    row.state_btn.click()
    assert row.state == 2
    row.state_btn.click()
    assert row.state == 0


def test_load_filter_populates_sub_state_and_threshold(qapp):
    e = FilterEditor()
    f = _mk()
    f.sub_requirements = {"SPD": 1, "CR": 2}
    f.min_values = {"SPD": 12, "CR": 6}
    e.load_filter(f)
    assert e._sub_rows["SPD"].state == 1
    assert e._sub_rows["CR"].state == 2
    assert e._sub_rows["SPD"].threshold.value() == 12
    assert e._sub_rows["CR"].threshold.value() == 6


def test_threshold_slider_and_spin_synchronized(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    row = e._sub_rows["SPD"]
    row.slider.setValue(20)
    assert row.threshold.value() == 20
    row.threshold.setValue(15)
    assert row.slider.value() == 15


def test_current_filter_writes_sub_reqs_and_min_values(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    e._sub_rows["SPD"].set_state(1)
    e._sub_rows["SPD"].threshold.setValue(12)
    e._sub_rows["CR"].set_state(2)
    e._sub_rows["CR"].threshold.setValue(6)
    f = e.current_filter()
    assert f.sub_requirements["SPD"] == 1
    assert f.sub_requirements["CR"] == 2
    assert f.min_values["SPD"] == 12
    assert f.min_values["CR"] == 6


def test_optional_count_radio_group(qapp):
    e = FilterEditor()
    f = _mk()
    f.optional_count = 3
    e.load_filter(f)
    assert e._optional_group.checkedId() == 3
    e._optional_group.button(2).setChecked(True)
    assert e.current_filter().optional_count == 2


def test_efficiency_slider_and_method_roundtrip(qapp):
    e = FilterEditor()
    f = _mk()
    f.efficiency = 85.0
    f.eff_method = "SWOP"
    e.load_filter(f)
    assert e._eff_slider.value() == 85
    assert e._eff_method.currentText() in ("SWOP", "S2US")
    e._eff_slider.setValue(70)
    e._eff_method.setCurrentText("S2US")
    g = e.current_filter()
    assert g.efficiency == 70.0
    assert g.eff_method == "S2US"


def test_grind_gem_dropdowns_roundtrip(qapp):
    e = FilterEditor()
    f = _mk()
    f.grind = 2
    f.gem = 3
    e.load_filter(f)
    assert e._grind_combo.currentIndex() == 2
    assert e._gem_combo.currentIndex() == 3
    e._grind_combo.setCurrentIndex(1)
    assert e.current_filter().grind == 1


def test_save_button_emits_filter_saved(qapp):
    from PySide6.QtWidgets import QPushButton
    e = FilterEditor()
    e.load_filter(_mk())
    received: list = []
    e.filter_saved.connect(received.append)
    save_btn = next(b for b in e.findChildren(QPushButton) if "SAVE" in b.text().upper())
    e._name_edit.setText("After Save")
    save_btn.click()
    assert len(received) == 1
    assert received[0].name == "After Save"
