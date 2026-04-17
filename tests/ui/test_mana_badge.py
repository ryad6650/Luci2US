from ui.widgets.mana_badge import ManaBadge


def test_initial_value(qapp):
    w = ManaBadge()
    assert w._value_label.text() == "0"


def test_set_value(qapp):
    w = ManaBadge()
    w.set_value(65)
    assert w._value_label.text() == "65"
