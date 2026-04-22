from __future__ import annotations

from models import Rune, SubStat
from swlens.collection_state import CollectionState
from swlens.priority_score import priority_score


def _rune(slot=4, prefix=None, subs=None):
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("DC", 80),
        prefix=SubStat(prefix[0], prefix[1]) if prefix else None,
        substats=[SubStat(t, v) for t, v in (subs or [])],
    )


def test_slot_bonus_values():
    col = CollectionState.from_runes([])
    assert priority_score(_rune(slot=1), col).slot_pts == 50
    assert priority_score(_rune(slot=2), col).slot_pts == 75
    assert priority_score(_rune(slot=3), col).slot_pts == 50
    assert priority_score(_rune(slot=4), col).slot_pts == 100
    assert priority_score(_rune(slot=5), col).slot_pts == 50
    assert priority_score(_rune(slot=6), col).slot_pts == 100


def test_innate_importance_acc_vs_hp():
    """ACC pondération 2.0, HP% 1.0 → ACC innate = 2× HP% innate à valeur égale."""
    col = CollectionState.from_runes([])
    acc = priority_score(_rune(prefix=("PRE", 8)), col)
    hp = priority_score(_rune(prefix=("PV%", 8)), col)
    assert acc.innate_pts == 2 * hp.innate_pts


def test_no_innate_zero_pts():
    col = CollectionState.from_runes([])
    result = priority_score(_rune(prefix=None), col)
    assert result.innate_pts == 0.0


def test_empty_collection_gap_zero_safe():
    """Collection vide : gap calculé mais pas d'erreur."""
    col = CollectionState.from_runes([])
    result = priority_score(_rune(), col)
    assert result.gap_pts >= 0


def test_total_is_sum_of_parts():
    col = CollectionState.from_runes([])
    r = priority_score(_rune(slot=4, prefix=("CC", 6)), col)
    assert r.total == int(round(r.innate_pts + r.slot_pts + r.gap_pts))
