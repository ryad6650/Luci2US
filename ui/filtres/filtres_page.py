"""Onglet Filtres S2US - panneau liste + éditeur multi-dossiers."""
from __future__ import annotations

import json
import os

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QWidget,
)

from s2us_filter import S2USFilter, load_s2us_file
from s2us_writer import save_s2us_file
from ui.filtres.dossier import Dossier
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


def _write_config(cfg: dict) -> None:
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


class FiltresPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._dossiers: list[Dossier] = []

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._list_panel = FilterListPanel()
        self._editor = FilterEditor()
        root.addWidget(self._list_panel)
        root.addWidget(self._editor, 1)

        self._load_dossiers_from_config()
        self._list_panel.set_dossiers(self._dossiers)
        self._list_panel.filter_added.connect(self._on_filter_added)
        self._list_panel.filter_removed.connect(self._on_filter_removed)
        self._list_panel.filter_moved.connect(self._on_filter_moved)
        self._list_panel.filter_selected.connect(self._on_filter_selected)
        self._list_panel.dossier_removed.connect(self._on_dossier_removed)
        self._list_panel.dossier_renamed.connect(self._on_dossier_renamed)
        self._list_panel.import_requested.connect(self._on_import)
        self._list_panel.export_requested.connect(self._on_export)
        self._list_panel.test_requested.connect(self._on_test)
        self._editor.filter_saved.connect(self._on_editor_saved)

    # ── Config persistence ─────────────────────────────────────
    def _load_dossiers_from_config(self) -> None:
        cfg = _read_config()
        s2us_cfg = cfg.get("s2us", {})
        entries = list(s2us_cfg.get("dossiers", []))

        # Backward-compat: legacy single filter_file → first dossier.
        legacy = s2us_cfg.get("filter_file")
        if legacy and not entries:
            entries = [{"name": _default_name(legacy), "path": legacy}]

        for entry in entries:
            path = entry.get("path", "")
            if not path or not os.path.isfile(path):
                continue
            try:
                filters, settings = load_s2us_file(path)
            except (OSError, json.JSONDecodeError):
                continue
            name = entry.get("name") or _default_name(path)
            self._dossiers.append(
                Dossier(name=name, path=path,
                        filters=filters, settings=settings)
            )

    def _persist_dossiers_to_config(self) -> None:
        cfg = _read_config()
        cfg.setdefault("s2us", {})
        cfg["s2us"]["dossiers"] = [
            {"name": d.name, "path": d.path} for d in self._dossiers
        ]
        cfg["s2us"].pop("filter_file", None)
        _write_config(cfg)

    def _save_dossier_file(self, didx: int) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        d = self._dossiers[didx]
        if not d.path:
            return
        try:
            save_s2us_file(d.path, d.filters, d.settings)
        except OSError:
            pass

    # ── Filter ops ─────────────────────────────────────────────
    def _on_filter_added(self, didx: int) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        new = S2USFilter(name="Nouveau filtre", enabled=True,
                         sub_requirements={}, min_values={})
        self._dossiers[didx].filters.append(new)
        new_idx = len(self._dossiers[didx].filters) - 1
        self._list_panel.set_dossiers(self._dossiers)
        self._list_panel.select_filter(didx, new_idx)
        self._save_dossier_file(didx)

    def _on_filter_removed(self, didx: int, fidx: int) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        filters = self._dossiers[didx].filters
        if not (0 <= fidx < len(filters)):
            return
        del filters[fidx]
        self._list_panel.set_dossiers(self._dossiers)
        if filters:
            self._list_panel.select_filter(didx, min(fidx, len(filters) - 1))
        self._save_dossier_file(didx)

    def _on_filter_moved(self, didx: int, src: int, dst: int) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        filters = self._dossiers[didx].filters
        if not (0 <= src < len(filters)) or not (0 <= dst < len(filters)):
            return
        item = filters.pop(src)
        filters.insert(dst, item)
        self._list_panel.set_dossiers(self._dossiers)
        self._list_panel.select_filter(didx, dst)
        self._save_dossier_file(didx)

    def _on_filter_selected(self, didx: int, fidx: int) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        filters = self._dossiers[didx].filters
        if 0 <= fidx < len(filters):
            self._editor.load_filter(filters[fidx])

    def _on_editor_saved(self, new_filter: S2USFilter) -> None:
        sel = self._list_panel.current_selection()
        if sel is None or sel[0] != "filter":
            return
        didx, fidx = int(sel[1]), int(sel[2])
        if not (0 <= didx < len(self._dossiers)):
            return
        filters = self._dossiers[didx].filters
        if not (0 <= fidx < len(filters)):
            return
        filters[fidx] = new_filter
        self._list_panel.set_dossiers(self._dossiers)
        self._list_panel.select_filter(didx, fidx)
        self._save_dossier_file(didx)

    # ── Dossier ops ────────────────────────────────────────────
    def _on_dossier_removed(self, didx: int) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        del self._dossiers[didx]
        self._list_panel.set_dossiers(self._dossiers)
        self._persist_dossiers_to_config()

    def _on_dossier_renamed(self, didx: int, new_name: str) -> None:
        if not (0 <= didx < len(self._dossiers)):
            return
        self._dossiers[didx].name = new_name
        self._persist_dossiers_to_config()

    # ── Import / Export / Test ─────────────────────────────────
    def _on_import(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Choisir ou créer un fichier .s2us", "",
            "Filtres S2US (*.s2us);;Tous les fichiers (*.*)",
        )
        if not path:
            return
        if os.path.isfile(path):
            try:
                filters, settings = load_s2us_file(path)
            except (OSError, json.JSONDecodeError):
                return
        else:
            filters, settings = [], {}
            try:
                save_s2us_file(path, filters, settings)
            except OSError:
                return
        d = Dossier(name=_default_name(path), path=path,
                    filters=filters, settings=settings)
        self._dossiers.append(d)
        self._list_panel.set_dossiers(self._dossiers)
        self._list_panel.select_dossier(len(self._dossiers) - 1)
        self._persist_dossiers_to_config()

    def _on_export(self) -> None:
        sel = self._list_panel.current_selection()
        if sel is None:
            return
        didx = int(sel[1])
        if not (0 <= didx < len(self._dossiers)):
            return
        d = self._dossiers[didx]
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le dossier vers un fichier .s2us",
            d.path or "",
            "Filtres S2US (*.s2us);;Tous les fichiers (*.*)",
        )
        if not path:
            return
        try:
            save_s2us_file(path, d.filters, d.settings)
        except OSError:
            pass

    def current_filters(self) -> list[S2USFilter]:
        """Tous les filtres de tous les dossiers à plat.

        Utilisé par la page Runes pour alimenter le modal RuneTesterModal
        quand l'utilisateur clique sur "Améliorer" depuis une rune-carte.
        """
        return [f for d in self._dossiers for f in d.filters]

    def _on_test(self) -> None:
        dlg = RuneTesterModal(filters=self.current_filters(), parent=self)
        dlg.exec()


def _default_name(path: str) -> str:
    base = os.path.basename(path)
    stem, _ = os.path.splitext(base)
    return stem or "Dossier"
