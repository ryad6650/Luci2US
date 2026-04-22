"""Module SWLens — système de tri de runes score-based.

API publique :
- rl_score(rune) → RLScoreResult
- priority_score(rune, collection) → PriorityResult
- gap_analysis(collection) → GapReport
- CollectionState.from_runes(runes) → CollectionState
- constantes de config (seuils, pondérations)
"""
from swlens.collection_state import CollectionState
from swlens.config import (
    CATEGORY_BOUNDS,
    GAP_CATEGORIES,
    GAP_MULTIPLIERS,
    INNATE_IMPORTANCE,
    KEEP_THRESHOLD_DEFAULT,
    SLOT_BONUS,
    category_for,
    step_for,
)
from swlens.gap_analysis import CategoryGap, GapReport, gap_analysis, gap_for_rune
from swlens.priority_score import PriorityResult, priority_score
from swlens.rl_score import RLScoreResult, rl_score

__all__ = [
    "rl_score", "priority_score", "gap_analysis", "gap_for_rune",
    "CollectionState", "RLScoreResult", "PriorityResult",
    "GapReport", "CategoryGap",
    "category_for", "step_for",
    "KEEP_THRESHOLD_DEFAULT", "CATEGORY_BOUNDS", "GAP_CATEGORIES",
    "GAP_MULTIPLIERS", "INNATE_IMPORTANCE", "SLOT_BONUS",
]
