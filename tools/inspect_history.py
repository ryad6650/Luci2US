"""Vérifie que les 6 HistoryRuneCard sont bien placées et visibles."""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget

from models import Rune, SubStat, Verdict
from ui.fonts import load_custom_fonts
from ui.scan.scan_page import ScanPage


def _rune(slot: int, set_name: str, level: int) -> Rune:
    return Rune(
        set=set_name, slot=slot, stars=6, grade="Legendaire", level=level,
        main_stat=SubStat("DC", 80), prefix=None,
        substats=[SubStat("VIT", 18), SubStat("PV%", 14),
                  SubStat("ATQ%", 22), SubStat("CC", 11)],
    )


def _verdict(dec: str) -> Verdict:
    return Verdict(
        decision=dec, source="s2us", reason="demo", score=4.2,
        details={"reason": "demo", "s2us": "38%", "swop": "45%"},
    )


def _bbox_of(w: QWidget, page: QWidget) -> tuple[int, int, int, int]:
    pt = w.mapTo(page, w.rect().topLeft())
    return (pt.x(), pt.y(), w.width(), w.height())


def main() -> int:
    app = QApplication(sys.argv)
    load_custom_fonts()
    page = ScanPage()
    page.resize(1408, 768)
    page.show()

    def _inject() -> None:
        sets = ["Rage", "Violent", "Rapide", "Will", "Fatal", "Desespoir"]
        for i, s in enumerate(sets):
            r = _rune(slot=(i % 6) + 1, set_name=s, level=12)
            v = _verdict("KEEP" if i % 2 == 0 else "SELL")
            page._history.add_rune(r, v)

    def _inspect() -> None:
        hp = page._history
        cards = getattr(hp, "_cards", [])
        print(f"HistoryPanel: bbox={_bbox_of(hp, page)} ; nb cards={len(cards)}")
        for i, c in enumerate(cards):
            bb = _bbox_of(c, page)
            print(f"  card[{i}]: bbox={bb}, visible={c.isVisible()}, "
                  f"set={c._rune.set}, name='{c._name.text()}', "
                  f"icon_pix_null={c._icon.pixmap().isNull()}")
        app.quit()

    QTimer.singleShot(200, _inject)
    QTimer.singleShot(800, _inspect)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
