from models import Rune, SubStat
from ui.scan.rune_details_card import RuneDetailsCard


def _mk_rune() -> Rune:
    return Rune(
        set="Rage", slot=2, stars=6, grade="Heroic", level=12,
        main_stat=SubStat(type="CC", value=23),
        prefix=None,
        substats=[
            SubStat(type="PV%",  value=10, grind_value=0.0),
            SubStat(type="ATQ%", value=10, grind_value=0.0),
            SubStat(type="VIT",  value=9,  grind_value=0.0),
            SubStat(type="CC",   value=9,  grind_value=0.0),
        ],
    )


def test_empty_state(qapp):
    w = RuneDetailsCard()
    assert w._title.text() == ""
    assert w._empty_hint.isHidden() is False


def test_populate(qapp):
    w = RuneDetailsCard()
    w.show()
    w.set_rune(_mk_rune())
    assert "RAGE RUNE" in w._title.text()
    assert "+12" in w._title.text()
    assert "6" in w._type_line.text()
    assert "HEROIC" in w._type_line.text().upper()
    assert "CRIT" in w._main_stat.text().upper() or "TX CRIT" in w._main_stat.text()
    assert "+23" in w._main_stat.text()
    assert all(lbl.isHidden() is False for lbl in w._sub_rows[:4])
