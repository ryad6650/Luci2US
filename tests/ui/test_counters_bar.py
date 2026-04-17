from ui.scan.counters_bar import CountersBar


def test_initial_all_zero(qapp):
    w = CountersBar()
    assert w._total.text() == "0"
    assert w._kept.text() == "0"
    assert w._sold.text() == "0"
    assert w._pwr.text() == "0"


def test_update(qapp):
    w = CountersBar()
    w.update_counts(total=10, kept=4, sold=5, pwrup=1)
    assert w._total.text() == "10"
    assert w._kept.text() == "4"
    assert w._sold.text() == "5"
    assert w._pwr.text() == "1"
