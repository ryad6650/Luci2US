import pytest

from models import Rune, SubStat
from s2us_filter import S2USFilter
from ui.filtres.rune_tester_modal import RuneTesterModal


def _rune() -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(type="ATQ%", value=63), prefix=None,
        substats=[
            SubStat(type="VIT", value=18),
            SubStat(type="CC", value=10),
            SubStat(type="DC", value=14),
            SubStat(type="PV%", value=5),
        ],
    )


def test_modal_instantiates(qapp):
    dlg = RuneTesterModal(filters=[])
    assert dlg is not None
    assert dlg.windowTitle() == "Rune Optimizer"


def test_modal_accepts_rune_via_api(qapp):
    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    assert dlg._slot_spin.value() == 2
    assert dlg._stars_spin.value() == 6
    assert dlg._level_spin.value() == 12


def test_optimize_button_populates_result_label(qapp):
    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    dlg._grind_combo.setCurrentIndex(3)
    dlg._gem_combo.setCurrentIndex(3)
    dlg._btn_optimize.click()
    text = dlg._result_label.text()
    assert "Eff" in text or "eff" in text


def test_optimize_populates_matching_filters_list(qapp):
    f_match = S2USFilter(name="MatchMe", efficiency=10.0,
                         sub_requirements={}, min_values={})
    f_no_match = S2USFilter(
        name="TooHigh", efficiency=999.0,
        sub_requirements={}, min_values={},
    )
    dlg = RuneTesterModal(filters=[f_match, f_no_match])
    dlg.set_rune(_rune())
    dlg._btn_optimize.click()
    items = [dlg._filters_list.item(i).text()
             for i in range(dlg._filters_list.count())]
    joined = " ".join(items)
    assert "MatchMe" in joined
    assert "TooHigh" not in joined


def test_plus0_uses_best_plus0(qapp, monkeypatch):
    calls = {"plus0": 0, "now": 0}

    from rune_optimizer import OptimizerResult
    from ui.filtres import rune_tester_modal

    def fake_plus0(r, max_grind_grade=3, max_gem_grade=3):
        calls["plus0"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    def fake_now(r, grind_grade=0, gem_grade=0):
        calls["now"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    monkeypatch.setattr(rune_tester_modal, "best_plus0", fake_plus0)
    monkeypatch.setattr(rune_tester_modal, "best_now", fake_now)

    dlg = RuneTesterModal(filters=[])
    r = _rune()
    r.level = 0
    dlg.set_rune(r)
    dlg._btn_optimize.click()
    assert calls["plus0"] == 1
    assert calls["now"] == 0


def test_plus12_uses_best_now(qapp, monkeypatch):
    calls = {"plus0": 0, "now": 0}

    from rune_optimizer import OptimizerResult
    from ui.filtres import rune_tester_modal

    def fake_plus0(r, max_grind_grade=3, max_gem_grade=3):
        calls["plus0"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    def fake_now(r, grind_grade=0, gem_grade=0):
        calls["now"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    monkeypatch.setattr(rune_tester_modal, "best_plus0", fake_plus0)
    monkeypatch.setattr(rune_tester_modal, "best_now", fake_now)

    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    dlg._btn_optimize.click()
    assert calls["plus0"] == 0
    assert calls["now"] == 1
