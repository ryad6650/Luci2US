"""Demo: feed the Scan page with fake runes every 2 seconds.

Run: `python scripts/demo_scan.py`

Proves the UI layer works end-to-end without booting SWEX.
"""
from __future__ import annotations
import os
import random
import sys

# Ensure repo root is importable when running from scripts/
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from models import Rune, SubStat, Verdict
from ui.main_window import MainWindow


SETS = ["Violent", "Rapide", "Fatal", "Rage", "Lame", "Desespoir", "Garde"]
SLOTS = [1, 2, 3, 4, 5, 6]
GRADES = ["Legendaire", "Heroique", "Rare", "Magique"]
MAINS = ["ATQ%", "DEF%", "PV%", "VIT", "CC", "DC"]


def fake_rune() -> Rune:
    return Rune(
        set=random.choice(SETS), slot=random.choice(SLOTS),
        stars=6, grade=random.choice(GRADES), level=random.randint(0, 15),
        main_stat=SubStat(random.choice(MAINS), random.randint(10, 30)),
        prefix=None,
        substats=[
            SubStat("PV%", random.randint(4, 10)),
            SubStat("ATQ%", random.randint(4, 10)),
            SubStat("VIT", random.randint(4, 10)),
            SubStat("CC", random.randint(4, 10)),
        ],
    )


def fake_verdict(score: float) -> Verdict:
    decision = "KEEP" if score >= 200 else "PWR-UP" if score >= 150 else "SELL"
    return Verdict(decision=decision, source="demo", reason="", score=score)


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    def tick() -> None:
        r = fake_rune()
        score = random.uniform(80, 250)
        v = fake_verdict(score)
        w.controller.push_from_worker(
            r, v, mana=random.randint(20, 100),
            swop=(random.uniform(60, 120), random.uniform(90, 150)),
            s2us=(random.uniform(80, 140), random.uniform(110, 160)),
            set_bonus=f"2 Set : {r.set} bonus",
        )

    t = QTimer()
    t.timeout.connect(tick)
    t.start(2000)
    w.controller.notify_state(True)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
