"""Capture the ScanPage at native 1408x768 for layout verification."""
from __future__ import annotations
import os
import sys

# Ensure repo root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ui.fonts import load_custom_fonts
from ui.scan.scan_page import ScanPage


def main() -> int:
    app = QApplication(sys.argv)
    load_custom_fonts()
    page = ScanPage()
    page.resize(1408, 768)
    page.show()

    out = os.path.join(os.path.dirname(__file__), "..", "batch1_empty_v2.png")
    out = os.path.abspath(out)

    def _grab() -> None:
        pix = page.grab()
        pix.save(out, "PNG")
        print(f"saved: {out} ({pix.width()}x{pix.height()})")
        app.quit()

    QTimer.singleShot(600, _grab)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
