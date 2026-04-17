from ui.scan.counters_bar import CountersBar


def test_initial_values(qapp):
    w = CountersBar()
    assert w._total.text() == "0"
    assert w._kept.text() == "0"
    assert w._sold.text() == "0"
    assert w._time.text() == "00:00"


def test_update_counts(qapp):
    w = CountersBar()
    w.update_counts(total=10, kept=4, sold=5)
    assert w._total.text() == "10"
    assert w._kept.text() == "4"
    assert w._sold.text() == "5"


def test_update_time_formats_mmss(qapp):
    w = CountersBar()
    w.update_time(0)
    assert w._time.text() == "00:00"
    w.update_time(65)
    assert w._time.text() == "01:05"
    w.update_time(754)
    assert w._time.text() == "12:34"
