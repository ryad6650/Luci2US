from models import Rune, SubStat
from ui.runes.rune_card_widget import RuneCardWidget


def _r(level: int = 12, grade: str = "Heroique", locked: bool = False) -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade=grade, level=level,
        main_stat=SubStat(type="VIT", value=39, grind_value=0),
        prefix=None,
        substats=[
            SubStat(type="CC", value=9, grind_value=0),
            SubStat(type="VIT", value=6, grind_value=2),
            SubStat(type="ATQ%", value=11, grind_value=0),
        ],
        swex_efficiency=92.0, swex_max_efficiency=100.0,
        rune_id=1,
    )


def test_card_instantiates(qapp):
    c = RuneCardWidget(_r())
    assert c is not None
    assert c.is_locked is False


def test_card_starts_locked(qapp):
    c = RuneCardWidget(_r(), locked=True)
    assert c.is_locked is True
    assert c._btn_lock.text() == "Verrouillée"


def test_edit_button_disabled(qapp):
    c = RuneCardWidget(_r())
    assert c._btn_edit.isEnabled() is False


def test_upgrade_emits_signal(qapp):
    c = RuneCardWidget(_r())
    received = []
    c.upgrade_clicked.connect(lambda r: received.append(r))
    c._btn_upgrade.click()
    assert received and received[0] is c.rune


def test_lock_toggle_emits_and_flips_state(qapp):
    c = RuneCardWidget(_r())
    received = []
    c.lock_toggled.connect(lambda r: received.append(r))
    c._btn_lock.click()
    assert received
    assert c.is_locked is True
    c._btn_lock.click()
    assert c.is_locked is False


def test_set_locked_updates_label(qapp):
    c = RuneCardWidget(_r())
    c.set_locked(True)
    assert c._btn_lock.text() == "Verrouillée"
    c.set_locked(False)
    assert c._btn_lock.text() == "Verrouiller"
