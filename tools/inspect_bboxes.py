"""Mesure les bboxes réelles des widgets + les compare aux zones de cadre.

Ouvre batch1_empty.png et batch1_full.png, capture les bboxes Qt via
QWidget.geometry() puis imprime le diagnostic par widget.
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", "")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget

from models import Rune, SubStat, Verdict
from ui.fonts import load_custom_fonts
from ui.scan.scan_page import ScanPage


BG_W, BG_H = 1408, 768
FRAME_DETAILS = (713, 95, 194, 252)
FRAME_UPGRADE = (1153, 436, 178, 265)
FRAME_RECO = (435, 665, 550, 80)
FRAME_HISTORY = (948, 65, 382, 343)


def _rune() -> Rune:
    return Rune(
        set="Rage", slot=2, stars=6, grade="Heroique", level=12,
        main_stat=SubStat("CC", 23),
        prefix=None,
        substats=[
            SubStat("PV%", 10), SubStat("ATQ%", 10),
            SubStat("VIT", 9), SubStat("CC", 9),
        ],
    )


def _verdict() -> Verdict:
    return Verdict(
        decision="SELL", source="demo", reason="Efficience faible",
        score=194.9,
        details={"s2us": "32%", "swop": "70%", "reason": "Efficience faible"},
    )


def _bbox_of(w: QWidget, page: QWidget) -> tuple[int, int, int, int]:
    pt = w.mapTo(page, w.rect().topLeft())
    return (pt.x(), pt.y(), w.width(), w.height())


def _check(label: str, widget_bbox, frame_bbox, margin: int = 6) -> str:
    wx, wy, ww, wh = widget_bbox
    fx, fy, fw, fh = frame_bbox
    left_ok = wx >= fx + margin
    top_ok = wy >= fy + margin
    right_ok = wx + ww <= fx + fw - margin
    bot_ok = wy + wh <= fy + fh - margin
    overflow = []
    if not left_ok:
        overflow.append(f"left by {fx + margin - wx}px")
    if not top_ok:
        overflow.append(f"top by {fy + margin - wy}px")
    if not right_ok:
        overflow.append(f"right by {(wx + ww) - (fx + fw - margin)}px")
    if not bot_ok:
        overflow.append(f"bot by {(wy + wh) - (fy + fh - margin)}px")
    status = "CONTENU" if not overflow else "DEBORDE: " + ", ".join(overflow)
    return f"{label}: bbox=({wx},{wy},{ww}x{wh}) frame=({fx},{fy},{fw}x{fh}) -> {status}"


def main() -> int:
    app = QApplication(sys.argv)
    load_custom_fonts()
    page = ScanPage()
    page.resize(BG_W, BG_H)
    page.show()

    def _inject() -> None:
        page.update_scanned_rune(_rune(), _verdict())

    def _inspect() -> None:
        print("=== Mode plein ===")
        print(_check("DetailsCard", _bbox_of(page._details, page), FRAME_DETAILS))
        # HistoryPanel: full bbox, then each card
        hbb = _bbox_of(page._history, page)
        print(_check("HistoryPanel", hbb, FRAME_HISTORY))
        try:
            entries = getattr(page._history, "_cards", None) or []
            for i, card in enumerate(entries):
                if card is not None:
                    cb = _bbox_of(card, page)
                    print(f"  History card[{i}]: bbox=({cb[0]},{cb[1]},{cb[2]}x{cb[3]})")
        except Exception as e:
            print(f"  (could not iterate history cards: {e})")
        print(_check("UpgradedPanel", _bbox_of(page._upgrade_card, page), FRAME_UPGRADE))
        print(_check("RecoPanel", _bbox_of(page._reco, page), FRAME_RECO))
        # Détails : sous-widgets
        d = page._details
        print(f"  _title: bbox={_bbox_of(d._title, page)}, text='{d._title.text()}'")
        print(f"  _type_line: bbox={_bbox_of(d._type_line, page)}")
        print(f"  _main_stat: bbox={_bbox_of(d._main_stat, page)}, text='{d._main_stat.text()}'")
        for i, row in enumerate(d._sub_rows):
            if row.isVisible():
                print(f"  _sub_rows[{i}]: bbox={_bbox_of(row, page)}")
        # Reco sous-widgets
        r = page._reco
        print(f"  reco._effi_s2us: bbox={_bbox_of(r._effi_s2us, page)}")
        print(f"  reco._effi_swop: bbox={_bbox_of(r._effi_swop, page)}")
        print(f"  reco._decision: bbox={_bbox_of(r._decision, page)}, text='{r._decision.text()}'")
        print(f"  reco._score: bbox={_bbox_of(r._score, page)}, text='{r._score.text()}'")
        print(f"  reco._reason: bbox={_bbox_of(r._reason, page)}, text='{r._reason.text()}'")
        print(f"  reco._confirm_btn: bbox={_bbox_of(r._confirm_btn, page)}")
        app.quit()

    QTimer.singleShot(300, _inject)
    QTimer.singleShot(1500, _inspect)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
