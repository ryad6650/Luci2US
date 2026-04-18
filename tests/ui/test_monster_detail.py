from PySide6.QtWidgets import QLabel, QPushButton

from models import Monster, Rune, SubStat
from ui.monsters.monster_detail import MonsterDetail


def _monster(name: str = "Lushen", runes: list | None = None) -> Monster:
    return Monster(
        name=name, element="Vent", stars=6, level=40, unit_master_id=11211,
        equipped_runes=runes or [],
    )


def test_detail_instantiates(qapp):
    assert MonsterDetail() is not None


def test_detail_back_button_exists_and_emits_signal(qapp):
    d = MonsterDetail()
    received: list = []
    d.back_clicked.connect(lambda: received.append(1))
    btns = [b for b in d.findChildren(QPushButton) if "Retour" in b.text()]
    assert len(btns) == 1
    btns[0].click()
    assert received == [1]


def test_set_monster_fills_header(qapp):
    d = MonsterDetail()
    d.set_monster(_monster(name="Lushen"))
    texts = " | ".join(lbl.text() for lbl in d.findChildren(QLabel))
    assert "Lushen" in texts
    assert "Vent" in texts
    assert "40" in texts


def test_set_monster_none_shows_empty_state(qapp):
    d = MonsterDetail()
    d.set_monster(None)
    assert d is not None


def _rune(slot: int, set_name: str = "Violent", main: str = "ATQ%", val: float = 63.0) -> Rune:
    return Rune(
        set=set_name, slot=slot, stars=6, grade="Legend", level=12,
        main_stat=SubStat(type=main, value=val),
        prefix=None, substats=[],
    )


def test_detail_shows_6_slot_cards(qapp):
    d = MonsterDetail()
    runes = [_rune(i) for i in range(1, 7)]
    d.set_monster(_monster(runes=runes))
    assert len(d._slot_containers) == 6


def _slot_texts(wrap) -> str:
    return " | ".join(lbl.text() for lbl in wrap.findChildren(QLabel))


def test_empty_slot_shows_placeholder(qapp):
    d = MonsterDetail()
    runes = [_rune(1), _rune(3)]
    d.set_monster(_monster(runes=runes))
    assert len(d._slot_containers) == 6
    assert "Vide" in _slot_texts(d._slot_containers[1])
    assert "Vide" in _slot_texts(d._slot_containers[3])


def test_filled_slot_shows_set_and_main(qapp):
    d = MonsterDetail()
    runes = [_rune(1, set_name="Violent", main="ATQ%", val=63.0)]
    d.set_monster(_monster(runes=runes))
    content = _slot_texts(d._slot_containers[0])
    assert "Violent" in content
    assert "ATQ" in content
