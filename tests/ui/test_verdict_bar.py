from ui.scan.verdict_bar import VerdictBar, VerdictKind


def test_defaults(qapp):
    w = VerdictBar()
    assert w._badge.text() == "KEEP"
    assert "Score" in w._score_label.text()


def test_update(qapp):
    w = VerdictBar()
    w.update_verdict(
        kind=VerdictKind.POWERUP,
        score=184,
        swop=(84.1, 118.6),
        s2us=(108.2, 152.0),
    )
    assert w._badge.text() == "PWR-UP"
    assert "184" in w._score_label.text()
    assert "84.1" in w._swop_label.text()
    assert "108.2" in w._s2us_label.text()
