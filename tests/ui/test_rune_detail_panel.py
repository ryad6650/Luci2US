from models import Rune, SubStat
from ui.runes.rune_detail_panel import RuneDetailPanel


def _r(**kw) -> Rune:
    defaults = dict(
        set="Violent", slot=2, stars=6, grade="Heroique", level=12,
        main_stat=SubStat(type="VIT", value=39, grind_value=0),
        prefix=None, substats=[
            SubStat(type="CC", value=9, grind_value=0),
            SubStat(type="VIT", value=6, grind_value=2),
        ],
        swex_efficiency=90.0, swex_max_efficiency=100.0, rune_id=1,
    )
    defaults.update(kw)
    return Rune(**defaults)


def _all_text(panel) -> str:
    """Recursively collect text from every QLabel in the panel for assertions."""
    from PySide6.QtWidgets import QLabel
    labels = panel.findChildren(QLabel)
    return " | ".join(lbl.text() for lbl in labels if lbl.text())


def test_panel_starts_with_placeholder(qapp):
    p = RuneDetailPanel()
    assert p._placeholder is not None
    assert "Cliquez" in p._placeholder.text()


def test_set_rune_updates_widget(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on="Lushen")
    text = _all_text(p)
    assert "Violent" in text
    assert "Slot 2" in text
    assert "Lushen" in text


def test_unequipped_shows_non_equipee(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    assert "Non équipée" in _all_text(p)


def test_level_chip_shows_value(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(level=15), equipped_on=None)
    assert "+15" in _all_text(p)


def test_efficiency_value_displayed(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    assert "90.0%" in _all_text(p)


def test_clear_returns_to_placeholder(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    p.clear()
    assert p._placeholder is not None
    assert "Cliquez" in p._placeholder.text()


def test_simulate_signal_emitted_from_cta(qapp):
    p = RuneDetailPanel()
    rune = _r()
    p.set_rune(rune, equipped_on=None)
    received = []
    p.simulate_clicked.connect(lambda r: received.append(r))
    p._on_cta()
    assert received and received[0] is rune
