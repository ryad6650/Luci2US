from ui.main_window import MainWindow


def test_stack_has_7_pages(qapp):
    mw = MainWindow()
    assert mw._stack.count() == 7


def test_on_nav_maps_all_7_keys(qapp):
    mw = MainWindow()
    expected = {
        "scan":          0,
        "swlens":        1,
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


def test_swlens_index_is_swlens_settings_page(qapp):
    from ui.swlens_settings.swlens_settings_page import SwlensSettingsPage
    mw = MainWindow()
    mw._on_nav("swlens")
    assert isinstance(mw._stack.currentWidget(), SwlensSettingsPage)


def test_monsters_index_is_monsters_page(qapp):
    from ui.monsters.monsters_page import MonstersPage
    mw = MainWindow()
    mw._on_nav("monsters")
    assert isinstance(mw._stack.currentWidget(), MonstersPage)


def test_runes_index_is_runes_page(qapp):
    from ui.runes.runes_page import RunesPage
    mw = MainWindow()
    mw._on_nav("runes")
    assert isinstance(mw._stack.currentWidget(), RunesPage)


def test_stats_history_index_is_stats_history_page(qapp):
    from ui.stats_history.stats_history_page import StatsHistoryPage
    mw = MainWindow()
    mw._on_nav("stats_history")
    current = mw._stack.currentWidget()
    assert isinstance(current, StatsHistoryPage)


def test_profile_loaded_signal_feeds_runes_page(qapp):
    from models import Monster, Rune, SubStat
    mw = MainWindow()
    r = Rune(
        set="Violent", slot=2, stars=6, grade="Heroique", level=12,
        main_stat=SubStat(type="VIT", value=39),
        prefix=None, substats=[], swex_efficiency=90.0,
        swex_max_efficiency=100.0, rune_id=1,
    )
    profile = {
        "wizard_name": "Test", "level": 40,
        "runes": [r], "monsters": [
            Monster(name="Lushen", element="Vent", stars=6, level=40,
                    unit_master_id=1, equipped_runes=[r]),
        ],
        "source": "manual",
    }
    mw.runes_page.apply_profile(profile, 0.0)
    assert len(mw.runes_page._grid._runes) == 1
    assert mw.runes_page._equipped_index.get(1) == "Lushen"


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


def test_profile_import_flows_to_profile_and_monsters(qapp, monkeypatch, tmp_path):
    import json

    mw = MainWindow()

    payload = {
        "wizard_info": {"wizard_name": "Lucius", "wizard_level": 42},
        "unit_list": [
            {"unit_master_id": 11211, "attribute": 3, "class": 6, "unit_level": 40, "runes": []},
        ],
        "runes": [],
    }
    fixture = tmp_path / "lucius.json"
    fixture.write_text(json.dumps(payload), encoding="utf-8")

    from ui import main_window as main_window_module
    monkeypatch.setattr(main_window_module, "save_profile_payload", lambda _p: None)

    mw.profile_page.import_requested.emit(str(fixture))

    assert mw.profile_page._name.text() == "Lucius"
    assert mw.profile_page._cell_level._value.text() == "42"
    assert mw.profile_page._cell_monsters._value.text() == "1"
    assert len(mw.monsters_page._list._rows) == 1
