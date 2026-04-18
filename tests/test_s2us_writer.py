"""Round-trip tests pour s2us_writer (inverse de s2us_filter.load_s2us_file)."""
from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from s2us_filter import S2USFilter, load_s2us_file
from s2us_writer import save_s2us_file, _encode_name, serialize_filter


def _make_minimal_filter(name: str = "SPD CR CD ACC") -> S2USFilter:
    return S2USFilter(
        name=name,
        enabled=True,
        sets={"Violent": True, "Swift": True},
        slots={f"Slot{i}": (i == 2) for i in range(1, 7)},
        grades={"Rare": False, "Hero": True, "Legend": True},
        stars={"FiveStars": False, "SixStars": True},
        main_stats={"MainSPD": True},
        ancient_type="",
        sub_requirements={"SPD": 1, "CR": 2, "CD": 2, "ACC": 2},
        min_values={"SPD": 12, "CR": 6, "CD": 9, "ACC": 0},
        optional_count=2,
        level=4,
        efficiency=80.0,
        eff_method="S2US",
        grind=4,
        gem=4,
        powerup_mandatory=0,
        powerup_optional=0,
        innate_required={},
    )


def test_encode_name_roundtrip():
    encoded = _encode_name("SPD CR CD ACC")
    assert base64.b64decode(encoded).decode("utf-8") == "SPD CR CD ACC"


def test_serialize_filter_sets_name_as_b64():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert base64.b64decode(raw["Name"]).decode("utf-8") == "SPD CR CD ACC"


def test_serialize_filter_has_all_sets_as_int():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert raw["Violent"] == 1
    assert raw["Swift"] == 1
    assert raw["Despair"] == 0
    assert raw["Will"] == 0


def test_serialize_filter_has_sub_and_min_fields():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert raw["SubSPD"] == 1
    assert raw["MinSPD"] == 12
    assert raw["SubCR"] == 2
    assert raw["MinCR"] == 6
    assert raw["SubHP"] == 0


def test_serialize_filter_writes_slots_and_grades():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert raw["Slot2"] == 1
    assert raw["Slot1"] == 0
    assert raw["Hero"] == 1
    assert raw["Legend"] == 1
    assert raw["Rare"] == 0
    assert raw["SixStars"] == 1
    assert raw["FiveStars"] == 0


def test_serialize_filter_writes_ancient_flags():
    f = _make_minimal_filter()
    f.ancient_type = "Ancient"
    raw = serialize_filter(f)
    assert raw["Ancient"] == 1
    assert raw["Normal"] == 0
    assert raw["_AncientMode"] == "Ancient"

    f.ancient_type = "NotAncient"
    raw = serialize_filter(f)
    assert raw["Ancient"] == 0
    assert raw["Normal"] == 1
    assert raw["_AncientMode"] == "NotAncient"

    # "Tous" : même empreinte binaire que le bot (1,0) + marqueur vide.
    f.ancient_type = ""
    raw = serialize_filter(f)
    assert raw["Ancient"] == 1
    assert raw["Normal"] == 0
    assert raw["_AncientMode"] == ""


def test_serialize_filter_innate_flag_and_specifics():
    f = _make_minimal_filter()
    f.innate_required = {"SPD": True, "CR": True}
    raw = serialize_filter(f)
    assert raw["Innate"] == 1
    assert raw["InnateSPD"] == 1
    assert raw["InnateCR"] == 1
    assert raw["InnateHP"] == 0


def test_serialize_filter_no_innate_flag_when_empty():
    f = _make_minimal_filter()
    f.innate_required = {}
    raw = serialize_filter(f)
    assert raw["Innate"] == 0


def test_save_and_reload_preserves_one_filter(tmp_path: Path):
    path = tmp_path / "out.s2us"
    f = _make_minimal_filter()
    save_s2us_file(str(path), [f], {"SmartPowerup": True, "RareLevel": 2,
                                     "HeroLevel": 4, "LegendLevel": 4})
    reloaded, settings = load_s2us_file(str(path))
    assert len(reloaded) == 1
    g = reloaded[0]
    assert g.name == f.name
    assert g.enabled == f.enabled
    assert g.level == f.level
    assert g.optional_count == f.optional_count
    assert g.efficiency == f.efficiency
    assert g.grind == f.grind
    assert g.gem == f.gem
    assert g.sub_requirements["SPD"] == 1
    assert g.min_values["CR"] == 6
    assert g.sets["Violent"] is True
    assert g.sets["Despair"] is False
    assert g.slots["Slot2"] is True
    assert g.grades["Hero"] is True
    assert g.stars["SixStars"] is True
    assert settings["SmartPowerup"] is True
    assert settings["RareLevel"] == 2


def test_save_and_reload_preserves_multiple_filters(tmp_path: Path):
    path = tmp_path / "multi.s2us"
    a = _make_minimal_filter("Filter A")
    b = _make_minimal_filter("Filter B")
    b.efficiency = 95.0
    save_s2us_file(str(path), [a, b], {})
    reloaded, _ = load_s2us_file(str(path))
    assert [f.name for f in reloaded] == ["Filter A", "Filter B"]
    assert reloaded[1].efficiency == 95.0


def test_save_file_is_utf8_json_with_runefilter_envelope(tmp_path: Path):
    path = tmp_path / "envelope.s2us"
    save_s2us_file(str(path), [_make_minimal_filter()], {})
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    assert "RuneFilter" in data
    assert "Filter" in data["RuneFilter"]
    assert isinstance(data["RuneFilter"]["Filter"], list)


def test_save_file_global_settings_written_in_envelope(tmp_path: Path):
    path = tmp_path / "settings.s2us"
    save_s2us_file(str(path), [], {
        "SmartPowerup": False, "RareLevel": 1, "HeroLevel": 3, "LegendLevel": 4,
    })
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    rf = data["RuneFilter"]
    assert rf["SmartPowerup"] is False
    assert rf["RareLevel"] == 1
    assert rf["HeroLevel"] == 3
    assert rf["LegendLevel"] == 4
