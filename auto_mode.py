"""Auto Mode – orchestrates SWEX bridge, evaluation chain, and history DB."""

from __future__ import annotations

import json
import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)

from evaluator_chain import evaluate_chain, evaluate_artifact_chain
from history_db import init_db, save_session, save_rune
from models import Artifact, Rune, Verdict
from swex_bridge import SWEXBridge


class State(Enum):
    IDLE = "IDLE"
    SCANNING = "SCANNING"
    ANALYZING = "ANALYZING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


@dataclass
class SessionStats:
    start_time: str = ""
    total_runes: int = 0
    keep: int = 0
    sell: int = 0
    mana_estimate: int = 0
    kept_runes: list[dict] = field(default_factory=list)
    best_rune: dict | None = None


class AutoMode:
    """Orchestrates automatic rune evaluation sessions."""

    def __init__(
        self,
        config: dict,
        on_state_change: Callable[[State], None] | None = None,
        on_rune_processed: Callable[[Rune, Verdict], None] | None = None,
        on_session_update: Callable[[SessionStats], None] | None = None,
        on_profile_loaded: Callable[[dict], None] | None = None,
    ) -> None:
        self._config = config
        self._on_state_change = on_state_change
        self._on_rune_processed = on_rune_processed
        self._on_session_update = on_session_update

        self._state = State.IDLE
        self._stats = SessionStats()
        self._db = init_db(config.get("db_path", "history.db"))
        self._session_id: int | None = None

        self._bridge = SWEXBridge(
            drops_dir=config["swex"]["drops_dir"],
            on_rune_drop=self._handle_rune,
            on_artifact_drop=self._handle_artifact,
            on_rune_upgrade=self._handle_upgrade,
            on_profile_loaded=on_profile_loaded,
            poll_interval=config["swex"].get("poll_interval", 0.5),
        )

        self._keepalive_thread: threading.Thread | None = None
        self._running = False

    # -- Properties --

    @property
    def state(self) -> State:
        return self._state

    @property
    def stats(self) -> SessionStats:
        return self._stats

    # -- Public API --

    def start(self) -> None:
        if self._running:
            return
        self._running = True

        self._stats = SessionStats(start_time=datetime.now().isoformat())
        self._session_id = save_session(
            self._db, start_time=self._stats.start_time
        )

        self._bridge.start()
        self._set_state(State.SCANNING)

        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop, daemon=True
        )
        self._keepalive_thread.start()

    def stop(self) -> None:
        self._running = False
        self._bridge.stop()

        if self._keepalive_thread is not None:
            self._keepalive_thread.join(timeout=2)
            self._keepalive_thread = None

        if self._session_id is not None:
            self._db.execute(
                "UPDATE sessions SET end_time = ?, total = ?, keep = ?, sell = ? "
                "WHERE id = ?",
                (
                    datetime.now().isoformat(),
                    self._stats.total_runes,
                    self._stats.keep,
                    self._stats.sell,
                    self._session_id,
                ),
            )
            self._db.commit()

        self._set_state(State.IDLE)

    # -- Internal handlers --

    def _handle_rune(self, rune: Rune) -> None:
        self._set_state(State.ANALYZING)
        try:
            verdict = evaluate_chain(rune, self._config)
            self._record_rune(rune, verdict)
            if self._on_rune_processed:
                self._on_rune_processed(rune, verdict)
        except Exception as e:
            logger.error("_handle_rune error: %s\n%s", e, traceback.format_exc())
            self._set_state(State.ERROR)
            return
        self._set_state(State.SCANNING)

    def _handle_artifact(self, artifact: Artifact) -> None:
        self._set_state(State.ANALYZING)
        try:
            verdict = evaluate_artifact_chain(artifact, self._config)
            if self._on_rune_processed:
                self._on_rune_processed(artifact, verdict)
        except Exception:
            self._set_state(State.ERROR)
            return
        self._set_state(State.SCANNING)

    def _handle_upgrade(self, rune: Rune, event: str, level: int) -> None:
        self._set_state(State.ANALYZING)
        try:
            verdict = evaluate_chain(rune, self._config)
            if verdict.decision != "POWER-UP":
                self._record_rune(rune, verdict)
            if self._on_rune_processed:
                self._on_rune_processed(rune, verdict)
        except Exception:
            self._set_state(State.ERROR)
            return
        self._set_state(State.SCANNING)

    # -- Helpers --

    def _record_rune(self, rune: Rune, verdict: Verdict) -> None:
        self._stats.total_runes += 1

        if verdict.decision == "KEEP":
            self._stats.keep += 1
            rune_info = {
                "set": rune.set, "slot": rune.slot, "stars": rune.stars,
                "grade": rune.grade, "score": verdict.score,
                "reason": verdict.reason,
            }
            self._stats.kept_runes.append(rune_info)
            if (
                self._stats.best_rune is None
                or (verdict.score or 0) > (self._stats.best_rune.get("score") or 0)
            ):
                self._stats.best_rune = rune_info
        else:
            self._stats.sell += 1
            self._stats.mana_estimate += _estimate_mana(rune)

        substats_json = json.dumps(
            [{"type": s.type, "value": s.value, "grind": s.grind_value}
             for s in rune.substats]
        )

        if self._session_id is not None:
            save_rune(
                self._db,
                session_id=self._session_id,
                timestamp=datetime.now().isoformat(),
                rune_set=rune.set,
                slot=rune.slot,
                stars=rune.stars,
                grade=rune.grade,
                level=rune.level,
                main_stat=rune.main_stat.type,
                substats_json=substats_json,
                verdict=verdict.decision,
                reason=verdict.reason,
                score=verdict.score,
                source=verdict.source,
            )

        if self._on_session_update:
            self._on_session_update(self._stats)

    def _set_state(self, new_state: State) -> None:
        self._state = new_state
        if self._on_state_change:
            self._on_state_change(new_state)

    def _keepalive_loop(self) -> None:
        while self._running:
            time.sleep(5)

    # -- Rune mana estimation --


def _estimate_mana(rune: Rune) -> int:
    base = {5: 7500, 6: 15000}.get(rune.stars, 3000)
    grade_mult = {
        "Legendaire": 1.0, "Heroique": 0.8, "Rare": 0.6,
        "Magique": 0.4, "Normal": 0.2,
    }.get(rune.grade, 0.3)
    return int(base * grade_mult)
