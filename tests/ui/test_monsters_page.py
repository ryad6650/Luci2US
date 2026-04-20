from models import Monster, Rune, SubStat
from ui.monsters.monsters_page import MonstersPage


def _rune(slot: int, eff: float | None = 100.0) -> Rune:
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(type="ATQ%", value=63.0),
        prefix=None, substats=[], swex_efficiency=eff,
    )


def _monster(
    name: str = "Lushen", element: str = "Vent", stars: int = 6, level: int = 40,
    uid: int = 11211, runes: list | None = None,
) -> Monster:
    return Monster(
        name=name, element=element, stars=stars, level=level,
        unit_master_id=uid, equipped_runes=runes or [],
    )


def test_monsters_page_instantiates(qapp):
    assert MonstersPage() is not None


def test_apply_profile_renders_cards_by_default(qapp):
    page = MonstersPage()
    page.apply_profile(
        {"monsters": [_monster("Lushen"), _monster("Bella"), _monster("Khmun")]},
        saved_at=0.0,
    )
    # Default view is grid -> proxy exposes grid cards
    assert len(page._list._rows) == 3


def test_apply_profile_empty_list_ok(qapp):
    page = MonstersPage()
    page.apply_profile({"monsters": []}, saved_at=0.0)
    assert len(page._list._rows) == 0


def test_default_sort_is_efficiency_desc(qapp):
    """Monsters with higher average efficiency come first."""
    page = MonstersPage()
    high = _monster("High", runes=[_rune(1, 120.0), _rune(2, 120.0)])
    low = _monster("Low",  runes=[_rune(1, 50.0),  _rune(2, 50.0)])
    page.apply_profile({"monsters": [low, high]}, saved_at=0.0)
    names = [c.monster.name for c in page._list._rows]
    assert names == ["High", "Low"]


def test_search_filters_by_name(qapp):
    page = MonstersPage()
    page.apply_profile(
        {"monsters": [_monster("Lushen"), _monster("Laika"), _monster("Bella")]},
        saved_at=0.0,
    )
    page._search_input.setText("lu")
    # Debounced by 150ms — trigger the filter manually.
    page._search_timer.stop()
    page._refilter()
    names = {c.monster.name for c in page._list._rows}
    assert names == {"Lushen"}


def test_element_chip_filters(qapp):
    page = MonstersPage()
    page.apply_profile(
        {"monsters": [
            _monster("A", element="Vent"),
            _monster("B", element="Feu"),
            _monster("C", element="Eau"),
        ]},
        saved_at=0.0,
    )
    page._toggle_element("fire")
    assert [c.monster.name for c in page._list._rows] == ["B"]
    page._toggle_element("fire")       # re-click deselects
    assert len(page._list._rows) == 3


def test_equipped_status_filter(qapp):
    page = MonstersPage()
    runed = _monster("Runed", runes=[_rune(1)])
    bare  = _monster("Bare", runes=[])
    page.apply_profile({"monsters": [runed, bare]}, saved_at=0.0)

    page._set_equipped("equipped")
    assert [c.monster.name for c in page._list._rows] == ["Runed"]
    page._set_equipped("empty")
    assert [c.monster.name for c in page._list._rows] == ["Bare"]
    page._set_equipped("all")
    assert len(page._list._rows) == 2


def test_view_toggle_switches_to_table_rows(qapp):
    page = MonstersPage()
    page.apply_profile(
        {"monsters": [_monster("A"), _monster("B")]},
        saved_at=0.0,
    )
    assert page._view == "grid"
    page._set_view("table")
    assert page._view == "table"
    # Proxy now exposes table rows
    assert len(page._list._rows) == 2


def test_clicking_card_updates_side_panel(qapp):
    page = MonstersPage()
    a, b = _monster("A"), _monster("B")
    page.apply_profile({"monsters": [a, b]}, saved_at=0.0)
    # First card auto-selected after refilter — click the other one.
    other = next(c for c in page._list._rows if c.monster is b)
    other.clicked.emit(other.monster)
    assert page._selected is b


def test_side_panel_cta_opens_modal(qapp):
    page = MonstersPage()
    mon = _monster("Lushen", runes=[_rune(1, 90.0)])
    page.apply_profile({"monsters": [mon]}, saved_at=0.0)
    # Trigger the side panel's "Voir le détail complet" programmatically.
    page._open_detail(mon)
    assert page._detail_modal is not None
    assert page._detail_modal._monster is mon
    # Clean up — dialog is modal, close it before pytest tears down.
    page._detail_modal.reject()
