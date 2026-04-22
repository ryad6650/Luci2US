"""Analyse de déficit de la collection sur 7 catégories SWLens."""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from swlens.collection_state import CollectionState
from swlens.config import (
    ELITE_SCORE_THRESHOLD,
    GAP_CATEGORIES,
    GAP_MULTIPLIERS,
)


@dataclass
class CategoryGap:
    category: str
    fast_count: int
    elite_count: int
    speed_mean: float
    slot_coverage: int
    multiplier: float
    score: int


@dataclass
class GapReport:
    per_category: dict[str, CategoryGap]


def _speed_mean(runes: list[Rune]) -> float:
    values: list[float] = []
    for r in runes:
        for sub in r.substats:
            if sub.type == "VIT":
                values.append(sub.value)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _slot_coverage(runes: list[Rune]) -> int:
    return len({r.slot for r in runes})


def _elite_count(runes: list[Rune]) -> int:
    from swlens.rl_score import rl_score
    return sum(1 for r in runes if rl_score(r).total >= ELITE_SCORE_THRESHOLD)


def _category_score(
    fast: int, elite: int, mean: float, coverage: int, total: int, multiplier: float,
) -> int:
    """Score 0-600+ : plus la catégorie est déficitaire, plus le score monte."""
    if total == 0:
        base = 600
    else:
        fast_fill = min(150, fast * 30)
        elite_fill = min(150, elite * 50)
        mean_fill = min(150, mean * 6)
        coverage_fill = min(150, coverage * 25)
        total_fill = fast_fill + elite_fill + mean_fill + coverage_fill
        base = max(0, 600 - total_fill)
    return int(round(base * multiplier))


def gap_analysis(collection: CollectionState) -> GapReport:
    per_category: dict[str, CategoryGap] = {}
    for cat in GAP_CATEGORIES:
        runes = collection.runes_in_category(cat)
        fast = collection.fast_count(cat)
        elite = _elite_count(runes)
        mean = _speed_mean(runes)
        coverage = _slot_coverage(runes)
        multiplier = GAP_MULTIPLIERS.get(cat, 1.0)
        score = _category_score(fast, elite, mean, coverage, len(runes), multiplier)
        per_category[cat] = CategoryGap(
            category=cat, fast_count=fast, elite_count=elite,
            speed_mean=mean, slot_coverage=coverage,
            multiplier=multiplier, score=score,
        )
    return GapReport(per_category=per_category)


def gap_for_rune(rune: Rune, collection: CollectionState) -> int:
    """Gap score pour la catégorie principale de la rune (main stat si mappée,
    sinon première substat mappée)."""
    candidates = [rune.main_stat.type] + [s.type for s in rune.substats]
    for cat in candidates:
        if cat in GAP_CATEGORIES:
            report = gap_analysis(collection)
            return report.per_category[cat].score
    return 0
