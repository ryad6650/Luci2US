from ui.runes.rune_filter_bar import RuneFilterBar


def test_filter_bar_instantiates(qapp):
    w = RuneFilterBar()
    assert w is not None


def test_defaults(qapp):
    w = RuneFilterBar()
    assert w.filter_set() is None
    assert w.filter_slot() is None
    assert w.filter_stars() is None
    assert w.filter_rarity() is None
    assert w.filter_level_min() == 0
    assert w.filter_main_stat() is None
    assert w.search_text() == ""
    assert w.sort_key() == "score"


def test_slot_pill_toggles(qapp):
    w = RuneFilterBar()
    w._slot_btns[3].click()
    assert w.filter_slot() == 3
    w._slot_btns[3].click()
    assert w.filter_slot() is None


def test_rarity_combo_sets_filter(qapp):
    w = RuneFilterBar()
    received = []
    w.changed.connect(lambda: received.append(True))
    idx = w._rarity_combo.findData("Legendaire")
    w._rarity_combo.setCurrentIndex(idx)
    assert w.filter_rarity() == "Legendaire"
    assert received


def test_stars_combo_sets_filter(qapp):
    w = RuneFilterBar()
    idx = w._stars_combo.findData(6)
    w._stars_combo.setCurrentIndex(idx)
    assert w.filter_stars() == 6


def test_level_combo_sets_filter(qapp):
    w = RuneFilterBar()
    idx = w._level_combo.findData(12)
    w._level_combo.setCurrentIndex(idx)
    assert w.filter_level_min() == 12


def test_main_stat_combo_sets_filter(qapp):
    w = RuneFilterBar()
    idx = w._main_combo.findData("VIT")
    w._main_combo.setCurrentIndex(idx)
    assert w.filter_main_stat() == "VIT"


def test_search_text_updates_state(qapp):
    w = RuneFilterBar()
    w._search.setText("Violent")
    assert w.search_text() == "violent"


def test_sort_switches_to_level(qapp):
    w = RuneFilterBar()
    w._rb_level.setChecked(True)
    assert w.sort_key() == "level"
    w._rb_score.setChecked(True)
    assert w.sort_key() == "score"


def test_populate_sets_lists_options(qapp):
    w = RuneFilterBar()
    w.populate_sets(["Violent", "Rapide"])
    assert w._set_combo.count() == 3  # "Tous" + 2


def test_reset_to_defaults_emits_single_changed(qapp):
    w = RuneFilterBar()
    w._rarity_combo.setCurrentIndex(w._rarity_combo.findData("Legendaire"))
    w._slot_btns[2].click()
    received = []
    w.changed.connect(lambda: received.append(True))
    w.reset_to_defaults()
    assert len(received) == 1
    assert w.filter_rarity() is None
    assert w.filter_slot() is None
