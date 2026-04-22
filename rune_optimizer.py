"""Choisit la meilleure configuration meule+gemme pour une rune.

Module pur (pas de Qt). Réutilise :
  - powerup_simulator.project_to_plus12(rune, grind_grade, gem_grade) pour
    énumérer toutes les variantes +12 atteignables.
  - swlens.rl_score pour scorer chaque variante.
"""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from powerup_simulator import project_to_plus12
from swlens import rl_score


@dataclass
class OptimizerResult:
    rune: Rune
    efficiency: float


def _score(rune: Rune) -> float:
    return float(rl_score(rune).total)


def best_variant(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
) -> OptimizerResult:
    """Énumère toutes les variantes +12 et retourne celle de max RL Score."""
    variants = project_to_plus12(
        rune, grind_grade=grind_grade, gem_grade=gem_grade,
    )
    if not variants:
        return OptimizerResult(rune=rune, efficiency=_score(rune))
    best = max(variants, key=_score)
    return OptimizerResult(rune=best, efficiency=_score(best))


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
