"""RL Score SWLens : Substat Score + Innate Bonus."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models import Rune
from swlens.config import category_for, step_for


@dataclass
class RLScoreResult:
    total: int
    category: str  # "Excellent" | "Bon" | "Médiocre" | "Faible"
    substat_breakdown: list[tuple[str, float, float]]  # (stat, raw, contribution)
    innate_bonus: float


def _substat_contribution(stat_fr: str, value: float, stars: int) -> tuple[float, float]:
    """Retourne (raw, contribution)."""
    step = step_for(stat_fr, stars)
    if step <= 0:
        return 0.0, 0.0
    raw = (value / step) - 1
    if raw <= 0:
        return raw, 0.0
    return raw, raw * 100


def _innate_bonus(stat_fr: str, value: float, stars: int) -> float:
    """Bonus = (value / max_roll * 100) / 2 — ici max_roll = step_for(stat, stars)."""
    step = step_for(stat_fr, stars)
    if step <= 0:
        return 0.0
    return (value / step * 100) / 2


def rl_score(rune: Rune) -> RLScoreResult:
    breakdown: list[tuple[str, float, float]] = []
    total = 0.0
    for sub in rune.substats:
        raw, contrib = _substat_contribution(sub.type, sub.value, rune.stars)
        breakdown.append((sub.type, raw, contrib))
        total += contrib

    innate_bonus = 0.0
    if rune.prefix:
        innate_bonus = _innate_bonus(rune.prefix.type, rune.prefix.value, rune.stars)
        total += innate_bonus

    total_int = int(round(total))
    return RLScoreResult(
        total=total_int,
        category=category_for(total_int),
        substat_breakdown=breakdown,
        innate_bonus=innate_bonus,
    )
