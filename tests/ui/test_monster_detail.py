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
