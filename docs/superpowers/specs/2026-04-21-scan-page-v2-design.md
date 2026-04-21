# Scan Page v2 — Design

Refonte de la page Scan pour reproduire la maquette `scan 2.png` en
utilisant `Fond 1.png` comme arrière-plan pleine page.

## Contexte

La maquette (`scan 2.png`) présente un tableau de bord "néon-tech" avec :

- Une sidebar à gauche (logo SW, profil ArtheZ, menu de navigation)
- Une zone centrale contenant : titre, hologramme de rune sur le cercle
  magique, carte de détails de rune, bouton de scan, et un panneau
  recommandation (VENDRE + gauges + bouton d'action)
- Une zone droite : historique de scan (grille 2×3) + panneau "Dernière
  Rune Améliorée"

L'arrière-plan `Fond 1.png` (1408×768) fournit déjà les cadres/glows
décoratifs correspondant à ces zones. Les widgets viennent se positionner
par-dessus en coordonnées absolues basées sur des ratios mesurés.

## Architecture

### Fond

- `_SCAN_BG_ASSET` pointe sur `assets/swarfarm/scan_bg/fond_1.png`.
- Mode d'affichage : **cover** (`KeepAspectRatioByExpanding`), centré,
  rogné si nécessaire. L'image remplit toute la `ScanPage` sans bandes.
- `_PageBg.image_rect()` retourne le rectangle visible de l'image après
  rognage, ce qui permet d'exprimer les zones en ratios **relatifs à
  l'image**, pas à la page. Les zones dessinées restent alignées avec les
  widgets peu importe le ratio réel de la fenêtre (dans la limite du
  raisonnable — cover coupe les bords).

### Zones (ratios x, y, w, h sur l'image 1408×768)

Les ratios ci-dessous sont mesurés sur `Fond 1.png` et la maquette
`scan 2.png`. Ils seront ajustés au pixel près lors de l'implémentation.

| Widget | Zone | Ratios (x, y, w, h) |
|---|---|---|
| Titre "Scan de Runes [AVANCÉ]" | haut centre | (0.12, 0.02, 0.55, 0.08) |
| Sous-titre "Last Scanned Rune" | au-dessus du cercle | (0.12, 0.10, 0.30, 0.05) |
| `HolographicRuneVisual` | centre du cercle | (0.12, 0.15, 0.30, 0.45) |
| Bouton "Scanner Nouvelle Rune" | sous hologramme | (0.13, 0.62, 0.26, 0.07) |
| `RuneDetailsCard` | droite du cercle | (0.42, 0.10, 0.32, 0.58) |
| `OptimizerRecommendationPanel` | bandeau horizontal | (0.20, 0.70, 0.56, 0.28) |
| `ScanHistoryPanel` (grille 2×3) | droite 2×3 | (0.76, 0.02, 0.23, 0.76) |
| `UpgradedRunePanel` | slot bas-droit | (0.76, 0.78, 0.23, 0.20) |

### Sidebar (re-skin)

- Logo Summoners War en haut
- Bloc profil : avatar circulaire + "ArtheZ" + barre XP bleue
- Menu : SCANNER / FILTRES / RUNES / MONSTRES / STATS & HISTORIQUE /
  PROFILS / PARAMÈTRES
- Entrée active : dégradé rouge/magenta subtil en fond, icône + texte
  magenta (#e85a7f ou proche), une fine barre rouge verticale à gauche
- Entrées inactives : icônes grises, texte blanc cassé, hover léger

## Composants nouveaux

### `HolographicRuneVisual`
`QLabel` simple qui affiche l'asset hologramme (extrait de `scan 2.png`
et sauvé dans `assets/scan_ui/hologram_rune.png`). En état vide :
placeholder semi-transparent "En attente de scan...". En état rempli :
hologramme statique (pas d'animation en v2).

### `RuneDetailsCard`
Remplace la partie "stats" de `LastScannedCard`. Affiche :
- Titre : "RAGE RUNE (+12)" (set + level)
- Ligne type/classe : "TYPE : 6★ | CLASSE : HÉROIQUE"
- Badge `[STAT PRINCIPALE]` + valeur en grand ("TX CRIT +23%")
- 4 lignes sub-stats avec icône + valeur + **growth bar** colorée :
  - PV / ATK / DEF / VIT / TX CRIT / DÉG CRIT / RES / PRE
  - Couleur growth bar : vert (≥90%), orange (70-89%), rouge (<70%)

### `OptimizerRecommendationPanel`
Panneau horizontal occupant le bandeau du fond. Contient :
- Bandeau titre "RECOMMANDATION DE L'OPTIMISEUR"
- Décision en grand et coloré : **VENDRE** (rouge) ou **GARDER** (vert)
- Ligne "Score : X.X/10" avec icône pièce
- Ligne descriptive courte (raison)
- Deux `CircularGauge` : EFFI S2US (magenta) / EFFI SWOP (or)
- Bouton d'action : "Confirmer Vendre" (rouge) / "Confirmer Garder" (vert)

### `CircularGauge`
Widget réutilisable. Rend un anneau de progression via `QPainter` :
- Fond gris sombre
- Anneau avant-plan coloré (paramètre)
- Valeur au centre (ex : "32%")
- Label sous l'anneau (ex : "EFFI S2US")

### `HistoryRuneCard`
Mini-carte rune pour la grille 2×3. Contient :
- Nom du set + niveau ("RAGE +12")
- Icône du set (24×24)
- Ligne résumé : une sub-stat marquante ("TX CRIT +23")
- Bouton "Vendre" compact (rouge)

`ScanHistoryPanel` est refondu pour afficher ces cartes en `QGridLayout`
2 colonnes × 3 lignes au lieu de la `QScrollArea` verticale actuelle.
Les 6 scans les plus récents sont affichés, en FIFO : la 7ᵉ entrée
éjecte la plus ancienne.

## Flux de données

- L'API existante de `ScanPage` reste : `on_rune(rune, verdict, …)` →
  `update_scanned_rune(rune, verdict)`. Aucun breaking change pour
  `ScanController`.
- Nouveau routing interne : `update_scanned_rune` met à jour
  `HolographicRuneVisual` + `RuneDetailsCard` +
  `OptimizerRecommendationPanel` + ajoute l'entrée à `ScanHistoryPanel`.
- `update_upgrade(…)` continue de cibler `UpgradedRunePanel`.
- `set_active(active)` réinitialise tous les panneaux en état vide.

## États

### État initial (avant scan)
- Hologramme : placeholder "En attente"
- Carte détails : vide avec message discret
- Panneau VENDRE : masqué ou en état neutre ("En attente de rune…")
- Scan History : 6 emplacements vides (placeholders pointillés)
- Dernière Rune Améliorée : état actuel (💤 + message)

### État rempli (après scan)
Conforme à la maquette `scan 2.png`.

## Assets

- `assets/swarfarm/scan_bg/fond_1.png` (déjà copié)
- `assets/scan_ui/hologram_rune.png` (à créer : crop depuis `scan 2.png`)
- Icônes de sets déjà présentes : `assets/swarfarm/runes/*.png`

## Conventions de style

- Couleurs :
  - Magenta/rose actif : `#e85a7f`
  - Rouge vendre : `#F87171` (déjà utilisé)
  - Vert garder : `#4ADE80` (déjà utilisé)
  - Or : `#ffd07a`
  - Bleu cercle/glow : `#5db5ff`
- Typographie : `theme.D.FONT_UI` (sans-serif) + `theme.D.FONT_MONO` pour
  les stats numériques.
- Les panneaux conservent un fond semi-transparent
  (`rgba(24, 28, 36, 0.78)`) pour laisser transparaître le fond.

## Tests / vérification

- Tests UI existants (`tests/ui/test_*`) doivent continuer à passer
  (vérifier les imports/API des composants modifiés).
- Vérification visuelle manuelle en lançant l'app : comparer avec
  `scan 2.png` en superposition mentale.
- `HistoryRuneCard` et `CircularGauge` ont des tests unitaires de base
  (rendu en état rempli / vide).

## Hors scope

- Animations avancées (pulsation de l'hologramme, transitions de panneau)
- Sons / effets haptiques
- Responsive design en dessous de 1100×720 (minimum de l'app)
- Localisation (déjà français partout)

## Ordre d'implémentation suggéré

1. Extraire l'asset hologramme depuis `scan 2.png`.
2. Changer `Fond 1.png` en mode cover + mettre à jour les ratios de
   zone dans `scan_page.py`.
3. Re-skinner la `Sidebar` (entrée active magenta/rouge).
4. Créer `CircularGauge` + test.
5. Créer `OptimizerRecommendationPanel` + test.
6. Créer `RuneDetailsCard` + test.
7. Créer `HolographicRuneVisual`.
8. Créer `HistoryRuneCard` + refondre `ScanHistoryPanel` en grille 2×3.
9. Brancher tous les panneaux dans `ScanPage.update_scanned_rune`.
10. Vérification visuelle finale contre `scan 2.png`.
