# Plan 03 — Onglet Runes (design)

**Date :** 2026-04-18
**Projet :** Luci2US (`C:\Users\louis\Desktop\Luci2US`)
**Scope :** page `Runes` (index 2 du `QStackedWidget`). Liste filtrable de toutes les runes du profil chargé (inventaire + équipées), panneau latéral de détail permanent, sans toucher au bot core.
**Parent spec :** `docs/superpowers/specs/2026-04-17-luci2us-tabs-design.md` §4.

---

## 1. Objectif

Offrir à l'utilisateur une vue inventaire complète de ses runes, avec :

- Filtrage multi-critères (Set, Slot, ★, Grade, substat focus, score min).
- Tri par clic sur n'importe quelle colonne.
- Détail rapide (panneau latéral permanent) de la rune sélectionnée.
- Lien visible avec le monstre équipé (colonne `Équipée`).

La page est branchée sur `ScanController.profile_loaded` (signal déjà émis par le contrôleur existant) et restaurée depuis le cache via `_restore_cached_profile`, comme `ProfilePage` et la future `MonstersPage`.

---

## 2. Contraintes

1. **Bot core intouchable** sauf ajout additif minime : un champ optionnel `rune_id: int | None = None` sur `Rune` (modèle `dataclass`) et son extraction dans `swex_bridge.parse_rune`. Tout le reste (`evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `profile_loader.py`, `profile_store.py`) reste inchangé.
2. **Thème v13** : couleurs, bordures, typographie via `ui/theme.py`.
3. **Stack** : PySide6 6.11.0, `QTableWidget` pour la liste (pas de `QAbstractTableModel`), pytest-qt.
4. **Volume cible** : 500 à 2500 runes par compte. `QTableWidget` est suffisant à cette échelle (pas de virtualisation).
5. **Ne pas régresser** Scan, Profils, Paramètres, Monstres (si plan 02 livré avant).

---

## 3. Architecture

### 3.1 Layout général (2 colonnes)

```
┌───────────────────────────────────────────────────┬──────────────┐
│ [Set ▾] [Slot ▾] [★ 5 ☐ 6 ☑] [Grade ▾] [Focus ▾] │              │
│ [Score: Eff ▾ ≥ ━●━━━━━━ 80]                      │              │
├───────────────────────────────────────────────────┤  DETAIL      │
│ ICN SL MAIN        SUBS/FOCUS      EFF MAX  É    │  PANEL       │
│ 🟣  2  ATQ +22%    VIT+12 · CC+9    92  96  L    │  (~180 px)   │
│ 🟣  4  DC +64%     CC+9 · DC+5      87  93  L    │              │
│  ...                                              │              │
└───────────────────────────────────────────────────┴──────────────┘
```

- **Gauche (flex)** : barre de filtres (haut) + table (dessous).
- **Droite (~180 px, permanent)** : `RuneDetailPanel`.

### 3.2 Composants internes

| Composant | Type | Rôle |
|---|---|---|
| `RunesPage` | `QWidget` | Orchestration. Layout 2 colonnes. Slot `apply_profile(profile, saved_at)`. |
| `RuneFilterBar` | `QWidget` | 6 contrôles. Émet `changed()` quand n'importe quel filtre bouge. |
| `RuneTable` | `QWidget` wrappant un `QTableWidget` | 7 colonnes. Tri natif par clic header. Émet `rune_selected(Rune)`. |
| `RuneDetailPanel` | `QWidget` | Panneau latéral. Slot `set_rune(rune, equipped_on)`. Placeholder si aucune rune. |

### 3.3 Widget réutilisable

| Widget | Rôle |
|---|---|
| `MultiCheckPopup` (dans `ui/widgets/`) | Bouton `[Label: val1, val2 (+N) ▾]` qui ouvre un popup flottant avec checkboxes. Émet `changed(set[str])`. Utilisé par Set / Slot / Grade. |

---

## 4. Data flow

### 4.1 Chargement d'un profil

1. `ScanController.profile_loaded(profile, saved_at)` est émis (au démarrage via `_restore_cached_profile`, ou après un scan, ou après import manuel).
2. `MainWindow` relaie vers `RunesPage.apply_profile(profile, saved_at)`.
3. `RunesPage` :
   - Construit `_equipped_index: dict[int, str]` → clé = `rune.rune_id` (fallback `id(rune)` Python si `rune_id is None`), valeur = `monster.name`. Obtenu en itérant `profile["monsters"]` et leurs `equipped_runes`.
   - Stocke `_all_runes = profile["runes"]` (déjà fusionné inventaire + équipées par `profile_loader`).
   - Appelle `_filter_bar.reset_to_defaults()` (tous les sets cochés, tous les slots, tous les ★, tous les grades, Focus = "Aucun", Score = "Eff ≥ 0").
   - Appelle `_refilter()` qui passe les runes filtrées à `_table.set_runes(runes, _equipped_index)`.
   - Appelle `_detail.clear()` (panneau placeholder).

### 4.2 Changement de filtre

1. `RuneFilterBar` émet `changed()`.
2. `RunesPage._refilter()` applique en mémoire (Python) :
   - Set ∈ sélection.
   - Slot ∈ sélection.
   - ★ ∈ sélection.
   - Grade ∈ sélection.
   - Si Focus != "Aucun" : la rune doit avoir cette stat en substat.
   - Score : `rune.swex_efficiency` (ou `swex_max_efficiency` selon le dropdown) ≥ valeur slider.
3. Rebuild table : `_table.set_runes(filtered, _equipped_index, focus_stat=...)`.

### 4.3 Focus stat dynamique

- Si `focus_stat == "Aucun"` : la colonne 4 s'appelle `Subs` et affiche `VIT+12 · CC+9 · ATQ+22 · PV+375` (les 4 substats condensées, grind ignoré ici pour concision). Tri par défaut = `Eff` desc.
- Si `focus_stat == "VIT"` (ou autre) : la colonne 4 s'appelle `Focus VIT` et affiche `VIT +12 (+5)` (valeur + grind). Tri par défaut = valeur de cette substat desc. Seules les runes ayant cette substat sont visibles.

### 4.4 Sélection d'une rune

1. Clic sur une ligne → `RuneTable.rune_selected(rune)`.
2. `RunesPage._on_rune_selected(rune)` → `_detail.set_rune(rune, equipped_on=_equipped_index.get(rune.rune_id or id(rune)))`.

### 4.5 Nouveau profil arrive (re-scan)

- **Reset complet des filtres** (valeurs par défaut).
- **Sélection détail clearée** (panneau revient au placeholder).
- Table re-remplie avec les nouvelles runes.

---

## 5. Colonnes de la table

| # | Titre | Contenu | Largeur | Tri |
|---|---|---|---|---|
| 1 | (vide) | Icône set 16 px + nom court (ex: `Violent`) | ~110 px | alphabétique sur nom |
| 2 | `SL` | Slot 1-6 | ~40 px | numérique |
| 3 | `Main` | `{type}+{value}{%}` (ex: `ATQ+22%`) | ~110 px | alphabétique |
| 4 | `Subs` ou `Focus VIT` | dynamique (voir §4.3) | flex | alphabétique (mode Subs) ou numérique (mode Focus) |
| 5 | `Eff` | `swex_efficiency` formaté `92` | ~50 px | numérique desc par défaut |
| 6 | `Max` | `swex_max_efficiency` formaté `96` | ~50 px | numérique |
| 7 | `Équipée` | nom du monstre ou `—` | ~120 px | alphabétique, `—` à la fin |

**Valeurs manquantes** : si `swex_efficiency is None`, afficher vide. Tri : valeurs vides poussées en bas.

---

## 6. Barre de filtres

| Contrôle | Type | Valeurs |
|---|---|---|
| Set | `MultiCheckPopup` | 23 sets `SETS_FR`. Défaut : tous cochés. Résumé : `Set: Tous` si tous cochés, sinon `Set: Violent, Fatal (+2)`. |
| Slot | `MultiCheckPopup` | 1, 2, 3, 4, 5, 6. Défaut : tous. |
| ★ | 2 checkboxes (5★, 6★) | Défaut : 5★ et 6★ cochés. |
| Grade | `MultiCheckPopup` | `Magique`, `Rare`, `Heroique`, `Legendaire` (on exclut `Normal` qui est peu pertinent). Défaut : tous cochés. |
| Focus stat | `QComboBox` | `Aucun`, puis les 11 `STATS_FR`. Défaut : `Aucun`. |
| Score | `QComboBox` (`Eff` / `Max`) + `QSlider` 0-100 | Défaut : `Eff ≥ 0`. Label dynamique affiche la valeur. |

**Signal unique** : `RuneFilterBar.changed()` émis sur tout changement. `RunesPage` branche un seul slot dessus.

**Méthode `reset_to_defaults()`** : remet tous les contrôles à leur état initial sans émettre de signaux intermédiaires (bloque avec `blockSignals(True)` puis émet un seul `changed` à la fin).

---

## 7. Panneau de détail

Lorsque `set_rune(rune, equipped_on)` est appelé :

```
┌────────────────────┐
│ Violent · Slot 2   │  ← titre (or, serif)
│ ★6 · +12 · Heroique│  ← meta (couleur grade)
├────────────────────┤
│ ATQ +22%           │  ← box main stat
├────────────────────┤
│ Subs               │
│ VIT +12 (+5)       │  ← valeur + (grind) si >0
│ PV% +9             │
│ CC +6              │
│ DC +5              │
├────────────────────┤
│ Équipée :          │
│ Lushen             │  ou "Inventaire"
├────────────────────┤
│ Eff  92   Max  96  │  ← badges bronze/or
└────────────────────┘
```

**Placeholder (no rune)** : `Cliquez une rune pour voir le détail.` centré, couleur `COLOR_TEXT_DIM`.

---

## 8. Fichiers

### 8.1 À créer

| Chemin | Rôle |
|---|---|
| `ui/runes/__init__.py` | Package init vide |
| `ui/runes/runes_page.py` | `RunesPage` (orchestration 2 colonnes) |
| `ui/runes/rune_filter_bar.py` | `RuneFilterBar` (6 contrôles + signal `changed`) |
| `ui/runes/rune_table.py` | `RuneTable` (`QTableWidget` 7 colonnes + signal `rune_selected`) |
| `ui/runes/rune_detail_panel.py` | `RuneDetailPanel` (panneau latéral) |
| `ui/widgets/multi_check_popup.py` | Widget réutilisable `MultiCheckPopup` |
| `tests/ui/test_runes_page.py` | Instanciation, apply_profile, reset filtres, signal profile_loaded |
| `tests/ui/test_rune_filter_bar.py` | Valeurs par défaut, signal changed, reset_to_defaults |
| `tests/ui/test_rune_table.py` | set_runes, tri, sélection, focus dynamique, valeurs manquantes |
| `tests/ui/test_rune_detail_panel.py` | set_rune, placeholder, grind affiché, "Inventaire" vs nom monstre |
| `tests/ui/test_multi_check_popup.py` | Sélection multiple, label résumé, signal changed |

### 8.2 À modifier (additif non-breaking)

| Chemin | Changement |
|---|---|
| `models.py` | Ajouter `rune_id: int \| None = None` à `Rune` (dernier champ, défaut `None`) |
| `swex_bridge.py` | Dans `parse_rune`, lire `rune.get("rune_id")` et le passer au constructeur `Rune(...)` |
| `ui/main_window.py` | Remplacer `_placeholder("Runes - a implementer")` par `RunesPage()` réel, brancher `profile_loaded` (`QueuedConnection`) et appel dans `_restore_cached_profile` |
| `tests/test_swex_bridge.py` | Ajouter un test qui vérifie l'extraction de `rune_id` |
| `tests/ui/test_main_window_nav.py` | Ajouter un test `test_runes_index_is_runes_page` et `test_profile_loaded_signal_feeds_runes_page` |

### 8.3 Intouchés

- `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `profile_loader.py`, `profile_store.py`, `monster_icons.py`
- `ui/sidebar.py`, `ui/scan/*`, `ui/profile/*`, `ui/theme.py`, `ui/settings/*`, `ui/monsters/*`
- Tabs legacy (`stats_tab.py`, `history_tab.py`, `profile_tab.py`, `auto_tab.py`, `settings_tab.py`)

---

## 9. Découpage en tâches (ordre optimisé pour visibilité E2E précoce)

| # | Tâche | Fichiers | Output visible |
|---|---|---|---|
| 1 | `rune_id` sur `Rune` + extraction `parse_rune` | `models.py`, `swex_bridge.py`, tests | Nouveau champ disponible côté parser |
| 2 | Widget `MultiCheckPopup` | `ui/widgets/multi_check_popup.py`, test | Widget isolé testable |
| 3 | **`RunesPage` squelette + câblage `MainWindow`** | `ui/runes/*` (stubs) + `ui/main_window.py` | **Page vide visible dans l'app dès la tâche 3** |
| 4 | `RuneTable` complet + `apply_profile` peuple | `rune_table.py`, `runes_page.py` | Toutes les runes apparaissent dans la table |
| 5 | `RuneFilterBar` + filtrage live (signal → re-render) | `rune_filter_bar.py`, `runes_page.py` | Filtres fonctionnent en temps réel |
| 6 | Focus stat dynamique | `rune_filter_bar.py`, `rune_table.py` | Colonne "Focus X" + tri par valeur |
| 7 | `RuneDetailPanel` complet | `rune_detail_panel.py`, `runes_page.py` | Clic sur une ligne → détail peuplé |
| 8 | Smoke test manuel | checklist | Validation utilisateur end-to-end |

Chaque tâche suit la discipline TDD : tests rouges → code → tests verts → commit ciblé.

**Totaux estimés** : ~800-1000 lignes de code, ~30 tests, 0 touche aux filtres/scan/auto_mode.

---

## 10. Tests (stratégie globale)

- **Unitaires par composant** : chaque widget (`RuneFilterBar`, `RuneTable`, `RuneDetailPanel`, `MultiCheckPopup`) testé isolément avec `qapp`.
- **Intégration page** : `test_runes_page.py` vérifie que `apply_profile` alimente la table et que le clic propage au détail.
- **Intégration main window** : `test_main_window_nav.py` vérifie que la clé `runes` affiche bien `RunesPage` et que `profile_loaded` est branché.
- **Core** : `test_swex_bridge.py` vérifie l'extraction de `rune_id` depuis un JSON SWEX minimal.

Cible CI : tous les tests UI existants (fondations + plan 01 + plan 02) continuent de passer + ~30 nouveaux tests.

---

## 11. Hors scope (reporté)

- **Édition inline** des runes dans la table.
- **Export CSV / JSON** de la sélection filtrée.
- **Actions en masse** (marquer, supprimer, transférer).
- **Sauvegarde des filtres** entre sessions (reset à chaque profil chargé).
- **Score recalculé** différemment que `swex_efficiency` (pas de scoring maison, on utilise ce que SWEX fournit).
- **Drag & drop** d'une rune vers un autre monstre (éditer l'équipement = plan futur).

---

## 12. Critères d'acceptation

1. Depuis l'onglet `Runes` de la sidebar, la page s'affiche (vide ou peuplée selon profil chargé).
2. Après un scan ou un import manuel de profil, toutes les runes apparaissent dans la table.
3. Cliquer sur n'importe quel header de colonne trie la table.
4. Chaque filtre (Set, Slot, ★, Grade, Focus, Score) filtre la liste en temps réel.
5. Sélectionner `Focus: VIT` → seules les runes avec VIT apparaissent, triées par valeur de VIT desc, colonne 4 affiche la valeur.
6. Cliquer sur une rune peuple le panneau latéral avec ses stats, grind affiché, monstre équipé indiqué.
7. Aucun test UI existant ne régresse.
8. Les modules bot core (`evaluator_chain`, `s2us_filter`, `auto_mode`, `profile_loader`, `profile_store`) ne sont pas modifiés. Seules additions : `rune_id` (modèle) et son extraction (parser).
