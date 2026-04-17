import pytest
from ui.widgets.tag_badge import TagBadge, TagKind


@pytest.mark.parametrize("kind,expected", [
    (TagKind.KEEP, "KEEP"),
    (TagKind.SELL, "SELL"),
    (TagKind.POWERUP, "PWR"),
])
def test_label_text(qapp, kind, expected):
    w = TagBadge(kind)
    assert w.text() == expected


def test_change_kind(qapp):
    w = TagBadge(TagKind.KEEP)
    w.set_kind(TagKind.SELL)
    assert w.text() == "SELL"
