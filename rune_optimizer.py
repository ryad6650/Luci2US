"""Choisit la meilleure configuration meule+gemme pour une rune.

Module pur (pas de Qt). Réutilise :
  - powerup_simulator.project_to_plus12(rune, grind_grade, gem_grade) pour
    énumérer toutes les variantes +12 atteignables.
  - s2us_filter.calculate_efficiency1 pour scorer chaque variante.
  - s2us_filter.match_filter pour savoir quels filtres matcheraient la
    variante optimisée.
"""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from powerup_simulator import project_to_plus12
from s2us_filter import (
    S2USFilter,
    calculate_efficiency1,
    match_filter,
)


@dataclass
class OptimizerResult:
    rune: Rune
    efficiency: float


def best_variant(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
) -> OptimizerResult:
    """Énumère toutes les variantes +12 et retourne celle de max Efficiency1."""
    variants = project_to_plus12(
        rune, grind_grade=grind_grade, gem_grade=gem_grade,
    )
    if not variants:
        return OptimizerResult(rune=rune, efficiency=float(calculate_efficiency1(rune)))
    best = max(variants, key=calculate_efficiency1)
    return OptimizerResult(rune=best, efficiency=float(calculate_efficiency1(best)))


def best_plus0(
    rune: Rune,
    max_grind_grade: int = 3,
    max_gem_grade: int = 3,
) -> OptimizerResult:
    """Rune à +0 (ou <+12) → config future optimale dans la limite des grades."""
    return best_variant(rune, grind_grade=max_grind_grade, gem_grade=max_gem_grade)


def best_now(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
) -> OptimizerResult:
    """Rune à +12 → meilleure amélioration immédiate avec ces grades."""
    return best_variant(rune, grind_grade=grind_grade, gem_grade=gem_grade)


def filters_that_match(
    rune: Rune,
    filters: list[S2USFilter],
) -> list[S2USFilter]:
    """Filtres enabled qui acceptent cette rune, triés par seuil décroissant."""
    matching = [f for f in filters if f.enabled and match_filter(rune, f)]
    matching.sort(key=lambda f: f.efficiency, reverse=True)
    return matching
