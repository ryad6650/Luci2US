from __future__ import annotations

from models import Artifact, Rune, Verdict
from s2us_filter import (
    calculate_efficiency1, calculate_efficiency2, calculate_score,
    evaluate_s2us, load_s2us_file, should_evaluate_now, S2USFilter,
)

# ── Cache module-level ───────────────────────────────────────────

_cached_filters: list[S2USFilter] | None = None
_cached_settings: dict | None = None
_cached_path: str | None = None


def _get_filters(config: dict) -> tuple[list[S2USFilter], dict]:
    global _cached_filters, _cached_settings, _cached_path

    path = config["s2us"]["filter_file"]
    if _cached_filters is not None and _cached_path == path:
        filters, settings = _cached_filters, dict(_cached_settings)  # type: ignore[arg-type]
    else:
        filters, settings = load_s2us_file(path)
        _cached_filters = filters
        _cached_settings = settings
        _cached_path = path

    overrides = config.get("s2us", {}).get("global_settings", {})
    if overrides:
        settings = {**settings, **overrides}

    return filters, settings


def reload_filters() -> None:
    """Forcer le rechargement du cache (ex: changement de fichier .S2US)."""
    global _cached_filters, _cached_settings, _cached_path
    _cached_filters = None
    _cached_settings = None
    _cached_path = None


# ── Evaluation ───────────────────────────────────────────────────

def _eff_details(rune: Rune) -> dict:
    """Calcule Score + Efficiency1 + Efficiency2 (+ alias SWOP/S2US)."""
    eff1 = calculate_efficiency1(rune)          # ex-S2US (méthode par défaut)
    eff2 = calculate_efficiency2(rune)          # ex-SWOP (style SW classique)
    score = calculate_score(rune)

    # SWEX peut fournir son propre style SW → on le privilégie s'il existe
    eff_swop = rune.swex_efficiency if rune.swex_efficiency is not None else float(eff2)
    max_swop = rune.swex_max_efficiency if rune.swex_max_efficiency is not None else float(eff2)

    return {
        "score": score,
        "efficiency1": eff1,
        "efficiency2": eff2,
        # Alias conservés pour RuneCard / tabs / DB
        "eff_swop": eff_swop,
        "max_swop": max_swop,
        "eff_s2us": float(eff1),
        "max_s2us": float(eff1),
    }


def evaluate_chain(rune: Rune, config: dict) -> Verdict:
    details = _eff_details(rune)

    path = config.get("s2us", {}).get("filter_file", "")
    if not path:
        return Verdict(
            decision="SELL",
            source="s2us",
            reason="Aucun fichier filtre configuré",
            score=details["eff_swop"],
            details=details,
        )

    filters, settings = _get_filters(config)

    evaluable = [f for f in filters if f.enabled and should_evaluate_now(rune, f, settings)]
    if not evaluable:
        if any(f.enabled for f in filters):
            return Verdict(
                decision="POWER-UP",
                source="s2us",
                reason="Attente checkpoint",
                score=details["eff_swop"],
                details=details,
            )
        return Verdict(
            decision="SELL",
            source="s2us",
            reason="Aucun filtre actif",
            score=details["eff_swop"],
            details=details,
        )

    verdict = evaluate_s2us(rune, evaluable, settings)
    verdict.details = details
    verdict.score = details["eff_swop"]
    return verdict


def evaluate_artifact_chain(artifact: Artifact, config: dict) -> Verdict:
    total = sum(sub.value for sub in artifact.substats)
    max_possible = len(artifact.substats) * 100
    efficiency = (total / max_possible * 100) if max_possible > 0 else 0.0

    threshold = config["s2us"].get("artifact_eff_threshold", 70)

    if efficiency >= threshold:
        return Verdict(
            decision="KEEP",
            source="s2us",
            reason=f"Efficience artifact {efficiency:.1f}% >= {threshold}%",
            score=efficiency,
        )
    return Verdict(
        decision="SELL",
        source="s2us",
        reason=f"Efficience artifact {efficiency:.1f}% < {threshold}%",
        score=efficiency,
    )
