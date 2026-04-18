"""Bridge between SW Exporter plugin JSON drops and Luci2US models."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Callable

from models import Rune, SubStat

# ---------------------------------------------------------------------------
# Mappings SWEX → FR
# ---------------------------------------------------------------------------

SWEX_TYPE_ID: dict[int, str] = {
    1: "PV", 2: "PV%", 3: "ATQ", 4: "ATQ%", 5: "DEF", 6: "DEF%",
    8: "VIT", 9: "CC", 10: "DC", 11: "RES", 12: "PRE",
}

SWEX_SET_ID: dict[int, str] = {
    1: "Energie", 2: "Garde", 3: "Rapide", 4: "Lame",
    5: "Rage", 6: "Concentration", 7: "Endurance", 8: "Fatal",
    10: "Desespoir", 11: "Vampire", 13: "Violent", 14: "Nemesis",
    15: "Will", 16: "Bouclier", 17: "Vengeance", 18: "Destruction",
    19: "Combat", 20: "Determination", 21: "Amelioration",
    22: "Precision", 23: "Tolerance", 24: "Sceau", 25: "Intangible",
    99: "Immemorial",
}

SWEX_RANK: dict[int, str] = {
    1: "Normal", 2: "Magique", 3: "Rare", 4: "Heroique", 5: "Legendaire",
    11: "Normal", 12: "Magique", 13: "Rare", 14: "Heroique", 15: "Legendaire",
}


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_substat(eff: list) -> SubStat | None:
    """Parse a SWEX effect array [type_id, value, ...] into a SubStat."""
    if not eff or eff[0] == 0:
        return None
    stat_type = SWEX_TYPE_ID.get(eff[0])
    if stat_type is None:
        return None
    value = eff[1] if len(eff) > 1 else 0
    grind = eff[2] if len(eff) > 2 else 0
    return SubStat(type=stat_type, value=value, grind_value=grind)


def parse_rune(data: dict) -> Rune:
    """Parse a SWEX rune JSON payload into a Rune dataclass."""
    rune = data if "slot_no" in data else data.get("rune", data)

    set_name = SWEX_SET_ID.get(rune["set_id"], str(rune["set_id"]))
    slot = rune["slot_no"]
    stars = rune.get("stars", rune.get("class", 6))
    if stars > 10:
        stars -= 10
    grade = SWEX_RANK.get(rune.get("rank", 1), "Normal")
    level = rune.get("upgrade_curr", 0)

    main_stat = _parse_substat(rune["pri_eff"])
    prefix = _parse_substat(rune.get("prefix_eff", [0, 0]))

    substats: list[SubStat] = []
    for sec in rune.get("sec_eff", []):
        ss = _parse_substat(sec)
        if ss is not None:
            substats.append(ss)

    swex_eff = rune.get("efficiency")
    swex_max = rune.get("max_efficiency")
    rune_id = rune.get("rune_id")

    return Rune(
        set=set_name,
        slot=slot,
        stars=stars,
        grade=grade,
        level=level,
        main_stat=main_stat,
        prefix=prefix if prefix else None,
        substats=substats,
        swex_efficiency=float(swex_eff) if swex_eff is not None else None,
        swex_max_efficiency=float(swex_max) if swex_max is not None else None,
        rune_id=int(rune_id) if rune_id is not None else None,
    )


# ---------------------------------------------------------------------------
# SWEX config discovery
# ---------------------------------------------------------------------------

def _swex_config_candidates() -> list[Path]:
    home = Path.home()
    return [
        Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
            / "Summoners War Exporter" / "storage" / "Config.json",
        home / "Library" / "Application Support" / "Summoners War Exporter"
            / "storage" / "Config.json",
        home / ".config" / "Summoners War Exporter" / "storage" / "Config.json",
    ]


def detect_drops_dir() -> str:
    """Return `<SWEX filesPath>/rune-bot-drops`, or empty string if not found."""
    for candidate in _swex_config_candidates():
        if not candidate.is_file():
            continue
        try:
            with open(candidate, encoding="utf-8") as f:
                data = json.load(f)
            files_path = data.get("App", {}).get("filesPath")
        except (OSError, json.JSONDecodeError):
            continue
        if files_path:
            return str(Path(files_path) / "rune-bot-drops")
    return ""


# ---------------------------------------------------------------------------
# SWEXBridge – folder watcher
# ---------------------------------------------------------------------------

class SWEXBridge:
    """Watch a folder for SWEX JSON drops and dispatch parsed objects."""

    def __init__(
        self,
        drops_dir: str | Path,
        on_rune_drop: Callable[[Rune], None] | None = None,
        on_artifact_drop: Callable | None = None,
        on_rune_upgrade: Callable[[Rune, str, int], None] | None = None,
        on_profile_loaded: Callable[[dict], None] | None = None,
        poll_interval: float = 0.5,
    ) -> None:
        self.drops_dir = Path(drops_dir)
        self.on_rune_drop = on_rune_drop
        self.on_artifact_drop = on_artifact_drop
        self.on_rune_upgrade = on_rune_upgrade
        self.on_profile_loaded = on_profile_loaded
        self._poll_interval = poll_interval
        self._seen: set[str] = set()
        self._last_mtime: float = 0.0
        self._profile_mtimes: dict[str, float] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    # -- public API --

    @property
    def available(self) -> bool:
        return self.drops_dir.is_dir()

    def start(self) -> None:
        if self._running:
            return
        # Ignore pre-existing latest_drop.json so we don't re-process old drops
        latest = self.drops_dir / "latest_drop.json"
        try:
            self._last_mtime = os.path.getmtime(latest)
        except OSError:
            self._last_mtime = 0.0
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    # -- internals --

    def _poll_loop(self) -> None:
        while self._running:
            if self.available:
                self._scan()
            time.sleep(self._poll_interval)

    def _scan(self) -> None:
        # Strategy 1: watch for individual drop_*.json / profile_*.json files
        try:
            entries = os.listdir(self.drops_dir)
        except OSError:
            return
        for name in entries:
            if not name.endswith(".json"):
                continue

            path = self.drops_dir / name

            # Strategy 2: watch latest_drop.json (old plugin format)
            # This file is overwritten on each drop, so detect changes via mtime
            if name == "latest_drop.json":
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if mtime <= self._last_mtime:
                    continue
                self._last_mtime = mtime
            elif name.startswith("profile_"):
                # Profile files get overwritten on re-login; track per-file mtime.
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if mtime <= self._profile_mtimes.get(name, 0.0):
                    continue
                self._profile_mtimes[name] = mtime
            else:
                if name in self._seen:
                    continue
                self._seen.add(name)

            try:
                with open(path, encoding="utf-8") as f:
                    payload = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            if name.startswith("profile_"):
                if self.on_profile_loaded:
                    self.on_profile_loaded(payload)
            else:
                self._dispatch(payload)

    def _dispatch(self, payload: dict) -> None:
        event = payload.get("event", "")

        # Old plugin format: drops[] array with formatted rune objects
        drops = payload.get("drops")
        if drops and isinstance(drops, list):
            for drop in drops:
                if drop.get("type") == "rune":
                    rune = parse_rune(drop)
                    if "Upgrade" in event or "Amplify" in event or "Convert" in event or "Revalue" in event:
                        if self.on_rune_upgrade:
                            self.on_rune_upgrade(rune, event, rune.level)
                    else:
                        if self.on_rune_drop:
                            self.on_rune_drop(rune)
            return

        # New plugin format: rune fields spread at top level
        if event in (
            "BattleDungeonResult_v2",
            "BattleScenarioResult",
            "BattleDimensionHoleDungeonResult_v2",
            "BuyGuildShopRune",
            "ConfirmRune",
        ):
            rune = parse_rune(payload)
            if self.on_rune_drop:
                self.on_rune_drop(rune)

        elif event in ("UpgradeRune", "AmplifyRune"):
            rune = parse_rune(payload)
            if self.on_rune_upgrade:
                self.on_rune_upgrade(rune, event, rune.level)
