"""Agrégation de l'inventaire de runes par catégorie (main stat + substats)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from models import Rune
from swlens.config import FAST_SPD_THRESHOLD, GAP_CATEGORIES


@dataclass
class CollectionState:
    by_category: dict[str, list[Rune]] = field(default_factory=lambda: defaultdict(list))
    total_count: int = 0

    @classmethod
    def from_runes(cls, runes: list[Rune]) -> "CollectionState":
        by_cat: dict[str, list[Rune]] = defaultdict(list)
        for rune in runes:
            stats_present = {rune.main_stat.type}
            for sub in rune.substats:
                stats_present.add(sub.type)
            for cat in GAP_CATEGORIES:
                if cat in stats_present:
                    by_cat[cat].append(rune)
        return cls(by_category=by_cat, total_count=len(runes))

    def runes_in_category(self, category: str) -> list[Rune]:
        return list(self.by_category.get(category, []))

    def fast_count(self, category: str) -> int:
        count = 0
        for rune in self.runes_in_category(category):
            for sub in rune.substats:
                if sub.type == "VIT" and sub.value >= FAST_SPD_THRESHOLD:
                    count += 1
                    break
            if rune.main_stat.type == "VIT" and rune.main_stat.value >= FAST_SPD_THRESHOLD:
                count += 1
        return count

    def invalidate(self) -> None:
        self.by_category.clear()
        self.total_count = 0
