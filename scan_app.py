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
            set_bonus="",
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
