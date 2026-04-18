from ui.widgets.multi_check_popup import MultiCheckPopup


def test_default_all_selected(qapp):
    w = MultiCheckPopup("Set", ["A", "B", "C"])
    assert w.selected() == {"A", "B", "C"}
    assert "Tous" in w.text()


def test_custom_default(qapp):
    w = MultiCheckPopup("Slot", ["1", "2", "3"], default=["1"])
    assert w.selected() == {"1"}
    assert "1" in w.text()


def test_set_selected_updates_label_and_emits(qapp):
    w = MultiCheckPopup("Set", ["A", "B", "C"])
    received: list[set] = []
    w.changed.connect(lambda s: received.append(s))
    w.set_selected(["A", "B"])
    assert w.selected() == {"A", "B"}
    assert received == [{"A", "B"}]
    assert "A" in w.text() and "B" in w.text()


def test_set_selected_no_change_no_emit(qapp):
    w = MultiCheckPopup("Set", ["A", "B"])
    received: list[set] = []
    w.changed.connect(lambda s: received.append(s))
    w.set_selected(["A", "B"])
    assert received == []


def test_label_summary_many(qapp):
    w = MultiCheckPopup("Set", ["A", "B", "C", "D"])
    w.set_selected(["A", "B", "C"], emit=False)
    assert "(+1)" in w.text()


def test_label_summary_empty(qapp):
    w = MultiCheckPopup("Set", ["A", "B"])
    w.set_selected([], emit=False)
    assert "Aucun" in w.text()


def test_reset_to_defaults(qapp):
    w = MultiCheckPopup("Set", ["A", "B", "C"])
    w.set_selected(["A"], emit=False)
    w.reset_to_defaults(emit=False)
    assert w.selected() == {"A", "B", "C"}


def test_toggle_checkbox_emits_changed(qapp):
    w = MultiCheckPopup("Set", ["A", "B"])
    w._build_popup()
    received: list[set] = []
    w.changed.connect(lambda s: received.append(s))
    w._checkboxes["B"].setChecked(False)
    assert received == [{"A"}]
    assert w.selected() == {"A"}


def test_unknown_values_ignored(qapp):
    w = MultiCheckPopup("Set", ["A", "B"])
    w.set_selected(["A", "Z"], emit=False)
    assert w.selected() == {"A"}
