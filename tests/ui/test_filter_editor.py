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
