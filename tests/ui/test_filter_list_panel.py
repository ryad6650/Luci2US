import pytest

from PySide6.QtWidgets import QPushButton, QTreeWidget

from s2us_filter import S2USFilter
from ui.filtres.filter_list_panel import FilterListPanel


def _mk(name: str, enabled: bool = True) -> S2USFilter:
    return S2USFilter(name=name, enabled=enabled,
                      sub_requirements={}, min_values={})


def test_panel_instantiates(qapp):
    p = FilterListPanel()
    assert p is not None


def test_panel_has_title(qapp):
    from PySide6.QtWidgets import QLabel
    p = FilterListPanel()
    labels = [l.text() for l in p.findChildren(QLabel)]
    assert any("Filtres" in t for t in labels)


def test_panel_has_round_buttons_plus_minus_up_down(qapp):
    p = FilterListPanel()
    buttons = [b.text() for b in p.findChildren(QPushButton)]
    assert "+" in buttons
    assert "\u2212" in buttons or "-" in buttons
    assert "\u25B2" in buttons
    assert "\u25BC" in buttons


def test_panel_has_rect_buttons_import_export_test(qapp):
    p = FilterListPanel()
    buttons = [b.text() for b in p.findChildren(QPushButton)]
    assert "Importer" in buttons
    assert "Exporter" in buttons
    assert "Test" in buttons


def test_set_filters_populates_tree(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B"), _mk("C")])
    tree = p._tree
    assert isinstance(tree, QTreeWidget)
    assert tree.topLevelItemCount() >= 1
    top = tree.topLevelItem(0)
    assert top.childCount() == 3
    assert [top.child(i).text(0) for i in range(3)] == ["A", "B", "C"]


def test_select_index_emits_filter_selected(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    received: list[int] = []
    p.filter_selected.connect(received.append)
    p.select_index(1)
    assert 1 in received


def test_plus_button_emits_filter_added(qapp):
    p = FilterListPanel()
    received: list[bool] = []
    p.filter_added.connect(lambda: received.append(True))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "+")
    btn.click()
    assert received == [True]


def test_minus_button_emits_filter_removed_with_index(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    p.select_index(1)
    received: list[int] = []
    p.filter_removed.connect(received.append)
    btn = next(b for b in p.findChildren(QPushButton)
               if b.text() in ("\u2212", "-"))
    btn.click()
    assert received == [1]


def test_up_button_emits_filter_moved_up(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B"), _mk("C")])
    p.select_index(2)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25B2")
    btn.click()
    assert received == [(2, 1)]


def test_down_button_emits_filter_moved_down(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B"), _mk("C")])
    p.select_index(0)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25BC")
    btn.click()
    assert received == [(0, 1)]


def test_up_button_noop_at_top(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    p.select_index(0)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25B2")
    btn.click()
    assert received == []


def test_down_button_noop_at_bottom(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    p.select_index(1)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25BC")
    btn.click()
    assert received == []


def test_disabled_filter_still_listed(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A", enabled=True), _mk("B", enabled=False)])
    top = p._tree.topLevelItem(0)
    txt = top.child(1).text(0)
    assert "B" in txt
