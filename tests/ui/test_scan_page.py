from models import Rune, SubStat, Verdict
from ui.scan.scan_page import ScanPage
from ui.scan.rune_card import RuneCardStatus


def _rune(set_name="Violent", decision="KEEP") -> tuple[Rune, Verdict]:
    r = Rune(
        set=set_name, slot=2, stars=6, grade="Heroique", level=9,
        main_stat=SubStat("VIT", 25), prefix=None,
        substats=[SubStat("PV%", 15), SubStat("CC", 9), SubStat("DC", 12), SubStat("PRE", 5)],
    )
    v = Verdict(decision=decision, source="s2us", reason="", score=215)
    return r, v


def test_on_rune_updates_last(qapp):
    page = ScanPage()
    r, v = _rune()
    page.on_rune(r, v, mana=65, swop=(98.3, 112.4), s2us=(127.4, 145.0))
    assert "Violent" in page._last_card._title.text()


def test_counters_increment(qapp):
    page = ScanPage()
    r, v = _rune(decision="KEEP")
    page.on_rune(r, v, mana=10, swop=(0, 0), s2us=(0, 0))
    r, v = _rune(decision="SELL")
    page.on_rune(r, v, mana=10, swop=(0, 0), s2us=(0, 0))
    assert page._counters._total.text() == "2"
    assert page._counters._kept.text() == "1"
    assert page._counters._sold.text() == "1"
