from ui.monsters.monsters_page import MonstersPage


def test_monsters_page_instantiates(qapp):
    page = MonstersPage()
    assert page is not None


def test_monsters_page_has_internal_stack_with_2_views(qapp):
    page = MonstersPage()
    assert page._stack.count() == 2


def test_monsters_page_starts_on_list_view(qapp):
    page = MonstersPage()
    assert page._stack.currentIndex() == 0


def test_apply_profile_accepts_monster_list(qapp):
    from models import Monster
    page = MonstersPage()
    profile = {"monsters": [
        Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211),
    ]}
    page.apply_profile(profile, saved_at=0.0)
    assert len(page._list._rows) == 1


def test_apply_profile_empty_list_ok(qapp):
    page = MonstersPage()
    page.apply_profile({"monsters": []}, saved_at=0.0)
    assert len(page._list._rows) == 0


def test_click_on_monster_switches_to_detail(qapp):
    from models import Monster
    page = MonstersPage()
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211)
    page.apply_profile({"monsters": [mon]}, saved_at=0.0)
    page._list.monster_clicked.emit(mon)
    assert page._stack.currentIndex() == 1
    assert page._detail._monster is mon


def test_back_returns_to_list(qapp):
    from models import Monster
    page = MonstersPage()
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211)
    page.apply_profile({"monsters": [mon]}, saved_at=0.0)
    page._list.monster_clicked.emit(mon)
    assert page._stack.currentIndex() == 1
    page._detail.back_clicked.emit()
    assert page._stack.currentIndex() == 0
