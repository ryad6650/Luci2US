"""Onglet Filtres S2US - panneau liste + éditeur."""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QWidget,
)

from s2us_filter import S2USFilter, load_s2us_file
from s2us_writer import save_s2us_file
from ui.filtres.filter_editor import FilterEditor
from ui.filtres.filter_list_panel import FilterListPanel
from ui.filtres.rune_tester_modal import RuneTesterModal


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.json")


def _read_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


class FiltresPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._filters: list[S2USFilter] = []
        self._global_settings: dict = {}
        self._filter_file_path: str = ""

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._list_panel = FilterListPanel()
        self._editor = FilterEditor()
        root.addWidget(self._list_panel)
        root.addWidget(self._editor, 1)

        self._load_filters_from_config()
        self._list_panel.set_filters(self._filters)
        self._list_panel.filter_added.connect(self._on_filter_added)
        self._list_panel.filter_removed.connect(self._on_filter_removed)
        self._list_panel.filter_moved.connect(self._on_filter_moved)
        self._list_panel.filter_selected.connect(self._on_filter_selected)
        self._list_panel.import_requested.connect(self._on_import)
        self._list_panel.export_requested.connect(self._on_export)
        self._list_panel.test_requested.connect(self._on_test)
        self._editor.filter_saved.connect(self._on_editor_saved)

    def _load_filters_from_config(self) -> None:
        cfg = _read_config()
        path = cfg.get("s2us", {}).get("filter_file", "")
        if not path or not os.path.isfile(path):
            self._filters = []
            self._global_settings = {}
            return
        try:
            self._filters, self._global_settings = load_s2us_file(path)
            self._filter_file_path = path
        except (OSError, json.JSONDecodeError):
            self._filters = []
            self._global_settings = {}

    def _on_filter_added(self) -> None:
        new = S2USFilter(name="Nouveau filtre", enabled=True,
                         sub_requirements={}, min_values={})
        self._filters.append(new)
        self._list_panel.set_filters(self._filters)
        self._list_panel.select_index(len(self._filters) - 1)

    def _on_filter_removed(self, idx: int) -> None:
        if not (0 <= idx < len(self._filters)):
            return
        del self._filters[idx]
        self._list_panel.set_filters(self._filters)
        if self._filters:
            self._list_panel.select_index(min(idx, len(self._filters) - 1))

    def _on_filter_moved(self, src: int, dst: int) -> None:
        if not (0 <= src < len(self._filters)):
            return
        if not (0 <= dst < len(self._filters)):
            return
        item = self._filters.pop(src)
        self._filters.insert(dst, item)
        self._list_panel.set_filters(self._filters)
        self._list_panel.select_index(dst)

    def _on_filter_selected(self, idx: int) -> None:
        if 0 <= idx < len(self._filters):
            self._editor.load_filter(self._filters[idx])

    def _on_editor_saved(self, new_filter: S2USFilter) -> None:
        idx = self._list_panel.current_index()
        if idx < 0 or idx >= len(self._filters):
            return
        self._filters[idx] = new_filter
        self._list_panel.set_filters(self._filters)
        self._list_panel.select_index(idx)
        self._write_filters_to_config_path()

    def _write_filters_to_config_path(self) -> None:
        path = self._filter_file_path
        if not path:
            return
        try:
            save_s2us_file(path, self._filters, self._global_settings)
        except OSError:
            pass

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer un fichier .s2us", "",
            "Filtres S2US (*.s2us);;Tous les fichiers (*.*)",
        )
        if not path:
            return
        try:
            self._filters, self._global_settings = load_s2us_file(path)
            self._filter_file_path = path
        except (OSError, json.JSONDecodeError):
            return
        self._list_panel.set_filters(self._filters)

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter un fichier .s2us", self._filter_file_path or "",
            "Filtres S2US (*.s2us);;Tous les fichiers (*.*)",
        )
        if not path:
            return
        save_s2us_file(path, self._filters, self._global_settings)

    def _on_test(self) -> None:
        dlg = RuneTesterModal(filters=self._filters, parent=self)
        dlg.exec()
