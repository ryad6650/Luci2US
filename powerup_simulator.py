from __future__ import annotations

import copy
from dataclasses import dataclass

from models import (
    GEM_MAX,
    GRIND_MAX,
    ROLL_MAX_5,
    ROLL_MAX_6,
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


def _add_missing_subs(rune: Rune) -> list[Rune]:
    """Étape 1: complète à 4 subs en testant toutes stats candidates.
    Nouvelles subs ont valeur initiale = 1 × max_roll (multiplier=1, cf. bot)."""
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
                    SubStat(type=stat, value=_max_roll(stat, new_v.stars))
                )
                nxt.append(new_v)
        variants = nxt
    return variants


def _apply_power_up(rune: Rune, excluded: set[int] | None = None) -> list[Rune]:
    """Étape 2: applique toutes les distributions de rolls de power-up sur les
    subs éligibles. Doit être appelé APRÈS _add_missing_subs pour que le 4ème
    sub participe aux rolls (sinon il reste figé à 1 × max_roll).

    `excluded` : indices de subs gemmés (valeur fixée par la gemme, ne reçoit
    aucun roll — règle SW confirmée par user 2026-04-18)."""
    rolls = _rolls_remaining(rune.grade, rune.level)
    skip = excluded or set()
    eligible = [i for i in range(len(rune.substats)) if i not in skip]
    variants: list[Rune] = []
    if not eligible:
        v = copy.deepcopy(rune)
        v.level = 12
        return [v]
    for dist in _distribute(rolls, len(eligible)):
        v = copy.deepcopy(rune)
        v.level = 12
        for k, idx in enumerate(eligible):
            if dist[k] > 0:
                sub = v.substats[idx]
                sub.value += dist[k] * _max_roll(sub.type, v.stars)
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
) -> list[Rune]:
    """Reproduit le pipeline du bot (-.18.cs lignes 1192-1694) :

    1. Ajoute les subs manquantes (toutes stats candidates, valeur = 1 max roll).
    2. Branche sans gemme : power-up distribue les rolls sur les 4 subs.
    3. Branche avec gemme : pour chaque slot × stat gemmable, pose la gemme
       AVANT le power-up et exclut ce slot des rolls (règle SW).
    4. Meule : ajoute grind_max à chaque sub grindable (in place).
    5. Dédup.

    Retourne la liste de toutes les variantes possibles à +12.
    """
    completed = _add_missing_subs(rune)
    all_variants: list[Rune] = []
    for v in completed:
        all_variants.extend(_apply_power_up(v))
        for gemmed, idx in _gem_variants(v, gem_grade):
            all_variants.extend(_apply_power_up(gemmed, excluded={idx}))
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
) -> SimulationOutput:
    """Génère toutes les variantes +12 et agrège best/worst par efficiency.

    Si `filters` est fourni, calcule `keep_rate` = % de variantes passant au
    moins un filtre (via `match_filter`).
    """
    # Import tardif pour éviter cycle
    from s2us_filter import calculate_efficiency1, match_filter

    variants = project_to_plus12(rune, grind_grade=grind_grade, gem_grade=gem_grade)
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
