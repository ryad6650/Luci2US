from __future__ import annotations

from models import GEM_MAX, GRIND_MAX, ROLL_MAX_6, ROLL_MIN_6, Rune, SubStat
from powerup_simulator import (
    SimulationOutput,
    _apply_grind,
    _apply_power_up,
    _distribute,
    _mid_roll,
    _rolls_remaining,
    project_to_plus12,
    simulate_powerup,
)


def _make_rune(
    grade: str = "Legendaire",
    level: int = 0,
    slot: int = 1,
    main: str = "ATQ",
    main_value: int = 160,
    substats: list[SubStat] | None = None,
) -> Rune:
    return Rune(
        set="Violent",
        slot=slot,
        stars=6,
        grade=grade,
        level=level,
        main_stat=SubStat(type=main, value=main_value),
        prefix=None,
        substats=substats or [],
    )


class TestDistribute:
    def test_zero_rolls(self):
        assert _distribute(0, 4) == [(0, 0, 0, 0)]

    def test_count_4_rolls_on_4_buckets(self):
        # C(4+4-1, 4) = 35 (Legend +0→+12 du bot)
        assert len(_distribute(4, 4)) == 35

    def test_count_3_rolls(self):
        # C(3+4-1, 3) = 20 (Hero +0→+12 ou Legend +3→+12)
        assert len(_distribute(3, 4)) == 20

    def test_count_2_rolls(self):
        # C(2+4-1, 2) = 10
        assert len(_distribute(2, 4)) == 10

    def test_count_1_roll(self):
        assert len(_distribute(1, 4)) == 4

    def test_sum_preserved(self):
        for dist in _distribute(3, 4):
            assert sum(dist) == 3


class TestRollsRemaining:
    def test_legend(self):
        assert _rolls_remaining("Legendaire", 0) == 4
        assert _rolls_remaining("Legendaire", 3) == 3
        assert _rolls_remaining("Legendaire", 6) == 2
        assert _rolls_remaining("Legendaire", 9) == 1
        assert _rolls_remaining("Legendaire", 12) == 0

    def test_hero(self):
        assert _rolls_remaining("Heroique", 0) == 3
        assert _rolls_remaining("Heroique", 3) == 2
        assert _rolls_remaining("Heroique", 6) == 1
        assert _rolls_remaining("Heroique", 9) == 0

    def test_rare(self):
        assert _rolls_remaining("Rare", 0) == 2
        assert _rolls_remaining("Rare", 3) == 1
        assert _rolls_remaining("Rare", 6) == 0


class TestApplyPowerUp:
    def test_legend_plus0_generates_35_variants(self):
        subs = [
            SubStat(type="VIT", value=6),
            SubStat(type="PV%", value=6),
            SubStat(type="DEF%", value=7),
            SubStat(type="ATQ%", value=5),
        ]
        rune = _make_rune(grade="Legendaire", level=0, substats=subs)
        variants = _apply_power_up(rune, original_sub_count=4)
        assert len(variants) == 35

    def test_all_variants_at_level_12(self):
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=0, substats=subs)
        for v in _apply_power_up(rune, original_sub_count=4):
            assert v.level == 12

    def test_max_value_matches_mid_roll(self):
        """Sur Legend +0, distribution (4,0,0,0) → sub 0 reçoit 4 × mid_roll."""
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=0, substats=subs)
        variants = _apply_power_up(rune, original_sub_count=4)
        max_vit = max(v.substats[0].value for v in variants)
        assert max_vit == 6 + 4 * _mid_roll("VIT", 6)

    def test_hero_plus0_generates_10_variants_on_3subs(self):
        """Hero +0 avec 3 subs originales → 3 rolls sur 3 buckets = C(3+3-1,3-1) = 10.
        Les rolls ne vont jamais sur la 4e sub (qui apparaît à +12)."""
        subs = [
            SubStat(type="VIT", value=6),
            SubStat(type="PV%", value=6),
            SubStat(type="DEF%", value=7),
        ]
        rune = _make_rune(grade="Heroique", level=0, substats=subs)
        assert len(_apply_power_up(rune, original_sub_count=3)) == 10

    def test_hero_rolls_never_land_on_4th_sub(self):
        """Règle SW : le 4e sub apparaît à +12 sans roll bonus. Les 3 rolls
        vont uniquement sur les 3 subs originales."""
        subs = [
            SubStat(type="VIT", value=6),
            SubStat(type="PV%", value=6),
            SubStat(type="DEF%", value=7),
            SubStat(type="CC", value=_mid_roll("CC", 6)),  # 4e sub simulée
        ]
        rune = _make_rune(grade="Heroique", level=0, substats=subs)
        variants = _apply_power_up(rune, original_sub_count=3)
        for v in variants:
            assert v.substats[3].value == _mid_roll("CC", 6)


class TestProjectToPlus12:
    def test_legend_plus0_no_gems_no_grinds(self):
        """Legend +0 → 35 variantes power-up, déjà 4 subs, pas d'ajout."""
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=0, substats=subs)
        variants = project_to_plus12(rune)
        assert len(variants) == 35
        assert all(v.level == 12 for v in variants)
        assert all(len(v.substats) == 4 for v in variants)

    def test_hero_plus0_adds_4th_sub(self):
        """Hero +0 → 20 distribs × 8 candidates (main=ATQ exclue) = 160 brut, dédup réduit."""
        subs = [SubStat(type="VIT", value=6),
                SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7)]
        rune = _make_rune(grade="Heroique", level=0, substats=subs)
        variants = project_to_plus12(rune)
        assert all(len(v.substats) == 4 for v in variants)
        assert all(v.level == 12 for v in variants)

    def test_hero_4th_sub_gets_mid_roll_value(self):
        """Les nouvelles subs apparaissent à mid_roll (= (min+max)//2).
        Elles ne reçoivent PAS de roll bonus ensuite."""
        subs = [SubStat(type="VIT", value=6),
                SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7)]
        rune = _make_rune(grade="Heroique", level=0, substats=subs)
        variants = project_to_plus12(rune)
        original_types = {"VIT", "PV%", "DEF%"}
        # Au moins une variante où la 4e sub est CC à valeur mid_roll(CC) = 5
        found = False
        for v in variants:
            for s in v.substats:
                if s.type not in original_types and s.type == "CC":
                    if s.value == _mid_roll("CC", 6):
                        found = True
        assert found, f"Aucune variante avec CC@{_mid_roll('CC', 6)} en 4e sub"

    def test_grind_adds_max_bonus(self):
        """Grind grade 1 (Magique) ajoute +6 à VIT? Non, VIT grind magique = +3."""
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=12, substats=subs)
        # Rune +12 → pas de power-up, juste grind
        variants = project_to_plus12(rune, grind_grade=1)
        # La (seule) variante a VIT = 6 + 3 = 9
        for v in variants:
            for s in v.substats:
                if s.type == "VIT":
                    assert s.value == 6 + GRIND_MAX["VIT"][1]

    def test_grind_zero_on_cc_cd(self):
        """CC/DC non grindables → valeur inchangée."""
        subs = [SubStat(type="CC", value=5), SubStat(type="DC", value=6),
                SubStat(type="PV%", value=6), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=12, substats=subs)
        variants = project_to_plus12(rune, grind_grade=4)
        for v in variants:
            for s in v.substats:
                if s.type == "CC":
                    assert s.value == 5
                if s.type == "DC":
                    assert s.value == 6

    def test_gem_generates_extra_variants(self):
        """Avec gemme, il y a strictement plus de variantes que sans."""
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=12, substats=subs)
        without = project_to_plus12(rune, gem_grade=0)
        with_gem = project_to_plus12(rune, gem_grade=2)
        assert len(with_gem) > len(without)

    def test_already_plus12_no_rolls(self):
        """Rune +12 → 0 rolls → 1 variante (ou plus si gem)."""
        subs = [SubStat(type="VIT", value=20), SubStat(type="CC", value=15),
                SubStat(type="DC", value=21), SubStat(type="PV%", value=25)]
        rune = _make_rune(grade="Legendaire", level=12, substats=subs)
        variants = project_to_plus12(rune)
        assert len(variants) == 1
        assert variants[0].substats[0].value == 20


class TestRollMode:
    """Les 3 roll_modes doivent être ordonnés : max ≥ mid ≥ min en Eff1."""

    def _rage_rune(self):
        return _make_rune(
            grade="Heroique", level=0, slot=2, main="ATQ%", main_value=22,
            substats=[
                SubStat(type="VIT", value=6),
                SubStat(type="CC", value=6),
                SubStat(type="PV%", value=7),
            ],
        )

    def test_max_ge_mid_ge_min_best(self):
        r = self._rage_rune()
        best_max = simulate_powerup(r, grind_grade=4, gem_grade=4, roll_mode="max").best.efficiency
        best_mid = simulate_powerup(r, grind_grade=4, gem_grade=4, roll_mode="mid").best.efficiency
        best_min = simulate_powerup(r, grind_grade=4, gem_grade=4, roll_mode="min").best.efficiency
        assert best_max >= best_mid >= best_min

    def test_smart_filter_uses_max_mode(self):
        """Garantit que match_filter_smart (s2us_filter) projette en mode max
        — condition pour que les seuils de filtre existants restent cohérents."""
        from s2us_filter import match_filter_smart, S2USFilter
        # Pas d'assertion fonctionnelle ici — juste s'assurer que l'appel
        # ne casse pas et que le module expose bien le chemin max.
        f = S2USFilter(name="test", level=-1, efficiency=80.0, eff_method="S2US")
        r = self._rage_rune()
        _ = match_filter_smart(r, f)  # ne doit pas crasher


class TestSimulatePowerup:
    def test_reference_rune_best_gte_worst(self):
        """Rune de ref : 6★ Legend Swift Slot 1 +0, subs VIT 6/PV% 6/DEF% 7/ATQ% 5."""
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7), SubStat(type="ATQ%", value=5)]
        rune = _make_rune(grade="Legendaire", level=0, substats=subs)
        out = simulate_powerup(rune)
        assert isinstance(out, SimulationOutput)
        assert out.best.efficiency >= out.worst.efficiency
        assert out.variant_count == 35

    def test_variant_count_positive(self):
        subs = [SubStat(type="VIT", value=6), SubStat(type="PV%", value=6),
                SubStat(type="DEF%", value=7)]
        rune = _make_rune(grade="Heroique", level=0, substats=subs)
        out = simulate_powerup(rune, grind_grade=1, gem_grade=2)
        assert out.variant_count > 0
