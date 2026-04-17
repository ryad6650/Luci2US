"""Standalone PySide6 entrypoint for the redesigned Scan page.

Run: `python scan_app.py`

The existing customtkinter app (`app.py`) continues to work untouched; this is
a parallel entrypoint while the migration is in progress.
"""
from __future__ import annotations
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
