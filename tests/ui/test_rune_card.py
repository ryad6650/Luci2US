from models import Rune, SubStat
from ui.scan.rune_card import RuneCard, RuneCardStatus


def _rune() -> Rune:
    return Rune(
        set="Endurance", slot=1, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("ATQ", 22),
        prefix=None,
        substats=[
            SubStat("PV%", 6), SubStat("ATQ%", 6),
            SubStat("VIT", 6), SubStat("PRE", 6),
        ],
    )


def test_update_populates_fields(qapp):
    w = RuneCard(status=RuneCardStatus.KEEP)
    w.update_rune(_rune(), mana=65)
    assert "Endurance" in w._title.text()
    assert "ATQ +22" in w._main.text()
    assert w._mana._value_label.text() == "65"
    assert len(w._sub_labels) == 4
    assert "PV +6%" in w._sub_labels[0].text()


def test_status_switch(qapp):
    w = RuneCard(status=RuneCardStatus.KEEP)
    w.set_status(RuneCardStatus.POWERUP)
    assert w._status == RuneCardStatus.POWERUP
