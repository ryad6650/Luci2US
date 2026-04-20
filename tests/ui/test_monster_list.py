"""Grid card + table row presentation tests."""
from PySide6.QtWidgets import QLabel

from models import Monster, Rune, SubStat
from ui.monsters.monster_card import MonsterCard, MonsterTableRow


def _rune(slot: int, eff: float = 100.0) -> Rune:
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(type="ATQ%", value=63.0),
        prefix=None, substats=[], swex_efficiency=eff,
    )


def _monster(name: str = "Lushen", element: str = "Vent", stars: int = 6, level: int = 40) -> Monster:
    return Monster(name=name, element=element, stars=stars, level=level,
                   unit_master_id=11211, equipped_runes=[])


def _label_texts(w) -> str:
    return " | ".join(lbl.text() for lbl in w.findChildren(QLabel))


def test_card_shows_name_element_label(qapp):
    card = MonsterCard(_monster("Lushen", element="Vent"), eff_avg=0.0, equipped_count=0)
    text = _label_texts(card)
    assert "Lushen" in text
    assert "Vent" in text


def test_card_shows_eff_value_when_equipped(qapp):
    card = MonsterCard(_monster("Bella"), eff_avg=87.3, equipped_count=4)
    text = _label_texts(card)
    assert "87.3%" in text


def test_card_shows_dash_when_not_equipped(qapp):
    card = MonsterCard(_monster("Bare"), eff_avg=0.0, equipped_count=0)
    text = _label_texts(card)
    assert "—" in text


def test_card_emits_click_signal(qapp):
    mon = _monster("Lushen")
    card = MonsterCard(mon, eff_avg=0.0, equipped_count=0)
    seen = []
    card.clicked.connect(seen.append)
    card.clicked.emit(mon)
    assert seen == [mon]


def test_card_selection_toggles_style(qapp):
    card = MonsterCard(_monster(), eff_avg=0.0, equipped_count=0)
    assert card._selected is False
    card.set_selected(True)
    assert card._selected is True


def test_table_row_shows_name_level_and_eff(qapp):
    row = MonsterTableRow(_monster("Lushen", level=40), eff_avg=90.0, equipped_count=6)
    text = _label_texts(row)
    assert "Lushen" in text
    assert "lv40" in text
    assert "90.0%" in text
