# Luci2US — Design des 5 onglets PySide6 restants

**Date :** 2026-04-17
**Projet :** Luci2US (bot Summoners War, `C:\Users\louis\Desktop\Luci2US`)
**Scope :** portage PySide6 des onglets `Filtres` (nouveau), `Runes` (nouveau), `Monstres` (nouveau), `Stats & Historique` (fusion legacy), `Paramètres` (minimal).

---

## 1. Contraintes

1. **Bot core intouchable** : `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `swex_bridge.py`. Seuls des callbacks optionnels strictement additifs sont acceptés.
2. **Source de vérité visuelle** : `scan-page-v13.html`. Le style (couleurs, tailles, typographie) de tout nouvel onglet doit s'aligner sur les constantes de `ui/theme.py`.
3. **Stack** : PySide6 6.11.0, pytest-qt pour les tests.
4. **Déjà livré** : `Scan`, `Profil`, `ScanController`, `MainWindow` + `Sidebar` (5 items). À ne pas régresser.
5. **Persistance disque** : `profile_cache.json` (profil), `history.db` (sessions + runes), `config.json` (réglages).

---

## 2. Sidebar — nouvel ordre (7 items)

```
Scan · Filtres · Runes · Monstres · Stats & Historique · Profils · Paramètres
```

Le mapping `ui/sidebar.py::NAV_ITEMS` est étendu. Les clés internes utilisées par `MainWindow._on_nav` :

| Ordre | Label | Clé interne |
|---|---|---|
| 1 | Scan | `scan` |
| 2 | Filtres | `filters` |
| 3 | Runes | `runes` |
| 4 | Monstres | `monsters` |
| 5 | Stats & Historique | `stats_history` |
| 6 | Profils | `profile` |
| 7 | Paramètres | `settings` |

Le `QStackedWidget` de `MainWindow` contiendra 7 pages (index 0-6 dans l'ordre ci-dessus).

---

## 3. Onglet Filtres

### Objectif

Permettre à l'utilisateur d'importer, créer, éditer, exporter et tester des filtres S2US directement depuis l'app. Remplace complètement la section « Filtres S2US » du `settings_tab.py` legacy.

### Layout : 2 colonnes, pas de sous-onglets

```
┌─────────────────────┬──────────────────────────────────────────┐
│  Filtres S2US       │  [●─] Nom : SPD (CR + CD + ACC)          │
│  ◯ ─ ▲ ▼ ◯          │  ┌─ SET ──────────────────────────────┐  │
│  [Importer][Exporter]│  │ ☐ Despair ☑ Energy ☑ Fatal ...  │  │
│  [   Test   ]       │  └────────────────────────────────────┘  │
│  ┌───────────────┐  │  ┌Niveau┬Rareté┬Slot┬★┬Classe────┐     │
│  │▼[S2US][...]   │  │  └──────┴──────┴────┴─┴──────────┘     │
│  │▼SLOT 4/6 ...  │  │  ┌ Propriété principale  Innate  ┐     │
│  │  SPD (ACC...) │  │  └────────────────────────────────┘     │
│  │ ►SPD (CR+CD)  │  │  ┌ Sous-propriétés (Obligatoire/Opt) ┐   │
│  │  ...          │  │  │ ☑ VIT ≥ 3   ━●━━━━    1 2 3 4    │   │
│  └───────────────┘  │  │ ☐ PV% ≥ 17  ━━━●━━                │   │
│                     │  └────────────────────────────────────┘  │
│                     │  ┌ Efficacité ┬ Meule/Gemme ┬ Marque ┐  │
│                     │  └────────────┴──────────────┴────────┘  │
│                     │           [      SAVE      ]              │
└─────────────────────┴──────────────────────────────────────────┘
```

### Panneau gauche (~230 px)

- **Titre** : « Filtres S2US »
- **4 boutons ronds** (bronze) : `+` (nouveau filtre vide), `−` (supprimer sélection), `▲` (monter la priorité), `▼` (descendre la priorité)
- **3 boutons rectangulaires** :
  - `Importer` : file picker `.s2us`, parse via `s2us_filter.load_s2us_file`, fusionne dans la collection courante
  - `Exporter` : file picker save, ré-écrit la collection via nouveau module `s2us_writer.py`
  - `Test` : ouvre la modale Rune Optimizer (voir § 3.3)
- **Liste catégorisée** : groupes repliables (`▼ [S2US][End-game]`, `▼ SLOT 4/6 FILTERS (PREMIUM)`, etc.). Chaque item sélectionnable, la sélection met à jour le panneau droit.

### Panneau droit (~550 px) — éditeur S2US complet

Reprise fidèle du layout S2US original adaptée au thème Luci2US :

| Bloc | Contenu |
|---|---|
| **Header** | Toggle `enabled` + input `Nom` |
| **Set** (libellé FR, ex-« Taper ») | Grille 6 colonnes des 23 sets (`SETS_FR` de `models.py`) avec bouton « Cocher/décocher » |
| **Niveau** | Slider (0-15) avec label « Smart Filter » |
| **Rareté** | ☑ Rare ☑ Hero ☑ Legend |
| **Slot** | Grille 2×3 des slots 1-6 |
| **Niveau★** | ☑ 5★ ☑ 6★ |
| **Classe** | ☑ Normal ☑ Ancient |
| **Propriété principale** | Grille 3 colonnes des main stats (colonnes grisées si non applicables à un slot choisi) |
| **Propriété innate (prefix)** | Même grille, pleine |
| **Sous-propriétés** | Pour chaque stat, état tri-valué via bouton bascule : **☑** (obligatoire — doit être présente avec valeur ≥ seuil) / **➖** (optionnelle — compte dans le quota de facultatives requis) / **☐** (ignorée — la stat ne joue aucun rôle dans le match). Chaque ligne : bouton tri-état + nom stat + seuil numérique `≥ N` (éditable) + slider synchronisé avec le seuil. À droite du bloc : compteur radio `Combien de sous-propriétés facultatives doit-il y avoir ? (1/2/3/4)` |
| **Efficacité** | Slider 0-100% + label valeur + dropdown « Méthode » (S2US) |
| **Simuler Meule/Gemme** | 2 dropdowns : Rare/Hero/Legend Grind, Rare/Hero/Legend Gem |
| **Marque rune** | Dropdown (tags disponibles) |
| **SAVE** | Bouton pleine largeur, bronze |

**Supprimé par rapport au screenshot S2US original** (sur demande utilisateur) :
- La section « Règles de power-up » (Améliorer +3 à +3 / Hero à +12 / Legend à +12 avec sliders)
- Les checkboxes « Use Grindstone (amplify) » et « Use Enchanted Gem (convert) »

### Modale Rune Optimizer (bouton Test)

**Input :** saisie ou collage d'une rune (set, slot, ★, niveau actuel 0-15, grade, main stat, substats avec grind actuel éventuel).

**Sortie :**

- **Si rune +0** : la meilleure configuration future `meule + gemme` qui maximise l'efficience S2US théorique (simulation des améliorations jusqu'à +12, best grind + best gem sur le sub optimal, respect des règles de grades autorisés — cf. `models.GRIND_MAX` / `models.GEM_MAX`).
- **Si rune +12** : que meuler et/ou gemmer **maintenant** sur cette rune spécifique pour maximiser l'efficience (sélection du sub qui donne le plus gros gain d'Eff après grind/gem).
- **Dans les deux cas** : affichage du verdict par filtre (quel(s) filtre(s) matche(nt) la rune dans sa config optimisée, en tenant compte de la priorité des filtres).

### Nouveaux modules à créer

| Fichier | Rôle |
|---|---|
| `s2us_writer.py` | Sérialise une liste de `S2USFilter` vers le format `.s2us` (inverse de `load_s2us_file`) |
| `rune_optimizer.py` | Logique pure : prend une `Rune`, renvoie meilleure combinaison meule+gemme pour max Eff S2US |
| `ui/filtres/filtres_page.py` | Page principale 2 colonnes |
| `ui/filtres/filter_list_panel.py` | Colonne gauche |
| `ui/filtres/filter_editor.py` | Colonne droite |
| `ui/filtres/rune_tester_modal.py` | Modale Test |

---

## 4. Onglet Runes

### Objectif

Vue inventaire complet des runes du profil chargé (équipées + inventaire). Permet de filtrer, trier et inspecter rapidement une rune.

### Layout : barre de filtres + liste + panneau latéral permanent (Q1)

```
┌─────────────────────────────────────────────────────────────────┐
│ [Set: Violent ▾] [Slot: Tous ▾] [★≥6] [Grade: Hero+] [Score≥80]│ filtres
├────────────────────────────────────────────────┬────────────────┤
│ SET     SL  MAIN        SUB            SCORE  │  Violent · S2  │
│ Violent 2   ATQ+22%     VIT+12          92    │  ★6 · +12 · H  │
│ Violent 4   DC+64%      CC+9            87    │                │
│ ► Violent 2 ATQ+22%     VIT+12          92    │  ATQ +22%      │
│ Violent 6   ATQ+51%     PV+375          85    │                │
│ Violent 3   DEF+8%      ATQ+22          83    │  Subs          │
│ Violent 5   PV+2448     CC+9            81    │  VIT +12 (+5)  │
│ ...                                            │  PV% +9        │
│                                                │  CC +6         │
│                                                │  DC +5         │
│                                                │  ─────         │
│                                                │  Équipée:      │
│                                                │  Lushen        │
│                                                │  Score 92 · E135│
└────────────────────────────────────────────────┴────────────────┘
```

### Barre de filtres (haut)

Facettes :
- `Set` : multi-select parmi `SETS_FR`
- `Slot` : multi-select 1-6
- `★` : checkboxes 5★, 6★
- `Grade` : Magique / Rare / Héroïque / Légendaire (multi)
- `Score min` : slider 0-100 avec valeur affichée

### Liste centrale

Table triable (colonnes cliquables) :
- Set (icône 16 px + nom court)
- Slot
- Main stat
- Top sub
- Score

Surlignage de la ligne sélectionnée (bordure gauche bronze, fond doré 8 %). Style repris de `ui/scan/history_list.py`.

### Panneau latéral droit (~180 px, permanent)

Affiche le détail de la rune sélectionnée :
- Set + Slot (titre serif or)
- Étoiles + niveau + grade
- Main stat (box sombre soulignée or)
- Substats avec indication du grind actuel entre parenthèses
- Monstre équipé (ou « Inventaire » si non équipée)
- Score + Efficience (badge bronze)

Si aucune rune sélectionnée : placeholder « Cliquez une rune pour voir le détail ».

### Nouveaux fichiers

| Fichier | Rôle |
|---|---|
| `ui/runes/runes_page.py` | Page principale (barre + table + panneau) |
| `ui/runes/rune_filter_bar.py` | Facettes filtrantes |
| `ui/runes/rune_table.py` | Liste triable des runes |
| `ui/runes/rune_detail_panel.py` | Détail latéral |

La page lit `profile["runes"]` exposé par `profile_loader` + signal `ScanController.profile_loaded`.

---

## 5. Onglet Monstres

### Objectif

Vue inventaire des monstres du compte. Clic sur un monstre → page dédiée plein écran avec ses runes équipées.

### Layout : liste dense + push page (mix A+C)

### Vue liste (par défaut)

```
┌─────────────────────────────────────────────────────────────────┐
│ [Élément: Tous ▾] [★≥6] [🔎 Nom...]                             │
├─────────────────────────────────────────────────────────────────┤
│  [IMG] Lushen    ★6  L40  Vent     Eff moyenne 128%    ►       │
│  [IMG] Laika     ★6  L40  Feu      Eff moyenne 115%    ►       │
│  [IMG] Bella     ★6  L40  Eau      Eff moyenne 112%    ►       │
│  [IMG] Khmun     ★6  L40  Tenèbres Eff moyenne 124%    ►       │
│  [IMG] Dominic   ★6  L40  Vent     Eff moyenne 108%    ►       │
│  ...                                                             │
└─────────────────────────────────────────────────────────────────┘
```

**Barre de filtres** :
- `Élément` : Eau / Feu / Vent / Lumière / Ténèbres / Tous
- `★` : ≥1 à ≥6
- `Nom` : recherche texte (filtrage live)

**Liste** : chaque ligne = photo (icône Swarfarm, cache local), nom, étoiles, niveau, élément, **Eff moyenne** (moyenne arithmétique des `swex_efficiency` des runes équipées, slots vides ignorés), chevron `►`. Surlignage hover bronze.

### Vue détail (push page)

Clic sur un monstre → remplace la vue par :

```
┌─────────────────────────────────────────────────────────────────┐
│  < Retour · Monstres / Lushen                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ╔══════╗  Lushen                                              │
│   ║ IMG  ║  Vent · ★6 · Niv 40                                  │
│   ╚══════╝  PV 12 450 · ATQ 2 248 · VIT 183 · CC 78% · DC 164% │
│                                                                 │
│  ┌─────────┬─────────┬─────────┐                               │
│  │ SLOT 1  │ SLOT 2  │ SLOT 3  │                               │
│  │ Fatal   │ Fatal   │ Fatal   │                               │
│  │ ATQ+22% │ ATQ+22% │ DEF+8%  │                               │
│  │ subs... │ subs... │ subs... │                               │
│  ├─────────┼─────────┼─────────┤                               │
│  │ SLOT 4  │ SLOT 5  │ SLOT 6  │                               │
│  │ Violent │ Violent │ Violent │                               │
│  │ DC+64%  │ PV+2448 │ ATQ+51% │                               │
│  │ subs... │ subs... │ subs... │                               │
│  └─────────┴─────────┴─────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Un bouton `< Retour` (breadcrumb) en haut ramène à la vue liste. Implémenté via un `QStackedWidget` interne à la page (index 0 = liste, index 1 = détail).

### Refresh icônes Swarfarm

Le bouton `Refresh icônes Swarfarm` (legacy `settings_tab.py`) est **déplacé ici** (coin haut-droit de la vue liste) car sémantiquement lié aux monstres.

### Nouveaux fichiers

| Fichier | Rôle |
|---|---|
| `ui/monsters/monsters_page.py` | Page (QStackedWidget liste/détail) |
| `ui/monsters/monster_list.py` | Vue liste + filtres |
| `ui/monsters/monster_detail.py` | Vue détail plein écran |

---

## 6. Onglet Stats & Historique

### Objectif

Fusion des onglets legacy `stats_tab.py` (charts) et `history_tab.py` (sessions). Deux sous-onglets internes qui partagent le filtre période.

### Layout : toolbar période partagée + 2 sous-onglets

```
┌─────────────────────────────────────────────────────────────────┐
│ [Stats] [Historique]                [Aujourd'hui][7j][30j][Tout]│
├─────────────────────────────────────────────────────────────────┤
│                    (contenu du sous-onglet)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Sous-onglet Stats

Grille 2×2 de cartes `QFrame` style Luci2US :

| | |
|---|---|
| **VERDICT** (barres empilées KEEP/SELL/POWER-UP) | **GRADE** (barres Magique/Rare/Héroïque/Légendaire) |
| **SESSIONS / JOUR** (barres chronologiques) | **TOP RUNES** (mini-liste des 5 meilleurs scores de la période) |

Les charts utilisent `QtCharts` (embarqué natif PySide6) pour rester cohérent avec le reste. En fallback : matplotlib embed comme le legacy.

### Sous-onglet Historique

**Liste scrollable des sessions** (récentes en haut) :
- Date + heure
- Durée
- Compteurs : scannées / keep / sell / power-up
- Eff moyenne

**Clic sur une session** → ouvre la **vue détail session** (remplace la liste, breadcrumb `< Retour`) :
- Mini-charts de la session (Verdict, Grade)
- Liste complète des runes scannées (table triable, identique à l'onglet Runes mais filtrée sur la session)

### Nouveaux fichiers

| Fichier | Rôle |
|---|---|
| `ui/stats_history/stats_history_page.py` | Page (toolbar + QTabWidget) |
| `ui/stats_history/stats_view.py` | Sous-onglet Stats (4 charts) |
| `ui/stats_history/history_view.py` | Sous-onglet Historique (liste + détail) |

La page lit `history.db` via l'API existante `history_db.py` (fonctions `get_sessions`, `get_runes_by_session`, `get_top_runes`).

---

## 7. Onglet Paramètres

### Objectif

Réglages résiduels — minimaliste après extraction des filtres et des icônes monstres.

### Contenu

```
┌─────────────────────────────────────────────────────────────────┐
│  Paramètres                                                     │
│                                                                 │
│   Langue                                                        │
│   [ FR ▾ ]                                                      │
│                                                                 │
│   SWEX — Dossier des drops                                      │
│   [C:\...\SWEX\drops          ] [Parcourir]                     │
│                                                                 │
│   [ Sauvegarder ]                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Nouveau fichier

| Fichier | Rôle |
|---|---|
| `ui/settings/settings_page.py` | Page (Langue + SWEX path + Save) |

Lecture/écriture via `config.json` existant (fonction `_save` équivalente au legacy).

---

## 8. Arborescence finale

```
ui/
├── __init__.py
├── theme.py                      (inchangé, étendu si besoin)
├── sidebar.py                    (NAV_ITEMS étendu à 7 items)
├── main_window.py                (QStackedWidget 7 pages, _on_nav mis à jour)
├── controllers/
│   └── scan_controller.py        (inchangé)
├── widgets/                      (inchangé)
├── scan/                         (inchangé)
├── profile/                      (inchangé)
├── filtres/                      ← NOUVEAU
│   ├── __init__.py
│   ├── filtres_page.py
│   ├── filter_list_panel.py
│   ├── filter_editor.py
│   └── rune_tester_modal.py
├── runes/                        ← NOUVEAU
│   ├── __init__.py
│   ├── runes_page.py
│   ├── rune_filter_bar.py
│   ├── rune_table.py
│   └── rune_detail_panel.py
├── monsters/                     ← NOUVEAU
│   ├── __init__.py
│   ├── monsters_page.py
│   ├── monster_list.py
│   └── monster_detail.py
├── stats_history/                ← NOUVEAU
│   ├── __init__.py
│   ├── stats_history_page.py
│   ├── stats_view.py
│   └── history_view.py
└── settings/                     ← NOUVEAU
    ├── __init__.py
    └── settings_page.py

s2us_writer.py                    ← NOUVEAU (écriture .s2us)
rune_optimizer.py                 ← NOUVEAU (calcul meule+gemme optimal)
```

Total : **5 nouveaux sous-dossiers UI**, **15 nouveaux fichiers UI métier** (+ 5 `__init__.py`), **2 nouveaux modules core additifs**.

---

## 9. Impact sur l'existant

### Modifications non-invasives

| Fichier | Changement |
|---|---|
| `ui/sidebar.py` | `NAV_ITEMS` étendu à 7 items dans l'ordre spécifié |
| `ui/main_window.py` | Imports des 5 nouvelles pages, `QStackedWidget` à 7 pages, `_on_nav` mapping à 7 clés |

### Aucune modification

- `evaluator_chain.py` — intouchable
- `s2us_filter.py` — lecture uniquement (écriture va dans `s2us_writer.py`)
- `auto_mode.py` — intouchable
- `swex_bridge.py` — intouchable
- `ui/controllers/scan_controller.py` — inchangé
- `ui/scan/*`, `ui/profile/*`, `ui/widgets/*` — inchangés

### Fichiers legacy à supprimer après portage validé

Après validation end-to-end des 5 nouvelles pages :
- `settings_tab.py`
- `stats_tab.py`
- `history_tab.py`
- `auto_tab.py`
- `profile_tab.py`

---

## 10. Tests (pytest-qt)

Pour chaque nouvelle page, un test minimum vérifiant :
1. La page s'instancie sans crash.
2. La page reçoit un profil via signal et peuple ses widgets (Runes, Monstres).
3. La page charge les sessions depuis `history.db` (Stats & Historique).
4. Le panneau de filtres déclenche correctement le signal de changement de sélection (Runes).
5. Le push page Monstres bascule bien entre liste et détail.
6. L'éditeur de filtres sauvegarde correctement un filtre modifié (Filtres — test d'intégration avec `s2us_writer`).

Cible : dossier `tests/ui/` étendu, pas de nouveau framework.

---

## 11. Hors scope (volontairement reporté)

- Drag & drop dans la liste des filtres (priorité gérée via boutons ▲▼ pour ce cycle).
- Édition inline dans la table Runes (lecture seule pour ce cycle).
- Export CSV/Excel des sessions depuis Historique.
- Thème clair / autre palette (la palette v13 reste la seule cible).
- Internationalisation des nouveaux onglets au-delà de FR/EN via `i18n.py` existant (les libellés neufs seront ajoutés dans `i18n.py` au fur et à mesure).

---

## 12. Ordre d'implémentation suggéré (à détailler dans le plan)

1. **Paramètres** (le plus simple, valide le pattern page → sidebar → QStackedWidget).
2. **Monstres** (liste + push page, pas de filtres complexes, teste le pattern QStackedWidget interne).
3. **Runes** (liste + panneau latéral, pattern maître-détail permanent).
4. **Stats & Historique** (fusion legacy, QTabWidget interne).
5. **Filtres** (le plus complexe, nécessite `s2us_writer` + `rune_optimizer` ; à faire en dernier quand tout le reste est stable).

Ce séquencement sera repris et détaillé par l'étape `writing-plans`.
