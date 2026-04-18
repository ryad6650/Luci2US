"""Sérialisation d'une liste de S2USFilter vers un fichier .s2us.

Inverse de s2us_filter.load_s2us_file. Respecte exactement le format attendu
par le bot (JSON UTF-8, enveloppe RuneFilter, Name en base64, flags int 0/1).
"""
from __future__ import annotations

import base64
import json

from s2us_filter import (
    S2USFilter,
    _SET_FIELDS,
    _STAT_KEYS,
)


def _encode_name(name: str) -> str:
    return base64.b64encode(name.encode("utf-8")).decode("ascii")


_MAIN_KEYS = [
    "MainSPD", "MainHP", "MainHP2", "MainATK", "MainATK2",
    "MainDEF", "MainDEF2", "MainCR", "MainCD", "MainACC", "MainRES",
]


def serialize_filter(f: S2USFilter) -> dict:
    """Retourne le dict JSON-ready correspondant à un S2USFilter."""
    raw: dict = {}
    raw["Name"] = _encode_name(f.name)
    raw["Enabled"] = bool(f.enabled)

    for s in _SET_FIELDS:
        raw[s] = 1 if f.sets.get(s) else 0

    for i in range(1, 7):
        key = f"Slot{i}"
        raw[key] = 1 if f.slots.get(key) else 0

    for g in ("Rare", "Hero", "Legend"):
        raw[g] = 1 if f.grades.get(g) else 0

    for s in ("FiveStars", "SixStars"):
        raw[s] = 1 if f.stars.get(s) else 0

    for k in _MAIN_KEYS:
        raw[k] = 1 if f.main_stats.get(k) else 0

    if f.ancient_type == "Ancient":
        raw["Ancient"], raw["Normal"] = 1, 0
    elif f.ancient_type == "NotAncient":
        raw["Ancient"], raw["Normal"] = 0, 1
    else:
        raw["Ancient"], raw["Normal"] = 0, 0

    for k in _STAT_KEYS:
        raw[f"Sub{k}"] = int(f.sub_requirements.get(k, 0))
        raw[f"Min{k}"] = int(f.min_values.get(k, 0))

    innate = {k: v for k, v in f.innate_required.items() if v}
    raw["Innate"] = 1 if innate else 0
    for k in _STAT_KEYS:
        raw[f"Innate{k}"] = 1 if innate.get(k) else 0

    raw["Optional"] = int(f.optional_count)
    raw["Level"] = int(f.level)
    raw["Efficiency"] = float(f.efficiency)
    raw["EffMethod"] = str(f.eff_method)
    raw["Grind"] = int(f.grind)
    raw["Gem"] = int(f.gem)
    raw["PowerupMandatory"] = int(f.powerup_mandatory)
    raw["PowerupOptional"] = int(f.powerup_optional)
    return raw


def save_s2us_file(
    path: str,
    filters: list[S2USFilter],
    global_settings: dict | None = None,
) -> None:
    """Sérialise `filters` vers `path` au format .s2us."""
    settings = global_settings or {}
    rf = {
        "SmartPowerup": bool(settings.get("SmartPowerup", True)),
        "RareLevel": int(settings.get("RareLevel", 0)),
        "HeroLevel": int(settings.get("HeroLevel", 0)),
        "LegendLevel": int(settings.get("LegendLevel", 0)),
        "Filter": [serialize_filter(f) for f in filters],
    }
    payload = {"RuneFilter": rf}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
