from __future__ import annotations

import base64
import json
import math
from dataclasses import dataclass, field

from models import (
    GRADE_SUBSTAT_COUNT,
    ROLL_MAX_6,
    SET_FR_TO_EN,
    Rune,
    Verdict,
)

# ── Mappings S2US <-> FR ──────────────────────────────────────────

S2US_TO_FR: dict[str, str] = {
    "SPD": "VIT", "HP": "PV%", "HP2": "PV",
    "ATK": "ATQ%", "ATK2": "ATQ",
    "DEF": "DEF%", "DEF2": "DEF",
    "CR": "CC", "CD": "DC", "ACC": "PRE", "RES": "RES",
}
FR_TO_S2US: dict[str, str] = {v: k for k, v in S2US_TO_FR.items()}

SETS_EN_TO_FR: dict[str, str] = {v: k for k, v in SET_FR_TO_EN.items()}

GRADES_S2US_TO_FR: dict[str, str] = {
    "Rare": "Rare", "Hero": "Heroique", "Legend": "Legendaire",
}
GRADES_FR_TO_S2US: dict[str, str] = {v: k for k, v in GRADES_S2US_TO_FR.items()}

FR_TO_MAIN_S2US: dict[str, str] = {
    "VIT": "MainSPD", "PV%": "MainHP", "PV": "MainHP2",
    "ATQ%": "MainATK", "ATQ": "MainATK2",
    "DEF%": "MainDEF", "DEF": "MainDEF2",
    "CC": "MainCR", "DC": "MainCD", "PRE": "MainACC", "RES": "MainRES",
}

_SET_FIELDS = [
    "Violent", "Swift", "Despair", "Will", "Rage", "Fatal",
    "Energy", "Blade", "Focus", "Guard", "Endure",
    "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
    "Determination", "Enhance", "Accuracy", "Tolerance",
    "Intangible", "Seal", "Shield",
]

_STAT_KEYS = [
    "SPD", "HP", "HP2", "ATK", "ATK2", "DEF", "DEF2",
    "CR", "CD", "ACC", "RES",
]

CHECKPOINTS = [3, 6, 9, 12, 15]
_LEVEL_TARGETS = [0, 3, 6, 9, 12, 15]


# ── Efficience — constantes des 3 formules ────────────────────────
#
# Index canonique des stats (spec Système tri de rune.md) :
#   0=SPD(VIT) 1=HP%(PV%) 2=HP(PV) 3=ATK%(ATQ%) 4=ATK(ATQ)
#   5=DEF%(DEF%) 6=DEF(DEF) 7=CD%(DC) 8=CR%(CC) 9=ACC%(PRE) 10=RES(RES)
_FR_TO_IDX: dict[str, int] = {
    "VIT": 0, "PV%": 1, "PV": 2, "ATQ%": 3, "ATQ": 4,
    "DEF%": 5, "DEF": 6, "DC": 7, "CC": 8, "PRE": 9, "RES": 10,
}

# ── Formule 1 : Score (poids fixes, inclut innate) ────────────────
_SCORE_WEIGHTS: list[float] = [
    3.3333,  # 0 SPD
    2.5,     # 1 HP%
    0.0187,  # 2 HP flat
    2.5,     # 3 ATK%
    0.35,    # 4 ATK flat
    2.5,     # 5 DEF%
    0.35,    # 6 DEF flat
    2.8571,  # 7 CD%
    3.3333,  # 8 CR%
    2.5,     # 9 ACC%
    2.5,     # 10 RES%
]


def calculate_score(rune: Rune) -> int:
    """Formule 1 : Score = Ceiling( SUM(sub × poids) + innate × poids )."""
    total = 0.0
    for sub in rune.substats:
        idx = _FR_TO_IDX[sub.type]
        total += sub.value * _SCORE_WEIGHTS[idx]
    if rune.prefix:
        idx = _FR_TO_IDX[rune.prefix.type]
        total += rune.prefix.value * _SCORE_WEIGHTS[idx]
    return math.ceil(total)


# ── Formule 2 : Efficiency1 (méthode par défaut, n'inclut PAS l'innate) ──
_EFF1_WEIGHTS_BY_STARS: dict[int, list[float]] = {
    # idx: 0=SPD 1=HP% 2=HP 3=ATK% 4=ATK 5=DEF% 6=DEF 7=CD 8=CR 9=ACC 10=RES
    1: [2.0,   1.0, 0.0167, 1.0, 0.20,  1.0, 0.20,  1.0,   2.0,   1.0,  1.0],
    2: [1.5,   1.0, 0.0143, 1.0, 0.24,  1.0, 0.24,  1.0,   1.5,   1.0,  1.0],
    3: [1.667, 1.0, 0.0152, 1.0, 0.25,  1.0, 0.25,  1.25,  1.667, 1.25, 1.25],
    4: [1.5,   1.0, 0.0133, 1.0, 0.24,  1.0, 0.24,  1.2,   1.5,   1.2,  1.2],
    5: [1.4,   1.0, 0.0117, 1.0, 0.187, 1.0, 0.187, 1.4,   1.4,   1.0,  1.0],
    6: [1.333, 1.0, 0.0107, 1.0, 0.16,  1.0, 0.16,  1.143, 1.333, 1.0,  1.0],
}

# Base du dénominateur par grade étoile et palier [Lv0, Lv3+, Lv6+, Lv9+, Lv12+]
_EFF1_BASE_BY_STARS: dict[int, list[int]] = {
    1: [0,  4,  8, 12, 16],
    2: [0,  6, 12, 16, 24],
    3: [0, 10, 20, 30, 40],
    4: [0, 12, 24, 36, 48],
    5: [0, 14, 28, 42, 56],
    6: [0, 16, 32, 48, 64],
}

# Bonus de rareté par palier non atteint (= numéro de grade étoile)
_EFF1_BONUS_BY_STARS: dict[int, int] = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7, 6: 8}

# Nb max de paliers selon la rareté (Legend=4 paliers [3,6,9,12] …)
_EFF1_MAX_TIERS_BY_RARITY: dict[str, int] = {
    "Legendaire": 4, "Heroique": 3, "Rare": 2, "Magique": 1, "Normal": 0,
}

_LEVEL_TIERS = [0, 3, 6, 9, 12]      # paliers de base
_RARITY_TIERS = [3, 6, 9, 12]        # paliers où un roll se produit


def calculate_efficiency1(rune: Rune) -> int:
    """Formule 2 : Efficiency1 — méthode par défaut (sans innate).

    Efficiency1 = Ceiling( SUM(sub × poids_grade) × 100 / denominateur )
    où denominateur = base(grade, palier_atteint) + bonus_par_palier_non_atteint.
    """
    weights = _EFF1_WEIGHTS_BY_STARS.get(rune.stars, _EFF1_WEIGHTS_BY_STARS[6])

    numer = 0.0
    for sub in rune.substats:
        idx = _FR_TO_IDX[sub.type]
        numer += sub.value * weights[idx]
    numer *= 100

    tier_idx = 0
    for i, lv in enumerate(_LEVEL_TIERS):
        if rune.level >= lv:
            tier_idx = i
    base = _EFF1_BASE_BY_STARS.get(rune.stars, _EFF1_BASE_BY_STARS[6])[tier_idx]

    max_tiers = _EFF1_MAX_TIERS_BY_RARITY.get(rune.grade, 4)
    missed = sum(1 for i in range(max_tiers) if rune.level < _RARITY_TIERS[i])
    bonus_per = _EFF1_BONUS_BY_STARS.get(rune.stars, 8)

    denom = base + missed * bonus_per
    if denom <= 0:
        return 0
    return math.ceil(numer / denom)


# ── Formule 3 : Efficiency2 (style SW classique, inclut l'innate) ────────
_EFF2_MAXROLL: dict[str, int] = {
    "VIT": 30, "PV%": 40, "PV": 3750, "ATQ%": 40, "ATQ": 200,
    "DEF%": 40, "DEF": 200, "DC": 35, "CC": 30, "PRE": 40, "RES": 40,
}

_EFF2_COEF: dict[int, float] = {
    1: 0.7959, 2: 0.8044, 3: 0.8554, 4: 0.898, 5: 0.9745, 6: 1.0,
}


def calculate_efficiency2(rune: Rune) -> int:
    """Formule 3 : Efficiency2 = Ceiling( coef × (100 + SUM + innate) / 2.8 )."""
    sub_sum = 0.0
    for sub in rune.substats:
        sub_sum += sub.value * 100 / _EFF2_MAXROLL[sub.type]
    innate_bonus = 0.0
    if rune.prefix:
        innate_bonus = rune.prefix.value * 100 / _EFF2_MAXROLL[rune.prefix.type]
    coef = _EFF2_COEF.get(rune.stars, 1.0)
    return math.ceil(coef * (100 + sub_sum + innate_bonus) / 2.8)


# ── Formule 4 : Efficacité Gemstone/Artefact ─────────────────────
# Efficiency = Ceiling( SUM(sub / (maxValue × rolls)) × 100 / divisor )
_ARTIFACT_RARITY: dict[str, tuple[float, int]] = {
    "Normal":     (4.0,  1),
    "Magique":    (2.5,  2),
    "Rare":       (2.0,  3),
    "Heroique":   (1.75, 4),
    "Legendaire": (1.6,  5),
}


def calculate_efficiency_artifact(
    obj, max_values: dict[str, float] | None = None,
) -> int:
    """Formule 4 : efficacité d'un artefact / gemstone.

    `max_values` = mapping type → max (cf. tableau 33 entrées de la spec).
    """
    rarity = getattr(obj, "grade", "Legendaire")
    divisor, rolls = _ARTIFACT_RARITY.get(rarity, (1.6, 5))
    substats = getattr(obj, "substats", [])
    mv_map = max_values or {}
    total = 0.0
    for sub in substats:
        mv = mv_map.get(sub.type, 0.0)
        if mv > 0:
            total += sub.value / (mv * rolls)
    return math.ceil(total * 100 / divisor)


# ── Alias de compatibilité (match_filter / evaluator_chain / …) ──
def calculate_efficiency_swop(rune: Rune) -> float:
    """Alias historique → Efficiency2 (style SW classique)."""
    return float(calculate_efficiency2(rune))


def calculate_efficiency_s2us(
    rune: Rune, grind: bool = False, gem: int = 0,
) -> float:
    """Alias historique → Efficiency1 (méthode par défaut).

    Les paramètres `grind` et `gem` sont conservés pour compatibilité de
    signature mais ne sont plus utilisés (la spec ne les prévoit pas ici).
    """
    return float(calculate_efficiency1(rune))


def calculate_max_efficiency(rune: Rune, method: str = "S2US") -> float:
    """Projection — Efficiency1 calcule déjà vs rolls restants, donc on
    retourne simplement l'efficience courante. Placeholder pour l'étape 2.
    """
    if method == "SWOP":
        return calculate_efficiency_swop(rune)
    return calculate_efficiency_s2us(rune)


# ── Dataclass S2USFilter ─────────────────────────────────────────

@dataclass
class S2USFilter:
    name: str
    enabled: bool = True
    sets: dict[str, bool] = field(default_factory=dict)
    slots: dict[str, bool] = field(default_factory=dict)
    grades: dict[str, bool] = field(default_factory=dict)
    stars: dict[str, bool] = field(default_factory=dict)
    main_stats: dict[str, bool] = field(default_factory=dict)
    ancient_type: str = ""
    sub_requirements: dict[str, int] = field(default_factory=dict)
    min_values: dict[str, int] = field(default_factory=dict)
    optional_count: int = 0
    level: int = 0
    efficiency: float = 0.0
    eff_method: str = "S2US"
    grind: int = 0
    gem: int = 0
    powerup_mandatory: int = 0
    powerup_optional: int = 0
    innate_required: dict[str, bool] = field(default_factory=dict)


# ── Parser ────────────────────────────────────────────────────────

def _decode_name(b64: str) -> str:
    try:
        return base64.b64decode(b64).decode("utf-8")
    except Exception:
        return b64


def _parse_filter(raw: dict) -> S2USFilter:
    name = _decode_name(raw.get("Name", ""))

    sets = {s: bool(raw.get(s, 0)) for s in _SET_FIELDS}
    slots = {f"Slot{i}": bool(raw.get(f"Slot{i}", 0)) for i in range(1, 7)}
    grades = {g: bool(raw.get(g, 0)) for g in ("Rare", "Hero", "Legend")}
    stars_ = {s: bool(raw.get(s, 0)) for s in ("FiveStars", "SixStars")}

    main_keys = [
        "MainSPD", "MainHP", "MainHP2", "MainATK", "MainATK2",
        "MainDEF", "MainDEF2", "MainCR", "MainCD", "MainACC", "MainRES",
    ]
    main_stats = {k: bool(raw.get(k, 0)) for k in main_keys}

    # Ancient type — marqueur Luci2US prioritaire (round-trip fiable), sinon
    # heuristique bot-compat : le bot écrit (Ancient=1,Normal=0) par défaut pour
    # "Tous", donc seul (0,1) signifie explicitement "NotAncient".
    if "_AncientMode" in raw:
        mode = raw.get("_AncientMode", "")
        ancient_type = mode if mode in ("Ancient", "NotAncient") else ""
    else:
        ancient = bool(raw.get("Ancient", 0))
        normal = bool(raw.get("Normal", 0))
        if normal and not ancient:
            ancient_type = "NotAncient"
        else:
            ancient_type = ""

    # Sous-stats
    sub_reqs = {k: raw.get(f"Sub{k}", 0) for k in _STAT_KEYS}
    min_vals = {k: raw.get(f"Min{k}", 0) for k in _STAT_KEYS}

    # Innate
    innate_req: dict[str, bool] = {}
    if raw.get("Innate", 0):
        has_specific = False
        for k in _STAT_KEYS:
            field_name = f"Innate{k}"
            if field_name in raw:
                innate_req[k] = bool(raw[field_name])
                has_specific = True
        if not has_specific:
            innate_req = {k: True for k in _STAT_KEYS}

    return S2USFilter(
        name=name,
        enabled=bool(raw.get("Enabled", True)),
        sets=sets,
        slots=slots,
        grades=grades,
        stars=stars_,
        main_stats=main_stats,
        ancient_type=ancient_type,
        sub_requirements=sub_reqs,
        min_values=min_vals,
        optional_count=raw.get("Optional", 0),
        level=raw.get("Level", 0),
        efficiency=float(raw.get("Efficiency", 0)),
        eff_method=raw.get("EffMethod", "S2US"),
        grind=int(raw.get("Grind", 0)),
        gem=int(raw.get("Gem", 0)),
        powerup_mandatory=raw.get("PowerupMandatory", 0),
        powerup_optional=raw.get("PowerupOptional", 0),
        innate_required=innate_req,
    )


def load_s2us_file(path: str) -> tuple[list[S2USFilter], dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    rf = data.get("RuneFilter", {})
    raw_filters = rf.get("Filter", [])
    filters = [_parse_filter(r) for r in raw_filters]

    global_settings = {
        "SmartPowerup": rf.get("SmartPowerup", True),
        "RareLevel": rf.get("RareLevel", 0),
        "HeroLevel": rf.get("HeroLevel", 0),
        "LegendLevel": rf.get("LegendLevel", 0),
    }
    return filters, global_settings


# ── Matching ──────────────────────────────────────────────────────

# Level Range (spec) : 1→(0-2), 2→(3-5), 3→(6-8), 4→(9-11), 5→(12-15)
_LEVEL_RANGES: dict[int, tuple[int, int]] = {
    1: (0, 2),
    2: (3, 5),
    3: (6, 8),
    4: (9, 11),
    5: (12, 15),
}

# Diviseurs Powerup (valeur de référence par roll) — spec §13
_POWERUP_DIVISORS: dict[int, dict[str, int]] = {
    6: {
        "VIT": 6, "PV%": 8, "PV": 375, "ATQ%": 8, "ATQ": 20,
        "DEF%": 8, "DEF": 20, "DC": 7, "CC": 6, "PRE": 8, "RES": 8,
    },
    5: {
        "VIT": 5, "PV%": 7, "PV": 300, "ATQ%": 7, "ATQ": 15,
        "DEF%": 7, "DEF": 15, "DC": 5, "CC": 5, "PRE": 7, "RES": 7,
    },
}


def _estimate_rolls(stat_fr: str, value: float, stars: int) -> int:
    """rolls_estimés = Ceiling(SubValue / diviseur) - 1, plancher 0."""
    divs = _POWERUP_DIVISORS.get(stars, _POWERUP_DIVISORS[6])
    div = divs.get(stat_fr, 0)
    if div <= 0:
        return 0
    return max(0, math.ceil(value / div) - 1)


def _rune_eff_for_filter(rune: Rune, eff_method: str) -> int:
    """Retourne Efficiency1 ou Efficiency2 selon EffMethod."""
    m = str(eff_method).upper()
    if m in ("SWOP", "EFFICIENCY2", "EFF2", "2"):
        return calculate_efficiency2(rune)
    return calculate_efficiency1(rune)


def match_filter(rune: Rune, f: S2USFilter, during_powerup: bool = False) -> bool:
    """Filtrage selon l'ordre exact de la spec (14 checks).

    Ordre : Enabled → Set → Level Range → Rarity → Grade → Slot → Ancient →
    Main stat → Innate → Subs obligatoires → Subs optionnelles → Powerup →
    Efficacité (+ baseline Score) → GET/SELL.
    """
    # 1. Enabled
    if not f.enabled:
        return False

    # 2. Set
    active_sets = {s for s, v in f.sets.items() if v}
    if active_sets:
        rune_set_en = SET_FR_TO_EN.get(rune.set, rune.set)
        if rune_set_en not in active_sets:
            return False

    # 3. Level Range (0/-1 → pas de filtre ; 1-5 → range strict)
    if f.level in _LEVEL_RANGES:
        lo, hi = _LEVEL_RANGES[f.level]
        if not (lo <= rune.level <= hi):
            return False

    # 4. Rarity (Rare / Hero / Legend)
    active_rarities = {g for g, v in f.grades.items() if v}
    if active_rarities:
        rune_rarity = GRADES_FR_TO_S2US.get(rune.grade, "")
        if rune_rarity not in active_rarities:
            return False

    # 5. Grade étoile (1★-6★ — ici 5 ou 6 dans le parser)
    active_stars = {s for s, v in f.stars.items() if v}
    if active_stars:
        star_key = {6: "SixStars", 5: "FiveStars"}.get(rune.stars, "")
        if star_key not in active_stars:
            return False

    # 6. Slot
    active_slots = {s for s, v in f.slots.items() if v}
    if active_slots and f"Slot{rune.slot}" not in active_slots:
        return False

    # 7. Ancient
    if f.ancient_type == "Ancient" and not rune.ancient:
        return False
    if f.ancient_type == "NotAncient" and rune.ancient:
        return False

    # 8. Main stat
    active_mains = {m for m, v in f.main_stats.items() if v}
    if active_mains:
        rune_main_key = FR_TO_MAIN_S2US.get(rune.main_stat.type, "")
        if rune_main_key not in active_mains:
            return False

    # 9. Innate
    active_innate = {k for k, v in f.innate_required.items() if v}
    if active_innate:
        if not rune.prefix:
            return False
        prefix_s2us = FR_TO_S2US.get(rune.prefix.type, "")
        if prefix_s2us not in active_innate:
            return False

    # 10-11. Sous-stats
    rune_subs = {sub.type: sub.value for sub in rune.substats}

    # 10. Obligatoires (req == 1) — toutes doivent être présentes >= seuil
    mandatory_subs: list[tuple[str, float]] = []
    for stat_s2us, req in f.sub_requirements.items():
        if req != 1:
            continue
        stat_fr = S2US_TO_FR.get(stat_s2us, stat_s2us)
        if stat_fr not in rune_subs:
            return False
        min_val = f.min_values.get(stat_s2us, 0)
        if min_val > 0 and rune_subs[stat_fr] < min_val:
            return False
        mandatory_subs.append((stat_fr, rune_subs[stat_fr]))

    # 11. Optionnelles (req == 2) — au moins `optional_count` présentes >= seuil
    optional_subs: list[tuple[str, float]] = []
    for stat_s2us, req in f.sub_requirements.items():
        if req != 2:
            continue
        stat_fr = S2US_TO_FR.get(stat_s2us, stat_s2us)
        if stat_fr not in rune_subs:
            continue
        min_val = f.min_values.get(stat_s2us, 0)
        if min_val > 0 and rune_subs[stat_fr] < min_val:
            continue
        optional_subs.append((stat_fr, rune_subs[stat_fr]))
    if len(optional_subs) < f.optional_count:
        return False

    # 12. Powerup — somme des rolls estimés
    if f.powerup_mandatory > 0:
        mand_rolls = sum(
            _estimate_rolls(s, v, rune.stars) for s, v in mandatory_subs
        )
        if mand_rolls < f.powerup_mandatory:
            return False
    if f.powerup_optional > 0:
        opt_rolls = sum(
            _estimate_rolls(s, v, rune.stars) for s, v in optional_subs
        )
        if opt_rolls < f.powerup_optional:
            return False

    # 13. Efficacité minimale — Score (baseline) + Efficiency1/2 selon EffMethod
    if f.efficiency > 0:
        seuil = f.efficiency
        if calculate_score(rune) < seuil:
            return False
        if _rune_eff_for_filter(rune, f.eff_method) < seuil:
            return False

    # 14. GET
    return True


# ── Evaluation multi-filtres ──────────────────────────────────────

def evaluate_s2us(
    rune: Rune,
    filters: list[S2USFilter],
    global_settings: dict,
) -> Verdict:
    """Itère sur tous les filtres, garde la meilleure correspondance
    (celle avec le seuil d'efficacité le plus haut parmi celles qui matchent).
    """
    score = calculate_score(rune)
    eff1 = calculate_efficiency1(rune)
    eff2 = calculate_efficiency2(rune)

    matching = [f for f in filters if match_filter_smart(rune, f)]

    base_details = {
        "score": score,
        "efficiency1": eff1,
        "efficiency2": eff2,
        # Alias pour compatibilité avec le reste de l'app
        "efficiency_swop": float(eff2),
        "efficiency_s2us": float(eff1),
        "max_efficiency": float(eff1),
    }

    if matching:
        best = max(matching, key=lambda x: x.efficiency)
        return Verdict(
            decision="KEEP",
            source="s2us",
            reason=best.name,
            score=float(eff2),
            details={"filter": best.name, **base_details},
        )

    return Verdict(
        decision="SELL",
        source="s2us",
        reason="Aucun filtre",
        score=float(eff2),
        details=base_details,
    )


# ── Smart Filter ──────────────────────────────────────────────────

def match_filter_smart(
    rune: Rune,
    f: S2USFilter,
) -> bool:
    """Mode Smart Filter (f.level == -1) : projette la rune à +12 via le
    simulator (power-up optimiste + gemme + meule selon f.gem / f.grind),
    puis retourne True si au moins une variante passe match_filter.

    Reproduit le pipeline du bot (-.18.cs lignes 1192-1694).
    """
    # Import tardif pour éviter cycle powerup_simulator ↔ s2us_filter
    from powerup_simulator import project_to_plus12

    if f.level != -1:
        return match_filter(rune, f)

    # Filter flags → tier index dans GRIND_MAX/GEM_MAX (0=Normal … 4=Légendaire)
    # Spec bot : Grind 0=off/1=on, Gem 0=off/1=medium/2=full.
    grind_tier = 4 if f.grind >= 1 else 0
    gem_tier = {0: 0, 1: 3, 2: 4}.get(f.gem, 0)

    # Mode 'max' : on cherche si AU MOINS UN scénario passe le filtre, donc
    # on projette au potentiel théorique (rolls max). Un Smart Filter est une
    # question de potentiel, pas de projection moyenne.
    variants = project_to_plus12(
        rune, grind_grade=grind_tier, gem_grade=gem_tier, roll_mode="max",
    )
    return any(match_filter(v, f) for v in variants)


def should_evaluate_now(
    rune: Rune,
    f: S2USFilter,
    global_settings: dict,
) -> bool:
    if f.level == -1:  # Smart
        smart_powerup = global_settings.get("SmartPowerup", True)
        if not smart_powerup:
            grade = rune.grade
            rare_idx = global_settings.get("RareLevel")
            rare_target = _LEVEL_TARGETS[rare_idx if rare_idx is not None else 2]
            hero_idx = global_settings.get("HeroLevel")
            hero_target = _LEVEL_TARGETS[hero_idx if hero_idx is not None else 4]
            legend_idx = global_settings.get("LegendLevel")
            legend_target = _LEVEL_TARGETS[legend_idx if legend_idx is not None else 4]
            if grade == "Rare" and rune.level < rare_target:
                return False
            if grade == "Heroique" and rune.level < hero_target:
                return False
            if grade == "Legendaire" and rune.level < legend_target:
                return False
        return rune.level in CHECKPOINTS
    else:
        target = _LEVEL_TARGETS[f.level] if 0 <= f.level < len(_LEVEL_TARGETS) else 0
        return rune.level >= target
