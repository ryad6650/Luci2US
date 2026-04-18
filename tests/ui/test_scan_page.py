from models import Rune, SubStat, Verdict
from ui.scan.scan_page import ScanPage


def _rune(set_name="Violent", decision="KEEP", score: float = 75.0) -> tuple[Rune, Verdict]:
    r = Rune(
        set=set_name, slot=2, stars=6, grade="Heroique", level=9,
        main_stat=SubStat("VIT", 25), prefix=None,
        substats=[SubStat("PV%", 15), SubStat("CC", 9), SubStat("DC", 12), SubStat("PRE", 5)],
    )
    v = Verdict(decision=decision, source="s2us", reason="", score=score)
    return r, v


def test_on_rune_updates_last(qapp):
    page = ScanPage()
    r, v = _rune()
    page.on_rune(r, v, mana=65, swop=(98.3, 112.4), s2us=(127.4, 145.0))
    assert "VIOLENT" in page._last_card._set_label.text()


def test_counters_increment(qapp):
    page = ScanPage()
    r, v = _rune(decision="KEEP", score=80.0)
    page.on_rune(r, v, mana=10, swop=(0, 0), s2us=(0, 0))
    r, v = _rune(decision="SELL", score=20.0)
    page.on_rune(r, v, mana=10, swop=(0, 0), s2us=(0, 0))
    assert page._total == 2
    assert page._kept == 1
    assert page._sold == 1
    assert page._stats._obtained._value.text() == "2"
    assert page._stats._kept._value.text() == "1"
    assert page._stats._sold._value.text() == "1"
