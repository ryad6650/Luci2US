from ui.runes.rune_filter_bar import RuneFilterBar
from models import SETS_FR


def test_filter_bar_instantiates(qapp):
    w = RuneFilterBar()
    assert w is not None


def test_defaults(qapp):
    w = RuneFilterBar()
    assert w.selected_sets() == set(SETS_FR)
    assert w.selected_slots() == {1, 2, 3, 4, 5, 6}
    assert w.selected_stars() == {5, 6}
    assert w.selected_grades() == {"Magique", "Rare", "Heroique", "Legendaire"}
    assert w.focus_stat() is None
    assert w.score_mode() == "Eff"
    assert w.score_threshold() == 0


def test_changed_emits_on_slider(qapp):
    w = RuneFilterBar()
    received = []
    w.changed.connect(lambda: received.append(True))
    w._score_slider.setValue(50)
    assert received
    assert w.score_threshold() == 50


def test_changed_emits_on_star(qapp):
    w = RuneFilterBar()
    received = []
    w.changed.connect(lambda: received.append(True))
    w._star5.setChecked(False)
    assert received
    assert w.selected_stars() == {6}


def test_focus_stat_returns_none_for_aucun(qapp):
    w = RuneFilterBar()
    w._focus.setCurrentIndex(0)
    assert w.focus_stat() is None


def test_focus_stat_returns_stat(qapp):
    w = RuneFilterBar()
    w._focus.setCurrentText("VIT")
    assert w.focus_stat() == "VIT"


def test_reset_to_defaults(qapp):
    w = RuneFilterBar()
    w._star5.setChecked(False)
    w._score_slider.setValue(80)
    w._focus.setCurrentText("VIT")
    w.reset_to_defaults()
    assert w.selected_stars() == {5, 6}
    assert w.score_threshold() == 0
    assert w.focus_stat() is None


def test_reset_to_defaults_emits_single_changed(qapp):
    w = RuneFilterBar()
    w._score_slider.setValue(80)
    received = []
    w.changed.connect(lambda: received.append(True))
    w.reset_to_defaults()
    assert len(received) == 1
