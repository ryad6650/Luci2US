"""Tests for profile_loader – SWEX JSON profile parsing."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from profile_loader import load_profile_from_dict, load_profile_from_file


def _make_rune(slot: int, set_id: int = 13, stars: int = 6) -> dict:
    """Build a minimal SWEX rune dict."""
    return {
        "rune_id": slot * 100,
        "slot_no": slot,
        "set_id": set_id,
        "class": stars,
        "rank": 5,  # Legendaire
        "upgrade_curr": 12,
        "pri_eff": [4, 63],         # ATQ%
        "prefix_eff": [8, 5],       # VIT
        "sec_eff": [
            [9, 12, 0, 0],          # CC
            [10, 14, 0, 0],         # DC
            [2, 10, 0, 0],          # PV%
            [6, 8, 0, 0],           # DEF%
        ],
    }


def _make_unit(unit_master_id: int, attribute: int, stars: int,
               level: int, runes: list[dict]) -> dict:
    return {
        "unit_master_id": unit_master_id,
        "attribute": attribute,
        "class": stars,
        "unit_level": level,
        "runes": runes,
    }


def _make_profile(units: list[dict], inv_runes: list[dict] | None = None) -> dict:
    return {
        "wizard_info": {
            "wizard_name": "TestWizard",
            "wizard_level": 50,
        },
        "unit_list": units,
        "runes": inv_runes or [],
    }


def _write_json(data: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


class TestLoadProfile:
    def test_basic_parsing(self) -> None:
        runes_m1 = [_make_rune(1), _make_rune(2)]
        runes_m2 = [_make_rune(1, set_id=3)]  # Swift
        units = [
            _make_unit(14102, 1, 6, 40, runes_m1),  # Eau
            _make_unit(19513, 5, 5, 35, runes_m2),   # Tenebres
        ]
        profile_data = _make_profile(units)
        path = _write_json(profile_data)

        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)

        assert result["wizard_name"] == "TestWizard"
        assert result["level"] == 50
        assert len(result["monsters"]) == 2
        # 2 + 1 equipped runes, no inventory
        assert len(result["runes"]) == 3

    def test_monster_fields(self) -> None:
        units = [_make_unit(14102, 2, 6, 40, [])]  # Feu
        path = _write_json(_make_profile(units))

        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)

        mon = result["monsters"][0]
        assert mon.element == "Feu"
        assert mon.stars == 6
        assert mon.level == 40
        assert mon.equipped_runes == []

    def test_equipped_runes_attached(self) -> None:
        runes = [_make_rune(slot) for slot in range(1, 7)]
        units = [_make_unit(14102, 1, 6, 40, runes)]
        path = _write_json(_make_profile(units))

        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)

        mon = result["monsters"][0]
        assert len(mon.equipped_runes) == 6
        slots = [r.slot for r in mon.equipped_runes]
        assert slots == [1, 2, 3, 4, 5, 6]

    def test_rune_parsing_details(self) -> None:
        units = [_make_unit(14102, 1, 6, 40, [_make_rune(1)])]
        path = _write_json(_make_profile(units))

        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)

        rune = result["monsters"][0].equipped_runes[0]
        assert rune.set == "Violent"
        assert rune.slot == 1
        assert rune.stars == 6
        assert rune.grade == "Legendaire"
        assert rune.level == 12
        assert rune.main_stat.type == "ATQ%"
        assert rune.prefix.type == "VIT"
        assert len(rune.substats) == 4

    def test_inventory_runes(self) -> None:
        inv = [_make_rune(3, set_id=25)]  # Rage, inventory
        units = [_make_unit(14102, 1, 6, 40, [_make_rune(1)])]
        path = _write_json(_make_profile(units, inv_runes=inv))

        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)

        # 1 equipped + 1 inventory
        assert len(result["runes"]) == 2

    def test_monster_name_fallback(self) -> None:
        units = [_make_unit(99999, 3, 5, 35, [])]
        path = _write_json(_make_profile(units))

        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)

        assert result["monsters"][0].name == "Monster #99999"


class TestLoadProfileFromDict:
    """Test load_profile_from_dict produces the same result as load_profile_from_file (except source)."""

    def test_same_result_except_source(self) -> None:
        runes_m1 = [_make_rune(1), _make_rune(2)]
        runes_m2 = [_make_rune(1, set_id=3)]
        inv = [_make_rune(3, set_id=25)]
        units = [
            _make_unit(14102, 1, 6, 40, runes_m1),
            _make_unit(19513, 5, 5, 35, runes_m2),
        ]
        profile_data = _make_profile(units, inv_runes=inv)

        # Load from file
        path = _write_json(profile_data)
        try:
            from_file = load_profile_from_file(path)
        finally:
            os.unlink(path)

        # Load from dict
        from_dict = load_profile_from_dict(profile_data)

        # Source differs
        assert from_file["source"] == "manual"
        assert from_dict["source"] == "auto"

        # Everything else is identical
        assert from_file["wizard_name"] == from_dict["wizard_name"]
        assert from_file["level"] == from_dict["level"]
        assert len(from_file["monsters"]) == len(from_dict["monsters"])
        assert len(from_file["runes"]) == len(from_dict["runes"])

        for mf, md in zip(from_file["monsters"], from_dict["monsters"]):
            assert mf.name == md.name
            assert mf.element == md.element
            assert mf.stars == md.stars
            assert mf.level == md.level
            assert len(mf.equipped_runes) == len(md.equipped_runes)

    def test_source_is_auto(self) -> None:
        profile_data = _make_profile([_make_unit(14102, 1, 6, 40, [])])
        result = load_profile_from_dict(profile_data)
        assert result["source"] == "auto"

    def test_source_is_manual(self) -> None:
        profile_data = _make_profile([_make_unit(14102, 1, 6, 40, [])])
        path = _write_json(profile_data)
        try:
            result = load_profile_from_file(path)
        finally:
            os.unlink(path)
        assert result["source"] == "manual"
