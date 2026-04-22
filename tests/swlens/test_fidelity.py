"""Golden tests contre runelens.swlens.io.

Protocole : aller sur https://runelens.swlens.io/analyzer, taper les runes
ci-dessous, noter le RL Score affiché, compléter les asserts.

Si divergence >= 5 points : ajuster swlens/config.STAT_STEPS_6 avant d'aller
plus loin.
"""
from __future__ import annotations

import pytest

from models import Rune, SubStat
from swlens.rl_score import rl_score


@pytest.mark.parametrize("name,rune_factory,expected_score", [
    (
        "violent_cd_speedy",
        lambda: Rune(
            set="Violent", slot=4, stars=6, grade="Legendaire", level=12,
            main_stat=SubStat("DC", 80),
            prefix=SubStat("CC", 6),
            substats=[
                SubStat("VIT", 24), SubStat("CC", 10),
                SubStat("ATQ%", 15), SubStat("RES", 8),
            ],
        ),
        None,
    ),
])
def test_golden_rl_score_matches_swlens(name, rune_factory, expected_score):
    if expected_score is None:
        pytest.skip(f"Golden value for {name} not yet captured from swlens.io")
    result = rl_score(rune_factory())
    delta = abs(result.total - expected_score)
    assert delta <= 5, f"{name}: got {result.total}, expected {expected_score} (delta={delta})"
