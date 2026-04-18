# Handoff: Runes Page (Luci2US)

## Overview

La page **Runes** permet à l'utilisateur de parcourir l'inventaire complet de ses runes (jusqu'à ~5 000 entités), de les filtrer/trier finement pour décider lesquelles garder ou vendre, et de simuler l'équipement d'une rune sur un monstre via une modal dédiée.

Elle fait partie de l'app desktop **Luci2US** (PyQt6, Windows, frameless) et utilise la même palette warm-dark / magenta que les pages Scan et Monsters.

## About the Design Files

Les fichiers de ce bundle sont des **références de design en HTML/React** — des prototypes montrant le look visé et le comportement attendu, **pas du code de production à copier**. La tâche consiste à **recréer ces designs dans l'environnement PyQt6 existant** (patterns, conventions et base classes déjà en place), **pas** à embarquer du HTML dans l'app.

## Fidelity

**High-fidelity.** Couleurs, typographies, espaces et interactions sont finaux. Les hexagones de runes et portraits de monstres (dans la modal de simulation) sont des **placeholders** à remplacer par les vrais assets Swarfarm côté code.

## Screens / Views

### 1. Liste Runes (vue principale)

**Nom** : Runes — Inventaire
**But** : Parcourir / filtrer / trier l'inventaire, sélectionner une rune pour voir son détail dans le side panel, lancer une simulation d'équipement.

**Layout général** (de haut en bas, dans la fenêtre) :
- `WinTitleBar` (32px) — barre titre frameless Windows custom
- Corps à deux colonnes :
  - **Sidebar** fixe à gauche (même composant que Monsters, Scan, etc.)
  - **Zone principale** à droite, en colonne :
    - Header (titre + compteurs) — `padding: 22px 28px 12px`
    - Toolbar de filtres (1 ligne, wrap possible) — `padding: 0 28px 14px`
    - Body split : tableau (`flex:1`, scroll vertical) + side panel détail (`320px` fixe)

#### Header
- Eyebrow "INVENTAIRE" : `11px / accent / weight 600 / letter-spacing 1.5 / uppercase`
- Titre "Runes" : `24px / #f5ecef / weight 600 / letter-spacing -0.5`
- Compteurs en ligne (12.5px, #c2a7af) : "`{filtrées}` sur `{total}` · `{+15}` +15 · `{libres}` libres"
  - Chiffres en JetBrains Mono / blanc
  - Séparateurs en `·` muted

#### Toolbar
Dans l'ordre, gap 8px, wrap autorisé :
1. **Select Set** : dropdown (`padding 6×10 / radius 999 / bg rgba(255,255,255,0.03) / border 1px / 12px weight 600`)
   - "Tous les sets" par défaut, puis liste triée alphabétiquement
2. **Filtre Slot** — segmented pills : label "Slot" (désélectionne tout) + 1, 2, 3, 4, 5, 6
3. **Filtre Grade** — segmented pills : Tous / 6★ / 5★
4. **Filtre Rareté** — segmented pills : Tous / **Légende** (`#f5c16e`) / **Héros** (`#7ba6ff`)
5. **Slider Level** : "Level ≥ `+N`" avec `<input type="range" min=0 max=15>`
   - **Track : `#2a1018`** (teinte du fond de page, pas le gris natif)
   - Thumb : rond 12×12, magenta `#f0689a`, `box-shadow 0 0 8px rgba(240,104,154,0.4)`
6. **Filtre Équipée** — segmented pills : Toutes / Équipées / Libres

#### Tableau (flex:1, overflow auto)
Conteneur : `bg rgba(36,20,26,0.72) / backdrop-filter blur(20px) / border 1px / radius 12 / overflow hidden`

**Grille des colonnes (9 cells)** :
```
32px | 36px | 80px | 44px | 80px | 260px | 1fr | 160px
```
(avec une cellule vide invisible entre la colonne Équipée et la colonne Substats via `1fr`)

**En-tête** : `padding 10×16 / fontSize 9.5 / uppercase 700 / letter-spacing 0.8 / color #7a6168 / bg rgba(0,0,0,0.2) / border-bottom 1px`
- Les colonnes Slot, Grade, Set, Lv, Eff. sont **cliquables pour tri** — indicateur ▼ (desc) / ▲ (asc) en magenta quand actif
- Label "Équipée sur / Eff." pour la colonne combinée

**Ligne** : `padding 8×16 / border-bottom 1px rgba(255,220,230,0.06) / transition bg 0.12s`
- Ligne sélectionnée : `bg rgba(240,104,154,0.14)`
- Hover : pas d'effet (la transition applique au clic)

**Contenu des cellules** :
1. **Hex mini** (28×28) — hexagone SVG avec numéro de slot, `fill accent22 / stroke accent 1.2`. Petit ★ jaune en haut-droite si grade ≥ 6
2. **Grade** : "6★" ou "5★" en JetBrains Mono 11 / 700 / couleur accent
3. **Set** : nom en `12px / #f5ecef / weight 600 / nowrap ellipsis` (80px max)
4. **Level** : "+N" en `11px Mono / 600 / marginLeft -14px` (collé au set).
   - Si +15 : accent magenta
5. **Main stat** : stack vertical
   - Nom en `10px / muted`
   - Valeur en `12px Mono / 700 / #f5ecef`
6. **Substats** : flex-wrap 260px, `gap 2px 8px / marginLeft -6`
   - Chaque substat : `{name}` (10px / fgDim) + valeur (10px Mono / 700 / fg) + `+N` si rolled > 1 (8px / 700 / accent)
7. (vide, `1fr`, pour pousser la colonne suivante à droite)
8. **Équipée sur / Eff.** (colonne 160px, stack vertical) :
   - Haut : nom du monstre (12px / fg si équipée, italic/muted si libre)
   - Bas : efficacité en Mono 11 / 700 / couleur selon seuil :
     - `> 90%` → `#5dd39e` (vert OK)
     - `> 75%` → `#f0689a` (magenta accent)
     - `> 60%` → `#c2a7af` (fgDim)
     - Sinon → `#7a6168` (muted)

#### Side Panel Détail (320px fixe, scrollable)
`bg rgba(36,20,26,0.72) / backdrop-filter blur(20px) / border 1px / radius 12 / padding 20 / flex column gap 16`

**Bloc 1 — Identité (centré)** :
- Hexagone grand format 88×88 avec gradient radial accent + stars si 6★
- Eyebrow `{set} · Slot {slot}` en accent 11 uppercase
- Rangée de 6 étoiles 13px accent (opacité 0.18 pour les non remplies) — peut-être remplacer par "N★" compact si besoin de place
- Chips : **Rarity chip** + **Level chip**
  - Rarity : `bg color+18 / border color+33 / color / 10px 600` (couleur selon hero/legend)
  - Level : `bg accentDim si +15 sinon rgba(255,255,255,0.04) / 11px Mono 700`

**Bloc 2 — Main stat** :
- Label "MAIN STAT" (9px uppercase muted)
- Carte `bg accentDim / border accent33 / radius 8 / padding 10×12`
- Nom 13px 600 à gauche, valeur 18px Mono 700 accent à droite

**Bloc 3 — Substats** (4 cartes empilées) :
- Label "SUBSTATS"
- Chaque : `bg rgba(255,255,255,0.02) / border 1px / radius 8 / padding 8×12 / flex row justify-between`
  - Gauche : nom 11px Mono fgDim + badge "+N" si rolled > 1 (`bg accentDim / color accent / 9px 700 / padding 1×5 / radius 3`)
  - Droite : valeur 13px Mono 700 fg

**Bloc 4 — Efficacité** :
- Label "EFFICACITÉ" + valeur 22px Mono 700 (couleur selon seuils)
- Barre 6px `bg rgba(255,255,255,0.04) / radius 3`
  - Fill 100% * eff/100, `box-shadow 0 0 8px color66`

**Bloc 5 — Équipée sur** :
- Label "ÉQUIPÉE SUR"
- Si équipée : carte avec portrait placeholder 36×36 + nom 13px 600 + "lv40 · 6★" 10px muted
- Si libre : carte `border 1px dashed / italic muted center / "Non équipée"`

**Bouton Simuler** (au fond, `marginTop: auto`) :
- `padding 10×14 / radius 8 / linear-gradient 180° accent→accent2 / #fff 12.5 600 / icône soleil 14×14 / box-shadow 0 8px 20px -8px accent`
- Libellé "Simuler sur un monstre"
- **Ouvre la Modal de Simulation**

### 2. Modal de Simulation d'Équipement

**Nom** : Simulation d'équipement
**But** : Lister des monstres candidats pour la rune sélectionnée, montrer l'impact (delta d'efficacité) d'équiper cette rune sur chacun, et permettre de valider l'équipement.

**Layout** :
- Overlay : `position absolute inset 0 / bg rgba(5,3,4,0.72) / backdrop-filter blur(6px) / padding 40 / center`
- Conteneur : `max-width 720 / max-height 600 / bg #1a0f14 / radius 16 / border 1px / box-shadow 0 40px 80px -20 rgba(0,0,0,0.6), 0 0 0 1px accent22 / overflow hidden`
- Structure :
  - **Header** : hexagone 56 + eyebrow "SIMULATION D'ÉQUIPEMENT" + titre "{Set} slot {N} +{level} · {eff}%" + bouton close × (34×34)
  - **Body** (flex 1 scroll, padding 20) :
    - Label "CANDIDATS SUGGÉRÉS"
    - Liste 5 candidats en grid `40px 1fr 90px 90px 90px`
      - Portrait placeholder 36×36 (rond)
      - Nom 13px 600 + "lv40 · 6★" 10px muted
      - "ACTUEL" (9px uppercase muted) + valeur en Mono 13 600 fgDim
      - "APRÈS" (9px uppercase muted) + valeur en Mono 13 700 (vert si gain, rouge si perte)
      - Badge delta : `▲ +X%` ou `▼ -X%` (vert ou rouge, bg color+18)
    - Sélection : carte sur fond `accentDim / border accent66`
    - Bloc info en bas (muted, border, 11.5px, 1.5 line-height)
  - **Footer** : boutons Annuler (outline) + Équiper (gradient accent)
    - Bouton Équiper **désactivé** (bg `rgba(255,255,255,0.04) / color muted / not-allowed`) tant qu'aucun candidat n'est sélectionné

## Interactions & Behavior

### Tableau
- **Click sur une ligne** → `selectedIdx` change → side panel met à jour
- **Click sur un en-tête sortable** (Slot, Grade, Set, Lv, Eff.) :
  - 1er clic : change la clé de tri, `dir = 'desc'`
  - Clics suivants sur la même clé : toggle `desc` ↔ `asc`
- Tri par défaut : `efficiency desc`

### Filtres
- Combinaison en AND
- Set select → exact match
- Slot/Grade pills → radio (click sur actif = désélectionne)
- Rarity pills → radio
- Level slider → `r.level >= filterLevelMin`
- Équipée pills → radio (all / equipped / free)
- Le compteur en header reflète les résultats filtrés en temps réel

### Side Panel
- Toujours visible (pas de toggle)
- Scrollable si le contenu déborde
- **Bouton "Simuler sur un monstre"** → ouvre la modal

### Modal Simulation
- **Click overlay** (hors conteneur) → ferme
- **Click ×** → ferme
- **Touche Échap** → ferme (à ajouter côté PyQt6, non présent dans le proto)
- **Click sur un candidat** → sélectionne (highlight), active le bouton Équiper
- **Click Équiper** → (à brancher sur le backend : déplace la rune, ferme la modal, rafraîchit la liste)
- **Click Annuler** → ferme sans action

### Animations
- Transitions d'état : `transition: background 0.12s` sur les lignes de tableau
- Pas d'animations d'entrée/sortie dans le proto — libre d'ajouter un fade 150ms sur la modal

## State Management

### Page
```python
sort_by: "efficiency"|"level"|"grade"|"slot"|"set"   # défaut "efficiency"
sort_dir: "desc"|"asc"                               # défaut "desc"
filter_set: str | None
filter_slot: int | None                              # 1..6
filter_grade: int | None                             # 5 or 6
filter_rarity: "hero"|"legend" | None
filter_level_min: int                                # 0..15, défaut 0
filter_equipped: "all"|"equipped"|"free"             # défaut "all"
selected_idx: int
simu_open: bool                                      # défaut False
```

### Modal Simulation
```python
target: int | None                                   # index du candidat sélectionné
```

### Données attendues (à brancher sur le backend/DB)
```python
Rune {
  idx: int
  set: str                     # Violent, Will, Swift, Despair, Focus, Energy, Fatal, Rage, Blade, Guard, Endure, Nemesis, Vampire, Destroy, Fight, ...
  slot: int                    # 1..6
  grade: int                   # 5 or 6
  level: int                   # 0..15
  rarity: "hero"|"legend"
  main_stat: str               # "ATK+", "ATK%", "SPD", "CRI Rate%", etc
  main_value: str | int        # "45%" ou 1297
  subs: list[Substat]          # exactement 4
  efficiency: float            # 0..150 (peut dépasser 100)
  equipped: bool
  owner_name: str | None       # nom du monstre équipé, None si libre
}

Substat {
  name: str                    # "HP+", "HP%", "ATK+", ... "CRI Rate%", "CRI Dmg%", "ACC%", "RES%"
  value: str | int             # "12%" ou 45
  rolled: int                  # 1..5 (1 = base, pas de "+N" affiché)
}

SimuCandidate {
  name: str
  stars: int
  current_eff: float           # eff moyenne actuelle du monstre
  delta: float                 # variation d'eff si on équipe cette rune (peut être négatif)
}
```

## Design Tokens

### Palette — identique à Scan / Monsters
```python
BG          = "#0d0907"
BG_GRAD     = "radial-gradient(ellipse at 12% 0%, #3a1624 0%, #0d0907 50%), radial-gradient(ellipse at 100% 100%, #2a1018 0%, #0d0907 55%)"
PANEL       = "rgba(36, 20, 26, 0.72)"
PANEL2      = "rgba(48, 26, 34, 0.45)"
BORDER      = "rgba(255, 220, 230, 0.06)"
BORDER_STR  = "rgba(255, 220, 230, 0.10)"
FG          = "#f5ecef"
FG_DIM      = "#c2a7af"
FG_MUTE     = "#7a6168"
ACCENT      = "#f0689a"
ACCENT_2    = "#d93d7a"
ACCENT_DIM  = "rgba(240, 104, 154, 0.14)"
OK          = "#5dd39e"
WARN        = "#f5c16e"
ERR         = "#ef6461"

# Slider track (fond de page sombre)
SLIDER_TRACK = "#2a1018"
```

### Raretés
```python
HERO   = "#7ba6ff"
LEGEND = "#f5c16e"
```

### Typographie
- **Inter** (400/500/600/700) — UI text
- **JetBrains Mono** (400/500/600/700) — chiffres, valeurs, levels, efficacités
- Hiérarchie utilisée :
  - `24px / 600 / -0.5` — titre page
  - `22px / 700 Mono` — efficacité side panel
  - `18px / 700 Mono` — valeur main stat side panel
  - `17px / 600` — titre modal
  - `13px / 600` — noms monstres, cartes substats
  - `12px / 600` — noms set, noms monstres dans le tableau
  - `11px / 600 Mono` — levels dans tableau, chips
  - `11px / 600 / 1.5 ls / uppercase` — eyebrow accent
  - `10px / muted` — labels main stat
  - `9.5px / 700 / 0.8 ls / uppercase` — table headers
  - `9px / 700 / 1 ls / uppercase` — side panel section labels

### Espaces & radius
- Spacing scale : 2, 3, 6, 8, 10, 12, 14, 16, 20, 24, 28
- Radius : 3 (barres fines), 4 (rarity chip), 8 (inputs/cards), 10 (buttons/cards modal), 12 (cards main), 16 (modal), 999 (pills)
- Hit targets mini : 34×34 (close button), 44×44 idéal en PyQt6

### Shadows
- Bouton Simuler : `0 8px 20px -8px accent` (glow)
- Barre d'efficacité : `box-shadow 0 0 8px <color>66` sur le fill
- Slider thumb : `box-shadow 0 0 8px rgba(240,104,154,0.4)`
- Modal : `0 40px 80px -20px rgba(0,0,0,0.6), 0 0 0 1px accent22`

## Assets

- **Hexagones de runes** : placeholders SVG avec numéro de slot + étoile. **À remplacer** par les icônes Swarfarm (par set et par slot). Emplacement suggéré : `assets/runes/<set>_<slot>.png`.
- **Portraits monstres** (modal simu + side panel) : placeholders dégradés. À remplacer par les vraies images Swarfarm.
- **Icônes sidebar** : inline SVG dans `shared.jsx` — à convertir en QIcon depuis SVG ou reproduire avec QPainter.

## Notes de traduction PyQt6

| HTML/React | PyQt6 |
|---|---|
| `grid-template-columns` (9 colonnes) | Utiliser `QTableView` + `QAbstractTableModel` pour les perfs sur 5k lignes (virtualisation native). Pour le layout complexe par cellule, implémenter un `QStyledItemDelegate` par colonne ou utiliser un `QListView` + custom row widget (moins perf mais layout plus libre). |
| Tri cliquable | `QHeaderView.setSectionsClickable(True)` + signal `sectionClicked` → `model.sort(column, order)` |
| `backdrop-filter: blur` | Pas natif Qt. Solution recommandée : fond opaque solide (compromis sur l'effet glass). |
| Pills segmented | `QButtonGroup` avec `QPushButton.setCheckable(True)` + QSS sur `:checked` |
| `<input type=range>` + styling track | `QSlider` + QSS :<br>`QSlider::groove:horizontal { background: #2a1018; height: 4px; border-radius: 2px; }`<br>`QSlider::handle:horizontal { background: #f0689a; width: 12px; height: 12px; border-radius: 6px; margin: -4px 0; }` |
| `<select>` (set) | `QComboBox` + QSS custom pour coller au thème |
| Hexagone SVG | `QPainter.drawPolygon()` dans un widget custom (32×32 mini / 88×88 big) ou précalculer en `QPixmap` |
| Modal overlay | `QDialog` frameless + `WindowModality.ApplicationModal` + `Qt.WA_TranslucentBackground` + fond peint dans `paintEvent` |
| Échap ferme modal | `keyPressEvent` → `if e.key() == Qt.Key_Escape: self.close()` |
| Shadows (`box-shadow`) | `QGraphicsDropShadowEffect` — un par widget max pour les perfs |
| Gradient radial sur hex | `QRadialGradient` dans le `QPainter` |

### Architecture suggérée
```
pages/
  runes_page.py
    class RunesPage(QWidget)
  runes_table.py
    class RunesTableModel(QAbstractTableModel)
    class RunesTableView(QTableView)
    class RuneRowDelegate(QStyledItemDelegate)
  runes_filters.py
    class RunesToolbar(QWidget)
  runes_side_panel.py
    class RunesSidePanel(QFrame)
      RarityChip, LevelChip, MainStatCard, SubstatCard, EfficiencyBlock, OwnerCard, SimuButton
  runes_simu_modal.py
    class SimuEquipModal(QDialog)
      CandidateRow, DeltaBadge
  widgets/
    rune_hex.py         # widget custom QPainter pour les hexagones (taille variable)
    rarity_chip.py

theme/
  tokens.py             # toutes les constantes design
  styles.qss            # QSS global (+ @keyframes de fade modal si souhaité)
```

## Files

- `Runes Page.html` — preview interactive (ouvre dans un navigateur)
- `runes.jsx` — page Runes, table, side panel, modal simu
- `monsters.jsx` — importé pour `MONSTER_NAMES` et `MONSTER_PORTRAIT_COLORS` (à isoler côté PyQt6 dans un module partagé)
- `shared.jsx` — WinTitleBar, Sidebar, icônes SVG
- `design-canvas.jsx` — wrapper de présentation Figma-like (pas à recréer en PyQt6)
