from __future__ import annotations

import copy
from dataclasses import dataclass

from models import (
    GEM_MAX,
    GRIND_MAX,
    ORIG_SUBS_BY_RARITY,
    ROLL_MAX_5,
    ROLL_MAX_6,
    ROLL_MID_5,
    ROLL_MID_6,
    ROLL_MIN_5,
    ROLL_MIN_6,
    Rune,
    SubStat,
)

# Stats pouvant apparaitre en substat
_ALL_SUB_STATS: list[str] = [
    "VIT", "PV%", "PV", "ATQ%", "ATQ", "DEF%", "DEF",
    "DC", "CC", "PRE", "RES",
]


def _max_roll(stat: str, stars: int) -> int:
    table = ROLL_MAX_6 if stars >= 6 else ROLL_MAX_5
    return table.get(stat, 0)


def _min_roll(stat: str, stars: int) -> int:
    table = ROLL_MIN_6 if stars >= 6 else ROLL_MIN_5
    return table.get(stat, 0)


def _mid_roll(stat: str, stars: int) -> int:
    """Valeur d'un roll alignée sur Script2us (-.18.cs l.1743).
    Le bot utilise ROLL_MAX par grade comme valeur plate (pas de tirage,
    pas de (min+max)//2) : 6★ → ROLL_MAX_6, 5★ → ROLL_MAX_5."""
    table = ROLL_MID_6 if stars >= 6 else ROLL_MID_5
    return table.get(stat, 0)


def _roll_value(stat: str, stars: int, mode: str) -> int:
    """Valeur d'un roll selon le mode : 'max' (optimiste), 'mid' (moyen),
    'min' (pessimiste)."""
    if mode == "max":
        return _max_roll(stat, stars)
    if mode == "min":
        return _min_roll(stat, stars)
    return _mid_roll(stat, stars)


def _rolls_remaining(rarity: str, level: int) -> int:
    """Rolls de power-up appliqués sur subs existantes, du niveau courant à +12.
    Reproduit les conditions du bot (-.18.cs lignes 1206-1644)."""
    if rarity == "Legendaire":
        if level < 3:  return 4
        if level < 6:  return 3
        if level < 9:  return 2
        if level < 12: return 1
        return 0
    if rarity == "Heroique":
        if level < 3:  return 3
        if level < 6:  return 2
        if level < 9:  return 1
        return 0
    if rarity == "Rare":
        if level < 3:  return 2
        if level < 6:  return 1
        return 0
    return 0


def _distribute(rolls: int, buckets: int = 4) -> list[tuple[int, ...]]:
    """Toutes les distributions entières non-négatives de `rolls` sur `buckets`."""
    if rolls == 0:
        return [(0,) * buckets]
    out: list[tuple[int, ...]] = []

    def rec(remaining: int, current: list[int]) -> None:
        if len(current) == buckets - 1:
            out.append(tuple(current + [remaining]))
            return
        for n in range(remaining + 1):
            rec(remaining - n, current + [n])

    rec(rolls, [])
    return out


def _candidate_stats(rune: Rune, exclude_current_subs: bool = True) -> list[str]:
    """Stats candidates pour substat (exclut Main, Innate et subs existantes)."""
    used = {rune.main_stat.type}
    if rune.prefix:
        used.add(rune.prefix.type)
    if exclude_current_subs:
        for s in rune.substats:
            used.add(s.type)
    return [s for s in _ALL_SUB_STATS if s not in used]


def _rune_key(rune: Rune) -> tuple:
    """Clé de déduplication: subs triés + level."""
    subs = tuple(sorted((s.type, s.value) for s in rune.substats))
    return (rune.level, subs)


def _add_missing_subs(rune: Rune, roll_mode: str = "mid") -> list[Rune]:
    """Étape 1: complète à 4 subs en testant toutes stats candidates.
    Nouvelles subs apparaissent avec roll selon `roll_mode` — pas de roll
    bonus à +12 pour ces subs (règle SW confirmée user 2026-04-19)."""
    missing = 4 - len(rune.substats)
    if missing <= 0:
        return [rune]
    variants = [rune]
    for _ in range(missing):
        nxt: list[Rune] = []
        for v in variants:
            for stat in _candidate_stats(v):
                new_v = copy.deepcopy(v)
                new_v.substats.append(
                    SubStat(type=stat, value=_roll_value(stat, new_v.stars, roll_mode))
                )
                nxt.append(new_v)
        variants = nxt
    return variants


def _apply_power_up(
    rune: Rune,
    original_sub_count: int,
    excluded: set[int] | None = None,
    roll_mode: str = "mid",
) -> list[Rune]:
    """Étape 2: distribue les rolls de power-up UNIQUEMENT sur les subs
    originales (indices < original_sub_count). Les subs apparues plus tard
    (ex: 4e sub d'une Hero à +12) ne reçoivent pas de roll — règle SW.

    Chaque roll ajoute `1 × roll_value(stat, mode)` de la stat.
    `roll_mode` : 'max' (optimiste, Smart Filter), 'mid' (moyen), 'min' (pire).

    `excluded` : indices de subs gemmés (valeur fixée par la gemme, ne reçoit
    aucun roll — règle SW confirmée user 2026-04-18)."""
    rolls = _rolls_remaining(rune.grade, rune.level)
    skip = excluded or set()
    eligible = [i for i in range(original_sub_count) if i not in skip]
    variants: list[Rune] = []
    if not eligible or rolls == 0:
        v = copy.deepcopy(rune)
        v.level = 12
        return [v]
    for dist in _distribute(rolls, len(eligible)):
        v = copy.deepcopy(rune)
        v.level = 12
        for k, idx in enumerate(eligible):
            if dist[k] > 0:
                sub = v.substats[idx]
                sub.value += dist[k] * _roll_value(sub.type, v.stars, roll_mode)
        variants.append(v)
    return variants


def _gem_variants(rune: Rune, gem_grade: int) -> list[tuple[Rune, int]]:
    """Étape 3 : génère les variantes gemmées AVANT power-up (la gemme fixe
    la valeur du sub et interdit les rolls dessus). Renvoie `(rune, idx)` où
    `idx` est le sub à exclure de la distribution des rolls."""
    if gem_grade <= 0:
        return []
    out: list[tuple[Rune, int]] = []
    for i in range(len(rune.substats)):
        forbidden = {rune.main_stat.type}
        if rune.prefix:
            forbidden.add(rune.prefix.type)
        for j, sub in enumerate(rune.substats):
            if j != i:
                forbidden.add(sub.type)
        for stat in _ALL_SUB_STATS:
            if stat in forbidden:
                continue
            gem_val = GEM_MAX.get(stat, [0, 0, 0, 0, 0])[gem_grade]
            if gem_val <= 0:
                continue
            new_v = copy.deepcopy(rune)
            new_v.substats[i] = SubStat(type=stat, value=gem_val)
            out.append((new_v, i))
    return out


def _apply_grind(runes: list[Rune], grind_grade: int) -> list[Rune]:
    """Étape 4: ajoute le max grind du grade à chaque sub grindable, en place."""
    if grind_grade <= 0:
        return runes
    for rune in runes:
        for sub in rune.substats:
            bonus = GRIND_MAX.get(sub.type, [0, 0, 0, 0, 0])[grind_grade]
            if bonus > 0:
                sub.value += bonus
    return runes


def _dedup(runes: list[Rune]) -> list[Rune]:
    seen: set = set()
    out: list[Rune] = []
    for r in runes:
        k = _rune_key(r)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def project_to_plus12(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
    roll_mode: str = "mid",
) -> list[Rune]:
    """Pipeline de projection +12 avec mécanique SW stricte :

    1. Apparition des subs manquantes (4 - subs actuelles) à `roll_mode`.
    2. Power-up : rolls distribués UNIQUEMENT sur les subs originales
       (selon rareté : Legend=4, Hero=3, Rare=2, Magique=1, Normal=0).
       Chaque roll vaut `roll_value(stat, mode)`.
    3. Gemme (optionnelle) : pour chaque slot × stat gemmable, fixe la valeur
       et exclut ce slot des rolls.
    4. Meule (optionnelle) : ajoute grind_max à chaque sub grindable.
    5. Dédup.

    `roll_mode` :
    - `'max'` : rolls au maximum — pour `match_filter_smart` (potentiel).
    - `'mid'` : rolls à la moyenne — pour affichage UI (projection attendue).
    - `'min'` : rolls au minimum — pour analyse pire cas.
    """
    original_sub_count = ORIG_SUBS_BY_RARITY.get(rune.grade, len(rune.substats))
    completed = _add_missing_subs(rune, roll_mode=roll_mode)
    all_variants: list[Rune] = []
    for v in completed:
        all_variants.extend(_apply_power_up(v, original_sub_count, roll_mode=roll_mode))
        for gemmed, idx in _gem_variants(v, gem_grade):
            all_variants.extend(
                _apply_power_up(gemmed, original_sub_count, excluded={idx}, roll_mode=roll_mode)
            )
    grinded = _apply_grind(all_variants, grind_grade)
    return _dedup(grinded)


# ── Résultats (compat legacy + nouveau contract) ──────────────────────

@dataclass
class SimResult:
    efficiency: float
    substats: list[SubStat]


@dataclass
class SimulationOutput:
    best: SimResult
    worst: SimResult
    variant_count: int
    keep_rate: float | None = None


def simulate_powerup(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
    filters=None,
    global_settings: dict | None = None,
    roll_mode: str = "mid",
) -> SimulationOutput:
    """Génère toutes les variantes +12 et agrège best/worst par efficiency.

    `roll_mode` = 'mid' par défaut (projection moyenne pour affichage UI).
    Utiliser 'max' pour potentiel théorique, 'min' pour pire cas.

    Si `filters` est fourni, calcule `keep_rate` = % de variantes passant au
    moins un filtre (via `match_filter`).
    """
    # Import tardif pour éviter cycle
    from s2us_filter import calculate_efficiency1, match_filter

    variants = project_to_plus12(
        rune, grind_grade=grind_grade, gem_grade=gem_grade, roll_mode=roll_mode,
    )
    if not variants:
        empty = SimResult(efficiency=0.0, substats=[])
        return SimulationOutput(best=empty, worst=empty, variant_count=0)

    scored = [(calculate_efficiency1(v), v) for v in variants]
    scored.sort(key=lambda x: x[0])

    worst_eff, worst_rune = scored[0]
    best_eff, best_rune = scored[-1]

    keep_rate: float | None = None
    if filters is not None:
        kept = 0
        for _, v in scored:
            if any(match_filter(v, f) for f in filters):
                kept += 1
        keep_rate = round(kept / len(scored) * 100, 2)

    return SimulationOutput(
        best=SimResult(efficiency=float(best_eff), substats=best_rune.substats),
        worst=SimResult(efficiency=float(worst_eff), substats=worst_rune.substats),
        variant_count=len(scored),
        keep_rate=keep_rate,
    )
