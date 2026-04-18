"""Detail modal smoke tests — it loads a monster and switches tabs."""
from PySide6.QtWidgets import QLabel

from models import Monster, Rune, SubStat
from ui.monsters.monster_detail_modal import MonsterDetailModal


def _rune(slot: int, set_name: str = "Violent", main: str = "ATQ%", val: float = 63.0) -> Rune:
    return Rune(
        set=set_name, slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(type=main, value=val),
        prefix=None, substats=[], swex_efficiency=90.0,
    )


def _monster(runes: list | None = None) -> Monster:
    return Monster(
        name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211,
        equipped_runes=runes or [],
    )


def _text(modal) -> str:
    return " | ".join(lbl.text() for lbl in modal.findChildren(QLabel))


def test_modal_instantiates_without_parent(qapp):
    assert MonsterDetailModal() is not None


def test_load_populates_header(qapp):
    modal = MonsterDetailModal()
    mon = _monster()
    modal.load(
        monster=mon,
        runes=[None] * 6,
        rune_effs=[None] * 6,
        base_stats={}, total_stats={},
        skills=[], passive=None, analysis="",
    )
    text = _text(modal)
    assert "Lushen" in text
    assert "Vent" in text
    assert "lv40" in text


def test_load_with_runes_sets_average_efficiency(qapp):
    modal = MonsterDetailModal()
    runes = [_rune(i) for i in range(1, 7)]
    effs = [90.0] * 6
    modal.load(
        monster=_monster(runes=runes),
        runes=runes,
        rune_effs=effs,
        base_stats={}, total_stats={},
        skills=[], passive=None, analysis="",
    )
    assert modal._avg_eff == 90.0
    assert modal._equipped_count == 6
    assert "90.0%" in _text(modal)


def test_switching_tabs_changes_stacked_index(qapp):
    modal = MonsterDetailModal()
    modal.load(
        monster=_monster(),
        runes=[None] * 6, rune_effs=[None] * 6,
        base_stats={}, total_stats={},
        skills=[], passive=None, analysis="",
    )
    modal._set_tab("stats")
    assert modal._body.currentIndex() == 1
    modal._set_tab("skills")
    assert modal._body.currentIndex() == 2
    modal._set_tab("runes")
    assert modal._body.currentIndex() == 0


def test_close_button_triggers_reject(qapp):
    modal = MonsterDetailModal()
    modal.load(
        monster=_monster(),
        runes=[None] * 6, rune_effs=[None] * 6,
        base_stats={}, total_stats={},
        skills=[], passive=None, analysis="",
    )
    closed: list[int] = []
    modal.rejected.connect(lambda: closed.append(1))
    modal._close_btn.click()
    assert closed == [1]


def test_optimize_button_emits_monster(qapp):
    modal = MonsterDetailModal()
    mon = _monster()
    modal.load(
        monster=mon,
        runes=[None] * 6, rune_effs=[None] * 6,
        base_stats={}, total_stats={},
        skills=[], passive=None, analysis="",
    )
    seen = []
    modal.optimize_clicked.connect(seen.append)
    modal._opt_btn.click()
    assert seen == [mon]
