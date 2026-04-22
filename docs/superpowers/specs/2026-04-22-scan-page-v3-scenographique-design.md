# Scan Page v3 — Refonte scénographique (design)

Refonte complète de la page Scan pour atteindre un look "scénographique" (pas app-dashboard), calé sur la maquette HTML validée `scan-mockup-v4-inline-v22.html`.

## Contexte

Les versions v1 et v2 reposaient sur un fond image (`Fond 1.png` / `image_19`) avec widgets positionnés par ratios absolus. Problèmes : dépendance au ratio de fenêtre, dégradation sur redimensionnement, esthétique "mockup décoré" plus que UI native.

La v3 reconstruit la page en widgets natifs PySide6 stylés via QSS, reproduisant la hiérarchie et l'atmosphère de la maquette HTML, mais sans l'image de fond. Le rendu doit rester **fidèle au pixel** à la maquette tout en étant 100% responsive via layouts Qt.

## Référence visuelle

`C:\Users\louis\Desktop\Luci2US\.superpowers\brainstorm\484-1776853083\content\scan-mockup-v4.html` (source avant inlining). La maquette sert de contrat visuel : couleurs, typographies, tailles, espacements, états.

## Architecture cible

### Shell applicatif (main_window, déjà en place)

Sidebar (existante dans `ui/sidebar.py`) + zone page. Aucune modification du shell — la refonte concerne uniquement le contenu de la tab Scan.

### `ScanPage` — composition top-down

```
ScanPage  (QWidget, layout vertical)
├── PageHeader          (eyebrow + titre + mode-pill + status-pill + bouton Pause)
├── SessionToolbar      (timer session + 4 stat-cells)
├── Separator
└── ScanBody            (QHBoxLayout — 2 colonnes)
    ├── ScanBodyLeft    (QVBoxLayout)
    │   ├── LastScannedStage   (3 états : scanned / analyzing / idle)
    │   └── HistoryGrid        (QGridLayout 2×3 de HistoryRuneCard)
    └── ScanBodyRight   (QVBoxLayout)
        ├── RecommendationPanel
        └── UpgradeCard
```

### Widgets à (re)construire

| Widget | Fichier | Responsabilité |
|---|---|---|
| `ScanPage` | `ui/scan/scan_page.py` | Composition + câblage callbacks |
| `PageHeader` | `ui/scan/page_header.py` (nouveau) | Titre + status pills + bouton Pause |
| `SessionToolbar` | `ui/scan/session_toolbar.py` (nouveau) | Timer + 4 compteurs (Scannées, Gardées, Vendues, Total) |
| `LastScannedStage` | `ui/scan/last_scanned_stage.py` (nouveau) | Portrait rune 180×180 + details + score global. 3 états |
| `RunePortrait` | `ui/scan/rune_portrait.py` (nouveau) | PNG slot légendaire + badge niveau dynamique |
| `HistoryGrid` | `ui/scan/history_grid.py` (nouveau, remplace `scan_history_panel.py`) | Grille 2×3 de cartes |
| `HistoryRuneCard` | `ui/scan/history_rune_card.py` (existe, à adapter) | Mini rune 44px + nom + meta + verdict |
| `RecommendationPanel` | `ui/scan/recommendation_panel.py` (refonte) | Verdict XL + score line + raison + 2 gauges circulaires + boutons |
| `UpgradeCard` | `ui/scan/upgrade_card.py` (refonte) | Rune amélioration + rarity chip + delta niveau + boost stat |

### Assets statiques requis

- `assets/swarfarm/rune_slots/slot{1..6}_legendaire.png` — frames SW propres (avec "+15" baked-in)
- `assets/swarfarm/rune_slots/slot{1..6}_legendaire0.png` — frames SW propres sans "+15" (badge overlay dynamique)
- `assets/swarfarm/runes/{set}.png` — 24 logos de sets monochromes

### RunePortrait — règle de sélection d'asset

```
si niveau == 15 → charge slot{N}_legendaire.png           (pas de badge overlay)
sinon           → charge slot{N}_legendaire0.png + overlay badge "+{level}"
```

Le logo du set est posé par-dessus comme `QLabel` centré (50% taille, couleur native, ombre portée via `QGraphicsDropShadowEffect`).

## Spécifications visuelles (depuis la maquette)

### Palette (à centraliser dans `ui/theme.py`)

```python
BG          = "#14161c"
BG_HI       = "#1d212b"
BG_LO       = "#0e1015"
PANEL       = "#1c1f28"
PANEL_HI    = "#232733"
BORDER      = "rgba(255,255,255,0.07)"
BORDER_S    = "rgba(255,255,255,0.13)"
FG          = "#f5ecef"
FG_DIM      = "#c2a7af"
FG_MUTE     = "#7a6168"
ACCENT      = "#f0689a"   # rose Luci2US
ACCENT_2    = "#d93d7a"
OK          = "#5dd39e"   # KEEP
ERR         = "#ef6461"   # SELL
WARN        = "#f4c05a"
INFO        = "#9dd9ff"   # SWEX
LEGEND      = "#f5c16e"   # légendaire
HERO        = "#ED8DED"   # héroïque
EXCEPT      = "#ffd877"   # gold exceptionnel
```

### Typographies

- UI : Inter (400/500/600/700/800/900)
- Monospace (nombres, timer) : JetBrains Mono (400/500/600/700/800)
- Fichiers TTF déjà présents dans `assets/fonts/`

### Layout

- Page : padding 24px
- Gap body horizontal : 18px
- Gap body-left vertical : 18px
- History grid : `grid-template-columns: repeat(3, 1fr); gap: 10px;`
- Rune portrait principal : 180×180, border-radius 22px, overflow hidden
- Portrait hist-card : 44×44, border-radius 8px

## États du stage (LastScannedStage)

| État | Affichage |
|---|---|
| `idle` | Message "En attente du prochain scan…" + cercle pulsant |
| `analyzing` | Rune portrait + spinner + texte "Analyse en cours…" |
| `scanned` | Rune portrait + scan-id (set, rarity chip, stats) + scan-score (big-score + grade-badge + potentiel) |
| `exception` | Variante de `scanned` avec halo doré + ribbon "✦ EXCEPTIONNEL" |

## Flux de données (conservé depuis v2)

```
AutoMode → ScanController → ScanPage.on_rune(rune, verdict, …)
                                   │
                                   ├→ _stage.show_scanned(rune, verdict)
                                   ├→ _history_grid.add(rune, verdict)
                                   ├→ _reco.set_verdict(verdict)
                                   └→ _toolbar.increment(verdict.decision)

AutoMode → ScanController → ScanPage.on_rune_upgraded(rune, verdict, …)
                                   └→ _upgrade_card.set(rune, verdict, delta)
```

## Décisions de scope

**Inclus :**
- Reconstruction complète des 8 widgets ci-dessus
- Intégration des 6 frames légendaires (slotX_legendaire.png + _legendaire0.png)
- Badge niveau dynamique +0/+3/+6/+9/+12 + cas +15 (asset natif)
- Suppression du fond `Fond 1.png` et du mode "ratios absolus"
- Suppression des anciens widgets devenus obsolètes (last_rune_card.py, scan_header.py, counters_bar.py, verdict_bar.py, session_stats.py redondants)

**Exclus (différé) :**
- Variante héroïque des frames (nécessite 6 captures supplémentaires, pas livrées)
- Animations d'entrée/sortie complexes (keyframes halo seulement, via `QPropertyAnimation` simple)
- Dark mode alternatif (seul le thème sombre actuel est supporté)
- Redimensionnement responsive en dessous de 1100×700 (taille minimale fixée)

## Build sequence (pour writing-plans)

1. Centraliser la palette/typos dans `ui/theme.py` et ajouter les utilitaires QSS
2. Construire `RunePortrait` (brique réutilisée partout)
3. Construire `PageHeader` + `SessionToolbar` (top fixe)
4. Construire `HistoryRuneCard` adapté + `HistoryGrid`
5. Construire `RecommendationPanel` avec gauges circulaires (`QPainter` custom)
6. Construire `UpgradeCard`
7. Construire `LastScannedStage` avec les 3 états
8. Assembler `ScanPage` et câbler les callbacks
9. Supprimer les fichiers obsolètes + mettre à jour les imports
10. Tester end-to-end : drop SWEX → rune apparaît, historique s'empile, reco affiche verdict, upgrade pousse dans la card dédiée

## Tests visuels

- Comparaison côte-à-côte avec la maquette HTML à 1408×900 (taille cible) et à 1100×700 (taille minimale)
- Vérification des 3 états de `LastScannedStage` via un harness de test qui injecte rune+verdict fictifs
- Vérification des 6 frames (1 rune par slot) + cas +15 et <+15

## Non-régression

- L'API publique de `ScanPage` (`set_active`, `on_rune`, `on_rune_upgraded`, `update_scanned_rune`, `update_upgrade`) est préservée — les controllers existants ne doivent pas changer.
- Les signaux sortants (`entry_clicked` sur history) sont préservés.
