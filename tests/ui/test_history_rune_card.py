from models import Rune, SubStat, Verdict
from ui.scan.history_rune_card import HistoryRuneCard


def _rune() -> Rune:
    return Rune(
        slot=2, set="Rage", grade="Heroic", stars=6, level=12,
        main_stat=SubStat(type="CC", value=23),
        prefix=None,
        substats=[SubStat(type="CC", value=23, grind_value=0.0)],
    )


def test_render(qapp):
    verdict = Verdict(decision="SELL", score=2.1, source="test", reason="low")
    card = HistoryRuneCard(_rune(), verdict)
    assert "RAGE" in card._name.text()
    assert "+12" in card._name.text()
    assert card._verdict_btn.text() == "Vendre"


def test_keep(qapp):
    verdict = Verdict(decision="KEEP", score=9.1, source="test", reason="high")
    card = HistoryRuneCard(_rune(), verdict)
    assert card._verdict_btn.text() == "Garder"
