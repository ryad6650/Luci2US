from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import Rune, SubStat
from s2us_filter import (
    S2USFilter,
    calculate_efficiency_s2us,
    calculate_efficiency_swop,
    calculate_max_efficiency,
    evaluate_s2us,
    load_s2us_file,
    match_filter,
    should_evaluate_now,
)

S2US_FILE = r"C:\Users\louis\Downloads\Fleq6_V2.3_LATEGAME.S2US"


# ── Helpers ───────────────────────────────────────────────────────

def _make_rune(**kwargs) -> Rune:
    defaults = dict(
        set="Violent",
        slot=1,
        stars=6,
        grade="Legendaire",
        level=12,
        main_stat=SubStat(type="ATQ", value=160),
        prefix=None,
        substats=[],
        ancient=False,
    )
    defaults.update(kwargs)
    return Rune(**defaults)


def _empty_filter(**kwargs) -> S2USFilter:
    kwargs.setdefault("name", "test")
    return S2USFilter(**kwargs)


# ── 1. Test parser ────────────────────────────────────────────────

class TestParser:
    @pytest.fixture(scope="class")
    def loaded(self):
        return load_s2us_file(S2US_FILE)

    def test_filter_count(self, loaded):
        filters, _ = loaded
        assert len(filters) == 170

    def test_majority_smart(self, loaded):
        filters, _ = loaded
        smart = sum(1 for f in filters if f.level == -1)
        assert smart > len(filters) // 2

    def test_filter_has_content(self, loaded):
        filters, _ = loaded
        # Le filtre 1 (ACC, RES) a des sets, subs, etc. non vides
        f = filters[1]
        assert f.name  # nom decode
        assert any(v for v in f.sets.values())
        assert any(v for v in f.sub_requirements.values())

    def test_global_settings(self, loaded):
        _, settings = loaded
        assert "RareLevel" in settings
        assert "HeroLevel" in settings
        assert "LegendLevel" in settings

    def test_base64_name_decoded(self, loaded):
        filters, _ = loaded
        # Le nom ne doit pas etre du base64 brut
        f = filters[1]
        assert not f.name.endswith("==")


# ── 2. Test efficience S2US ───────────────────────────────────────

class TestEfficiencyS2US:
    @pytest.fixture
    def legend_rune(self):
        return _make_rune(
            set="Violent",
            slot=1,
            stars=6,
            grade="Legendaire",
            level=12,
            main_stat=SubStat(type="ATQ", value=160),
            prefix=SubStat(type="VIT", value=5),
            substats=[
                SubStat(type="ATQ%", value=20),
                SubStat(type="CC", value=12),
                SubStat(type="DC", value=14),
                SubStat(type="PV%", value=16),
            ],
        )

    def test_s2us_base(self, legend_rune):
        # Calcul a la main:
        # sub_ratios: 20/8=2.5, 12/6=2.0, 14/7=2.0, 16/8=2.0 -> sum=8.5
        # prefix: 5/6=0.833
        # ratio_sum = 9.333
        # diviseur = 1 + 1(prefix) + 4+4(legend+12) = 10
        # main_ratio = 1.0 (6*)
        # eff = (1.0 + 9.333) / 10 * 100 = 103.33
        eff = calculate_efficiency_s2us(legend_rune)
        assert eff == pytest.approx(103.33, abs=0.1)

    def test_s2us_no_prefix(self):
        rune = _make_rune(
            prefix=None,
            substats=[
                SubStat(type="ATQ%", value=20),
                SubStat(type="CC", value=12),
                SubStat(type="DC", value=14),
                SubStat(type="PV%", value=16),
            ],
        )
        # diviseur = 1 + 0 + 8 = 9
        # eff = (1.0 + 8.5) / 9 * 100 = 105.56
        eff = calculate_efficiency_s2us(rune)
        assert eff == pytest.approx(105.56, abs=0.1)

    def test_s2us_with_grind(self, legend_rune):
        eff_base = calculate_efficiency_s2us(legend_rune, grind=False)
        eff_grind = calculate_efficiency_s2us(legend_rune, grind=True)
        assert eff_grind > eff_base

    def test_s2us_with_gem(self, legend_rune):
        eff_base = calculate_efficiency_s2us(legend_rune, gem=0)
        eff_gem1 = calculate_efficiency_s2us(legend_rune, gem=1)
        # Gem remplace le pire sub (CC=2.0) par 1.0 si 1.0 > 2.0 -> non
        # Tous les subs ont ratio >= 1.0, gem n'ameliore pas
        # Ici le pire sub est DC a 14/7=2.0, remplacement par 1.0 serait pire
        # Donc gem ne change rien quand les subs sont deja bons
        assert eff_gem1 == pytest.approx(eff_base, abs=0.01)


# ── 3. Test efficience SWOP ──────────────────────────────────────

class TestEfficiencySWOP:
    @pytest.fixture
    def legend_rune(self):
        return _make_rune(
            prefix=SubStat(type="VIT", value=5),
            substats=[
                SubStat(type="ATQ%", value=20),
                SubStat(type="CC", value=12),
                SubStat(type="DC", value=14),
                SubStat(type="PV%", value=16),
            ],
        )

    def test_swop_base(self, legend_rune):
        # ATQ%: 20/40=0.5, CC: 12/30=0.4, DC: 14/35=0.4, PV%: 16/40=0.4
        # prefix VIT: 5/30=0.167
        # sum = 1.867
        # (1 + 1.867) / 2.8 * 100 = 102.38
        eff = calculate_efficiency_swop(legend_rune)
        assert eff == pytest.approx(102.38, abs=0.1)

    def test_swop_flat_conversion(self):
        rune = _make_rune(
            prefix=SubStat(type="PV", value=375),
            substats=[SubStat(type="RES", value=8)],
        )
        # PV: 375/(375*8)=0.125, RES: 8/(8*5)=0.2
        # (1 + 0.325) / 2.8 * 100 = 47.32
        eff = calculate_efficiency_swop(rune)
        assert eff == pytest.approx(47.32, abs=0.1)


# ── 4. Test max efficiency ───────────────────────────────────────

class TestMaxEfficiency:
    def test_max_eff_at_plus12(self):
        rune = _make_rune(
            level=12,
            substats=[SubStat(type="ATQ%", value=16)],
        )
        eff = calculate_efficiency_swop(rune)
        max_eff = calculate_max_efficiency(rune, method="SWOP")
        assert max_eff == pytest.approx(eff, abs=0.01)

    def test_max_eff_below_12(self):
        rune = _make_rune(
            level=0,
            grade="Legendaire",
            substats=[
                SubStat(type="ATQ%", value=8),
                SubStat(type="CC", value=6),
                SubStat(type="DC", value=7),
                SubStat(type="PV%", value=8),
            ],
        )
        eff = calculate_efficiency_swop(rune)
        max_eff = calculate_max_efficiency(rune, method="SWOP")
        remaining = (12 - 0) // 3  # 4
        expected_bonus = remaining * (1 / 2.8 * 100)
        assert max_eff == pytest.approx(eff + expected_bonus, abs=0.01)


# ── 5. Test matching ─────────────────────────────────────────────

class TestMatching:
    @pytest.fixture
    def hero_rune(self):
        return _make_rune(
            set="Violent",
            slot=2,
            stars=6,
            grade="Heroique",
            level=0,
            main_stat=SubStat(type="VIT", value=7),
            prefix=None,
            substats=[
                SubStat(type="PV%", value=8),
                SubStat(type="RES", value=8),
                SubStat(type="DC", value=7),
                SubStat(type="DEF%", value=8),
            ],
        )

    def test_strict_filter_no_match(self, hero_rune):
        # Filtre strict: Violent, slot 2, main SPD, sub SPD requis
        f = S2USFilter(
            name="Strict SPD",
            sets={s: (s == "Violent") for s in [
                "Violent", "Swift", "Despair", "Will", "Rage", "Fatal",
                "Energy", "Blade", "Focus", "Guard", "Endure",
                "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
                "Determination", "Enhance", "Accuracy", "Tolerance",
                "Intangible", "Seal", "Shield",
            ]},
            slots={f"Slot{i}": (i == 2) for i in range(1, 7)},
            grades={"Rare": False, "Hero": True, "Legend": True},
            stars={"FiveStars": False, "SixStars": True},
            main_stats={
                "MainSPD": True, "MainHP": False, "MainHP2": False,
                "MainATK": False, "MainATK2": False, "MainDEF": False,
                "MainDEF2": False, "MainCR": False, "MainCD": False,
                "MainACC": False, "MainRES": False,
            },
            sub_requirements={
                "SPD": 1, "HP": 0, "HP2": 0, "ATK": 0, "ATK2": 0,
                "DEF": 0, "DEF2": 0, "CR": 0, "CD": 0, "ACC": 0, "RES": 0,
            },
            min_values={k: 0 for k in [
                "SPD", "HP", "HP2", "ATK", "ATK2", "DEF", "DEF2",
                "CR", "CD", "ACC", "RES",
            ]},
        )
        # La rune n'a pas de sub VIT -> pas de match
        assert match_filter(hero_rune, f) is False

    def test_relaxed_filter_match(self, hero_rune):
        # Filtre laxiste: Violent, slot 2, 6*, 1 sub optionnel parmi PV%/RES/DC/DEF%
        f = S2USFilter(
            name="Relaxed",
            sets={s: (s == "Violent") for s in [
                "Violent", "Swift", "Despair", "Will", "Rage", "Fatal",
                "Energy", "Blade", "Focus", "Guard", "Endure",
                "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
                "Determination", "Enhance", "Accuracy", "Tolerance",
                "Intangible", "Seal", "Shield",
            ]},
            slots={f"Slot{i}": (i == 2) for i in range(1, 7)},
            grades={"Rare": False, "Hero": True, "Legend": True},
            stars={"FiveStars": False, "SixStars": True},
            main_stats={k: False for k in [
                "MainSPD", "MainHP", "MainHP2", "MainATK", "MainATK2",
                "MainDEF", "MainDEF2", "MainCR", "MainCD",
                "MainACC", "MainRES",
            ]},
            sub_requirements={
                "SPD": 0, "HP": 2, "HP2": 0, "ATK": 0, "ATK2": 0,
                "DEF": 2, "DEF2": 0, "CR": 0, "CD": 2, "ACC": 0, "RES": 2,
            },
            min_values={k: 0 for k in [
                "SPD", "HP", "HP2", "ATK", "ATK2", "DEF", "DEF2",
                "CR", "CD", "ACC", "RES",
            ]},
            optional_count=1,
        )
        # La rune a PV%, RES, DC, DEF% -> 4 optionnels presents, >= 1
        assert match_filter(hero_rune, f) is True

    def test_grade_mismatch(self, hero_rune):
        f = _empty_filter(
            grades={"Rare": False, "Hero": False, "Legend": True},
        )
        # Rune est Heroique, filtre exige Legend only
        assert match_filter(hero_rune, f) is False

    def test_ancient_filter(self):
        rune_ancient = _make_rune(ancient=True, substats=[])
        rune_normal = _make_rune(ancient=False, substats=[])
        f_ancient = _empty_filter(ancient_type="Ancient")
        f_not_ancient = _empty_filter(ancient_type="NotAncient")
        f_any = _empty_filter(ancient_type="")

        assert match_filter(rune_ancient, f_ancient) is True
        assert match_filter(rune_normal, f_ancient) is False
        assert match_filter(rune_ancient, f_not_ancient) is False
        assert match_filter(rune_normal, f_not_ancient) is True
        assert match_filter(rune_ancient, f_any) is True
        assert match_filter(rune_normal, f_any) is True


# ── 6. Test evaluate multi-filtres ───────────────────────────────

class TestEvaluate:
    def test_keep_first_match(self):
        rune = _make_rune(
            set="Violent",
            substats=[SubStat(type="VIT", value=18)],
        )
        f1 = _empty_filter(
            name="SPD filter",
            sub_requirements={"SPD": 1},
            min_values={"SPD": 10},
        )
        f2 = _empty_filter(name="Catch-all")
        verdict = evaluate_s2us(rune, [f1, f2], {})
        assert verdict.decision == "KEEP"
        assert verdict.reason == "SPD filter"

    def test_sell_no_match(self):
        rune = _make_rune(substats=[])
        f = _empty_filter(
            name="SPD only",
            sub_requirements={"SPD": 1},
        )
        verdict = evaluate_s2us(rune, [f], {})
        assert verdict.decision == "SELL"

    def test_disabled_filter_skipped(self):
        rune = _make_rune(substats=[])
        f = _empty_filter(name="disabled", enabled=False)
        verdict = evaluate_s2us(rune, [f], {})
        assert verdict.decision == "SELL"


# ── 7. Test Smart Filter ─────────────────────────────────────────

class TestSmartFilter:
    @pytest.fixture
    def smart_filter(self):
        return _empty_filter(level=-1)

    @pytest.fixture
    def settings_smart_on(self):
        return {"SmartPowerup": True}

    def test_level_0_not_ready(self, smart_filter, settings_smart_on):
        rune = _make_rune(level=0, grade="Legendaire")
        assert should_evaluate_now(rune, smart_filter, settings_smart_on) is False

    def test_level_3_ready(self, smart_filter, settings_smart_on):
        rune = _make_rune(level=3, grade="Legendaire")
        assert should_evaluate_now(rune, smart_filter, settings_smart_on) is True

    def test_level_5_not_checkpoint(self, smart_filter, settings_smart_on):
        rune = _make_rune(level=5, grade="Legendaire")
        assert should_evaluate_now(rune, smart_filter, settings_smart_on) is False

    def test_level_6_ready(self, smart_filter, settings_smart_on):
        rune = _make_rune(level=6, grade="Legendaire")
        assert should_evaluate_now(rune, smart_filter, settings_smart_on) is True

    def test_fixed_level_target(self):
        # Level=4 -> target +12
        f = _empty_filter(level=4)
        settings = {"SmartPowerup": True}
        rune_11 = _make_rune(level=11)
        rune_12 = _make_rune(level=12)
        assert should_evaluate_now(rune_11, f, settings) is False
        assert should_evaluate_now(rune_12, f, settings) is True

    def test_smart_powerup_off_rarity_floor(self):
        f = _empty_filter(level=-1)
        settings = {"SmartPowerup": False}

        # Rare a +3 -> floor est 6, pas encore
        rune_rare = _make_rune(level=3, grade="Rare")
        assert should_evaluate_now(rune_rare, f, settings) is False

        # Rare a +6 -> ok
        rune_rare_6 = _make_rune(level=6, grade="Rare")
        assert should_evaluate_now(rune_rare_6, f, settings) is True

        # Hero a +6 -> floor est 9, pas encore
        rune_hero = _make_rune(level=6, grade="Heroique")
        assert should_evaluate_now(rune_hero, f, settings) is False

        # Legend a +9 -> floor est 12, pas encore
        rune_legend = _make_rune(level=9, grade="Legendaire")
        assert should_evaluate_now(rune_legend, f, settings) is False

        # Legend a +12 -> ok
        rune_legend_12 = _make_rune(level=12, grade="Legendaire")
        assert should_evaluate_now(rune_legend_12, f, settings) is True
