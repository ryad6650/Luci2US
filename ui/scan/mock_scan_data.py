"""Mock rune data for the redesigned Scan page.

Exposes ready-to-render dataclasses mirroring the maquette (Plan page scan.png):
    - `MOCK_LAST_RUNE`        -> Violence Rune (+12) Legendaire
    - `MOCK_UPGRADED_RUNE`    -> +15 Legendary Rage Rune (slot 4)
    - `MOCK_HISTORY_ENTRIES`  -> list of 6 ScanHistoryEntry (Violence, Swift,
                                 Focus, Rage, Energy, Will)

All values come from real Rune + Verdict instances so future wiring to the
AutoMode controller only needs to swap the source.
"""
from __future__ import annotations
from dataclasses import dataclass

from models import Rune, SubStat, Verdict


@dataclass
class ScanHistoryEntry:
    """Compact payload consumed by the Scan History panel."""
    rune: Rune
    verdict: Verdict
    short_name: str
    main_line: str


MOCK_LAST_RUNE: Rune = Rune(
    set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
    main_stat=SubStat("ATQ%", 63),
    prefix=SubStat("PV", 720),
    substats=[
        SubStat("VIT", 16),
        SubStat("PV%", 18),
        SubStat("ATQ%", 9),
        SubStat("CC", 6),
    ],
)

# Score affiché "9.1/10", Effi S2US "112%", Effi SWOP "105%" — formatté côté widget.
MOCK_LAST_VERDICT: Verdict = Verdict(
    decision="KEEP",
    source="s2us",
    reason="Roll VIT + ATQ% main stat",
    score=9.1,
    details={"score_label": "9.1/10", "s2us": "112%", "swop": "105%"},
)


MOCK_UPGRADED_RUNE: Rune = Rune(
    set="Rage", slot=4, stars=6, grade="Legendaire", level=15,
    main_stat=SubStat("DC", 80),
    prefix=None,
    substats=[
        SubStat("VIT", 18),
        SubStat("PV%", 14),
        SubStat("ATQ%", 22),
        SubStat("CC", 11),
    ],
)

MOCK_UPGRADED_VERDICT: Verdict = Verdict(
    decision="KEEP",
    source="s2us",
    reason="Amelioration +12 -> +15",
    score=95.0,
    details={"previous_level": 12, "new_level": 15, "boosted": ("CC", 11)},
)


def _mk(set_name: str, slot: int, level: int, main: SubStat,
        decision: str, score: float, short: str, line: str) -> ScanHistoryEntry:
    rune = Rune(
        set=set_name, slot=slot, stars=6, grade="Legendaire", level=level,
        main_stat=main, prefix=None,
        substats=[SubStat("VIT", 10), SubStat("PV%", 8)],
    )
    verdict = Verdict(decision=decision, source="mock", reason="", score=score)
    return ScanHistoryEntry(rune=rune, verdict=verdict,
                            short_name=short, main_line=line)


MOCK_HISTORY_ENTRIES: list[ScanHistoryEntry] = [
    _mk("Violent",       2, 12, SubStat("PV%",  63), "KEEP", 92.0,
        "VIOLENCE (+12)", "6\u2605, HP+63%"),
    _mk("Rapide",        4,  9, SubStat("ATQ%", 55), "KEEP", 85.0,
        "SWIFT (+9)",     "6\u2605, ATK+55%"),
    _mk("Concentration", 6,  6, SubStat("PV%",  15), "SELL", 48.0,
        "FOCUS (+6)",     "6\u2605, HP+15%"),
    _mk("Rage",          4, 12, SubStat("DC",   80), "KEEP", 94.0,
        "RAGE (+12)",     "6\u2605, CRIT DMG+80%"),
    _mk("Energie",       5,  3, SubStat("ATQ%", 12), "SELL", 34.0,
        "ENERGY (+3)",    "6\u2605, ATK+12%"),
]


MOCK_UPGRADE_NOTES = {
    "level_from": 12,
    "level_to":   15,
    "boosted_stat": "CRIT RATE",
    "boosted_delta": 11,
}
