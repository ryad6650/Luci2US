import pytest

from PySide6.QtWidgets import QPushButton, QTreeWidget

from s2us_filter import S2USFilter
from ui.filtres.dossier import Dossier
from ui.filtres.filter_list_panel import FilterListPanel


def _mk(name: str, enabled: bool = True) -> S2USFilter:
    return S2USFilter(name=name, enabled=enabled,
                      sub_requirements={}, min_values={})


def _dossier(name: str, filters: list[S2USFilter]) -> Dossier:
    return Dossier(name=name, path=f"/tmp/{name}.s2us", filters=filters)


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


def test_set_dossiers_populates_tree(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B"), _mk("C")])])
    tree = p._tree
    assert isinstance(tree, QTreeWidget)
    assert tree.topLevelItemCount() == 1
    top = tree.topLevelItem(0)
    assert top.text(0) == "D1"
    assert top.childCount() == 3
    assert [top.child(i).text(0) for i in range(3)] == ["A", "B", "C"]


def test_set_dossiers_multiple_roots(qapp):
    p = FilterListPanel()
    p.set_dossiers([
        _dossier("D1", [_mk("A")]),
        _dossier("D2", [_mk("X"), _mk("Y")]),
    ])
    tree = p._tree
    assert tree.topLevelItemCount() == 2
    assert tree.topLevelItem(0).text(0) == "D1"
    assert tree.topLevelItem(1).text(0) == "D2"
    assert tree.topLevelItem(1).childCount() == 2


def test_select_filter_emits_filter_selected(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B")])])
    received: list[tuple[int, int]] = []
    p.filter_selected.connect(lambda d, f: received.append((d, f)))
    p.select_filter(0, 1)
    assert (0, 1) in received


def test_select_dossier_emits_dossier_selected(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A")])])
    received: list[int] = []
    p.dossier_selected.connect(received.append)
    p.select_dossier(0)
    assert received == [0]


def test_plus_button_emits_filter_added_with_dossier_idx(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A")])])
    p.select_dossier(0)
    received: list[int] = []
    p.filter_added.connect(received.append)
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "+")
    btn.click()
    assert received == [0]


def test_plus_button_noop_when_no_selection(qapp):
    p = FilterListPanel()
    p.set_dossiers([])
    received: list[int] = []
    p.filter_added.connect(received.append)
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "+")
    btn.click()
    assert received == []


def test_plus_button_uses_parent_dossier_when_filter_selected(qapp):
    p = FilterListPanel()
    p.set_dossiers([
        _dossier("D1", [_mk("A")]),
        _dossier("D2", [_mk("B")]),
    ])
    p.select_filter(1, 0)
    received: list[int] = []
    p.filter_added.connect(received.append)
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "+")
    btn.click()
    assert received == [1]


def test_minus_on_filter_emits_filter_removed(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B")])])
    p.select_filter(0, 1)
    received: list[tuple[int, int]] = []
    p.filter_removed.connect(lambda d, f: received.append((d, f)))
    btn = next(b for b in p.findChildren(QPushButton)
               if b.text() in ("\u2212", "-"))
    btn.click()
    assert received == [(0, 1)]


def test_minus_on_dossier_emits_dossier_removed(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A")])])
    p.select_dossier(0)
    received: list[int] = []
    p.dossier_removed.connect(received.append)
    btn = next(b for b in p.findChildren(QPushButton)
               if b.text() in ("\u2212", "-"))
    btn.click()
    assert received == [0]


def test_up_button_emits_filter_moved_up(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B"), _mk("C")])])
    p.select_filter(0, 2)
    received: list[tuple[int, int, int]] = []
    p.filter_moved.connect(lambda d, s, t: received.append((d, s, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25B2")
    btn.click()
    assert received == [(0, 2, 1)]


def test_down_button_emits_filter_moved_down(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B"), _mk("C")])])
    p.select_filter(0, 0)
    received: list[tuple[int, int, int]] = []
    p.filter_moved.connect(lambda d, s, t: received.append((d, s, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25BC")
    btn.click()
    assert received == [(0, 0, 1)]


def test_up_button_noop_at_top(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B")])])
    p.select_filter(0, 0)
    received: list[tuple] = []
    p.filter_moved.connect(lambda *args: received.append(args))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25B2")
    btn.click()
    assert received == []


def test_down_button_noop_at_bottom(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A"), _mk("B")])])
    p.select_filter(0, 1)
    received: list[tuple] = []
    p.filter_moved.connect(lambda *args: received.append(args))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25BC")
    btn.click()
    assert received == []


def test_disabled_filter_still_listed(qapp):
    p = FilterListPanel()
    p.set_dossiers([
        _dossier("D1", [_mk("A", enabled=True), _mk("B", enabled=False)]),
    ])
    top = p._tree.topLevelItem(0)
    txt = top.child(1).text(0)
    assert "B" in txt


def test_dossier_rename_emits_signal(qapp):
    from PySide6.QtCore import Qt
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A")])])
    received: list[tuple[int, str]] = []
    p.dossier_renamed.connect(lambda d, n: received.append((d, n)))
    top = p._tree.topLevelItem(0)
    top.setText(0, "Renommé")
    assert received == [(0, "Renommé")]


def test_current_selection_returns_tuple(qapp):
    p = FilterListPanel()
    p.set_dossiers([_dossier("D1", [_mk("A")])])
    p.select_filter(0, 0)
    sel = p.current_selection()
    assert sel is not None
    assert sel[0] == "filter"
    assert sel[1] == 0
    assert sel[2] == 0
