from models import (
    SubStat, ArtifactSubStat, Rune, Verdict, Artifact,
    ROLL_MAX_6, SETS_FR, SETS_EN, SET_FR_TO_EN,
    STATS_FR, GRADES_FR, GRADE_SUBSTAT_COUNT, MAIN_STATS_BY_SLOT,
)


def test_substat():
    s = SubStat("ATQ%", 7.0)
    assert s.type == "ATQ%"
    assert s.value == 7.0
    assert s.grind_value == 0.0


def test_substat_with_grind():
    s = SubStat("DEF%", 5.0, 3.0)
    assert s.grind_value == 3.0


def test_artifact_substat():
    a = ArtifactSubStat("DMG_CD", 4.0)
    assert a.type == "DMG_CD"
    assert a.value == 4.0


def test_rune():
    main = SubStat("ATQ", 160.0)
    sub1 = SubStat("VIT", 5.0)
    r = Rune("Violent", 1, 6, "Legendaire", 15, main, None, [sub1])
    assert r.set == "Violent"
    assert r.slot == 1
    assert r.ancient is False
    assert r.prefix is None
    assert len(r.substats) == 1


def test_rune_ancient():
    main = SubStat("ATQ", 160.0)
    r = Rune("Violent", 1, 6, "Legendaire", 15, main, None, [], ancient=True)
    assert r.ancient is True


def test_verdict():
    v = Verdict("keep", "rule_engine", "Good efficiency")
    assert v.decision == "keep"
    assert v.score is None
    assert v.details is None


def test_verdict_with_optionals():
    v = Verdict("sell", "ai", "Low rolls", score=3.2, details={"eff": 50})
    assert v.score == 3.2
    assert v.details == {"eff": 50}


def test_artifact():
    main = SubStat("ATQ%", 12.0)
    subs = [ArtifactSubStat("DMG_CD", 4.0)]
    a = Artifact("element", "feu", main, "Legendaire", 15, subs)
    assert a.artifact_type == "element"
    assert len(a.substats) == 1


def test_roll_max_6_count():
    assert len(ROLL_MAX_6) == 11


def test_sets_fr_count():
    assert len(SETS_FR) == 23


def test_sets_en_count():
    assert len(SETS_EN) == 23


def test_set_fr_to_en_mapping():
    assert SET_FR_TO_EN["Rapide"] == "Swift"
    assert SET_FR_TO_EN["Desespoir"] == "Despair"
    assert SET_FR_TO_EN["Bouclier"] == "Shield"
    assert SET_FR_TO_EN["Violent"] == "Violent"
    assert len(SET_FR_TO_EN) == 23


def test_stats_fr():
    assert len(STATS_FR) == 11
    assert "ATQ%" in STATS_FR
    assert "CC" in STATS_FR


def test_grades_fr():
    assert len(GRADES_FR) == 5


def test_grade_substat_count():
    assert GRADE_SUBSTAT_COUNT["Normal"] == 0
    assert GRADE_SUBSTAT_COUNT["Legendaire"] == 4
    assert len(GRADE_SUBSTAT_COUNT) == 5


def test_main_stats_by_slot():
    assert MAIN_STATS_BY_SLOT[1] == ["ATQ"]
    assert MAIN_STATS_BY_SLOT[3] == ["DEF"]
    assert MAIN_STATS_BY_SLOT[5] == ["PV"]
    assert len(MAIN_STATS_BY_SLOT) == 6
    assert "CC" in MAIN_STATS_BY_SLOT[4]
    assert "RES" in MAIN_STATS_BY_SLOT[6]
