# swlens/config.py
"""Constantes et defaults du système de tri SWLens.

Source des step values : ROLL_MAX_6 de models.py (vérifié identique à
la table SWLens publique : SPD=6, CR=6, CD=7).
"""
from __future__ import annotations

from models import ROLL_MAX_5, ROLL_MAX_6


# RL Score step values (valeur d'un roll "moyen" par stat)
STAT_STEPS_6 = dict(ROLL_MAX_6)
STAT_STEPS_5 = dict(ROLL_MAX_5)


def step_for(stat_fr: str, stars: int) -> int:
    """Retourne la step value pour une stat donnée selon le grade étoile."""
    table = STAT_STEPS_6 if stars >= 6 else STAT_STEPS_5
    return int(table.get(stat_fr, 0))


# Seuils de catégorisation RL Score
KEEP_THRESHOLD_DEFAULT = 230
CATEGORY_BOUNDS = [
    (300, "Excellent"),
    (230, "Bon"),
    (150, "Médiocre"),
    (0,   "Faible"),
]


def category_for(total: int) -> str:
    for bound, label in CATEGORY_BOUNDS:
        if total >= bound:
            return label
    return "Faible"


# Priority Score — pondérations Innate (stat FR)
INNATE_IMPORTANCE = {
    "PRE": 2.0, "CC": 2.0,        # ACC, CR
    "RES": 1.5, "DC": 1.5,        # RES, CD
    "VIT": 1.0,                   # SPD
    "PV%": 1.0, "ATQ%": 1.0, "DEF%": 1.0,
    "PV": 1.0, "ATQ": 1.0, "DEF": 1.0,
}

# Priority Score — bonus par slot
SLOT_BONUS = {1: 50, 2: 75, 3: 50, 4: 100, 5: 50, 6: 100}


# Gap Analysis — 7 catégories SWLens
GAP_CATEGORIES = ["PV%", "ATQ%", "DEF%", "CC", "DC", "PRE", "VIT"]

# Gap Analysis — multiplicateurs par catégorie
GAP_MULTIPLIERS = {
    "PV%": 1.3, "ATQ%": 1.2,
    "DEF%": 1.0, "CC": 1.0, "DC": 1.0, "PRE": 1.0, "VIT": 1.0,
}

# Seuil "rune rapide" (SPD substat)
FAST_SPD_THRESHOLD = 20

# Seuil "elite rune" (RL Score)
ELITE_SCORE_THRESHOLD = 300
