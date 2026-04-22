from __future__ import annotations

import pytest

from models import Rune, SubStat
from swlens.rl_score import rl_score


def _make_rune(substats: list[tuple[str, float]], prefix=None, stars=6):
    return Rune(
        set="Violent", slot=4, stars=stars, grade="Legendaire", level=12,
        main_stat=SubStat("DC", 80),
        prefix=SubStat(prefix[0], prefix[1]) if prefix else None,
        substats=[SubStat(t, v) for t, v in substats],
    )


def test_rl_score_single_substat_one_roll():
    """VIT=6 sur 6★ → step=6 → raw=0 → 0 points."""
    rune = _make_rune([("VIT", 6)])
    result = rl_score(rune)
    assert result.total == 0
    assert result.category == "Faible"


def test_rl_score_single_substat_two_rolls():
    """VIT=12 sur 6★ → raw=1 → 100 points."""
    rune = _make_rune([("VIT", 12)])
    result = rl_score(rune)
    assert result.total == 100
    assert result.category == "Faible"


def test_rl_score_innate_bonus():
    """Innate CC=6 (max 6) → bonus = (6/6 * 100)/2 = 50."""
    rune = _make_rune([], prefix=("CC", 6))
    result = rl_score(rune)
    assert result.innate_bonus == 50.0


def test_rl_score_category_boundaries():
    """Teste les bornes 150/230/300."""
    from swlens.config import category_for
    assert category_for(149) == "Faible"
    assert category_for(150) == "Médiocre"
    assert category_for(229) == "Médiocre"
    assert category_for(230) == "Bon"
    assert category_for(299) == "Bon"
    assert category_for(300) == "Excellent"


def test_rl_score_breakdown_structure():
    rune = _make_rune([("VIT", 18), ("CC", 12)])
    result = rl_score(rune)
    assert len(result.substat_breakdown) == 2
    stats = [b[0] for b in result.substat_breakdown]
    assert "VIT" in stats and "CC" in stats


def test_rl_score_stars_5_uses_smaller_steps():
    """VIT=10 sur 5★ → step=5 → raw=1 → 100 points."""
    rune = _make_rune([("VIT", 10)], stars=5)
    result = rl_score(rune)
    assert result.total == 100
