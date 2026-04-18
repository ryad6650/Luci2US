from models import Monster, Rune, SubStat
from ui.monsters.monster_list import MonsterList


def _rune(slot: int, eff: float = 100.0) -> Rune:
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legend", level=12,
        main_stat=SubStat(type="ATQ%", value=63.0),
        prefix=None, substats=[],
        swex_efficiency=eff,
    )


def _monster(name: str, element: str = "Vent", stars: int = 6, level: int = 40,
             runes: list | None = None) -> Monster:
    return Monster(name=name, element=element, stars=stars, level=level,
                   unit_master_id=1, equipped_runes=runes or [])


def test_list_renders_one_row_per_monster(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("Lushen"), _monster("Bella"), _monster("Khmun")])
    assert len(ml._rows) == 3


def test_row_displays_name_stars_level_element(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("Lushen", element="Vent", stars=6, level=40)])
    row = ml._rows[0]
    texts = [lbl.text() for lbl in row.findChildren(__import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel)]
    joined = " | ".join(texts)
    assert "Lushen" in joined
    assert "6" in joined  # stars
    assert "40" in joined  # level
    assert "Vent" in joined


def test_eff_moyenne_computed_from_equipped_runes(qapp):
    ml = MonsterList()
    mon = _monster("Lushen", runes=[_rune(1, 100.0), _rune(2, 80.0), _rune(3, 120.0)])
    ml.set_monsters([mon])
    row = ml._rows[0]
    assert abs(row._eff_avg - 100.0) < 0.01


def test_eff_moyenne_ignores_missing_swex_efficiency(qapp):
    ml = MonsterList()
    r1 = _rune(1, 100.0)
    r2 = _rune(2, 80.0)
    r2.swex_efficiency = None
    mon = _monster("Lushen", runes=[r1, r2])
    ml.set_monsters([mon])
    row = ml._rows[0]
    assert abs(row._eff_avg - 100.0) < 0.01


def test_eff_moyenne_zero_when_no_runes(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("Bare", runes=[])])
    assert ml._rows[0]._eff_avg == 0.0


def test_set_monsters_clears_previous_rows(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("A"), _monster("B")])
    assert len(ml._rows) == 2
    ml.set_monsters([_monster("C")])
    assert len(ml._rows) == 1
