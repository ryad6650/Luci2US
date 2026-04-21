from models import Rune, SubStat, Verdict
from ui.scan.scan_history_panel import ScanHistoryPanel


def _rune(set_name: str, level: int) -> Rune:
    return Rune(
        slot=2, set=set_name, grade="Heroic",
        stars=6, level=level,
        main_stat=SubStat(type="CC", value=10),
        prefix=None,
        substats=[SubStat(type="CC", value=5, grind_value=0.0)],
    )


def _v() -> Verdict:
    return Verdict(decision="SELL", score=1.0, source="t", reason="")


def test_empty(qapp):
    p = ScanHistoryPanel()
    assert p.count() == 0


def test_add_limited_to_6(qapp):
    p = ScanHistoryPanel()
    for i, s in enumerate(["Rage", "Guard", "Despair", "Violent", "Swift", "Energy", "Blade"]):
        p.add_rune(_rune(s, 12 - i), _v())
    assert p.count() == 6
    sets = [c._rune.set for c in p._cards]
    assert "Rage" not in sets
    assert "Blade" in sets


def test_clear(qapp):
    p = ScanHistoryPanel()
    p.add_rune(_rune("Rage", 12), _v())
    p.clear()
    assert p.count() == 0
