from models import Rune, SubStat, Verdict
from ui.controllers.scan_controller import ScanController


def test_emits_rune_evaluated(qapp, qtbot):
    ctrl = ScanController()
    r = Rune(set="Violent", slot=2, stars=6, grade="Heroique", level=9,
             main_stat=SubStat("VIT", 25), prefix=None, substats=[])
    v = Verdict(decision="KEEP", source="s2us", reason="", score=180)

    with qtbot.waitSignal(ctrl.rune_evaluated, timeout=500) as blocker:
        ctrl.push_from_worker(r, v, mana=50, swop=(85.0, 120.0), s2us=(120.0, 140.0))

    emitted = blocker.args
    assert emitted[0].set == "Violent"
    assert emitted[1].decision == "KEEP"
    assert emitted[2] == 50
