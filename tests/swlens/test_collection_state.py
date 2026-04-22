from __future__ import annotations

from models import Rune, SubStat
from swlens.collection_state import CollectionState


def _rune(subs, slot=4, spd_main=False):
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("VIT" if spd_main else "DC", 80),
        prefix=None,
        substats=[SubStat(t, v) for t, v in subs],
    )


def test_empty_collection():
    col = CollectionState.from_runes([])
    assert col.total_count == 0
    assert col.runes_in_category("CC") == []


def test_indexes_runes_by_substat_category():
    r1 = _rune([("CC", 10)])
    r2 = _rune([("DC", 15), ("CC", 8)])
    col = CollectionState.from_runes([r1, r2])
    cc_runes = col.runes_in_category("CC")
    assert len(cc_runes) == 2


def test_indexes_runes_by_main_stat_category():
    r_spd_main = _rune([], spd_main=True)
    col = CollectionState.from_runes([r_spd_main])
    vit_runes = col.runes_in_category("VIT")
    assert len(vit_runes) == 1


def test_fast_count():
    r_fast = _rune([("VIT", 22)])
    r_slow = _rune([("VIT", 10)])
    col = CollectionState.from_runes([r_fast, r_slow])
    assert col.fast_count("VIT") == 1


def test_invalidation():
    r = _rune([("CC", 10)])
    col = CollectionState.from_runes([r])
    assert col.total_count == 1
    col.invalidate()
    assert col.total_count == 0
