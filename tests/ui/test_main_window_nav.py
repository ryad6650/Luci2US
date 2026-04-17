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
