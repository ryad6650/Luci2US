"""QMainWindow shell: frameless Windows-style title bar + sidebar + content stack.

Scan, Profils, Parametres sont implementes; Filtres / Runes / Monstres /
Stats & Historique affichent un placeholder.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel,
)

import monster_icons
from profile_loader import invalidate_bestiary_cache, load_profile_from_dict
from profile_store import load_profile_payload, save_profile_payload
from ui import theme
from ui.controllers.scan_controller import ScanController
from ui.filtres.filtres_page import FiltresPage
from ui.monsters.monsters_page import MonstersPage
from ui.profile.profile_page import ProfilePage
from ui.runes.runes_page import RunesPage
from ui.settings.settings_page import SettingsPage
from ui.sidebar import Sidebar
from ui.scan.scan_page import ScanPage
from ui.widgets.background import BackgroundPane
from ui.widgets.title_bar import WinTitleBar


def _placeholder(text: str) -> QWidget:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:14px;")
    return lbl


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Luci2US")
        self.resize(1280, 900)
        self.setMinimumSize(1100, 720)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet(f"QMainWindow {{ background:{theme.D.BG}; }}")

        root = QWidget()
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        self._title_bar = WinTitleBar("Luci2US \u2014 Scan")
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.close_clicked.connect(self.close)
        self._title_bar.maximize_toggled.connect(self._toggle_max_restore)
        root_lay.addWidget(self._title_bar)

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.nav_changed.connect(self._on_nav)
        body_lay.addWidget(self._sidebar)

        content = QWidget()
        content_lay = QHBoxLayout(content)
        content_lay.setContentsMargins(0, 0, 0, 0)

        bg = BackgroundPane()
        bg_lay = QHBoxLayout(bg)
        bg_lay.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        self.scan_page = ScanPage()
        self.profile_page = ProfilePage()

        # Index 0 : Scan
        self._stack.addWidget(self.scan_page)
        # Index 1 : Filtres
        self.filtres_page = FiltresPage()
        self._stack.addWidget(self.filtres_page)
        # Index 2 : Runes
        self.runes_page = RunesPage()
        self._stack.addWidget(self.runes_page)
        # Index 3 : Monstres
        self.monsters_page = MonstersPage()
        self._stack.addWidget(self.monsters_page)
        # Index 4 : Stats & Historique (placeholder, Plan 4)
        self._stack.addWidget(_placeholder("Stats & Historique - a implementer"))
        # Index 5 : Profils
        self._stack.addWidget(self.profile_page)
        # Index 6 : Paramètres
        self.settings_page = SettingsPage()
        self._stack.addWidget(self.settings_page)

        bg_lay.addWidget(self._stack)

        content_lay.addWidget(bg)
        body_lay.addWidget(content, 1)
        root_lay.addWidget(body, 1)

        self.setCentralWidget(root)

        self.controller = ScanController(self)
        self.controller.rune_evaluated.connect(
            self.scan_page.on_rune,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.rune_upgraded.connect(
            self.scan_page.on_rune_upgraded,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.profile_loaded.connect(
            self.profile_page.apply_profile,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.profile_loaded.connect(
            self.monsters_page.apply_profile,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.profile_loaded.connect(
            self.runes_page.apply_profile,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.state_changed.connect(
            self.scan_page.set_active,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.state_changed.connect(
            self._sidebar.set_live,
            type=Qt.ConnectionType.QueuedConnection,
        )

        self.profile_page.import_requested.connect(self._on_profile_import)

        self._last_profile_payload: dict | None = None
        self._last_profile_saved_at: object = ""

        self._restore_cached_profile()
        self._maybe_fetch_bestiary()

    def _maybe_fetch_bestiary(self) -> None:
        """If bestiary.json is missing, fetch names in background and reapply."""
        if monster_icons.is_bestiary_available():
            return
        monster_icons.download_bestiary_async(on_done=self._on_bestiary_ready)

    def _on_bestiary_ready(self) -> None:
        invalidate_bestiary_cache()
        monster_icons.invalidate_names_cache()
        if self._last_profile_payload is None:
            return
        try:
            profile = load_profile_from_dict(self._last_profile_payload)
        except Exception:
            return
        profile["source"] = "cache"
        self.profile_page.apply_profile(profile, self._last_profile_saved_at)
        self.monsters_page.apply_profile(profile, self._last_profile_saved_at)
        self.runes_page.apply_profile(profile, self._last_profile_saved_at)

    def _restore_cached_profile(self) -> None:
        cached = load_profile_payload()
        if cached is None:
            return
        payload, saved_at = cached
        try:
            profile = load_profile_from_dict(payload)
        except Exception:
            return
        profile["source"] = "cache"
        self._last_profile_payload = payload
        self._last_profile_saved_at = saved_at
        self.profile_page.apply_profile(profile, saved_at)
        self.monsters_page.apply_profile(profile, saved_at)
        self.runes_page.apply_profile(profile, saved_at)

    def _on_profile_import(self, path: str) -> None:
        import datetime
        import json
        import os
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError):
            return
        try:
            save_profile_payload(payload)
        except OSError:
            pass
        try:
            profile = load_profile_from_dict(payload)
        except Exception:
            return
        profile["source"] = "manual"
        try:
            mtime = datetime.datetime.fromtimestamp(
                os.path.getmtime(path)
            ).isoformat(timespec="seconds")
        except OSError:
            mtime = ""
        self._last_profile_payload = payload
        self._last_profile_saved_at = mtime
        self.profile_page.apply_profile(profile, mtime)
        self.monsters_page.apply_profile(profile, mtime)
        self.runes_page.apply_profile(profile, mtime)

    def _on_nav(self, key: str) -> None:
        pages = {
            "scan":          (0, "Scan"),
            "filters":       (1, "Filtres"),
            "runes":         (2, "Runes"),
            "monsters":      (3, "Monstres"),
            "stats_history": (4, "Stats & Historique"),
            "profile":       (5, "Profils"),
            "settings":      (6, "Parametres"),
        }
        index, label = pages.get(key, (0, "Scan"))
        self._stack.setCurrentIndex(index)
        self._title_bar.set_title(f"Luci2US \u2014 {label}")

    def _toggle_max_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
