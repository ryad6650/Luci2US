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
    assert w.filter_equipped() == "all"


def test_changed_emits_on_level_slider(qapp):
    w = RuneFilterBar()
    received = []
    w.changed.connect(lambda: received.append(True))
    w._level_slider.setValue(12)
    assert received
    assert w.filter_level_min() == 12


def test_slot_pill_toggles_filter(qapp):
    w = RuneFilterBar()
    w._slot_btns[3].click()
    assert w.filter_slot() == 3
    w._slot_btns[3].click()
    assert w.filter_slot() is None


def test_stars_pill_toggles_filter(qapp):
    w = RuneFilterBar()
    w._grade_btns[6].click()
    assert w.filter_stars() == 6
    w._grade_btns[6].click()
    assert w.filter_stars() is None


def test_rarity_pill_selects_legendaire(qapp):
    w = RuneFilterBar()
    w._rarity_btns["Legendaire"].click()
    assert w.filter_rarity() == "Legendaire"


def test_equipped_pill_selects_free(qapp):
    w = RuneFilterBar()
    w._equipped_btns["free"].click()
    assert w.filter_equipped() == "free"


def test_populate_sets_lists_options(qapp):
    w = RuneFilterBar()
    w.populate_sets(["Violent", "Rapide"])
    # 3 = "Tous les sets" + 2 supplied
    assert w._set_combo.count() == 3


def test_reset_to_defaults_emits_single_changed(qapp):
    w = RuneFilterBar()
    w._level_slider.setValue(12)
    w._rarity_btns["Legendaire"].click()
    received = []
    w.changed.connect(lambda: received.append(True))
    w.reset_to_defaults()
    assert len(received) == 1
    assert w.filter_level_min() == 0
    assert w.filter_rarity() is None
