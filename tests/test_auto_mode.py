"""Tests for AutoMode – state transitions and session stats."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from auto_mode import AutoMode, State, _estimate_mana
from models import Rune, SubStat, Verdict


# -- Fixtures --

def _make_rune(**overrides) -> Rune:
    defaults = dict(
        set="Violent", slot=1, stars=6, grade="Legendaire", level=0,
        main_stat=SubStat(type="ATQ", value=160),
        prefix=None,
        substats=[
            SubStat(type="VIT", value=18),
            SubStat(type="CC", value=12),
            SubStat(type="DC", value=14),
            SubStat(type="PV%", value=8),
        ],
    )
    defaults.update(overrides)
    return Rune(**defaults)


def _base_config(tmp_path) -> dict:
    drops = tmp_path / "drops"
    drops.mkdir()
    return {
        "db_path": str(tmp_path / "test.db"),
        "swex": {
            "drops_dir": str(drops),
            "poll_interval": 0.05,
        },
        "s2us": {
            "filter_file": "dummy.s2us",
        },
    }


# -- Tests --

class TestStateTransitions:
    def test_initial_state_is_idle(self, tmp_path):
        config = _base_config(tmp_path)
        with patch("auto_mode.init_db"):
            am = AutoMode(config)
        assert am.state == State.IDLE

    def test_start_sets_scanning(self, tmp_path):
        config = _base_config(tmp_path)
        states: list[State] = []
        with patch("auto_mode.init_db"):
            am = AutoMode(config, on_state_change=states.append)
            am.start()
            assert am.state == State.SCANNING
            am.stop()
        assert State.SCANNING in states

    def test_stop_returns_to_idle(self, tmp_path):
        config = _base_config(tmp_path)
        with patch("auto_mode.init_db"):
            am = AutoMode(config)
            am.start()
            am.stop()
        assert am.state == State.IDLE

    def test_rune_processing_transitions(self, tmp_path):
        config = _base_config(tmp_path)
        states: list[State] = []
        keep_verdict = Verdict(decision="KEEP", source="s2us", reason="good", score=85.0)

        with patch("auto_mode.init_db"), \
             patch("auto_mode.evaluate_chain", return_value=keep_verdict), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config, on_state_change=states.append)
            am.start()
            states.clear()

            rune = _make_rune()
            am._handle_rune(rune)

        assert states == [State.ANALYZING, State.SCANNING]

    def test_error_state_on_eval_failure(self, tmp_path):
        config = _base_config(tmp_path)
        states: list[State] = []

        with patch("auto_mode.init_db"), \
             patch("auto_mode.evaluate_chain", side_effect=RuntimeError("boom")):
            am = AutoMode(config, on_state_change=states.append)
            am.start()
            states.clear()

            am._handle_rune(_make_rune())

        assert State.ERROR in states


class TestSessionStats:
    def test_keep_increments(self, tmp_path):
        config = _base_config(tmp_path)
        keep_verdict = Verdict(decision="KEEP", source="s2us", reason="good", score=90.0)

        with patch("auto_mode.init_db"), \
             patch("auto_mode.evaluate_chain", return_value=keep_verdict), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config)
            am.start()
            am._handle_rune(_make_rune())

        assert am.stats.total_runes == 1
        assert am.stats.keep == 1
        assert am.stats.sell == 0
        assert len(am.stats.kept_runes) == 1

    def test_sell_increments_and_mana(self, tmp_path):
        config = _base_config(tmp_path)
        sell_verdict = Verdict(decision="SELL", source="s2us", reason="bad", score=30.0)

        with patch("auto_mode.init_db"), \
             patch("auto_mode.evaluate_chain", return_value=sell_verdict), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config)
            am.start()
            am._handle_rune(_make_rune(stars=6, grade="Legendaire"))

        assert am.stats.sell == 1
        assert am.stats.mana_estimate == 15000

    def test_best_rune_tracked(self, tmp_path):
        config = _base_config(tmp_path)

        with patch("auto_mode.init_db"), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config)
            am.start()

            v1 = Verdict(decision="KEEP", source="s2us", reason="ok", score=70.0)
            v2 = Verdict(decision="KEEP", source="s2us", reason="great", score=95.0)
            with patch("auto_mode.evaluate_chain", return_value=v1):
                am._handle_rune(_make_rune())
            with patch("auto_mode.evaluate_chain", return_value=v2):
                am._handle_rune(_make_rune())

        assert am.stats.best_rune["score"] == 95.0

    def test_multiple_runes_stats(self, tmp_path):
        config = _base_config(tmp_path)
        verdicts = [
            Verdict(decision="KEEP", source="s2us", reason="", score=80.0),
            Verdict(decision="SELL", source="s2us", reason="", score=20.0),
            Verdict(decision="SELL", source="s2us", reason="", score=15.0),
        ]

        with patch("auto_mode.init_db"), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config)
            am.start()
            for v in verdicts:
                with patch("auto_mode.evaluate_chain", return_value=v):
                    am._handle_rune(_make_rune())

        assert am.stats.total_runes == 3
        assert am.stats.keep == 1
        assert am.stats.sell == 2


class TestCallbacks:
    def test_on_rune_processed_called(self, tmp_path):
        config = _base_config(tmp_path)
        cb = MagicMock()
        verdict = Verdict(decision="SELL", source="s2us", reason="", score=10.0)

        with patch("auto_mode.init_db"), \
             patch("auto_mode.evaluate_chain", return_value=verdict), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config, on_rune_processed=cb)
            am.start()
            rune = _make_rune()
            am._handle_rune(rune)

        cb.assert_called_once_with(rune, verdict)

    def test_on_session_update_called(self, tmp_path):
        config = _base_config(tmp_path)
        cb = MagicMock()
        verdict = Verdict(decision="KEEP", source="s2us", reason="", score=50.0)

        with patch("auto_mode.init_db"), \
             patch("auto_mode.evaluate_chain", return_value=verdict), \
             patch("auto_mode.save_rune"):
            am = AutoMode(config, on_session_update=cb)
            am.start()
            am._handle_rune(_make_rune())

        cb.assert_called_once()
        stats = cb.call_args[0][0]
        assert stats.total_runes == 1


class TestManaEstimation:
    def test_6star_legendaire(self):
        assert _estimate_mana(_make_rune(stars=6, grade="Legendaire")) == 15000

    def test_5star_heroique(self):
        assert _estimate_mana(_make_rune(stars=5, grade="Heroique")) == 6000

    def test_unknown_stars(self):
        assert _estimate_mana(_make_rune(stars=4, grade="Normal")) == 600
