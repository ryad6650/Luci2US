from ui.widgets.state_indicator import StateIndicator


def test_default_label(qapp):
    w = StateIndicator()
    assert w._label.text().upper() == "INACTIF"


def test_set_active(qapp):
    w = StateIndicator()
    w.set_active(True)
    assert w._label.text().upper() == "ACTIF"
    assert w._active is True


def test_set_inactive(qapp):
    w = StateIndicator()
    w.set_active(True)
    w.set_active(False)
    assert w._active is False
