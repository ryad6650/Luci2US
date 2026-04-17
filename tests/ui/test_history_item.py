from models import Rune, SubStat, Verdict
from ui.scan.history_item import HistoryItem
from ui.widgets.tag_badge import TagKind


def _make_rune() -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=9,
        main_stat=SubStat("VIT", 19),
        prefix=None, substats=[],
    )


def test_displays_set_and_level(qapp):
    r = _make_rune()
    v = Verdict(decision="KEEP", source="s2us", reason="")
    w = HistoryItem(r, v)
    assert "Violent" in w._name_label.text()
    assert "+9" in w._sub_label.text()


def test_tag_matches_verdict(qapp):
    r = _make_rune()
    v = Verdict(decision="SELL", source="s2us", reason="")
    w = HistoryItem(r, v)
    assert w._tag.text() == "SELL"


def test_tag_powerup(qapp):
    r = _make_rune()
    v = Verdict(decision="PWR-UP", source="s2us", reason="")
    w = HistoryItem(r, v)
    assert w._tag.text() == "PWR"
