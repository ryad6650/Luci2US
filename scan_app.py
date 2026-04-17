"""Standalone PySide6 entrypoint for the redesigned Scan page.

Run: `python scan_app.py`

Boots the real AutoMode worker and wires its on_rune_processed callback to the
ScanController, which queues updates onto the Qt UI thread.
"""
from __future__ import annotations
import copy
import json
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from auto_mode import AutoMode, State
from models import Rune, Verdict
from ui.main_window import MainWindow


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


_SET_BONUS: dict[str, str] = {
    "Energie": "2 Set : PV +15%",
    "Garde": "2 Set : DEF +15%",
    "Rapide": "4 Set : VIT +25%",
    "Lame": "2 Set : TC +12%",
    "Concentration": "2 Set : PRE +20%",
    "Endurance": "2 Set : RES +20%",
    "Fatal": "4 Set : ATQ +35%",
    "Desespoir": "4 Set : Etourdissement 25%",
    "Vampire": "4 Set : Drain 35%",
    "Will": "2 Set : Immunite 1 tour",
    "Violent": "4 Set : Tour additionnel",
    "Nemesis": "2 Set : Barre ATB +4%",
    "Vengeance": "2 Set : Contre-attaque 15%",
    "Destruction": "2 Set : Ignore 30% PV max",
    "Combat": "2 Set : ATQ +8% allies",
    "Determination": "2 Set : DEF +8% allies",
    "Amelioration": "2 Set : PV +8% allies",
    "Precision": "2 Set : PRE +10% allies",
    "Tolerance": "2 Set : RES +10% allies",
    "Rage": "4 Set : DC +40%",
    "Bouclier": "2 Set : Bouclier 15% PV",
    "Intangible": "2 Set : Intangible 1 tour",
    "Sceau": "2 Set : Sceau 1 tour",
    "Immemorial": "2 Set : Immemorial",
}

DEFAULT_CONFIG = {
    "db_path": "history.db",
    "lang": "FR",
    "swex": {
        "drops_dir": os.path.join(
            os.path.expanduser("~"),
            "AppData", "Local", "Programs", "sw-exporter", "rune-bot-drops",
        ),
        "poll_interval": 0.5,
    },
    "s2us": {"filter_file": "", "artifact_eff_threshold": 70},
}


def _load_config() -> dict:
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            on_disk = json.load(f)
        for k, v in on_disk.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def _estimate_mana(rune: Rune) -> int:
    base = {5: 7500, 6: 15000}.get(rune.stars, 3000)
    grade_mult = {
        "Legendaire": 1.0, "Heroique": 0.8, "Rare": 0.6,
        "Magique": 0.4, "Normal": 0.2,
    }.get(rune.grade, 0.3)
    return int(base * grade_mult)


def main() -> int:
    cfg = _load_config()

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    def on_rune_processed(rune: Rune, verdict: Verdict) -> None:
        d = verdict.details or {}
        swop = (float(d.get("eff_swop", 0)), float(d.get("max_swop", 0)))
        s2us = (float(d.get("eff_s2us", 0)), float(d.get("max_s2us", 0)))
        w.controller.push_from_worker(
            rune, verdict,
            mana=_estimate_mana(rune) if verdict.decision == "SELL" else 0,
            swop=swop, s2us=s2us,
            set_bonus=_SET_BONUS.get(rune.set, ""),
        )

    def on_state_change(state: State) -> None:
        w.controller.notify_state(state in (State.SCANNING, State.ANALYZING))

    mode = AutoMode(
        config=cfg,
        on_state_change=on_state_change,
        on_rune_processed=on_rune_processed,
    )

    def toggle_mode() -> None:
        if mode.state == State.IDLE:
            mode.start()
        else:
            mode.stop()

    w.scan_page.start_requested.connect(toggle_mode)

    exit_code = app.exec()
    mode.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
