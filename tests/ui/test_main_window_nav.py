from ui.main_window import MainWindow


def test_stack_has_7_pages(qapp):
    mw = MainWindow()
    assert mw._stack.count() == 7


def test_on_nav_maps_all_7_keys(qapp):
    mw = MainWindow()
    expected = {
        "scan":          0,
        "filters":       1,
        "runes":         2,
        "monsters":      3,
        "stats_history": 4,
        "profile":       5,
        "settings":      6,
    }
    for key, index in expected.items():
        mw._on_nav(key)
        assert mw._stack.currentIndex() == index, f"{key} -> {mw._stack.currentIndex()} expected {index}"


def test_on_nav_unknown_key_defaults_to_scan(qapp):
    mw = MainWindow()
    mw._on_nav("does-not-exist")
    assert mw._stack.currentIndex() == 0


def test_settings_index_is_settings_page(qapp):
    from ui.settings.settings_page import SettingsPage
    mw = MainWindow()
    mw._on_nav("settings")
    current = mw._stack.currentWidget()
    assert isinstance(current, SettingsPage)


def test_filters_index_is_filtres_page(qapp):
    from ui.filtres.filtres_page import FiltresPage
    mw = MainWindow()
    mw._on_nav("filters")
    assert isinstance(mw._stack.currentWidget(), FiltresPage)


def test_monsters_index_is_monsters_page(qapp):
    from ui.monsters.monsters_page import MonstersPage
    mw = MainWindow()
    mw._on_nav("monsters")
    assert isinstance(mw._stack.currentWidget(), MonstersPage)


def test_profile_loaded_signal_feeds_monsters_page(qapp):
    from models import Monster
    mw = MainWindow()
    profile = {
        "wizard_name": "Test", "level": 40,
        "runes": [], "monsters": [
            Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=1),
        ],
        "source": "manual",
    }
    mw.monsters_page.apply_profile(profile, 0.0)
    assert len(mw.monsters_page._list._rows) == 1
