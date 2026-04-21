from models import Verdict
from ui.scan.optimizer_recommendation import OptimizerRecommendationPanel


def _mk_verdict(decision: str, score: float, s2us: str = "32%", swop: str = "70%") -> Verdict:
    return Verdict(
        decision=decision,
        source="test",
        reason="Efficience sous le seuil",
        score=score,
        details={"s2us": s2us, "swop": swop, "reason": "Efficience sous le seuil"},
    )


def test_empty_state(qapp):
    w = OptimizerRecommendationPanel()
    assert w._decision.text() == ""
    assert not w._confirm_btn.isVisible()


def test_sell_verdict(qapp):
    w = OptimizerRecommendationPanel()
    w.show()
    w.set_verdict(_mk_verdict("SELL", 1.949, s2us="32%", swop="70%"))
    assert w._decision.text() == "VENDRE"
    assert w._confirm_btn.text() == "Confirmer Vendre"
    assert w._gauge_s2us.value() == 0.32
    assert w._gauge_swop.value() == 0.70


def test_keep_verdict_switches_colors(qapp):
    w = OptimizerRecommendationPanel()
    w.show()
    w.set_verdict(_mk_verdict("KEEP", 8.5, s2us="95%", swop="88%"))
    assert w._decision.text() == "GARDER"
    assert w._confirm_btn.text() == "Confirmer Garder"
