"""Orchestration verdict KEEP/SELL basée sur SWLens RL Score.

Remplace le système S2US filter-based. `evaluate_artifact_chain` inchangé
(artifacts restent orthogonaux).
"""
from __future__ import annotations

from models import Artifact, Rune, Verdict
from swlens import KEEP_THRESHOLD_DEFAULT, rl_score


def evaluate_chain(rune: Rune, config: dict) -> Verdict:
    threshold = config.get("swlens", {}).get("keep_threshold", KEEP_THRESHOLD_DEFAULT)
    result = rl_score(rune)
    decision = "KEEP" if result.total >= threshold else "SELL"
    return Verdict(
        decision=decision,
        source="swlens",
        reason=f"RL Score {result.total} ({result.category})",
        score=float(result.total),
        details={
            "rl_score": result.total,
            "category": result.category,
            "breakdown": result.substat_breakdown,
            "innate_bonus": result.innate_bonus,
        },
    )


def evaluate_artifact_chain(artifact: Artifact, config: dict) -> Verdict:
    total = sum(sub.value for sub in artifact.substats)
    max_possible = len(artifact.substats) * 100
    efficiency = (total / max_possible * 100) if max_possible > 0 else 0.0
    threshold = config.get("artifact_eff_threshold", 70)
    if efficiency >= threshold:
        return Verdict(
            decision="KEEP", source="swlens",
            reason=f"Efficience artifact {efficiency:.1f}% >= {threshold}%",
            score=efficiency,
        )
    return Verdict(
        decision="SELL", source="swlens",
        reason=f"Efficience artifact {efficiency:.1f}% < {threshold}%",
        score=efficiency,
    )
