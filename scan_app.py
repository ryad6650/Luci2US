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
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from auto_mode import AutoMode, State
from models import Rune, Verdict
from profile_loader import load_profile_from_dict
from profile_store import save_profile_payload
from swex_bridge import detect_drops_dir
from ui.main_window import MainWindow
from ui.widgets.splash import SplashScreen
from ui.widgets.verdict_overlay import VerdictOverlay


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
        "drops_dir": detect_drops_dir(),
        "poll_interval": 0.5,
    },
    "s2us": {"filter_file": "", "artifact_eff_threshold": 70},
    "overlay": {"enabled": True, "duration_ms": 3000},
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


def _save_config(cfg: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


def _estimate_mana(rune: Rune) -> int:
    base = {5: 7500, 6: 15000}.get(rune.stars, 3000)
    grade_mult = {
        "Legendaire": 1.0, "Heroique": 0.8, "Rare": 0.6,
        "Magique": 0.4, "Normal": 0.2,
    }.get(rune.grade, 0.3)
    return int(base * grade_mult)


def _apply_app_icon(app: QApplication, window) -> None:
    """Icône Luci2US pour la fenêtre + barre des tâches Windows."""
    # Windows : AppUserModelID propre à l'app, sinon la barre des tâches
    # hérite de l'icône de python.exe.
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Luci2US.ScanApp")
        except Exception:
            pass

    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    for fname in ("icon.ico", "logo.png"):
        path = os.path.join(assets_dir, fname)
        if os.path.isfile(path):
            icon = QIcon(path)
            if not icon.isNull():
                app.setWindowIcon(icon)
                window.setWindowIcon(icon)
                return


def main() -> int:
    cfg = _load_config()

    app = QApplication(sys.argv)

    splash = SplashScreen(duration_ms=1800)
    splash.start()
    app.processEvents()

    w = MainWindow()
    _apply_app_icon(app, w)
    splash.finished.connect(w.show)

    # Navigation initiale optionnelle (utilisee par visual-ui-verification).
    _start_page = os.environ.get("LUCI2US_START_PAGE", "").strip().lower()
    if _start_page:
        splash.finished.connect(lambda k=_start_page: w._on_nav(k))

    overlay_cfg = cfg.setdefault("overlay", {})
    overlay_cfg.setdefault("enabled", True)
    overlay_cfg.setdefault("duration_ms", 3000)
    overlay: VerdictOverlay | None = None
    if overlay_cfg.get("enabled", True):
        pos = None
        if "x" in overlay_cfg and "y" in overlay_cfg:
            pos = (int(overlay_cfg["x"]), int(overlay_cfg["y"]))

        def _on_overlay_moved(x: int, y: int) -> None:
            overlay_cfg["x"] = x
            overlay_cfg["y"] = y
            _save_config(cfg)

        overlay = VerdictOverlay(
            pos=pos,
            duration_ms=int(overlay_cfg.get("duration_ms", 3000)),
            on_position_changed=_on_overlay_moved,
        )
        w.controller.rune_evaluated.connect(
            overlay.on_rune_signal, type=Qt.ConnectionType.QueuedConnection,
        )
        w.controller.rune_upgraded.connect(
            overlay.on_rune_signal, type=Qt.ConnectionType.QueuedConnection,
        )

    def _payload(rune: Rune, verdict: Verdict) -> tuple:
        d = verdict.details or {}
        swop = (float(d.get("eff_swop", 0)), float(d.get("max_swop", 0)))
        s2us = (float(d.get("eff_s2us", 0)), float(d.get("max_s2us", 0)))
        mana = _estimate_mana(rune) if verdict.decision == "SELL" else 0
        return mana, swop, s2us, _SET_BONUS.get(rune.set, "")

    def on_rune_processed(rune: Rune, verdict: Verdict) -> None:
        mana, swop, s2us, set_bonus = _payload(rune, verdict)
        w.controller.push_from_worker(
            rune, verdict, mana=mana, swop=swop, s2us=s2us, set_bonus=set_bonus,
        )

    def on_rune_upgraded(rune: Rune, verdict: Verdict) -> None:
        mana, swop, s2us, set_bonus = _payload(rune, verdict)
        w.controller.push_upgrade(
            rune, verdict, mana=mana, swop=swop, s2us=s2us, set_bonus=set_bonus,
        )

    def on_state_change(state: State) -> None:
        w.controller.notify_state(state in (State.SCANNING, State.ANALYZING))

    def on_profile_loaded(payload: dict) -> None:
        try:
            save_profile_payload(payload)
        except OSError:
            pass
        try:
            profile = load_profile_from_dict(payload)
        except Exception:
            return
        w.controller.push_profile(profile, "")

    mode = AutoMode(
        config=cfg,
        on_state_change=on_state_change,
        on_rune_processed=on_rune_processed,
        on_rune_upgraded=on_rune_upgraded,
        on_profile_loaded=on_profile_loaded,
    )

    # Auto-start so no rune is missed while the user waits on a Start click.
    mode.start()

    exit_code = app.exec()
    mode.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
