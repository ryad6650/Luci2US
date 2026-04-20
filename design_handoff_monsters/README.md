# Handoff: Monsters Page (Luci2US)

## Overview

La page **Monsters** permet à l'utilisateur de parcourir sa collection de monstres (typiquement ~200-500 entités), de les filtrer, trier, et d'ouvrir le détail complet d'un monstre pour inspecter ses runes équipées, stats et compétences, et lancer une optimisation.

Elle fait partie de l'app desktop **Luci2US** (PyQt6, Windows, frameless) et réutilise la même palette warm-dark / magenta que la page Scan.

## About the Design Files

Les fichiers de ce bundle sont des **références de design en HTML/React** — des prototypes montrant le look visé et le comportement attendu, **pas du code de production à copier**. La tâche consiste à **recréer ces designs dans l'environnement PyQt6 existant** (patterns, conventions et base classes déjà en place dans le codebase), **pas** à embarquer du HTML dans l'app.

Si une partie du style ne se traduit pas directement en QSS (ex : `backdrop-filter`), utilise un substitut fidèle (voir section **Notes de traduction PyQt6** ci-dessous).

## Fidelity

**High-fidelity.** Toutes les couleurs, typographies, espaces et interactions sont finaux. Les portraits de monstres et les icônes de runes sont des **placeholders** (hexagones colorés avec teinte élément / numéro de slot) — à remplacer par les vrais assets Swarfarm côté code.

## Screens / Views

### 1. Liste Monsters

**Nom** : Monsters — Collection
**But** : Parcourir, filtrer, trier la collection ; sélectionner un monstre pour voir un aperçu latéral ; ouvrir le détail complet.

**Layout général** (de haut en bas, dans la fenêtre) :
- `WinTitleBar` (32px) — barre titre frameless Windows custom
- Corps à deux colonnes :
  - **Sidebar** (collapsible) à gauche : navigation Scan / Filtres / Runes / Monsters (actif) / Profile / Settings + bloc user en bas
  - **Zone principale** à droite, en colonne :
    - Header (titre, compteur, toggle Grille/Tableau) — `padding: 22px 28px 14px`
    - Toolbar (search + filtres élément + filtres statut runes + select tri) — `padding: 0 28px 14px`
    - Body split : liste (flex:1, scroll vertical) + side panel détail (300px fixe)

**Composants clés** :

#### Header
- Eyebrow "COLLECTION" : `11px / accent (#f0689a) / weight 600 / letter-spacing 1.5 / uppercase`
- Titre "Monstres" : `24px / #f5ecef / weight 600 / letter-spacing -0.5`
- Compteur : `12.5px / #c2a7af` — ex "36 sur 36 · 3 nat 6★", avec le chiffre en JetBrains Mono
- Toggle Grille/Tableau : `pill / padding 3px / bg rgba(255,255,255,0.04) / border rgba(255,220,230,0.06)`
  - Bouton actif : `bg accent / color #0d0907 / padding 6×14 / radius 999 / weight 600 / 11.5px`

#### Toolbar
- Search : `radius 8 / padding 7×12 / bg rgba(255,255,255,0.03) / border rgba(255,220,230,0.06) / min-width 240 / input 12.5px Inter`
  - Icône loupe (14×14) à gauche, `color #7a6168`
- Filtre élément : segmented `pill` avec chip "Tous" + 5 chips élément (Feu, Eau, Vent, Lumière, Ombre)
  - Chip inactif : `color #7a6168 / bg transparent`
  - Chip actif : `bg <el.color>22 / color <el.color>` + puce 6×6 colorée
- Filtre statut : segmented `pill` (Tous / Runés / Vides)
- Select tri : `padding 6×10 / radius 8 / bg rgba(255,255,255,0.03) / border rgba(255,220,230,0.06) / 12px Inter`

#### Liste — vue Grille
- `grid / auto-fill minmax(220px, 1fr) / gap 12`
- Carte monstre : `padding 12 / radius 12 / border 1px rgba(255,220,230,0.06) / bg rgba(255,255,255,0.02)`
  - Carte sélectionnée : `bg rgba(240,104,154,0.14) / border rgba(240,104,154,0.40)`
  - Structure :
    - Rangée haut : portrait 56×56 + (nom 13px 600 + étoiles 11px + chip élément)
    - Séparateur `1px rgba(255,220,230,0.06)`
    - Rangée bas : à gauche → "RUNES" (9.5px uppercase muted) + 6 pastilles 7×7 (`bg accent si équipée, sinon rgba(255,255,255,0.08)`, `box-shadow 0 0 6px accent66` sur les équipées)
    - À droite → "EFF. MOY." + valeur JetBrains Mono 13px 700 (vert #5dd39e si >85%, accent sinon, #7a6168 si pas runé)

#### Liste — vue Tableau
- Conteneur : `bg rgba(36,20,26,0.72) / backdrop-filter blur(20px) / border 1px / radius 12 / overflow hidden`
- Entête de colonnes : `grid-template-columns: 48px 1fr 90px 90px 70px 130px 90px / gap 14 / padding 10×18 / 9.5px uppercase 700 letter-spacing 0.8 / color #7a6168 / bg rgba(0,0,0,0.15)`
- Colonnes : (portrait) | Nom | Étoiles | Élément | Niveau | Runes | Eff.
- Ligne : même grid, `padding 8×18 / border-bottom 1px rgba(255,220,230,0.06)`
  - Sélectionnée : `bg rgba(240,104,154,0.14)`

#### Side panel détail (monstre sélectionné)
- `width 300 / bg rgba(36,20,26,0.72) / backdrop-filter blur(20px) / border 1px / radius 12 / padding 20 / flex column gap 16`
- Bloc haut centré : portrait 88×88, nom 16px 600, étoiles 13px, chip élément + chip niveau lv_X_ (Mono 11.5)
- Bloc "RUNES ÉQUIPÉES" : 6 cases 1:1 flex=1, `radius 8 / border 1px dashed`
  - Slot rempli : `bg accentDim / border accent55 / color accent 700 Mono`
  - Slot vide : `bg transparent / border rgba(255,220,230,0.06) / color #7a6168`
- Bloc "STATS" : 4 lignes HP/ATK/DEF/SPD en Mono 12, `color #7a6168` à gauche, `color #f5ecef 600` à droite
- Ligne "EFF. MOY." : 22px Mono 700 (vert ou magenta)
- Bouton "Voir le détail complet" : `padding 10×14 / radius 8 / linear-gradient 180° accent→accent2 / color #fff / 12.5px 600`
  - **Ouvre le Monster Detail Modal**

### 2. Monster Detail Modal

**Nom** : Monster Detail
**But** : Inspection complète d'un monstre — runes équipées détaillées, stats calculées, skills, + action **Optimiser**.

**Layout** :
- Overlay : `position absolute inset 0 / bg rgba(5,3,4,0.72) / backdrop-filter blur(6px) / padding 40 / center`
- Conteneur modal :
  - `max-width 1120 / max-height 720 / bg #1a0f14 / radius 16 / border 1px / box-shadow 0 40px 80px -20 rgba(0,0,0,0.6), 0 0 0 1px accent22`
  - Click sur l'overlay (hors modal) ou sur × → ferme
- Structure verticale :
  - **Header** (padding 20×24, `linear-gradient 180° <el.color>14 → transparent`)
  - **Tabs** (3 onglets, padding 0×24 + border-bottom)
  - **Body** (flex:1 overflow:auto, padding 24)

#### Header modal
- Avatar 72×72 `radius 14 / bg linear-gradient 135° <el.color>44 → <el.color>11 / border 1.5 <el.color>66`
- Contenu : eyebrow "MONSTER DETAIL" magenta 11 uppercase → nom 22px 600 → ligne meta (étoiles · élément · niveau)
- Droite : bloc "EFF. MOYENNE" 22px Mono 700 + bouton **Optimiser** + bouton fermer (34×34, ×)
- Bouton Optimiser : `padding 10×16 / radius 10 / gradient accent→accent2 / box-shadow 0 8px 20px -8 accent / icône étoile 14×14`

#### Tabs
- 3 onglets : "Runes équipées" (défaut) / "Stats" / "Skills"
- Inactif : `color #c2a7af / padding 12×16 / border-bottom 2px transparent`
- Actif : `color accent / border-bottom 2px accent`

#### Body — onglet Runes équipées
- Intro : "{n}/6 équipées · sets principaux : X + Y + Z" (14px 600) + hint droite 11px
- Grille `3 × 2 / gap 12`
- Carte rune (slot rempli) : `padding 14 / radius 12 / bg rgba(255,255,255,0.02) / border 1px`
  - Sélectionnée : `bg accentDim / border accent66`
  - Haut : hexagone placeholder 52 + (set 13px 600 / +level 10px Mono / main stat 11px muted / valeur 14px Mono 700)
  - Milieu : 4 substats en Mono 11px, rolled ×N en accent 9px
  - Bas : label "EFFICACITÉ" + valeur 13px Mono 700 (couleur selon seuils 90/75) + barre fine 3px
- Slot vide : `border 1px dashed / min-height 180 / flex center column / hexagone muted + "Slot N vide"`

#### Body — onglet Stats
- En-tête colonnes : `grid 70px / 1fr / 70px / 70px — Stat | Contribution runes | Base | Total` (9px uppercase muted)
- 8 lignes : HP, ATK, DEF, SPD, CRI R, CRI D, RES, ACC
- Barre contribution : fond gris sombre pour la base + barre magenta pour le gain (highlight full magenta pour SPD)
- Total : Mono 12.5 700 + pill "+X%" accent si diff > 0
- Bloc analyse en bas : `bg accentDim / border accent33 / radius 10 / padding 14` avec eyebrow "ANALYSE" et texte conseil

#### Body — onglet Skills
- 3 lignes skill : badge numéroté 32×32 accent + (nom 13px 600 / "CD Nt" 10px Mono muted / description 11px 1.4) + à droite "MULT" + valeur Mono 12
- Bloc passif en bas : `bg rgba(255,255,255,0.03) / border 1px / radius 10 / padding 14`

## Interactions & Behavior

### Liste
- Click sur carte/ligne → change `selectedId` → side panel met à jour
- Toggle Grille/Tableau → change `view`
- Recherche → filtre sur `name.toLowerCase().includes(query)` (debounce 150ms recommandé côté Qt)
- Chip élément → toggle filtre (re-click = désélectionne)
- Chip statut → radio (Tous / Runés / Vides)
- Select tri → change le critère (name, stars, level, element, efficiency)
- Tri par défaut : **efficiency desc**
- Filtres combinés en AND

### Modal
- Bouton "Voir le détail complet" → ouvre modal (`detailOpen = true`)
- Click sur overlay (hors container) → ferme
- Click sur × → ferme
- Touche **Échap** → ferme (à ajouter côté PyQt6, non présent dans le proto HTML)
- Tabs → change de contenu sans refermer
- Click sur une rune équipée → sélectionne la rune (surlignage). À brancher plus tard sur une vue détail rune.
- Bouton "Optimiser" → hook à connecter sur le flow d'optimisation (non spécifié ici)

### Animations
- Transitions d'état (`background`, `border-color`) : `transition: all 0.15s` — à implémenter via `QPropertyAnimation` en PyQt6, ou laisser instantané (acceptable).
- Pas d'animation d'entrée modal dans le proto — libre à toi d'ajouter un fade 150ms.

## State Management

### Liste
```python
view: "grid" | "table"            # défaut "grid"
sort_by: str                      # défaut "efficiency"
filter_element: str | None        # None = tous
filter_equipped: "all"|"equipped"|"empty"  # défaut "all"
search: str                       # défaut ""
selected_id: int
detail_open: bool                 # défaut False
```

### Modal
```python
selected_slot: int                # défaut 1
tab: "runes" | "stats" | "skills" # défaut "runes"
```

### Données attendues (à brancher sur le backend/DB)
```python
Monster {
  id: int
  name: str
  element: "fire"|"water"|"wind"|"light"|"dark"
  stars: int           # 1..6 (natural)
  level: int           # 1..40
  portrait_path: str   # asset local
  equipped_count: int  # 0..6
  efficiency: float    # moyenne des runes équipées, 0..100

  # Chargé à l'ouverture du détail :
  runes: list[Rune]    # 6 entries, None = slot vide
  base_stats: dict     # HP/ATK/DEF/SPD/CRI R/CRI D/RES/ACC
  skills: list[Skill]
}

Rune {
  slot: int            # 1..6
  set: str             # Violent, Will, Swift, ...
  grade: int           # 5 or 6
  level: int           # 0..15
  main_stat: str       # "ATK+", "ATK%", etc
  main_value: str | int
  substats: list[Substat]   # 4 entries
  efficiency: float    # 0..150
}

Substat { name: str, value: str, rolled: int }   # rolled 1..5 (1 = base, pas de "+N" affiché)

Skill { n: int, name: str, desc: str, mult: str, cd: int | None }
```

## Design Tokens

### Palette (warm-dark magenta) — identique à Scan
```python
BG        = "#0d0907"
BG_GRAD   = "radial-gradient(ellipse at 12% 0%, #3a1624 0%, #0d0907 50%), radial-gradient(ellipse at 100% 100%, #2a1018 0%, #0d0907 55%)"
PANEL     = "rgba(36, 20, 26, 0.72)"   # cards glass
PANEL2    = "rgba(48, 26, 34, 0.45)"
BORDER    = "rgba(255, 220, 230, 0.06)"
BORDER_STR= "rgba(255, 220, 230, 0.10)"

FG        = "#f5ecef"   # primary text
FG_DIM    = "#c2a7af"   # secondary text
FG_MUTE   = "#7a6168"   # tertiary / labels

ACCENT    = "#f0689a"   # magenta principal
ACCENT_2  = "#d93d7a"   # dégradé / hover
ACCENT_DIM= "rgba(240, 104, 154, 0.14)"   # highlight selected

OK        = "#5dd39e"   # efficacité excellente
ERR       = "#ef6461"
```

### Éléments (couleurs symboliques)
```python
fire  = "#ff7a5a"
water = "#5aa6ff"
wind  = "#9be37a"
light = "#f5d76e"
dark  = "#a77ae0"
```

### Typographie
- **Inter** (400/500/600/700) — UI text
- **JetBrains Mono** (400/500/600/700) — chiffres, IDs, values
- Hiérarchie utilisée :
  - `22px / 600 / -0.3 letter-spacing` — titre modal
  - `24px / 600 / -0.5` — titre page
  - `16px / 600` — nom monstre (side panel)
  - `14px / 600` — sous-titres
  - `13px / 600` — nom en carte, nom skill
  - `12.5px / 400` — body text
  - `11px / 600` — chips, boutons pill
  - `11px / 600 / 1.5 ls / uppercase` — eyebrow accent
  - `10px / 700 / 1 ls / uppercase` — mini-labels muted
  - `9px / 700 / 1 ls / uppercase` — table headers

### Espaces & radius
- Spacing scale : 4, 6, 8, 10, 12, 14, 16, 20, 24, 28
- Radius : 8 (inputs, chips), 10 (buttons), 12 (cards), 14 (modal avatar), 16 (modal container), 999 (pills)
- Hit targets mini : 34×34 (close button), 44×44 idéal en PyQt6

### Shadows
- Carte rune sélectionnée : pas d'ombre, juste border + bg
- Bouton Optimiser : `0 8px 20px -8px <accent>` (glow accent)
- Modal : `0 40px 80px -20px rgba(0,0,0,0.6), 0 0 0 1px <accent>22`

## Assets

- **Portraits de monstres** : placeholders HTML (hexagone/cercle coloré avec teinte élément). **À remplacer** par les vraies images Swarfarm (probablement `.png` ~128×128). Emplacement suggéré : `assets/monsters/<monster_id>.png`.
- **Icônes de runes** : placeholders hexagonaux. À remplacer par les icônes Swarfarm par set et par slot. Emplacement suggéré : `assets/runes/<set>_<slot>.png`.
- **Icônes sidebar** : inline SVG dans `shared.jsx`. Soit convertir en QIcon depuis SVG, soit reproduire avec QPainter.

## Notes de traduction PyQt6

| HTML/React | PyQt6 |
|---|---|
| Layout flex/grid | `QHBoxLayout` / `QVBoxLayout` / `QGridLayout` |
| `backdrop-filter: blur(20px)` | Pas natif. Option 1 : `QGraphicsBlurEffect` sur un widget sous-jacent (coûteux). Option 2 : simuler avec couleur semi-opaque solide, accepter perte de l'effet glass. Recommandé : **option 2** pour les perfs. |
| `border-radius` + couleurs | **QSS** (Qt Style Sheets, syntaxe CSS-like) |
| `linear-gradient` / `radial-gradient` | QSS `qlineargradient()` / `qradialgradient()` |
| `box-shadow` | `QGraphicsDropShadowEffect` — un par widget max pour les perfs |
| Polices Inter / JetBrains Mono | `QFontDatabase.addApplicationFont()` au boot |
| Hexagone rune (SVG) | `QPainter.drawPolygon()` dans un widget custom, ou précalculer en `QPixmap` |
| Modal overlay | `QDialog` avec `WindowModality.ApplicationModal`, `Qt.FramelessWindowHint`, `Qt.WA_TranslucentBackground` et fond `rgba(5,3,4,0.72)` peint au `paintEvent` |
| Échap ferme modal | `keyPressEvent` → `if e.key() == Qt.Key_Escape: self.close()` |
| Scroll liste | `QScrollArea` ou `QListView` custom delegate |
| Pills toggle | `QButtonGroup` avec boutons `checkable` + QSS conditionnelle sur `[checked="true"]` |

### Architecture suggérée
```
pages/
  monsters_page.py
    class MonstersPage(QWidget)
  monster_card.py
    class MonsterCard(QFrame)              # grille
    class MonsterTableRow(QFrame)          # tableau
  monster_side_panel.py
    class MonsterSidePanel(QFrame)
  monster_detail_modal.py
    class MonsterDetailModal(QDialog)
  monster_detail/
    runes_tab.py       class RuneSlotCard(QFrame)
    stats_tab.py       class StatRow(QWidget)
    skills_tab.py      class SkillRow(QWidget)

theme/
  tokens.py            # toutes les constantes design ci-dessus
  styles.qss           # QSS global
  fonts.py             # chargement Inter + JetBrains Mono
```

## Files

- `Monsters Page.html` — preview (ouvre dans un navigateur pour voir le rendu final)
- `monsters.jsx` — page liste : MonsterCard, MonsterTableRow, MonstersPage
- `monster-detail.jsx` — modal détail : MonsterDetailModal + RuneSlotCard, StatRow, SkillRow
- `shared.jsx` — WinTitleBar, Sidebar, VerdictBadge, icônes SVG
- `design-canvas.jsx` — wrapper canvas de présentation (Figma-like, pas à recréer en PyQt6)
