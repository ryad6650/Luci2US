"""Tests purs pour rune_optimizer.best_variant et filters_that_match."""
from __future__ import annotations

from models import Rune, SubStat
from s2us_filter import S2USFilter
from rune_optimizer import (
    OptimizerResult,
    best_variant,
    best_plus0,
    best_now,
    filters_that_match,
)


def _rune_plus0_legend() -> Rune:
    return Rune(
        set="Violent",
        slot=2,
        stars=6,
        grade="Legendaire",
        level=0,
        main_stat=SubStat(type="ATQ%", value=63),
        prefix=None,
        substats=[
            SubStat(type="VIT", value=5),
            SubStat(type="CC", value=4),
            SubStat(type="DC", value=5),
            SubStat(type="PV%", value=4),
        ],
        ancient=False,
    )


def _rune_plus12_legend() -> Rune:
    return Rune(
        set="Violent",
        slot=2,
        stars=6,
        grade="Legendaire",
        level=12,
        main_stat=SubStat(type="ATQ%", value=63),
        prefix=None,
        substats=[
            SubStat(type="VIT", value=18),
            SubStat(type="CC", value=10),
            SubStat(type="DC", value=14),
            SubStat(type="PV%", value=5),
        ],
        ancient=False,
    )


def test_best_variant_returns_optimizer_result():
    r = _rune_plus12_legend()
    res = best_variant(r, grind_grade=0, gem_grade=0)
    assert isinstance(res, OptimizerResult)
    assert res.efficiency >= 0
    assert res.rune is not None


def test_best_variant_at_plus12_zero_materials_returns_same_rune_eff():
    from s2us_filter import calculate_efficiency1
    r = _rune_plus12_legend()
    res = best_variant(r, grind_grade=0, gem_grade=0)
    assert res.efficiency == calculate_efficiency1(r)


def test_best_variant_higher_with_grind_than_without():
    r = _rune_plus12_legend()
    low = best_variant(r, grind_grade=0, gem_grade=0)
    high = best_variant(r, grind_grade=3, gem_grade=0)
    assert high.efficiency >= low.efficiency


def test_best_variant_higher_with_gem_than_without():
    r = _rune_plus12_legend()
    low = best_variant(r, grind_grade=0, gem_grade=0)
    high = best_variant(r, grind_grade=0, gem_grade=3)
    assert high.efficiency >= low.efficiency


def test_best_variant_returns_grind_applied_on_substats():
    r = _rune_plus12_legend()
    res = best_variant(r, grind_grade=3, gem_grade=0)
    in_values = {s.type: s.value for s in r.substats}
    out_values = {s.type: s.value for s in res.rune.substats}
    grind_applied = any(
        out_values.get(k, 0) > in_values.get(k, 0) for k in in_values
    )
    assert grind_applied


def test_best_plus0_uses_filter_authorized_grades():
    r = _rune_plus0_legend()
    res = best_plus0(r, max_grind_grade=3, max_gem_grade=3)
    assert isinstance(res, OptimizerResult)
    assert res.efficiency > 0


def test_best_now_projects_current_level():
    r = _rune_plus12_legend()
    a = best_now(r, grind_grade=2, gem_grade=2)
    b = best_variant(r, grind_grade=2, gem_grade=2)
    assert a.efficiency == b.efficiency


def test_filters_that_match_returns_list_ordered_by_efficiency_desc():
    r = _rune_plus12_legend()
    f_low = S2USFilter(name="low", efficiency=30.0,
                       sub_requirements={}, min_values={})
    f_high = S2USFilter(name="high", efficiency=85.0,
                        sub_requirements={}, min_values={})
    f_disabled = S2USFilter(name="off", enabled=False,
                            sub_requirements={}, min_values={})
    matches = filters_that_match(r, [f_disabled, f_low, f_high])
    names = [f.name for f in matches]
    assert "off" not in names
    assert names.index("high") < names.index("low")


def test_filters_that_match_handles_empty_filters():
    r = _rune_plus12_legend()
    assert filters_that_match(r, []) == []
