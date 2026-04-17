"""Tests for swex_bridge module."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from models import Rune, SubStat
from swex_bridge import (
    SWEX_RANK,
    SWEX_SET_ID,
    SWEX_TYPE_ID,
    SWEXBridge,
    parse_rune,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RUNE_PAYLOAD = {
    "event": "BattleDungeonResult_v2",
    "wizard_id": 123456,
    "set_id": 13,
    "slot_no": 2,
    "class": 6,
    "rank": 5,
    "upgrade_curr": 12,
    "pri_eff": [8, 39],
    "prefix_eff": [9, 5],
    "sec_eff": [
        [4, 15, 3, 0],
        [6, 10, 0, 0],
        [2, 12, 0, 0],
        [10, 7, 0, 0],
    ],
}


# ---------------------------------------------------------------------------
# Mapping tests
# ---------------------------------------------------------------------------

class TestMappings:
    def test_type_id_mapping(self):
        assert SWEX_TYPE_ID[1] == "PV"
        assert SWEX_TYPE_ID[4] == "ATQ%"
        assert SWEX_TYPE_ID[8] == "VIT"
        assert SWEX_TYPE_ID[9] == "CC"
        assert SWEX_TYPE_ID[12] == "PRE"

    def test_set_id_mapping(self):
        assert SWEX_SET_ID[13] == "Violent"
        assert SWEX_SET_ID[3] == "Rapide"
        assert SWEX_SET_ID[11] == "Will"
        assert SWEX_SET_ID[25] == "Rage"
        assert SWEX_SET_ID[8] == "Desespoir"

    def test_rank_mapping(self):
        assert SWEX_RANK[1] == "Normal"
        assert SWEX_RANK[3] == "Rare"
        assert SWEX_RANK[5] == "Legendaire"


# ---------------------------------------------------------------------------
# parse_rune tests
# ---------------------------------------------------------------------------

class TestParseRune:
    def test_basic_fields(self):
        rune = parse_rune(SAMPLE_RUNE_PAYLOAD)
        assert isinstance(rune, Rune)
        assert rune.set == "Violent"
        assert rune.slot == 2
        assert rune.stars == 6
        assert rune.grade == "Legendaire"
        assert rune.level == 12

    def test_main_stat(self):
        rune = parse_rune(SAMPLE_RUNE_PAYLOAD)
        assert rune.main_stat.type == "VIT"
        assert rune.main_stat.value == 39

    def test_prefix(self):
        rune = parse_rune(SAMPLE_RUNE_PAYLOAD)
        assert rune.prefix is not None
        assert rune.prefix.type == "CC"
        assert rune.prefix.value == 5

    def test_substats(self):
        rune = parse_rune(SAMPLE_RUNE_PAYLOAD)
        assert len(rune.substats) == 4
        assert rune.substats[0].type == "ATQ%"
        assert rune.substats[0].value == 15
        assert rune.substats[0].grind_value == 3

    def test_no_prefix(self):
        payload = {**SAMPLE_RUNE_PAYLOAD, "prefix_eff": [0, 0]}
        rune = parse_rune(payload)
        assert rune.prefix is None

    def test_nested_rune_key(self):
        """parse_rune should handle payload with a 'rune' wrapper key."""
        payload = {"rune": SAMPLE_RUNE_PAYLOAD}
        rune = parse_rune(payload)
        assert rune.set == "Violent"


# ---------------------------------------------------------------------------
# SWEXBridge integration tests
# ---------------------------------------------------------------------------

class TestSWEXBridge:
    def test_available_false_when_no_dir(self, tmp_path):
        bridge = SWEXBridge(drops_dir=tmp_path / "nonexistent")
        assert bridge.available is False

    def test_available_true_when_dir_exists(self, tmp_path):
        bridge = SWEXBridge(drops_dir=tmp_path)
        assert bridge.available is True

    def test_detects_new_json(self, tmp_path):
        received: list[Rune] = []
        bridge = SWEXBridge(
            drops_dir=tmp_path,
            on_rune_drop=lambda r: received.append(r),
            poll_interval=0.1,
        )
        bridge.start()
        try:
            drop_file = tmp_path / "drop_001.json"
            drop_file.write_text(json.dumps(SAMPLE_RUNE_PAYLOAD), encoding="utf-8")
            # Give the polling thread time to pick it up
            time.sleep(0.5)
        finally:
            bridge.stop()

        assert len(received) == 1
        assert received[0].set == "Violent"

    def test_does_not_reprocess_same_file(self, tmp_path):
        received: list[Rune] = []
        bridge = SWEXBridge(
            drops_dir=tmp_path,
            on_rune_drop=lambda r: received.append(r),
            poll_interval=0.1,
        )
        drop_file = tmp_path / "drop_001.json"
        drop_file.write_text(json.dumps(SAMPLE_RUNE_PAYLOAD), encoding="utf-8")

        bridge.start()
        try:
            time.sleep(0.5)
        finally:
            bridge.stop()

        assert len(received) == 1

    def test_upgrade_callback(self, tmp_path):
        upgrades: list[tuple] = []
        payload = {**SAMPLE_RUNE_PAYLOAD, "event": "UpgradeRune"}
        bridge = SWEXBridge(
            drops_dir=tmp_path,
            on_rune_upgrade=lambda r, evt, lvl: upgrades.append((r, evt, lvl)),
            poll_interval=0.1,
        )
        bridge.start()
        try:
            (tmp_path / "up_001.json").write_text(json.dumps(payload), encoding="utf-8")
            time.sleep(0.5)
        finally:
            bridge.stop()

        assert len(upgrades) == 1
        assert upgrades[0][1] == "UpgradeRune"
        assert upgrades[0][2] == 12

    def test_profile_loaded_callback(self, tmp_path):
        profile_data = {
            "wizard_info": {"wizard_id": 123456, "wizard_name": "TestWizard"},
            "unit_list": [{"unit_id": 1, "name": "Belladeon"}],
            "runes": [{"rune_id": 100, "set_id": 13}],
        }
        received: list[dict] = []
        bridge = SWEXBridge(
            drops_dir=tmp_path,
            on_profile_loaded=lambda data: received.append(data),
            poll_interval=0.1,
        )
        bridge.start()
        try:
            profile_file = tmp_path / "profile_1713300000.json"
            profile_file.write_text(json.dumps(profile_data), encoding="utf-8")
            time.sleep(0.5)
        finally:
            bridge.stop()

        assert len(received) == 1
        assert received[0]["wizard_info"]["wizard_id"] == 123456
        assert received[0]["unit_list"][0]["name"] == "Belladeon"
        assert received[0]["runes"][0]["set_id"] == 13

    def test_profile_not_dispatched_as_rune(self, tmp_path):
        """A profile file should NOT trigger on_rune_drop."""
        runes: list[Rune] = []
        profiles: list[dict] = []
        bridge = SWEXBridge(
            drops_dir=tmp_path,
            on_rune_drop=lambda r: runes.append(r),
            on_profile_loaded=lambda d: profiles.append(d),
            poll_interval=0.1,
        )
        bridge.start()
        try:
            (tmp_path / "profile_9999.json").write_text(
                json.dumps({"wizard_info": {}}), encoding="utf-8"
            )
            time.sleep(0.5)
        finally:
            bridge.stop()

        assert len(profiles) == 1
        assert len(runes) == 0
