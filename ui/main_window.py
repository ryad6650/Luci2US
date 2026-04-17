"""QMainWindow shell: sidebar + content stack. Only Scan is implemented;
other nav items show a placeholder."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel,
)

from ui import theme
from ui.controllers.scan_controller import ScanController
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
        self.resize(1200, 720)
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
        self._stack.addWidget(self.scan_page)
        for name in ("Profil", "Historique", "Stats", "Parametres"):
            self._stack.addWidget(_placeholder(f"{name} - a implementer"))
        bg_lay.addWidget(self._stack)

        content_lay.addWidget(bg)
        root_lay.addWidget(content, 1)

        self.setCentralWidget(root)

        self.controller = ScanController(self)
        self.controller.rune_evaluated.connect(
            self.scan_page.on_rune,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self.controller.state_changed.connect(
            self.scan_page.set_active,
            type=Qt.ConnectionType.QueuedConnection,
        )

    def _on_nav(self, key: str) -> None:
        index = {"scan": 0, "profile": 1, "history": 2, "stats": 3, "settings": 4}.get(key, 0)
        self._stack.setCurrentIndex(index)
