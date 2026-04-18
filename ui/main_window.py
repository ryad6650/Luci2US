"""QMainWindow shell: sidebar + content stack. Scan, Profils, Parametres sont implementes;
Filtres / Runes / Monstres / Stats & Historique affichent un placeholder."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel,
)

from profile_loader import load_profile_from_dict
from profile_store import load_profile_payload
from ui import theme
from ui.controllers.scan_controller import ScanController
from ui.filtres.filtres_page import FiltresPage
from ui.monsters.monsters_page import MonstersPage
from ui.profile.profile_page import ProfilePage
from ui.settings.settings_page import SettingsPage
from ui.sidebar import Sidebar
from ui.scan.scan_page import ScanPage
from ui.widgets.background import BackgroundPane


def _placeholder(text: str) -> QWidget:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:14px;")
    return lbl


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Luci2US")
        self.resize(1200, 1000)
        self.setMinimumSize(1000, theme.SIZE_APP_MIN_H)
        self.setStyleSheet(f"QMainWindow {{ background:{theme.COLOR_BG_APP}; }}")

        root = QWidget()
        root_lay = QHBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.nav_changed.connect(self._on_nav)
        root_lay.addWidget(self._sidebar)

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
        # Index 2 : Runes (placeholder, Plan 3)
        self._stack.addWidget(_placeholder("Runes - a implementer"))
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
        root_lay.addWidget(content, 1)

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
        self.controller.state_changed.connect(
            self.scan_page.set_active,
            type=Qt.ConnectionType.QueuedConnection,
        )

        self._restore_cached_profile()

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
        self.profile_page.apply_profile(profile, saved_at)
        self.monsters_page.apply_profile(profile, saved_at)

    def _on_nav(self, key: str) -> None:
        index = {
            "scan":          0,
            "filters":       1,
            "runes":         2,
            "monsters":      3,
            "stats_history": 4,
            "profile":       5,
            "settings":      6,
        }.get(key, 0)
        self._stack.setCurrentIndex(index)
