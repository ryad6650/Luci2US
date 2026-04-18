from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class SubStat:
    type: str
    value: float
    grind_value: float = 0.0


@dataclass
class ArtifactSubStat:
    type: str
    value: float


@dataclass
class Rune:
    set: str
    slot: int
    stars: int
    grade: str
    level: int
    main_stat: SubStat
    prefix: SubStat | None
    substats: list[SubStat]
    ancient: bool = False
    swex_efficiency: float | None = None
    swex_max_efficiency: float | None = None
    rune_id: int | None = None


@dataclass
class Verdict:
    decision: str
    source: str
    reason: str
    score: float | None = None
    details: dict | None = None


@dataclass
class Monster:
    name: str
    element: str
    stars: int
    level: int
    unit_master_id: int = 0
    equipped_runes: list[Rune] = field(default_factory=list)


@dataclass
class Artifact:
    artifact_type: str
    attribute: str
    main_stat: SubStat
    grade: str
    level: int
    substats: list[ArtifactSubStat]


# --- Constantes ---

ROLL_MAX_6: dict[str, int] = {
    "ATQ%": 8, "DEF%": 8, "PV%": 8, "VIT": 6, "CC": 6,
    "DC": 7, "RES": 8, "PRE": 8, "ATQ": 20, "DEF": 20, "PV": 375,
}

ROLL_MAX_5: dict[str, int] = {
    "ATQ%": 7, "DEF%": 7, "PV%": 7, "VIT": 5, "CC": 5,
    "DC": 5, "RES": 7, "PRE": 7, "ATQ": 15, "DEF": 15, "PV": 300,
}

# Max grind par stat selon grade de meule (0=aucune, 1=Magique, 2=Rare,
# 3=Heroique, 4=Legendaire). CC/DC/PRE/RES = 0 (non grindables).
# Valeurs in-game confirmees par user 2026-04-18 (le bot original n'exposait
# que 4 grades en sautant Magique, cf -.18.cs ligne 1813).
GRIND_MAX: dict[str, list[int]] = {
    "VIT":  [0, 2, 3, 4, 5],
    "ATQ%": [0, 5, 6, 7, 10],
    "DEF%": [0, 5, 6, 7, 10],
    "PV%":  [0, 5, 6, 7, 10],
    "CC":   [0, 0, 0, 0, 0],
    "DC":   [0, 0, 0, 0, 0],
    "PRE":  [0, 0, 0, 0, 0],
    "RES":  [0, 0, 0, 0, 0],
    "ATQ":  [0, 12, 18, 22, 30],
    "DEF":  [0, 12, 18, 22, 30],
    "PV":   [0, 200, 250, 450, 550],
}

# Max gem par stat selon grade de gemme (0=aucune, 1=Magique, 2=Rare,
# 3=Heroique, 4=Legendaire). Valeurs in-game confirmees par user 2026-04-18.
GEM_MAX: dict[str, list[int]] = {
    "VIT":  [0, 4, 6, 8, 10],
    "ATQ%": [0, 7, 9, 11, 13],
    "DEF%": [0, 7, 9, 11, 13],
    "PV%":  [0, 7, 9, 11, 13],
    "DC":   [0, 5, 6, 8, 10],
    "CC":   [0, 4, 5, 7, 9],
    "PRE":  [0, 6, 8, 9, 11],
    "RES":  [0, 6, 8, 9, 11],
    "ATQ":  [0, 16, 23, 30, 40],
    "DEF":  [0, 16, 23, 30, 40],
    "PV":   [0, 220, 310, 420, 580],
}

SETS_FR: list[str] = [
    "Violent", "Will", "Rapide", "Desespoir", "Rage", "Fatal",
    "Energie", "Lame", "Concentration", "Garde", "Endurance",
    "Vengeance", "Nemesis", "Vampire", "Destruction", "Combat",
    "Determination", "Amelioration", "Precision", "Tolerance",
    "Intangible", "Sceau", "Bouclier",
]

SETS_EN: list[str] = [
    "Violent", "Will", "Swift", "Despair", "Rage", "Fatal",
    "Energy", "Blade", "Focus", "Guard", "Endure",
    "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
    "Determination", "Enhance", "Accuracy", "Tolerance",
    "Intangible", "Seal", "Shield",
]

SET_FR_TO_EN: dict[str, str] = dict(zip(SETS_FR, SETS_EN))

STATS_FR: list[str] = [
    "ATQ", "ATQ%", "DEF", "DEF%", "PV", "PV%", "VIT",
    "CC", "DC", "RES", "PRE",
]

GRADES_FR: list[str] = [
    "Legendaire", "Heroique", "Rare", "Magique", "Normal",
]

GRADE_SUBSTAT_COUNT: dict[str, int] = {
    "Normal": 0, "Magique": 1, "Rare": 2, "Heroique": 3, "Legendaire": 4,
}

MAIN_STATS_BY_SLOT: dict[int, list[str]] = {
    1: ["ATQ"],
    2: ["ATQ", "ATQ%", "DEF", "DEF%", "PV", "PV%", "VIT"],
    3: ["DEF"],
    4: ["ATQ", "ATQ%", "DEF", "DEF%", "PV", "PV%", "CC", "DC"],
    5: ["PV"],
    6: ["ATQ", "ATQ%", "DEF", "DEF%", "PV", "PV%", "RES", "PRE"],
}
