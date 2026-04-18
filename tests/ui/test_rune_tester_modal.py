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
    dlg._grind_combo.setCurrentIndex(4)
    dlg._gem_combo.setCurrentIndex(4)
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


def test_optimize_calls_best_tied_variants(qapp, monkeypatch):
    """Le bouton passe par best_tied_variants (pas best_plus0/best_now)."""
    calls = {"tied": 0}
    from ui.filtres import rune_tester_modal

    def fake_tied(r, grind_grade=0, gem_grade=0):
        calls["tied"] += 1
        return [r]

    monkeypatch.setattr(rune_tester_modal, "best_tied_variants", fake_tied)

    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    dlg._btn_optimize.click()
    assert calls["tied"] == 1


def test_score_eff_stable_across_clicks(qapp):
    """Clics multiples sur la même rune : Score / Eff affichés ne bougent pas."""
    dlg = RuneTesterModal(filters=[])
    r = _rune()
    r.level = 0
    dlg.set_rune(r)

    dlg._btn_optimize.click()
    first_proj = dlg._eff_projected.text()
    for _ in range(5):
        dlg._btn_optimize.click()
        assert dlg._eff_projected.text() == first_proj


def test_cache_reused_when_source_unchanged(qapp, monkeypatch):
    """Source identique : best_tied_variants n'est pas rappelée."""
    calls = {"tied": 0}
    from ui.filtres import rune_tester_modal
    real = rune_tester_modal.best_tied_variants

    def counting_tied(r, grind_grade=0, gem_grade=0):
        calls["tied"] += 1
        return real(r, grind_grade=grind_grade, gem_grade=gem_grade)

    monkeypatch.setattr(rune_tester_modal, "best_tied_variants", counting_tied)

    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    dlg._btn_optimize.click()
    dlg._btn_optimize.click()
    dlg._btn_optimize.click()
    assert calls["tied"] == 1


def test_breakdown_same_stat_gem_not_counted_as_rolls(qapp):
    """Gem qui remplace une sub par le même type → affiché comme Gemme,
    pas comme Rolls fantômes (ATQ% 5 → gem legend = 13 + grind 10 = 23)."""
    dlg = RuneTesterModal(filters=[])
    orig = Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=0,
        main_stat=SubStat(type="VIT", value=0), prefix=None,
        substats=[SubStat(type="ATQ%", value=5)],
    )
    opt = Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(type="VIT", value=0), prefix=None,
        substats=[SubStat(type="ATQ%", value=23)],
    )
    # grind=4 (Legend), gem=4 (Legend). ATQ% gem legend = 13, grind legend = +10.
    lines = dlg._sub_breakdown(orig, opt, grind=4, gem=4)
    atq_line = lines[0]
    assert "Gemme" in atq_line
    assert "Rolls" not in atq_line


def test_cache_invalidated_when_grade_changes(qapp, monkeypatch):
    """Changement de grind/gem : cache invalidé, best_tied_variants rappelée."""
    calls = {"tied": 0}
    from ui.filtres import rune_tester_modal
    real = rune_tester_modal.best_tied_variants

    def counting_tied(r, grind_grade=0, gem_grade=0):
        calls["tied"] += 1
        return real(r, grind_grade=grind_grade, gem_grade=gem_grade)

    monkeypatch.setattr(rune_tester_modal, "best_tied_variants", counting_tied)

    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    dlg._grind_combo.setCurrentIndex(0)
    dlg._gem_combo.setCurrentIndex(0)
    dlg._btn_optimize.click()
    dlg._grind_combo.setCurrentIndex(4)
    dlg._btn_optimize.click()
    assert calls["tied"] == 2
