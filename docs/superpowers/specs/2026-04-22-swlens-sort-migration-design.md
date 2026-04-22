# Migration du système de tri de runes vers SWLens

**Date** : 2026-04-22
**Statut** : Spec approuvée, en attente de plan d'implémentation
**Objectif** : Remplacer intégralement le système de tri S2US actuel par une réplique fidèle du système SWLens (runelens.swlens.io), avec sauvegarde externe du système existant.

## 1. Contexte

### Système actuel (à remplacer)
Paradigme **filter-based** : l'utilisateur configure des filtres (sets, slots, sous-stats, seuils) dans des fichiers `.S2US`. Une rune est `KEEP` si au moins un filtre matche les 14 checks ordonnés.

Fichiers concernés :
- `s2us_filter.py` — 4 formules (Score, Efficiency1, Efficiency2, artifact) + parser + matching
- `evaluator_chain.py` — orchestration KEEP/SELL
- `powerup_simulator.py` — projection +12 pour Smart Filter (conservé, utilisé hors scoring par `rune_optimizer`)
- `ui/filtres/` — 6 fichiers UI (dossier, filter_editor, filter_list_panel, filtres_page, rune_tester_modal)
- `tests/test_s2us_filter.py`, `tests/test_evaluator_chain.py`

### Cible (SWLens)
Paradigme **score-based** : chaque rune reçoit un score numérique (RL Score) → catégorie (Excellent/Bon/Médiocre/Faible) → KEEP/SELL selon seuil configurable. Ajout de Priority Score et Gap Analysis pour identifier les candidats à réapprainage en tenant compte des déficits de la collection.

**Principe directeur** : fidélité stricte à SWLens. Pas de fonctionnalités inventées, pas de reliquats de l'ancien système (pas de Smart Filter +12, pas de filtres, pas de .S2US).

## 2. Décisions de conception (validées)

| Question | Choix |
|----------|-------|
| Périmètre | Remplacement complet du paradigme (B) |
| Fonctionnalités SWLens | Full : RL Score + Priority + Gap + farming priority (C) |
| Backup | Dossier externe `C:\Users\louis\Desktop\Luci2US_backup_s2us\` (C) |
| Page Filtres | Remplacée par page "Paramètres SWLens" (B) |
| Scoring artifacts | Inchangé, hors scope (A) |

## 3. Architecture

Nouveau module `swlens/` à la racine :

```
swlens/
├── __init__.py           # Exports publics: score_rune, priority_rune, gap_analysis
├── rl_score.py           # RL Score = Substat Score + Innate Bonus (4 catégories)
├── priority_score.py     # Priority = Innate(0-200) + Slot(50-100) + Gap(0-600+)
├── gap_analysis.py       # Analyse collection sur 7 catégories
├── collection_state.py   # Agrégation inventaire (cache)
└── config.py             # Seuils, pondérations, step values, multiplicateurs
```

Nouvelle UI : `ui/swlens_settings/` (remplace `ui/filtres/`).

`evaluator_chain.py` conservé (fin) : orchestration qui appelle `swlens.score_rune()` et produit un `Verdict` (dataclass inchangé) avec `decision=KEEP/SELL` selon seuil.

## 4. Components

### 4.1 `rl_score.py`

**Formule** :
- Pour chaque sous-stat : `raw = (value / step) - 1`, si `raw > 0` → contribution `+= raw × 100`
- Innate bonus : `(innate_value / max_roll × 100) / 2`
- RL Score total = somme des contributions sous-stat + innate bonus

**Step values** (`config.STAT_STEPS`) — à reconstituer complètement depuis le data game officiel. Valeurs connues publiquement : SPD=6, CR%=6, CD%=7. À compléter pour ATK%/HP%/DEF%/ACC%/RES% et versions flat, validé contre golden runes depuis runelens.swlens.io.

**Seuils (catégories)** :
- `< 150` → Faible
- `150–229` → Médiocre
- `230–299` → Bon (seuil défaut = **230**)
- `≥ 300` → Excellent

**API** :
```python
@dataclass
class RLScoreResult:
    total: int
    category: Literal["Excellent", "Bon", "Médiocre", "Faible"]
    substat_breakdown: list[tuple[str, float, float]]  # (stat, raw, contribution)
    innate_bonus: float

def rl_score(rune: Rune) -> RLScoreResult: ...
```

### 4.2 `priority_score.py`

**Composantes** :
- **Innate Score (0-200)** : `(innate_value / max_roll × 200) × importance_weight[stat]`
  - Pondérations : `ACC=2.0, CR=2.0, RES=1.5, CD=1.5, autres=1.0`
- **Slot Score** : `{1:50, 2:75, 3:50, 4:100, 5:50, 6:100}`
- **Gap Score** : délégué à `gap_analysis.gap_for_rune(rune, collection)` → 0 à 600+

**API** :
```python
@dataclass
class PriorityResult:
    total: int
    innate_pts: float
    slot_pts: int
    gap_pts: int

def priority_score(rune: Rune, collection: CollectionState) -> PriorityResult: ...
```

### 4.3 `gap_analysis.py`

Évalue la collection sur 7 catégories : `HP%, ATK%, DEF%, CR%, CD%, ACC%, SPD`.

Pour chaque catégorie :
- `fast_count` — nombre de runes avec SPD ≥ 20
- `elite_count` — nombre de runes avec RL Score ≥ 300
- `speed_mean` — moyenne des SPD substats dans la catégorie
- `slot_coverage` — couverture par slot (diversité)

**Multiplicateurs** : `HP=1.3, ATK=1.2, autres=1.0`.

Le gap score pour une catégorie déficitaire peut atteindre 600+ ; pour une catégorie saturée, il tend vers 0.

**API** :
```python
@dataclass
class GapReport:
    per_category: dict[str, CategoryGap]  # fast, elite, mean, coverage, score

def gap_analysis(collection: CollectionState) -> GapReport: ...
def gap_for_rune(rune: Rune, collection: CollectionState) -> int: ...
```

### 4.4 `collection_state.py`

Indexe `list[Rune]` par catégorie (main stat + subs pertinents). Cache avec TTL 60s ou invalidation explicite sur mutation (scan, ajout SWEX, édition manuelle).

```python
class CollectionState:
    @classmethod
    def from_runes(cls, runes: list[Rune]) -> CollectionState: ...
    def runes_in_category(self, cat: str) -> list[Rune]: ...
    def invalidate(self) -> None: ...
```

### 4.5 `evaluator_chain.evaluate_chain`

Remplace le corps actuel :

```python
def evaluate_chain(rune: Rune, config: dict) -> Verdict:
    threshold = config["swlens"]["keep_threshold"]  # défaut 230
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
```

`evaluate_artifact_chain` reste inchangé (artifacts hors scope).

### 4.6 `ui/swlens_settings/`

Page de paramètres (remplace `ui/filtres/`) :
- Slider seuil RL Score KEEP/SELL (défaut 230, plage 100–400)
- Table éditable : pondérations Innate par stat
- Table éditable : multiplicateurs Gap par catégorie
- Aperçu en temps réel sur une rune de test

## 5. Data flow

### 5.1 Scan temps réel
```
OCR → Rune → evaluate_chain(rune, config)
                ↓
          rl_score(rune)
                ↓
          decision = total ≥ threshold ? KEEP : SELL
                ↓
          Verdict(decision, score=total, details={...})
                ↓
          ui/scan/verdict_bar.py → affichage coloré
          ui/scan/rune_card.py    → breakdown sous-stats
```

### 5.2 Tri d'inventaire (page Runes)
```
runes_page.py charge tous les Rune
      ↓
CollectionState.from_runes(all_runes)  [cache]
      ↓
pour chaque rune :
  - rl_score(rune)
  - priority_score(rune, collection)
      ↓
tri par colonne (RL Score | Priority | Slot) + filtres catégorie
```

### 5.3 Paramètres
```
ui/swlens_settings/page.py → save → settings.json
                                  ↓
                        evaluator_chain / priority_score
                        lisent config.swlens au besoin
```

## 6. Edge cases

| Cas | Comportement |
|-----|--------------|
| Collection vide | Gap = 0, Priority = Innate + Slot seulement, pas de crash |
| Rune sans innate | `innate_bonus = 0`, `innate_pts = 0` |
| Stat inconnue (OCR corrompu) | Skip avec warning log, pas de `KeyError` |
| Rune `level < 12` | Scorée telle quelle (pas de projection +12, fidèle à SWLens) |
| Artifact | Passe par `evaluate_artifact_chain` — circuit séparé, inchangé |
| Config `settings.json` corrompue | Fallback sur defaults hardcodés dans `swlens/config.py` |
| Ancien Verdict en DB (historique) | Lecture-compatible : détection du format `details.efficiency1/2/score` vs `details.rl_score/category` |

## 7. Testing

### 7.1 Unit tests (`tests/swlens/`)

- `test_rl_score.py` — runes connues → scores attendus ; catégories aux bornes (149/150, 229/230, 299/300) ; innate absent/présent ; flat vs % ; rune 1★ à 6★
- `test_priority_score.py` — pondérations innate (ACC 2× HP) ; slot bonus ; Gap=0 quand collection vide
- `test_gap_analysis.py` — collection déséquilibrée → catégories déficitaires ; multiplicateurs HP×1.3 / ATK×1.2
- `test_collection_state.py` — agrégation correcte ; invalidation cache

### 7.2 Integration
- `test_evaluator_chain_swlens.py` — remplace l'ancien : scan → Verdict correcte selon seuil

### 7.3 Fidélité SWLens
- `test_fidelity.py` — 10 runes de référence scorées sur runelens.swlens.io → tests golden (valeurs exactes attendues)

### 7.4 UI
- `test_swlens_settings_page.py`
- `test_runes_page_swlens_sort.py`

### 7.5 Tests supprimés
- `test_s2us_filter.py`
- `test_evaluator_chain.py` (ancien contenu)
- `test_filter_editor.py`, `test_filter_list_panel.py`, `test_filtres_page.py`, `test_rune_tester_modal.py`

## 8. Stratégie d'implémentation (Approche 1 — parallèle puis bascule)

1. **Backup externe** : copie complète de `s2us_filter.py`, `evaluator_chain.py` (version actuelle), `ui/filtres/`, tests S2US, `docs/Système tri de rune.md` → `C:\Users\louis\Desktop\Luci2US_backup_s2us\` avec timestamp.
2. **Création `swlens/`** : modules neufs, testés en isolation avec `tests/swlens/`.
3. **Création `ui/swlens_settings/`** : page neuve, testée en isolation.
4. **Bascule `evaluator_chain.py`** : on débranche l'appel à `s2us_filter` et on le remplace par `swlens.score_rune()`. Dataclass `Verdict` inchangé → call sites (`auto_mode`, `rune_optimizer`, `ui/scan/`, `ui/monsters/`) continuent de fonctionner sans modif.
5. **Bascule UI** : `ui/main_window.py` / sidebar pointent vers `ui/swlens_settings/` au lieu de `ui/filtres/`.
6. **Suppression** : `s2us_filter.py`, `ui/filtres/`, anciens tests, `docs/Système tri de rune.md`.
7. **Nettoyage imports** : recherche globale des références résiduelles à `s2us_filter` / `S2USFilter` / `calculate_efficiency1/2` / `calculate_score` → suppression ou remplacement.
8. **Validation** : suite de tests complète verte, smoke test manuel (scan réel, navigation UI, persistance settings).

## 9. Points ouverts / recherche

- **Step values complètes** : le guide SWLens ne publie que SPD=6, CR=6, CD=7. Reconstituer la table complète par tests golden sur runelens.swlens.io avant d'écrire `rl_score.py` définitivement. Si divergence, documenter dans `swlens/config.py`.
- **Gap Analysis — formule exacte** : les multiplicateurs HP×1.3, ATK×1.2 sont connus, mais la pondération interne (fast / elite / mean / coverage) n'est pas publique. À calibrer par tests golden sur collections de référence.
- **Migration settings.json** : si l'utilisateur a déjà configuré des filtres S2US, ceux-ci sont abandonnés (paradigme différent, aucun mapping possible). Les seuils SWLens démarrent aux defaults.
