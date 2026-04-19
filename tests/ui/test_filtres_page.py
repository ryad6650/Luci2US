import json
from pathlib import Path

import pytest

from ui.filtres.filtres_page import FiltresPage


def test_filtres_page_instantiates(qapp):
    page = FiltresPage()
    assert page is not None


def test_filtres_page_has_list_and_editor(qapp):
    from ui.filtres.filter_editor import FilterEditor
    from ui.filtres.filter_list_panel import FilterListPanel
    page = FiltresPage()
    assert page.findChild(FilterListPanel) is not None
    assert page.findChild(FilterEditor) is not None


def test_filtres_page_loads_dossiers_from_config(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    f = S2USFilter(name="TestFilter", enabled=True,
                   sub_requirements={}, min_values={})
    s2us_path = tmp_path / "test.s2us"
    save_s2us_file(str(s2us_path), [f], {})

    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "Mon dossier", "path": str(s2us_path)}]},
    }), encoding="utf-8")

    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    assert len(page._dossiers) == 1
    assert page._dossiers[0].name == "Mon dossier"
    assert len(page._dossiers[0].filters) == 1
    assert page._dossiers[0].filters[0].name == "TestFilter"


def test_filtres_page_migrates_legacy_filter_file(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    f = S2USFilter(name="Legacy", enabled=True,
                   sub_requirements={}, min_values={})
    s2us_path = tmp_path / "legacy.s2us"
    save_s2us_file(str(s2us_path), [f], {})

    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"filter_file": str(s2us_path)},
    }), encoding="utf-8")

    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    assert len(page._dossiers) == 1
    assert page._dossiers[0].name == "legacy"
    assert page._dossiers[0].filters[0].name == "Legacy"


def test_filtres_page_handles_missing_config(qapp, tmp_path, monkeypatch):
    cfg_path = tmp_path / "missing.json"
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    assert page._dossiers == []


def test_page_adds_filter_to_selected_dossier(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter, load_s2us_file
    s2us_path = tmp_path / "d.s2us"
    save_s2us_file(str(s2us_path), [], {})
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(s2us_path)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    assert page._dossiers[0].filters == []
    page._list_panel.filter_added.emit(0)
    assert len(page._dossiers[0].filters) == 1
    assert page._dossiers[0].filters[0].name == "Nouveau filtre"
    # And the file was persisted.
    reloaded, _ = load_s2us_file(str(s2us_path))
    assert reloaded[0].name == "Nouveau filtre"


def test_page_removes_filter_on_panel_signal(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter, load_s2us_file
    filters = [
        S2USFilter(name="A", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="B", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="C", enabled=True, sub_requirements={}, min_values={}),
    ]
    s2us_path = tmp_path / "d.s2us"
    save_s2us_file(str(s2us_path), filters, {})
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(s2us_path)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    page._list_panel.filter_removed.emit(0, 1)
    assert [f.name for f in page._dossiers[0].filters] == ["A", "C"]
    reloaded, _ = load_s2us_file(str(s2us_path))
    assert [f.name for f in reloaded] == ["A", "C"]


def test_page_moves_filter_on_panel_signal(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    filters = [
        S2USFilter(name="A", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="B", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="C", enabled=True, sub_requirements={}, min_values={}),
    ]
    s2us_path = tmp_path / "d.s2us"
    save_s2us_file(str(s2us_path), filters, {})
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(s2us_path)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    page._list_panel.filter_moved.emit(0, 2, 0)
    assert [f.name for f in page._dossiers[0].filters] == ["C", "A", "B"]


def test_page_import_creates_new_dossier_and_persists(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    src = tmp_path / "new.s2us"
    save_s2us_file(str(src), [S2USFilter(name="Imported",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *a, **kw: (str(src), "")),
    )

    page = FiltresPage()
    assert page._dossiers == []
    page._list_panel.import_requested.emit()
    assert len(page._dossiers) == 1
    assert page._dossiers[0].path == str(src)
    assert page._dossiers[0].filters[0].name == "Imported"
    # Config now lists the dossier.
    cfg_data = json.loads(cfg.read_text(encoding="utf-8"))
    assert cfg_data["s2us"]["dossiers"][0]["path"] == str(src)


def test_page_import_creates_empty_file_if_new(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    target = tmp_path / "brand_new.s2us"
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *a, **kw: (str(target), "")),
    )

    page = FiltresPage()
    page._list_panel.import_requested.emit()
    assert target.exists()
    assert page._dossiers[0].filters == []


def test_page_export_writes_selected_dossier(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter, load_s2us_file
    src = tmp_path / "src.s2us"
    save_s2us_file(str(src), [S2USFilter(name="X",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(src)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    out = tmp_path / "out.s2us"
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *a, **kw: (str(out), "")),
    )

    page = FiltresPage()
    page._list_panel.select_dossier(0)
    page._list_panel.export_requested.emit()

    assert out.exists()
    reloaded, _ = load_s2us_file(str(out))
    assert reloaded[0].name == "X"


def test_page_propagates_editor_save_to_dossier_file(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter, load_s2us_file
    src = tmp_path / "s.s2us"
    save_s2us_file(str(src), [S2USFilter(name="Orig",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(src)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()
    page._list_panel.select_filter(0, 0)
    page._editor._name_edit.setText("Renamed")
    page._editor.filter_saved.emit(page._editor.current_filter())

    assert page._dossiers[0].filters[0].name == "Renamed"
    reloaded, _ = load_s2us_file(str(src))
    assert reloaded[0].name == "Renamed"


def test_page_dossier_rename_persists_to_config(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    src = tmp_path / "d.s2us"
    save_s2us_file(str(src), [], {})
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(src)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()
    page._list_panel.dossier_renamed.emit(0, "PvP")
    assert page._dossiers[0].name == "PvP"
    cfg_data = json.loads(cfg.read_text(encoding="utf-8"))
    assert cfg_data["s2us"]["dossiers"][0]["name"] == "PvP"


def test_page_dossier_remove_keeps_file_on_disk(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    src = tmp_path / "d.s2us"
    save_s2us_file(str(src), [], {})
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({
        "s2us": {"dossiers": [{"name": "D", "path": str(src)}]},
    }), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()
    page._list_panel.dossier_removed.emit(0)
    assert page._dossiers == []
    assert src.exists()
    cfg_data = json.loads(cfg.read_text(encoding="utf-8"))
    assert cfg_data["s2us"]["dossiers"] == []


def test_page_test_opens_rune_tester_modal(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()

    called = {"open": 0}

    class _StubDialog:
        def __init__(self, *a, **kw):
            called["open"] += 1

        def exec(self):
            return 0

    monkeypatch.setattr(
        "ui.filtres.filtres_page.RuneTesterModal", _StubDialog,
    )
    page._list_panel.test_requested.emit()
    assert called["open"] == 1
