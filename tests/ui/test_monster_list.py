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


def test_eff_moyenne_falls_back_when_swex_efficiency_missing(qapp):
    """Runes without swex_efficiency fall back to computed efficiency (non-zero)."""
    ml = MonsterList()
    r1 = _rune(1, 100.0)
    r2 = _rune(2, 80.0)
    r2.swex_efficiency = None
    mon = _monster("Lushen", runes=[r1, r2])
    ml.set_monsters([mon])
    row = ml._rows[0]
    # r1 contributes 100.0; r2 fallback yields a non-None float. Avg must be >0
    # and NOT equal to 100 (i.e. r2 participates in the average).
    assert row._eff_avg > 0.0
    assert row._eff_avg != 100.0


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


def test_filter_by_element(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("Lushen", element="Vent"),
        _monster("Laika", element="Feu"),
        _monster("Bella", element="Eau"),
    ])
    ml._element_combo.setCurrentText("Vent")
    assert len(ml._rows) == 1
    assert ml._rows[0]._monster.name == "Lushen"


def test_filter_by_min_stars(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("A", stars=4),
        _monster("B", stars=5),
        _monster("C", stars=6),
    ])
    ml._stars_combo.setCurrentText(">=6")
    assert len(ml._rows) == 1
    assert ml._rows[0]._monster.name == "C"


def test_filter_by_name_substring(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("Lushen"),
        _monster("Laika"),
        _monster("Lupine"),
    ])
    ml._name_search.setText("Lu")
    names = {r._monster.name for r in ml._rows}
    assert names == {"Lushen", "Lupine"}


def test_filter_all_element_shows_all(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("A", element="Vent"),
        _monster("B", element="Feu"),
    ])
    ml._element_combo.setCurrentText("Tous")
    assert len(ml._rows) == 2


def test_filters_combine(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("Laika", element="Feu", stars=6),
        _monster("Laika2", element="Feu", stars=5),
        _monster("Lushen", element="Vent", stars=6),
    ])
    ml._element_combo.setCurrentText("Feu")
    ml._stars_combo.setCurrentText(">=6")
    assert len(ml._rows) == 1
    assert ml._rows[0]._monster.name == "Laika"


def test_monster_icon_loaded_via_monster_icons(qapp, monkeypatch, tmp_path):
    from PySide6.QtGui import QPixmap
    import monster_icons
    called_with: list[int] = []

    def fake_get_icon(uid: int):
        called_with.append(uid)
        p = QPixmap(1, 1)
        p.fill()
        path = tmp_path / f"{uid}.png"
        p.save(str(path))
        return path

    monkeypatch.setattr(monster_icons, "get_monster_icon", fake_get_icon)

    ml = MonsterList()
    mon = _monster("Lushen")
    mon.unit_master_id = 11211
    ml.set_monsters([mon])
    assert 11211 in called_with


def test_refresh_icons_button_exists(qapp):
    from PySide6.QtWidgets import QPushButton
    ml = MonsterList()
    btns = [b for b in ml.findChildren(QPushButton) if "Refresh" in b.text() or "icones" in b.text().lower()]
    assert len(btns) >= 1
