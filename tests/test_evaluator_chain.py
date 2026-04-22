from __future__ import annotations

from evaluator_chain import evaluate_chain
from models import Rune, SubStat


def _high_score_rune():
    return Rune(
        set="Violent", slot=4, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("DC", 80),
        prefix=SubStat("CC", 6),
        substats=[
            SubStat("VIT", 30), SubStat("CC", 15),
            SubStat("ATQ%", 15), SubStat("RES", 10),
        ],
    )


def _low_score_rune():
    return Rune(
        set="Energy", slot=1, stars=6, grade="Rare", level=3,
        main_stat=SubStat("ATQ", 100), prefix=None,
        substats=[SubStat("RES", 4)],
    )


def test_keep_when_score_above_threshold():
    cfg = {"swlens": {"keep_threshold": 230}}
    v = evaluate_chain(_high_score_rune(), cfg)
    assert v.decision == "KEEP"
    assert v.source == "swlens"
    assert "rl_score" in v.details
    assert v.details["category"] in {"Bon", "Excellent"}


def test_sell_when_score_below_threshold():
    cfg = {"swlens": {"keep_threshold": 230}}
    v = evaluate_chain(_low_score_rune(), cfg)
    assert v.decision == "SELL"


def test_default_threshold_when_missing():
    v = evaluate_chain(_high_score_rune(), {})
    assert v.source == "swlens"
