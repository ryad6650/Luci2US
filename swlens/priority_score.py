"""Priority Score SWLens = Innate (0-200) + Slot (50-100) + Gap (0-600+)."""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from swlens.collection_state import CollectionState
from swlens.config import INNATE_IMPORTANCE, SLOT_BONUS, step_for
from swlens.gap_analysis import gap_for_rune


@dataclass
class PriorityResult:
    total: int
    innate_pts: float
    slot_pts: int
    gap_pts: int


def _innate_points(rune: Rune) -> float:
    if rune.prefix is None:
        return 0.0
    step = step_for(rune.prefix.type, rune.stars)
    if step <= 0:
        return 0.0
    importance = INNATE_IMPORTANCE.get(rune.prefix.type, 1.0)
    return (rune.prefix.value / step * 200) * importance


def priority_score(rune: Rune, collection: CollectionState) -> PriorityResult:
    innate_pts = _innate_points(rune)
    slot_pts = SLOT_BONUS.get(rune.slot, 50)
    gap_pts = gap_for_rune(rune, collection)
    total = int(round(innate_pts + slot_pts + gap_pts))
    return PriorityResult(
        total=total, innate_pts=innate_pts, slot_pts=slot_pts, gap_pts=gap_pts,
    )
