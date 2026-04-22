from __future__ import annotations

from models import Rune, SubStat
from swlens.collection_state import CollectionState
from swlens.gap_analysis import gap_analysis, gap_for_rune


def _rune(subs, main="DC"):
    return Rune(
        set="Violent", slot=4, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(main, 80), prefix=None,
        substats=[SubStat(t, v) for t, v in subs],
    )


def test_empty_collection_zero_gap():
    col = CollectionState.from_runes([])
    report = gap_analysis(col)
    for cat in ("VIT", "CC", "DC", "PRE", "PV%", "ATQ%", "DEF%"):
        assert report.per_category[cat].fast_count == 0


def test_hp_multiplier_higher_than_def():
    """À quantité de runes égales, HP% devrait scorer plus que DEF% (×1.3 vs ×1.0)."""
    runes_hp = [_rune([("PV%", 8)]) for _ in range(3)]
    runes_def = [_rune([("DEF%", 8)]) for _ in range(3)]
    col = CollectionState.from_runes(runes_hp + runes_def)
    report = gap_analysis(col)
    assert report.per_category["PV%"].multiplier == 1.3
    assert report.per_category["ATQ%"].multiplier == 1.2
    assert report.per_category["DEF%"].multiplier == 1.0


def test_gap_for_rune_uses_main_stat_category():
    col = CollectionState.from_runes([])
    rune_cd = _rune([("CC", 10)], main="DC")
    score = gap_for_rune(rune_cd, col)
    assert score >= 0


def test_fast_count_and_elite_count_present():
    fast_rune = _rune([("VIT", 25)])
    col = CollectionState.from_runes([fast_rune])
    report = gap_analysis(col)
    assert report.per_category["VIT"].fast_count == 1
