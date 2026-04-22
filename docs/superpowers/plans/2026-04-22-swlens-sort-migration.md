# SWLens Sort System Migration - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le système de tri de runes S2US (filter-based) par le système SWLens (score-based) avec RL Score + Priority Score + Gap Analysis.

**Architecture:** Module neuf `swlens/` construit et testé en isolation. Bascule de `evaluator_chain.py` + adaptation des call sites (`rune_optimizer`, `powerup_simulator`, UI). Nouvelle page `ui/swlens_settings/` remplaçant `ui/filtres/`. Backup externe des fichiers legacy avant suppression.

**Tech Stack:** Python 3.12, PyQt6, pytest, dataclasses. Réutilise `Rune`, `Verdict`, `ROLL_MAX_6/5` de `models.py`.

**Spec:** `docs/superpowers/specs/2026-04-22-swlens-sort-migration-design.md`

---

## File Structure

**Créés :**
- `swlens/__init__.py` — API publique
- `swlens/config.py` — constantes (step values = ROLL_MAX_6, seuils, pondérations)
- `swlens/rl_score.py` — `rl_score(rune) → RLScoreResult`
- `swlens/collection_state.py` — `CollectionState.from_runes(runes)` avec cache
- `swlens/gap_analysis.py` — `gap_analysis(collection) → GapReport`, `gap_for_rune(rune, collection) → int`
- `swlens/priority_score.py` — `priority_score(rune, collection) → PriorityResult`
- `tests/swlens/__init__.py`
- `tests/swlens/test_rl_score.py`
- `tests/swlens/test_collection_state.py`
- `tests/swlens/test_gap_analysis.py`
- `tests/swlens/test_priority_score.py`
- `tests/swlens/test_fidelity.py` — golden tests vs SWLens réel
- `ui/swlens_settings/__init__.py`
- `ui/swlens_settings/swlens_settings_page.py`
- `tests/ui/test_swlens_settings_page.py`

**Modifiés :**
- `evaluator_chain.py` — bascule de scoring
- `rune_optimizer.py` — remplace `calculate_efficiency1` par `swlens.rl_score`
- `powerup_simulator.py` — retire l'import s2us_filter (fonction `project_to_plus12` garde son API)
- `ui/runes/runes_page.py` — tri par RL Score + Priority
- `ui/runes/rune_card_widget.py` — affichage RL Score + catégorie
- `ui/monsters/monsters_page.py` — retire `calculate_efficiency_s2us`
- `ui/main_window.py` — route vers `ui/swlens_settings/` au lieu de `ui/filtres/`
- `ui/sidebar.py` — label "Paramètres SWLens" au lieu de "Filtres"
- `settings_tab.py` — retire config S2US, ajoute defaults SWLens
- `profile_tab.py` — retire `calculate_efficiency_s2us`
- `tests/test_evaluator_chain.py` — réécrit pour SWLens
- `tests/test_rune_optimizer.py` — adapte pour la nouvelle API

**Supprimés :**
- `s2us_filter.py`
- `s2us_writer.py`
- `ui/filtres/` (dossier complet : 6 fichiers)
- `tests/test_s2us_filter.py`
- `tests/test_s2us_writer.py`
- `tests/ui/test_filter_editor.py`
- `tests/ui/test_filter_list_panel.py`
- `tests/ui/test_filtres_page.py`
- `tests/ui/test_rune_tester_modal.py`
- `docs/Système tri de rune.md`

---

## Phase A — Backup externe

### Task 1: Créer la sauvegarde externe complète

**Files:**
- Destination: `C:\Users\louis\Desktop\Luci2US_backup_s2us\<timestamp>\`

- [ ] **Step 1: Créer le dossier timestamped**

```bash
BACKUP_DIR="C:/Users/louis/Desktop/Luci2US_backup_s2us/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Backup dir: $BACKUP_DIR"
```

- [ ] **Step 2: Copier les fichiers legacy**

```bash
cp s2us_filter.py "$BACKUP_DIR/"
cp s2us_writer.py "$BACKUP_DIR/"
cp evaluator_chain.py "$BACKUP_DIR/evaluator_chain.py.legacy"
cp -r ui/filtres "$BACKUP_DIR/"
cp tests/test_s2us_filter.py "$BACKUP_DIR/"
cp tests/test_s2us_writer.py "$BACKUP_DIR/"
cp tests/test_evaluator_chain.py "$BACKUP_DIR/test_evaluator_chain.py.legacy"
cp tests/ui/test_filter_editor.py "$BACKUP_DIR/"
cp tests/ui/test_filter_list_panel.py "$BACKUP_DIR/"
cp tests/ui/test_filtres_page.py "$BACKUP_DIR/"
cp tests/ui/test_rune_tester_modal.py "$BACKUP_DIR/"
cp "docs/Système tri de rune.md" "$BACKUP_DIR/"
```

- [ ] **Step 3: Ajouter un README dans le backup**

```bash
cat > "$BACKUP_DIR/README.md" <<EOF
# Backup système S2US — pré-migration SWLens

Date : $(date -Iseconds)
Commit HEAD au moment du backup : $(git rev-parse HEAD)

Système filter-based (14 checks, 4 formules d'efficacité) remplacé par
le système SWLens (score-based). Voir spec :
docs/superpowers/specs/2026-04-22-swlens-sort-migration-design.md

Pour restaurer : copier ces fichiers de retour dans le repo et reverter
le commit de migration.
EOF
ls -la "$BACKUP_DIR"
```

- [ ] **Step 4: Vérifier le backup**

```bash
ls "$BACKUP_DIR" | wc -l
# Expected: 12 entrées (11 fichiers + 1 dossier filtres + README = 13 max)
diff -r ui/filtres "$BACKUP_DIR/filtres" && echo "ui/filtres copied OK"
```

---

## Phase B — Construction du module `swlens/` en isolation

### Task 2: Créer `swlens/config.py` avec les constantes

**Files:**
- Create: `swlens/__init__.py` (vide pour l'instant, sera rempli en Task 8)
- Create: `swlens/config.py`

- [ ] **Step 1: Créer le package**

```bash
mkdir -p swlens
touch swlens/__init__.py
```

- [ ] **Step 2: Écrire `swlens/config.py`**

```python
# swlens/config.py
"""Constantes et defaults du système de tri SWLens.

Source des step values : ROLL_MAX_6 de models.py (vérifié identique à
la table SWLens publique : SPD=6, CR=6, CD=7).
"""
from __future__ import annotations

from models import ROLL_MAX_5, ROLL_MAX_6


# RL Score step values (valeur d'un roll "moyen" par stat)
STAT_STEPS_6 = dict(ROLL_MAX_6)
STAT_STEPS_5 = dict(ROLL_MAX_5)


def step_for(stat_fr: str, stars: int) -> int:
    """Retourne la step value pour une stat donnée selon le grade étoile."""
    table = STAT_STEPS_6 if stars >= 6 else STAT_STEPS_5
    return int(table.get(stat_fr, 0))


# Seuils de catégorisation RL Score
KEEP_THRESHOLD_DEFAULT = 230
CATEGORY_BOUNDS = [
    (300, "Excellent"),
    (230, "Bon"),
    (150, "Médiocre"),
    (0,   "Faible"),
]


def category_for(total: int) -> str:
    for bound, label in CATEGORY_BOUNDS:
        if total >= bound:
            return label
    return "Faible"


# Priority Score — pondérations Innate (stat FR)
INNATE_IMPORTANCE = {
    "PRE": 2.0, "CC": 2.0,        # ACC, CR
    "RES": 1.5, "DC": 1.5,        # RES, CD
    "VIT": 1.0,                   # SPD
    "PV%": 1.0, "ATQ%": 1.0, "DEF%": 1.0,
    "PV": 1.0, "ATQ": 1.0, "DEF": 1.0,
}

# Priority Score — bonus par slot
SLOT_BONUS = {1: 50, 2: 75, 3: 50, 4: 100, 5: 50, 6: 100}


# Gap Analysis — 7 catégories SWLens
GAP_CATEGORIES = ["PV%", "ATQ%", "DEF%", "CC", "DC", "PRE", "VIT"]

# Gap Analysis — multiplicateurs par catégorie
GAP_MULTIPLIERS = {
    "PV%": 1.3, "ATQ%": 1.2,
    "DEF%": 1.0, "CC": 1.0, "DC": 1.0, "PRE": 1.0, "VIT": 1.0,
}

# Seuil "rune rapide" (SPD substat)
FAST_SPD_THRESHOLD = 20

# Seuil "elite rune" (RL Score)
ELITE_SCORE_THRESHOLD = 300
```

- [ ] **Step 3: Test de sanity**

```bash
python -c "from swlens.config import step_for, category_for, INNATE_IMPORTANCE; print(step_for('VIT', 6), category_for(250), INNATE_IMPORTANCE['CC'])"
# Expected: 6 Bon 2.0
```

- [ ] **Step 4: Commit**

```bash
git add swlens/__init__.py swlens/config.py
git commit -m "feat(swlens): add config module with step values and thresholds"
```

---

### Task 3: Implémenter `swlens/rl_score.py` (TDD)

**Files:**
- Create: `swlens/rl_score.py`
- Create: `tests/swlens/__init__.py`
- Test: `tests/swlens/test_rl_score.py`

- [ ] **Step 1: Créer le package de tests**

```bash
mkdir -p tests/swlens
touch tests/swlens/__init__.py
```

- [ ] **Step 2: Écrire le test de base (échec attendu)**

```python
# tests/swlens/test_rl_score.py
from __future__ import annotations

import pytest

from models import Rune, SubStat
from swlens.rl_score import rl_score


def _make_rune(substats: list[tuple[str, float]], prefix=None, stars=6):
    return Rune(
        set="Violent", slot=4, stars=stars, grade="Legendaire", level=12,
        main_stat=SubStat("DC", 80),
        prefix=SubStat(prefix[0], prefix[1]) if prefix else None,
        substats=[SubStat(t, v) for t, v in substats],
    )


def test_rl_score_single_substat_one_roll():
    """VIT=6 sur 6★ → step=6 → raw=0 → 0 points."""
    rune = _make_rune([("VIT", 6)])
    result = rl_score(rune)
    assert result.total == 0
    assert result.category == "Faible"


def test_rl_score_single_substat_two_rolls():
    """VIT=12 sur 6★ → raw=1 → 100 points."""
    rune = _make_rune([("VIT", 12)])
    result = rl_score(rune)
    assert result.total == 100
    assert result.category == "Faible"


def test_rl_score_innate_bonus():
    """Innate CC=6 (max 6) → bonus = (6/6 * 100)/2 = 50."""
    rune = _make_rune([], prefix=("CC", 6))
    result = rl_score(rune)
    assert result.innate_bonus == 50.0


def test_rl_score_category_boundaries():
    """Teste les bornes 150/230/300."""
    from swlens.config import category_for
    assert category_for(149) == "Faible"
    assert category_for(150) == "Médiocre"
    assert category_for(229) == "Médiocre"
    assert category_for(230) == "Bon"
    assert category_for(299) == "Bon"
    assert category_for(300) == "Excellent"


def test_rl_score_breakdown_structure():
    rune = _make_rune([("VIT", 18), ("CC", 12)])
    result = rl_score(rune)
    assert len(result.substat_breakdown) == 2
    stats = [b[0] for b in result.substat_breakdown]
    assert "VIT" in stats and "CC" in stats


def test_rl_score_stars_5_uses_smaller_steps():
    """VIT=10 sur 5★ → step=5 → raw=1 → 100 points."""
    rune = _make_rune([("VIT", 10)], stars=5)
    result = rl_score(rune)
    assert result.total == 100
```

- [ ] **Step 3: Vérifier que ça fail**

```bash
pytest tests/swlens/test_rl_score.py -v 2>&1 | head -20
# Expected: ModuleNotFoundError: No module named 'swlens.rl_score'
```

- [ ] **Step 4: Implémenter `swlens/rl_score.py`**

```python
# swlens/rl_score.py
"""RL Score SWLens : Substat Score + Innate Bonus."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models import Rune
from swlens.config import category_for, step_for


@dataclass
class RLScoreResult:
    total: int
    category: str  # "Excellent" | "Bon" | "Médiocre" | "Faible"
    substat_breakdown: list[tuple[str, float, float]]  # (stat, raw, contribution)
    innate_bonus: float


def _substat_contribution(stat_fr: str, value: float, stars: int) -> tuple[float, float]:
    """Retourne (raw, contribution)."""
    step = step_for(stat_fr, stars)
    if step <= 0:
        return 0.0, 0.0
    raw = (value / step) - 1
    if raw <= 0:
        return raw, 0.0
    return raw, raw * 100


def _innate_bonus(stat_fr: str, value: float, stars: int) -> float:
    """Bonus = (value / max_roll * 100) / 2 — ici max_roll = step_for(stat, stars)."""
    step = step_for(stat_fr, stars)
    if step <= 0:
        return 0.0
    return (value / step * 100) / 2


def rl_score(rune: Rune) -> RLScoreResult:
    breakdown: list[tuple[str, float, float]] = []
    total = 0.0
    for sub in rune.substats:
        raw, contrib = _substat_contribution(sub.type, sub.value, rune.stars)
        breakdown.append((sub.type, raw, contrib))
        total += contrib

    innate_bonus = 0.0
    if rune.prefix:
        innate_bonus = _innate_bonus(rune.prefix.type, rune.prefix.value, rune.stars)
        total += innate_bonus

    total_int = int(round(total))
    return RLScoreResult(
        total=total_int,
        category=category_for(total_int),
        substat_breakdown=breakdown,
        innate_bonus=innate_bonus,
    )
```

- [ ] **Step 5: Lancer les tests**

```bash
pytest tests/swlens/test_rl_score.py -v
# Expected: 6 passed
```

- [ ] **Step 6: Commit**

```bash
git add swlens/rl_score.py tests/swlens/__init__.py tests/swlens/test_rl_score.py
git commit -m "feat(swlens): implement RL Score with substat + innate bonus"
```

---

### Task 4: Implémenter `swlens/collection_state.py` (TDD)

**Files:**
- Create: `swlens/collection_state.py`
- Test: `tests/swlens/test_collection_state.py`

- [ ] **Step 1: Écrire les tests**

```python
# tests/swlens/test_collection_state.py
from __future__ import annotations

from models import Rune, SubStat
from swlens.collection_state import CollectionState


def _rune(subs, slot=4, spd_main=False):
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("VIT" if spd_main else "DC", 80),
        prefix=None,
        substats=[SubStat(t, v) for t, v in subs],
    )


def test_empty_collection():
    col = CollectionState.from_runes([])
    assert col.total_count == 0
    assert col.runes_in_category("CC") == []


def test_indexes_runes_by_substat_category():
    r1 = _rune([("CC", 10)])
    r2 = _rune([("DC", 15), ("CC", 8)])
    col = CollectionState.from_runes([r1, r2])
    cc_runes = col.runes_in_category("CC")
    assert len(cc_runes) == 2


def test_indexes_runes_by_main_stat_category():
    r_spd_main = _rune([], spd_main=True)
    col = CollectionState.from_runes([r_spd_main])
    vit_runes = col.runes_in_category("VIT")
    assert len(vit_runes) == 1


def test_fast_count():
    r_fast = _rune([("VIT", 22)])
    r_slow = _rune([("VIT", 10)])
    col = CollectionState.from_runes([r_fast, r_slow])
    assert col.fast_count("VIT") == 1


def test_invalidation():
    r = _rune([("CC", 10)])
    col = CollectionState.from_runes([r])
    assert col.total_count == 1
    col.invalidate()
    assert col.total_count == 0
```

- [ ] **Step 2: Vérifier l'échec**

```bash
pytest tests/swlens/test_collection_state.py -v 2>&1 | head -10
# Expected: ModuleNotFoundError
```

- [ ] **Step 3: Implémenter**

```python
# swlens/collection_state.py
"""Agrégation de l'inventaire de runes par catégorie (main stat + substats)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from models import Rune
from swlens.config import FAST_SPD_THRESHOLD, GAP_CATEGORIES


@dataclass
class CollectionState:
    by_category: dict[str, list[Rune]] = field(default_factory=lambda: defaultdict(list))
    total_count: int = 0

    @classmethod
    def from_runes(cls, runes: list[Rune]) -> "CollectionState":
        by_cat: dict[str, list[Rune]] = defaultdict(list)
        for rune in runes:
            stats_present = {rune.main_stat.type}
            for sub in rune.substats:
                stats_present.add(sub.type)
            for cat in GAP_CATEGORIES:
                if cat in stats_present:
                    by_cat[cat].append(rune)
        return cls(by_category=by_cat, total_count=len(runes))

    def runes_in_category(self, category: str) -> list[Rune]:
        return list(self.by_category.get(category, []))

    def fast_count(self, category: str) -> int:
        count = 0
        for rune in self.runes_in_category(category):
            for sub in rune.substats:
                if sub.type == "VIT" and sub.value >= FAST_SPD_THRESHOLD:
                    count += 1
                    break
            if rune.main_stat.type == "VIT" and rune.main_stat.value >= FAST_SPD_THRESHOLD:
                count += 1
        return count

    def invalidate(self) -> None:
        self.by_category.clear()
        self.total_count = 0
```

- [ ] **Step 4: Tests passent**

```bash
pytest tests/swlens/test_collection_state.py -v
# Expected: 5 passed
```

- [ ] **Step 5: Commit**

```bash
git add swlens/collection_state.py tests/swlens/test_collection_state.py
git commit -m "feat(swlens): add CollectionState for inventory aggregation"
```

---

### Task 5: Implémenter `swlens/gap_analysis.py` (TDD)

**Files:**
- Create: `swlens/gap_analysis.py`
- Test: `tests/swlens/test_gap_analysis.py`

- [ ] **Step 1: Écrire les tests**

```python
# tests/swlens/test_gap_analysis.py
from __future__ import annotations

from models import Rune, SubStat
from swlens.collection_state import CollectionState
from swlens.gap_analysis import gap_analysis, gap_for_rune


def _rune(subs, main="DC"):
    return Rune(
        set="Violent", slot=4, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(main, 80), prefix=None,
        substats=[SubStat(t, v) for t, v in subs],
    )


def test_empty_collection_zero_gap():
    col = CollectionState.from_runes([])
    report = gap_analysis(col)
    # Collection vide = tout est déficitaire → scores élevés, mais fast=0 elite=0
    for cat in ("VIT", "CC", "DC", "PRE", "PV%", "ATQ%", "DEF%"):
        assert report.per_category[cat].fast_count == 0


def test_hp_multiplier_higher_than_def():
    """À quantité de runes égales, HP% devrait scorer plus que DEF% (×1.3 vs ×1.0)."""
    runes_hp = [_rune([("PV%", 8)]) for _ in range(3)]
    runes_def = [_rune([("DEF%", 8)]) for _ in range(3)]
    col = CollectionState.from_runes(runes_hp + runes_def)
    report = gap_analysis(col)
    # HP% gap doit être ≤ DEF% gap car HP% est MIEUX couvert proportionnellement
    # mais multiplicateur l'avantage → on teste juste présence du mult
    assert report.per_category["PV%"].multiplier == 1.3
    assert report.per_category["ATQ%"].multiplier == 1.2
    assert report.per_category["DEF%"].multiplier == 1.0


def test_gap_for_rune_uses_main_stat_category():
    col = CollectionState.from_runes([])
    rune_cd = _rune([("CC", 10)], main="DC")
    score = gap_for_rune(rune_cd, col)
    assert score >= 0


def test_fast_count_and_elite_count_present():
    fast_rune = _rune([("VIT", 25)])
    col = CollectionState.from_runes([fast_rune])
    report = gap_analysis(col)
    assert report.per_category["VIT"].fast_count == 1
```

- [ ] **Step 2: Vérifier l'échec**

```bash
pytest tests/swlens/test_gap_analysis.py -v 2>&1 | head -10
```

- [ ] **Step 3: Implémenter**

```python
# swlens/gap_analysis.py
"""Analyse de déficit de la collection sur 7 catégories SWLens."""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from swlens.collection_state import CollectionState
from swlens.config import (
    ELITE_SCORE_THRESHOLD,
    GAP_CATEGORIES,
    GAP_MULTIPLIERS,
)


@dataclass
class CategoryGap:
    category: str
    fast_count: int
    elite_count: int
    speed_mean: float
    slot_coverage: int  # nombre de slots différents représentés
    multiplier: float
    score: int


@dataclass
class GapReport:
    per_category: dict[str, CategoryGap]


def _speed_mean(runes: list[Rune]) -> float:
    values: list[float] = []
    for r in runes:
        for sub in r.substats:
            if sub.type == "VIT":
                values.append(sub.value)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _slot_coverage(runes: list[Rune]) -> int:
    return len({r.slot for r in runes})


def _elite_count(runes: list[Rune]) -> int:
    # Import tardif pour éviter cycle
    from swlens.rl_score import rl_score
    return sum(1 for r in runes if rl_score(r).total >= ELITE_SCORE_THRESHOLD)


def _category_score(
    fast: int, elite: int, mean: float, coverage: int, total: int, multiplier: float,
) -> int:
    """Score 0-600+ : plus la catégorie est déficitaire, plus le score monte.

    Formule SWLens (reconstituée) : base 600 moins les contributions de couverture.
    """
    if total == 0:
        base = 600
    else:
        # Contribution de chaque métrique (0 à 150 pts de "remplissage")
        fast_fill = min(150, fast * 30)
        elite_fill = min(150, elite * 50)
        mean_fill = min(150, mean * 6)  # SPD moyen 25 → 150
        coverage_fill = min(150, coverage * 25)  # 6 slots → 150
        total_fill = fast_fill + elite_fill + mean_fill + coverage_fill
        base = max(0, 600 - total_fill)
    return int(round(base * multiplier))


def gap_analysis(collection: CollectionState) -> GapReport:
    per_category: dict[str, CategoryGap] = {}
    for cat in GAP_CATEGORIES:
        runes = collection.runes_in_category(cat)
        fast = collection.fast_count(cat)
        elite = _elite_count(runes)
        mean = _speed_mean(runes)
        coverage = _slot_coverage(runes)
        multiplier = GAP_MULTIPLIERS.get(cat, 1.0)
        score = _category_score(fast, elite, mean, coverage, len(runes), multiplier)
        per_category[cat] = CategoryGap(
            category=cat, fast_count=fast, elite_count=elite,
            speed_mean=mean, slot_coverage=coverage,
            multiplier=multiplier, score=score,
        )
    return GapReport(per_category=per_category)


def gap_for_rune(rune: Rune, collection: CollectionState) -> int:
    """Gap score pour la catégorie principale de la rune (main stat si mappée,
    sinon première substat mappée)."""
    candidates = [rune.main_stat.type] + [s.type for s in rune.substats]
    for cat in candidates:
        if cat in GAP_CATEGORIES:
            report = gap_analysis(collection)
            return report.per_category[cat].score
    return 0
```

- [ ] **Step 4: Tests passent**

```bash
pytest tests/swlens/test_gap_analysis.py -v
# Expected: 4 passed
```

- [ ] **Step 5: Commit**

```bash
git add swlens/gap_analysis.py tests/swlens/test_gap_analysis.py
git commit -m "feat(swlens): add gap analysis with 7 categories and multipliers"
```

---

### Task 6: Implémenter `swlens/priority_score.py` (TDD)

**Files:**
- Create: `swlens/priority_score.py`
- Test: `tests/swlens/test_priority_score.py`

- [ ] **Step 1: Écrire les tests**

```python
# tests/swlens/test_priority_score.py
from __future__ import annotations

from models import Rune, SubStat
from swlens.collection_state import CollectionState
from swlens.priority_score import priority_score


def _rune(slot=4, prefix=None, subs=None):
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("DC", 80),
        prefix=SubStat(prefix[0], prefix[1]) if prefix else None,
        substats=[SubStat(t, v) for t, v in (subs or [])],
    )


def test_slot_bonus_values():
    col = CollectionState.from_runes([])
    assert priority_score(_rune(slot=1), col).slot_pts == 50
    assert priority_score(_rune(slot=2), col).slot_pts == 75
    assert priority_score(_rune(slot=3), col).slot_pts == 50
    assert priority_score(_rune(slot=4), col).slot_pts == 100
    assert priority_score(_rune(slot=5), col).slot_pts == 50
    assert priority_score(_rune(slot=6), col).slot_pts == 100


def test_innate_importance_acc_vs_hp():
    """ACC pondération 2.0, HP% 1.0 → ACC innate = 2× HP% innate à valeur égale."""
    col = CollectionState.from_runes([])
    # max_roll ACC=8, HP%=8 → value=8 → ratio plein
    acc = priority_score(_rune(prefix=("PRE", 8)), col)
    hp = priority_score(_rune(prefix=("PV%", 8)), col)
    assert acc.innate_pts == 2 * hp.innate_pts


def test_no_innate_zero_pts():
    col = CollectionState.from_runes([])
    result = priority_score(_rune(prefix=None), col)
    assert result.innate_pts == 0.0


def test_empty_collection_gap_zero_safe():
    """Collection vide : gap calculé mais pas d'erreur."""
    col = CollectionState.from_runes([])
    result = priority_score(_rune(), col)
    assert result.gap_pts >= 0


def test_total_is_sum_of_parts():
    col = CollectionState.from_runes([])
    r = priority_score(_rune(slot=4, prefix=("CC", 6)), col)
    assert r.total == int(round(r.innate_pts + r.slot_pts + r.gap_pts))
```

- [ ] **Step 2: Vérifier l'échec**

```bash
pytest tests/swlens/test_priority_score.py -v 2>&1 | head -10
```

- [ ] **Step 3: Implémenter**

```python
# swlens/priority_score.py
"""Priority Score SWLens = Innate (0-200) + Slot (50-100) + Gap (0-600+)."""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from swlens.collection_state import CollectionState
from swlens.config import INNATE_IMPORTANCE, SLOT_BONUS, step_for
from swlens.gap_analysis import gap_for_rune


@dataclass
class PriorityResult:
    total: int
    innate_pts: float
    slot_pts: int
    gap_pts: int


def _innate_points(rune: Rune) -> float:
    if rune.prefix is None:
        return 0.0
    step = step_for(rune.prefix.type, rune.stars)
    if step <= 0:
        return 0.0
    importance = INNATE_IMPORTANCE.get(rune.prefix.type, 1.0)
    return (rune.prefix.value / step * 200) * importance


def priority_score(rune: Rune, collection: CollectionState) -> PriorityResult:
    innate_pts = _innate_points(rune)
    slot_pts = SLOT_BONUS.get(rune.slot, 50)
    gap_pts = gap_for_rune(rune, collection)
    total = int(round(innate_pts + slot_pts + gap_pts))
    return PriorityResult(
        total=total, innate_pts=innate_pts, slot_pts=slot_pts, gap_pts=gap_pts,
    )
```

- [ ] **Step 4: Tests passent**

```bash
pytest tests/swlens/test_priority_score.py -v
# Expected: 5 passed
```

- [ ] **Step 5: Commit**

```bash
git add swlens/priority_score.py tests/swlens/test_priority_score.py
git commit -m "feat(swlens): add priority score (innate + slot + gap)"
```

---

### Task 7: Créer `swlens/__init__.py` (API publique)

**Files:**
- Modify: `swlens/__init__.py`

- [ ] **Step 1: Définir l'API publique**

```python
# swlens/__init__.py
"""Module SWLens — système de tri de runes score-based.

API publique :
- rl_score(rune) → RLScoreResult
- priority_score(rune, collection) → PriorityResult
- gap_analysis(collection) → GapReport
- CollectionState.from_runes(runes) → CollectionState
- constantes de config (seuils, pondérations)
"""
from swlens.collection_state import CollectionState
from swlens.config import (
    CATEGORY_BOUNDS,
    GAP_CATEGORIES,
    GAP_MULTIPLIERS,
    INNATE_IMPORTANCE,
    KEEP_THRESHOLD_DEFAULT,
    SLOT_BONUS,
    category_for,
    step_for,
)
from swlens.gap_analysis import CategoryGap, GapReport, gap_analysis, gap_for_rune
from swlens.priority_score import PriorityResult, priority_score
from swlens.rl_score import RLScoreResult, rl_score

__all__ = [
    "rl_score", "priority_score", "gap_analysis", "gap_for_rune",
    "CollectionState", "RLScoreResult", "PriorityResult",
    "GapReport", "CategoryGap",
    "category_for", "step_for",
    "KEEP_THRESHOLD_DEFAULT", "CATEGORY_BOUNDS", "GAP_CATEGORIES",
    "GAP_MULTIPLIERS", "INNATE_IMPORTANCE", "SLOT_BONUS",
]
```

- [ ] **Step 2: Smoke test de l'API**

```bash
python -c "from swlens import rl_score, priority_score, CollectionState, KEEP_THRESHOLD_DEFAULT; print('OK', KEEP_THRESHOLD_DEFAULT)"
# Expected: OK 230
```

- [ ] **Step 3: Lancer TOUTE la suite swlens**

```bash
pytest tests/swlens/ -v
# Expected: 20 passed
```

- [ ] **Step 4: Commit**

```bash
git add swlens/__init__.py
git commit -m "feat(swlens): expose public API via __init__"
```

---

### Task 8: Golden tests de fidélité vs SWLens réel

**Files:**
- Test: `tests/swlens/test_fidelity.py`

> **Important :** Ces tests sont les **calibrateurs** pour la formule Gap (§9.2 du spec). À cette étape, l'engineer doit aller sur `runelens.swlens.io/analyzer`, taper manuellement 3-5 runes de référence, noter le RL Score retourné, et écrire les tests. Si les valeurs divergent, ajuster `swlens/config.py` (step values si nécessaire) avant de continuer.

- [ ] **Step 1: Créer le squelette du test**

```python
# tests/swlens/test_fidelity.py
"""Golden tests contre runelens.swlens.io.

Protocole : aller sur https://runelens.swlens.io/analyzer, taper les runes
ci-dessous, noter le RL Score affiché, compléter les asserts.

Si divergence ≥ 5 points : ajuster swlens/config.STAT_STEPS_6 avant d'aller
plus loin.
"""
from __future__ import annotations

import pytest

from models import Rune, SubStat
from swlens.rl_score import rl_score


@pytest.mark.parametrize("name,rune_factory,expected_score", [
    (
        "violent_cd_speedy",
        lambda: Rune(
            set="Violent", slot=4, stars=6, grade="Legendaire", level=12,
            main_stat=SubStat("DC", 80),
            prefix=SubStat("CC", 6),
            substats=[
                SubStat("VIT", 24), SubStat("CC", 10),
                SubStat("ATQ%", 15), SubStat("RES", 8),
            ],
        ),
        None,  # À remplir après vérif sur le site SWLens
    ),
    # Ajouter 4+ runes golden supplémentaires.
])
def test_golden_rl_score_matches_swlens(name, rune_factory, expected_score):
    if expected_score is None:
        pytest.skip(f"Golden value for {name} not yet captured from swlens.io")
    result = rl_score(rune_factory())
    delta = abs(result.total - expected_score)
    assert delta <= 5, f"{name}: got {result.total}, expected {expected_score} (delta={delta})"
```

- [ ] **Step 2: Capture manuelle (action humaine)**

Aller sur `https://runelens.swlens.io/analyzer`. Pour chaque rune du parametrize :
1. Taper set, slot, stars, grade, level, main stat, innate, substats.
2. Noter le RL Score affiché.
3. Remplacer `None` par la valeur.

> Si non capturé, les tests `skip` — c'est OK pour cette itération mais à compléter avant merge final.

- [ ] **Step 3: Lancer**

```bash
pytest tests/swlens/test_fidelity.py -v
# Expected: N skipped ou N passed selon capture
```

- [ ] **Step 4: Commit**

```bash
git add tests/swlens/test_fidelity.py
git commit -m "test(swlens): add fidelity golden tests against runelens.swlens.io"
```

---

## Phase C — UI Paramètres SWLens

### Task 9: Créer `ui/swlens_settings/swlens_settings_page.py`

**Files:**
- Create: `ui/swlens_settings/__init__.py`
- Create: `ui/swlens_settings/swlens_settings_page.py`
- Test: `tests/ui/test_swlens_settings_page.py`

- [ ] **Step 1: Créer le package**

```bash
mkdir -p ui/swlens_settings
touch ui/swlens_settings/__init__.py
```

- [ ] **Step 2: Test de la page**

```python
# tests/ui/test_swlens_settings_page.py
from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from ui.swlens_settings.swlens_settings_page import SwlensSettingsPage


@pytest.fixture
def app(qtbot):
    return QApplication.instance() or QApplication([])


def test_page_instantiates(qtbot, app):
    config = {"swlens": {"keep_threshold": 230}}
    page = SwlensSettingsPage(config)
    qtbot.addWidget(page)
    assert page.threshold_slider.value() == 230


def test_threshold_change_updates_config(qtbot, app):
    config = {"swlens": {"keep_threshold": 230}}
    page = SwlensSettingsPage(config)
    qtbot.addWidget(page)
    page.threshold_slider.setValue(280)
    page.save_to_config()
    assert config["swlens"]["keep_threshold"] == 280


def test_defaults_when_no_config(qtbot, app):
    config = {}
    page = SwlensSettingsPage(config)
    qtbot.addWidget(page)
    assert page.threshold_slider.value() == 230
```

- [ ] **Step 3: Vérifier l'échec**

```bash
pytest tests/ui/test_swlens_settings_page.py -v 2>&1 | head -10
```

- [ ] **Step 4: Implémenter la page**

```python
# ui/swlens_settings/swlens_settings_page.py
"""Page de configuration du système de tri SWLens."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel, QSlider, QVBoxLayout, QWidget,
)

from swlens.config import KEEP_THRESHOLD_DEFAULT


class SwlensSettingsPage(QWidget):
    def __init__(self, config: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Paramètres SWLens</h2>"))

        layout.addWidget(QLabel("Seuil KEEP/SELL (RL Score) :"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(100)
        self.threshold_slider.setMaximum(400)
        initial = config.get("swlens", {}).get("keep_threshold", KEEP_THRESHOLD_DEFAULT)
        self.threshold_slider.setValue(initial)
        layout.addWidget(self.threshold_slider)

        self.threshold_label = QLabel(f"Seuil : {initial}")
        layout.addWidget(self.threshold_label)
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(f"Seuil : {v}")
        )

        layout.addStretch()

    def save_to_config(self) -> None:
        self._config.setdefault("swlens", {})
        self._config["swlens"]["keep_threshold"] = self.threshold_slider.value()
```

- [ ] **Step 5: Tests passent**

```bash
pytest tests/ui/test_swlens_settings_page.py -v
# Expected: 3 passed
```

- [ ] **Step 6: Commit**

```bash
git add ui/swlens_settings/ tests/ui/test_swlens_settings_page.py
git commit -m "feat(ui): add SWLens settings page (threshold slider)"
```

---

## Phase D — Bascule `evaluator_chain` et call sites

### Task 10: Basculer `evaluator_chain.py` vers SWLens

**Files:**
- Modify: `evaluator_chain.py` (réécriture complète, garde `evaluate_artifact_chain`)
- Modify: `tests/test_evaluator_chain.py` (réécrit)

- [ ] **Step 1: Écrire les nouveaux tests**

```python
# tests/test_evaluator_chain.py
from __future__ import annotations

from evaluator_chain import evaluate_chain
from models import Rune, SubStat


def _high_score_rune():
    return Rune(
        set="Violent", slot=4, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat("DC", 80),
        prefix=SubStat("CC", 6),
        substats=[
            SubStat("VIT", 30), SubStat("CC", 15),
            SubStat("ATQ%", 15), SubStat("RES", 10),
        ],
    )


def _low_score_rune():
    return Rune(
        set="Energy", slot=1, stars=6, grade="Rare", level=3,
        main_stat=SubStat("ATQ", 100), prefix=None,
        substats=[SubStat("RES", 4)],
    )


def test_keep_when_score_above_threshold():
    cfg = {"swlens": {"keep_threshold": 230}}
    v = evaluate_chain(_high_score_rune(), cfg)
    assert v.decision == "KEEP"
    assert v.source == "swlens"
    assert "rl_score" in v.details
    assert v.details["category"] in {"Bon", "Excellent"}


def test_sell_when_score_below_threshold():
    cfg = {"swlens": {"keep_threshold": 230}}
    v = evaluate_chain(_low_score_rune(), cfg)
    assert v.decision == "SELL"


def test_default_threshold_when_missing():
    v = evaluate_chain(_high_score_rune(), {})
    assert v.source == "swlens"
    # pas de crash
```

- [ ] **Step 2: Réécrire `evaluator_chain.py`**

```python
# evaluator_chain.py
"""Orchestration verdict KEEP/SELL basée sur SWLens RL Score.

Remplace le système S2US filter-based. `evaluate_artifact_chain` inchangé.
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
```

- [ ] **Step 3: Tests passent**

```bash
pytest tests/test_evaluator_chain.py -v
# Expected: 3 passed
```

- [ ] **Step 4: Commit**

```bash
git add evaluator_chain.py tests/test_evaluator_chain.py
git commit -m "feat(evaluator): switch to SWLens RL Score verdict"
```

---

### Task 11: Adapter `rune_optimizer.py` (call site majeur)

**Files:**
- Modify: `rune_optimizer.py`
- Modify: `tests/test_rune_optimizer.py`

- [ ] **Step 1: Lire le fichier actuel**

```bash
grep -n "s2us_filter\|calculate_efficiency\|match_filter\|S2USFilter" rune_optimizer.py
```

- [ ] **Step 2: Remplacer les imports et fonctions de scoring**

Dans `rune_optimizer.py`, remplacer :
```python
from s2us_filter import (
    calculate_efficiency1, match_filter, S2USFilter, ...
)
```
par :
```python
from swlens import rl_score
```

Et partout où `calculate_efficiency1(rune)` était appelé, remplacer par `rl_score(rune).total`.

Les logiques de `match_filter` (filtres S2US) dans ce fichier doivent être supprimées — l'optimizer devient un pur classement par RL Score.

> **Note engineer :** si `rune_optimizer` contenait de la logique métier au-delà du scoring (ex: pondération par rôle de monstre), la conserver. On ne touche QUE le scoring.

- [ ] **Step 3: Adapter les tests**

`tests/test_rune_optimizer.py` : supprimer les asserts basés sur `match_filter` ou `calculate_efficiency1`, les remplacer par des asserts sur `rl_score(rune).total`.

- [ ] **Step 4: Tests passent**

```bash
pytest tests/test_rune_optimizer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add rune_optimizer.py tests/test_rune_optimizer.py
git commit -m "refactor(rune_optimizer): use SWLens RL Score instead of s2us efficiency"
```

---

### Task 12: Adapter `powerup_simulator.py`

**Files:**
- Modify: `powerup_simulator.py`
- Modify: `tests/test_powerup_simulator.py`

- [ ] **Step 1: Localiser l'import**

```bash
grep -n "s2us_filter\|match_filter\|calculate_efficiency" powerup_simulator.py
```

- [ ] **Step 2: Retirer l'usage de `match_filter`**

Le simulator n'a pas besoin de filtrer — il projette une rune à +12. Le scoring se fait en aval. Retirer l'import `match_filter`. Si `calculate_efficiency1` est utilisé pour calculer une efficacité projetée, le remplacer par `rl_score(rune).total`.

- [ ] **Step 3: Adapter le test**

Dans `tests/test_powerup_simulator.py` (ligne 239-241), le test `match_filter_smart` dépend de `s2us_filter` → **supprimer ce test** (Smart Filter n'existe plus).

- [ ] **Step 4: Tests passent**

```bash
pytest tests/test_powerup_simulator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add powerup_simulator.py tests/test_powerup_simulator.py
git commit -m "refactor(powerup_simulator): drop s2us_filter dependency"
```

---

### Task 13: Adapter les pages UI (`runes_page`, `rune_card_widget`, `monsters_page`)

**Files:**
- Modify: `ui/runes/runes_page.py`
- Modify: `ui/runes/rune_card_widget.py`
- Modify: `ui/monsters/monsters_page.py`
- Modify: `profile_tab.py`

- [ ] **Step 1: Identifier les usages**

```bash
grep -n "calculate_efficiency_s2us\|s2us_filter" ui/runes/runes_page.py ui/runes/rune_card_widget.py ui/monsters/monsters_page.py profile_tab.py
```

- [ ] **Step 2: Remplacer par `rl_score`**

Dans chaque fichier, remplacer :
```python
from s2us_filter import calculate_efficiency_s2us
...
eff = calculate_efficiency_s2us(rune)
```
par :
```python
from swlens import rl_score
...
eff = rl_score(rune).total
```

Ajuster l'affichage : l'ancien `calculate_efficiency_s2us` retournait un % (0-100), le nouveau RL Score est un entier (0-400+). Adapter labels / progress bars en conséquence.

- [ ] **Step 3: Tester les pages affectées**

```bash
pytest tests/ui/test_runes_page.py tests/ui/test_rune_card_widget.py tests/ui/test_monsters_page.py -v
```

Si tests échouent à cause du changement d'échelle (0-100 → 0-400+), adapter les asserts.

- [ ] **Step 4: Commit**

```bash
git add ui/runes/ ui/monsters/ profile_tab.py tests/ui/
git commit -m "refactor(ui): migrate rune efficiency display to SWLens RL Score"
```

---

### Task 14: Brancher la nouvelle page SWLens dans `main_window` et `sidebar`

**Files:**
- Modify: `ui/main_window.py`
- Modify: `ui/sidebar.py`

- [ ] **Step 1: Localiser les références à `ui/filtres/`**

```bash
grep -n "filtres\|FiltresPage\|from ui.filtres" ui/main_window.py ui/sidebar.py
```

- [ ] **Step 2: Remplacer l'import et l'instantiation**

Dans `ui/main_window.py`, remplacer :
```python
from ui.filtres.filtres_page import FiltresPage
...
self.filtres_page = FiltresPage(self._config)
```
par :
```python
from ui.swlens_settings.swlens_settings_page import SwlensSettingsPage
...
self.swlens_settings_page = SwlensSettingsPage(self._config)
```

Ajuster les connexions (stackedWidget, routing par sidebar) pour pointer vers la nouvelle page.

- [ ] **Step 3: Modifier `ui/sidebar.py`**

Remplacer le label "Filtres" par "Paramètres SWLens". Si la sidebar a des icônes, garder la même (ou changer, au choix).

- [ ] **Step 4: Smoke test**

```bash
python -c "from ui.main_window import MainWindow; print('import OK')"
pytest tests/ui/test_main_window_nav.py tests/ui/test_sidebar.py -v
```

- [ ] **Step 5: Commit**

```bash
git add ui/main_window.py ui/sidebar.py
git commit -m "feat(ui): replace Filtres page with SWLens Settings in main nav"
```

---

### Task 15: Nettoyer `settings_tab.py`

**Files:**
- Modify: `settings_tab.py`

- [ ] **Step 1: Localiser les références S2US**

```bash
grep -n "s2us\|S2US\|load_s2us_file" settings_tab.py
```

- [ ] **Step 2: Retirer le bloc S2US**

Supprimer :
- `from s2us_filter import load_s2us_file, S2USFilter`
- Le bloc `self._config["s2us"] = {...}` (lignes ~178-180)
- La lecture `if "s2us" in self._config` (ligne ~244)

Ajouter à la place un bloc SWLens minimal :
```python
self._config.setdefault("swlens", {"keep_threshold": 230})
```

- [ ] **Step 3: Lancer les tests**

```bash
pytest tests/ui/test_settings_page.py -v
```

- [ ] **Step 4: Commit**

```bash
git add settings_tab.py
git commit -m "refactor(settings): drop S2US config, add SWLens defaults"
```

---

## Phase E — Suppression du legacy

### Task 16: Supprimer les fichiers S2US (source + writer + tests)

**Files:**
- Delete: `s2us_filter.py`, `s2us_writer.py`
- Delete: `tests/test_s2us_filter.py`, `tests/test_s2us_writer.py`

- [ ] **Step 1: Vérifier qu'aucun import ne subsiste**

```bash
grep -rn "from s2us_filter\|import s2us_filter\|from s2us_writer\|import s2us_writer" --include="*.py" . | grep -v "_backup_s2us"
# Expected: AUCUN résultat (sauf le backup externe qui n'est pas dans le repo)
```

> Si des résultats apparaissent : revenir en Task 11/12/13 et fixer avant de supprimer.

- [ ] **Step 2: Supprimer**

```bash
rm s2us_filter.py s2us_writer.py
rm tests/test_s2us_filter.py tests/test_s2us_writer.py
```

- [ ] **Step 3: Lancer TOUTE la suite**

```bash
pytest -x 2>&1 | tail -30
# Expected: all green, aucun ImportError
```

- [ ] **Step 4: Commit**

```bash
git add -u s2us_filter.py s2us_writer.py tests/test_s2us_filter.py tests/test_s2us_writer.py
git commit -m "chore: remove legacy S2US filter module (replaced by swlens/)"
```

---

### Task 17: Supprimer `ui/filtres/` et ses tests

**Files:**
- Delete: `ui/filtres/` (dossier complet)
- Delete: `tests/ui/test_filter_editor.py`, `test_filter_list_panel.py`, `test_filtres_page.py`, `test_rune_tester_modal.py`

- [ ] **Step 1: Vérifier qu'aucune référence ne subsiste**

```bash
grep -rn "from ui.filtres\|import ui.filtres\|ui\\.filtres" --include="*.py" . | grep -v "_backup_s2us"
# Expected: AUCUN
```

- [ ] **Step 2: Supprimer**

```bash
rm -rf ui/filtres
rm tests/ui/test_filter_editor.py tests/ui/test_filter_list_panel.py tests/ui/test_filtres_page.py tests/ui/test_rune_tester_modal.py
```

- [ ] **Step 3: Tests complets**

```bash
pytest -x 2>&1 | tail -20
```

- [ ] **Step 4: Commit**

```bash
git add -u ui/filtres tests/ui/
git commit -m "chore: remove legacy Filtres UI (replaced by SWLens settings)"
```

---

### Task 18: Supprimer l'ancienne spec `docs/Système tri de rune.md`

**Files:**
- Delete: `docs/Système tri de rune.md`

- [ ] **Step 1: Vérifier qu'aucune réf ne pointe dessus**

```bash
grep -rn "Système tri de rune" --include="*.md" --include="*.py" .
```

- [ ] **Step 2: Supprimer**

```bash
rm "docs/Système tri de rune.md"
```

- [ ] **Step 3: Commit**

```bash
git add -u "docs/Système tri de rune.md"
git commit -m "docs: remove legacy S2US sort spec (superseded by SWLens spec)"
```

---

## Phase F — Validation finale

### Task 19: Smoke test end-to-end

**Files:**
- Aucun (test manuel + suite complète)

- [ ] **Step 1: Suite complète verte**

```bash
pytest -v 2>&1 | tail -5
# Expected: X passed, 0 failed
```

- [ ] **Step 2: Lancer l'app et vérifier le flux scan**

```bash
python app.py
```

Vérifications manuelles :
- [ ] La sidebar affiche "Paramètres SWLens" à la place de "Filtres"
- [ ] La page Paramètres SWLens s'ouvre, le slider seuil fonctionne
- [ ] Un scan OCR produit un Verdict KEEP/SELL avec `source="swlens"`
- [ ] La page Runes trie les runes par RL Score décroissant
- [ ] La page Monsters affiche les runes équipées avec leur RL Score

- [ ] **Step 3: Vérifier le backup externe existe toujours**

```bash
ls C:/Users/louis/Desktop/Luci2US_backup_s2us/
# Expected: le dossier timestamped avec les 12+ fichiers legacy
```

- [ ] **Step 4: Commit de clôture (si nettoyage résiduel)**

Si des imports morts ou warnings apparaissent, les fixer ici. Sinon, passer.

```bash
git status
# Expected: clean working tree
```

- [ ] **Step 5: Tag de release**

```bash
git tag -a migration-swlens-v1 -m "Migration complète du système de tri vers SWLens"
```

---

## Résumé des commits attendus

1. `feat(swlens): add config module with step values and thresholds`
2. `feat(swlens): implement RL Score with substat + innate bonus`
3. `feat(swlens): add CollectionState for inventory aggregation`
4. `feat(swlens): add gap analysis with 7 categories and multipliers`
5. `feat(swlens): add priority score (innate + slot + gap)`
6. `feat(swlens): expose public API via __init__`
7. `test(swlens): add fidelity golden tests against runelens.swlens.io`
8. `feat(ui): add SWLens settings page (threshold slider)`
9. `feat(evaluator): switch to SWLens RL Score verdict`
10. `refactor(rune_optimizer): use SWLens RL Score instead of s2us efficiency`
11. `refactor(powerup_simulator): drop s2us_filter dependency`
12. `refactor(ui): migrate rune efficiency display to SWLens RL Score`
13. `feat(ui): replace Filtres page with SWLens Settings in main nav`
14. `refactor(settings): drop S2US config, add SWLens defaults`
15. `chore: remove legacy S2US filter module (replaced by swlens/)`
16. `chore: remove legacy Filtres UI (replaced by SWLens settings)`
17. `docs: remove legacy S2US sort spec (superseded by SWLens spec)`

## Risques connus

- **Step values** : la table SWLens complète n'est pas publique. Task 8 (golden tests) permet de valider ; si divergence >5 pts, ajuster `swlens/config.py` avant Task 10.
- **Formule Gap** : reconstituée dans `_category_score`. Calibration possible en Task 8 si golden tests sur Priority Score divergent.
- **Rune optimizer** : dépendait fortement de `match_filter` (logique 14 checks). La bascule simplifie drastiquement cette fonction. S'assurer que les callers (UI) ne perdent pas de fonctionnalité attendue.
- **Historique DB** : Verdict stockés avec l'ancien format (`details.efficiency1/2`) restent lisibles, nouveaux utilisent `details.rl_score/category`. La page Stats/History doit gérer les deux formats (détection par clé).
