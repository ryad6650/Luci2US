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


def test_panel_starts_with_placeholder(qapp):
    p = RuneDetailPanel()
    assert "Cliquez" in p._placeholder.text()


def test_set_rune_updates_widget(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on="Lushen")
    texts = [p._lay.itemAt(i).widget().text() for i in range(p._lay.count())
             if p._lay.itemAt(i).widget() is not None and hasattr(p._lay.itemAt(i).widget(), "text")]
    joined = " | ".join(texts)
    assert "Violent" in joined
    assert "Slot 2" in joined
    assert "Lushen" in joined


def test_unequipped_shows_inventaire(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    texts = [p._lay.itemAt(i).widget().text() for i in range(p._lay.count())
             if p._lay.itemAt(i).widget() is not None and hasattr(p._lay.itemAt(i).widget(), "text")]
    joined = " | ".join(texts)
    assert "Inventaire" in joined


def test_grind_displayed(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    texts = [p._lay.itemAt(i).widget().text() for i in range(p._lay.count())
             if p._lay.itemAt(i).widget() is not None and hasattr(p._lay.itemAt(i).widget(), "text")]
    joined = " | ".join(texts)
    assert "(+2)" in joined


def test_clear_returns_to_placeholder(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    p.clear()
    assert "Cliquez" in p._placeholder.text()


def test_eff_max_displayed(qapp):
    p = RuneDetailPanel()
    p.set_rune(_r(), equipped_on=None)
    texts = [p._lay.itemAt(i).widget().text() for i in range(p._lay.count())
             if p._lay.itemAt(i).widget() is not None and hasattr(p._lay.itemAt(i).widget(), "text")]
    joined = " | ".join(texts)
    assert "Eff" in joined and "Max" in joined
