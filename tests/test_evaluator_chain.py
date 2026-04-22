from __future__ import annotations

import json
import os
import tempfile

import pytest

from models import Artifact, ArtifactSubStat, Rune, SubStat, Verdict
from evaluator_chain import (
    _get_filters,
    evaluate_artifact_chain,
    evaluate_chain,
    reload_filters,
)


# ── Helpers ──────────────────────────────────────────────────────

def _make_s2us_file(filters: list[dict], **global_kw) -> str:
    """Ecrit un fichier .S2US temporaire et retourne son chemin."""
    import base64

    for f in filters:
        if "Name" not in f:
            f["Name"] = base64.b64encode(b"Test Filter").decode()
        f.setdefault("Enabled", 1)

    data = {
        "RuneFilter": {
            "Filter": filters,
            **global_kw,
        }
    }
    fd, path = tempfile.mkstemp(suffix=".S2US")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return path


def _config(path: str, **extra) -> dict:
    return {"s2us": {"filter_file": path, **extra}}


def _rune(**kw) -> Rune:
    defaults = dict(
        set="Violent",
        slot=1,
        stars=6,
        grade="Legendaire",
        level=12,
        main_stat=SubStat(type="ATQ", value=160),
        prefix=None,
        substats=[
            SubStat(type="VIT", value=18),
            SubStat(type="CC", value=12),
            SubStat(type="DC", value=14),
            SubStat(type="PV%", value=16),
        ],
    )
    defaults.update(kw)
    return Rune(**defaults)


# ── Tests evaluate_chain ─────────────────────────────────────────

class TestEvaluateChain:
    def setup_method(self):
        reload_filters()

    def test_keep_when_filter_matches(self):
        path = _make_s2us_file([{"Violent": 1, "Slot1": 1}])
        try:
            v = evaluate_chain(_rune(), _config(path))
            assert v.decision == "KEEP"
            assert v.source == "s2us"
        finally:
            os.unlink(path)

    def test_sell_when_no_filter_matches(self):
        # Filtre exige Swift, rune est Violent
        path = _make_s2us_file([{"Swift": 1}])
        try:
            v = evaluate_chain(_rune(), _config(path))
            assert v.decision == "SELL"
        finally:
            os.unlink(path)

    def test_disabled_filter_skipped(self):
        path = _make_s2us_file([{"Violent": 1, "Enabled": 0}])
        try:
            v = evaluate_chain(_rune(), _config(path))
            assert v.decision == "SELL"
        finally:
            os.unlink(path)


# ── Tests cache ──────────────────────────────────────────────────

class TestCache:
    def setup_method(self):
        reload_filters()

    def test_cache_reused_on_same_path(self):
        path = _make_s2us_file([{"Violent": 1}])
        try:
            cfg = _config(path)
            f1, s1 = _get_filters(cfg)
            f2, s2 = _get_filters(cfg)
            assert f1 is f2
            assert s1 == s2
        finally:
            os.unlink(path)

    def test_cache_invalidated_on_path_change(self):
        path1 = _make_s2us_file([{"Violent": 1}])
        path2 = _make_s2us_file([{"Swift": 1}])
        try:
            f1, _ = _get_filters(_config(path1))
            f2, _ = _get_filters(_config(path2))
            assert f1 is not f2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_reload_forces_fresh_load(self):
        path = _make_s2us_file([{"Violent": 1}])
        try:
            cfg = _config(path)
            f1, _ = _get_filters(cfg)
            reload_filters()
            f2, _ = _get_filters(cfg)
            assert f1 is not f2
        finally:
            os.unlink(path)


# ── Tests evaluate_artifact_chain ────────────────────────────────

class TestEvaluateArtifactChain:
    def _artifact(self, values: list[float]) -> Artifact:
        return Artifact(
            artifact_type="Element",
            attribute="Fire",
            main_stat=SubStat(type="ATQ", value=100),
            grade="Legendaire",
            level=15,
            substats=[ArtifactSubStat(type=f"sub{i}", value=v) for i, v in enumerate(values)],
        )

    def test_keep_above_threshold(self):
        art = self._artifact([80, 90, 75, 85])
        v = evaluate_artifact_chain(art, _config("unused", artifact_eff_threshold=70))
        assert v.decision == "KEEP"

    def test_sell_below_threshold(self):
        art = self._artifact([10, 20, 15, 5])
        v = evaluate_artifact_chain(art, _config("unused", artifact_eff_threshold=70))
        assert v.decision == "SELL"

    def test_default_threshold_70(self):
        art = self._artifact([70, 70, 70, 70])
        v = evaluate_artifact_chain(art, _config("unused"))
        assert v.decision == "KEEP"

    def test_empty_substats(self):
        art = self._artifact([])
        v = evaluate_artifact_chain(art, _config("unused"))
        assert v.decision == "SELL"


# ── Tests Smart level (level=-1) ────────────────────────────────

class TestSmartLevelPowerUp:
    """Intégration : filtres avec level=-1 (Smart) et should_evaluate_now."""

    def setup_method(self):
        reload_filters()

    def _make_smart_filter_file(self):
        """Crée un fichier .S2US avec un filtre Violent level=-1 (Smart)."""
        return _make_s2us_file([{"Violent": 1, "Slot1": 1, "Level": -1}])

    def test_level0_smart_evaluates_via_projection(self):
        """Rune level 0 + filtre Smart → évaluation immédiate via projection +12."""
        path = self._make_smart_filter_file()
        try:
            rune = _rune(level=0)
            v = evaluate_chain(rune, _config(path))
            assert v.decision in ("KEEP", "SELL")
            assert v.source == "s2us"
        finally:
            os.unlink(path)

    def test_level3_smart_evaluates_normally(self):
        """Rune level 3 + filtre Smart → évaluation normale."""
        path = self._make_smart_filter_file()
        try:
            rune = _rune(level=3)
            v = evaluate_chain(rune, _config(path))
            assert v.decision in ("KEEP", "SELL")
            assert v.source == "s2us"
        finally:
            os.unlink(path)

    def test_level5_smart_evaluates_via_projection(self):
        """Rune level 5 + filtre Smart → évaluation immédiate via projection +12."""
        path = self._make_smart_filter_file()
        try:
            rune = _rune(level=5)
            v = evaluate_chain(rune, _config(path))
            assert v.decision in ("KEEP", "SELL")
            assert v.source == "s2us"
        finally:
            os.unlink(path)


class TestSmartPowerupOverride:
    """Vérifie que les overrides SmartPowerup depuis la config sont appliqués."""

    def setup_method(self):
        reload_filters()

    def test_config_overrides_smart_powerup(self):
        """SmartPowerup=False dans config override le fichier .S2US (SmartPowerup=True)."""
        path = _make_s2us_file(
            [{"Violent": 1, "Slot1": 1, "Level": -1}],
            SmartPowerup=True,
        )
        try:
            cfg = _config(path)
            cfg["s2us"]["global_settings"] = {"SmartPowerup": False, "RareLevel": 2}

            # Rune Rare level 3 : avec SmartPowerup=False et RareLevel=2,
            # le filtre exige level >= 6 pour Rare, donc should_evaluate_now → False
            # → aucun filtre évaluable → SELL
            rune = _rune(level=3, grade="Rare")
            v = evaluate_chain(rune, cfg)
            assert v.decision == "SELL"
            assert "Aucun filtre actif" in v.reason
        finally:
            os.unlink(path)

    def test_config_overrides_smart_powerup_enabled(self):
        """SmartPowerup=True dans config → évaluation à chaque checkpoint."""
        path = _make_s2us_file(
            [{"Violent": 1, "Slot1": 1, "Level": -1}],
            SmartPowerup=False,
        )
        try:
            cfg = _config(path)
            cfg["s2us"]["global_settings"] = {"SmartPowerup": True}

            # Rune Rare level 3 : avec SmartPowerup=True, pas de plancher grade,
            # level 3 est un checkpoint → évaluation normale
            rune = _rune(level=3, grade="Rare")
            v = evaluate_chain(rune, cfg)
            assert v.decision in ("KEEP", "SELL")
        finally:
            os.unlink(path)
