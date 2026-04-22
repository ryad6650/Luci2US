"""Injection d'une rune demo dans ScanPage + grab full_mode_v2.png.

Rune : Rage 6* Heroique +12, stat principale TX CRIT +23%,
substats PV+10%, ATK+10%, VIT+9, TX CRIT+9%.
Verdict : VENDRE, score 194.9, raison "Efficience faible",
EFFI S2US 32%, EFFI SWOP 70%.
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from models import Rune, SubStat, Verdict
from ui.fonts import load_custom_fonts
from ui.scan.scan_page import ScanPage


def build_rune() -> Rune:
    return Rune(
        set="Rage", slot=2, stars=6, grade="Heroique", level=12,
        main_stat=SubStat("CC", 23),
        prefix=None,
        substats=[
            SubStat("PV%", 10),
            SubStat("ATQ%", 10),
            SubStat("VIT", 9),
            SubStat("CC", 9),
        ],
    )


def build_verdict() -> Verdict:
    return Verdict(
        decision="SELL",
        source="demo",
        reason="Efficience faible",
        score=194.9,
        details={
            "s2us": "32%",
            "swop": "70%",
            "reason": "Efficience faible",
        },
    )


def main() -> int:
    app = QApplication(sys.argv)
    load_custom_fonts()
    page = ScanPage()
    page.resize(1408, 768)
    page.show()

    out = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "after_annotation_fix.png",
    ))

    def _inject() -> None:
        page.on_rune(build_rune(), build_verdict())

    def _grab() -> None:
        pix = page.grab()
        pix.save(out, "PNG")
        print(f"saved: {out} ({pix.width()}x{pix.height()})")
        app.quit()

    QTimer.singleShot(300, _inject)
    QTimer.singleShot(2300, _grab)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
