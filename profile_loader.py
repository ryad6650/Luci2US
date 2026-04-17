"""Load a full SWEX JSON profile export into Luci2US models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import Monster, Rune
from swex_bridge import parse_rune

# ---------------------------------------------------------------------------
# SWEX attribute_id -> element name (FR)
# ---------------------------------------------------------------------------

SWEX_ATTRIBUTE: dict[int, str] = {
    1: "Eau",
    2: "Feu",
    3: "Vent",
    4: "Lumiere",
    5: "Tenebres",
}

# ---------------------------------------------------------------------------
# Monster name resolution
# ---------------------------------------------------------------------------

_BESTIARY: dict[int, str] | None = None


def _load_bestiary() -> dict[int, str]:
    """Try to load swarfarm bestiary.json for monster name lookup."""
    global _BESTIARY
    if _BESTIARY is not None:
        return _BESTIARY

    bestiary_path = Path(__file__).parent / "bestiary.json"
    if bestiary_path.is_file():
        with open(bestiary_path, encoding="utf-8") as f:
            data = json.load(f)
        _BESTIARY = {}
        for entry in data:
            mid = entry.get("unit_master_id") or entry.get("com2us_id")
            name = entry.get("name", "")
            if mid and name:
                _BESTIARY[int(mid)] = name
    else:
        _BESTIARY = {}
    return _BESTIARY


def _resolve_monster_name(unit_master_id: int) -> str:
    bestiary = _load_bestiary()
    return bestiary.get(unit_master_id, f"Monster #{unit_master_id}")


# ---------------------------------------------------------------------------
# Profile loader
# ---------------------------------------------------------------------------

def _parse_monster(unit: dict[str, Any]) -> Monster:
    unit_master_id = unit["unit_master_id"]
    attribute = SWEX_ATTRIBUTE.get(unit.get("attribute", 0), "?")
    stars = unit.get("class", 1)
    level = unit.get("unit_level", 1)
    name = _resolve_monster_name(unit_master_id)

    equipped: list[Rune] = []
    for rune_data in unit.get("runes", []):
        if isinstance(rune_data, dict):
            equipped.append(parse_rune(rune_data))

    # Sort by slot so slots 1-6 are in order
    equipped.sort(key=lambda r: r.slot)

    return Monster(
        name=name,
        element=attribute,
        stars=stars,
        level=level,
        unit_master_id=unit_master_id,
        equipped_runes=equipped,
    )


def _parse_profile_data(data: dict[str, Any], source: str) -> dict:
    """Parse raw SWEX JSON data into a profile dict.

    Returns dict with keys:
        wizard_name: str
        level: int
        runes: list[Rune]       -- all runes (inventory + equipped)
        monsters: list[Monster]
        source: str              -- "auto" or "manual"
    """
    wizard_info = data.get("wizard_info", {})
    wizard_name = wizard_info.get("wizard_name", "Unknown")
    wizard_level = wizard_info.get("wizard_level", 0)

    # Parse monsters from unit_list
    monsters: list[Monster] = []
    for unit in data.get("unit_list", []):
        monsters.append(_parse_monster(unit))

    # Collect all runes: inventory runes + equipped runes
    all_runes: list[Rune] = []

    # Inventory runes (not equipped on any monster)
    for rune_data in data.get("runes", []):
        if isinstance(rune_data, dict):
            all_runes.append(parse_rune(rune_data))

    # Equipped runes (from monsters)
    for monster in monsters:
        all_runes.extend(monster.equipped_runes)

    return {
        "wizard_name": wizard_name,
        "level": wizard_level,
        "runes": all_runes,
        "monsters": monsters,
        "source": source,
    }


def load_profile_from_file(path: str | Path) -> dict:
    """Load a SWEX JSON profile from a file path (manual load)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return _parse_profile_data(data, source="manual")


def load_profile_from_dict(data: dict[str, Any]) -> dict:
    """Parse a SWEX JSON profile from a dict (auto-detected by SWEX bridge)."""
    return _parse_profile_data(data, source="auto")


# Backward-compatible alias
load_profile = load_profile_from_file
