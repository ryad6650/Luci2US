# Scan Page Redesign — Luci2US

**Date** : 2026-04-17
**Statut** : Design validé, prêt pour plan d'implémentation
**Référence visuelle** : `.superpowers/brainstorm/1160-1776439696/content/scan-page-v13.html`

## 1. Contexte

Luci2US est un bot Summoners War décompilé, actuellement sur `customtkinter`. La page **Scan** (ancien `auto_tab.py`) est refondue visuellement pour passer en **PySide6** avec un rendu pixel-perfect conforme au mockup v13. La logique du bot (evaluator_chain, s2us_filter, monster_icons, swex_bridge) est **inchangée** : seule la couche de présentation est remplacée.

## 2. Objectifs

1. Remplacer l'interface Scan actuelle par un design Rune Forge (direction B — dark brown + bronze).
2. Pixel-perfect : le rendu PySide6 doit être identique au mockup HTML v13 (positions, tailles, couleurs, animations).
3. Conserver toutes les fonctionnalités de l'ancien `auto_tab` (démarrer/arrêter, compteurs, historique, dernière rune, meilleure rune).
4. Intégrer les assets réels swarfarm (logos de sets) et l'icône rune.png de swarfarm pour le Score.

## 3. Direction visuelle — Rune Forge B

| Élément | Valeur |
|---|---|
| Background app | `#0a0604` → cadre `#120a05` avec bordure `#5a3d1f` 2px |
| Background tab (main) | radial-gradients bronze/orange + linear `#1a0f07` → `#120a05` |
| Cercles runiques | `.rc-1` top-left 280px (borderline `rgba(232,176,64,.12)`), `.rc-2` bottom-right 320px (`rgba(200,80,40,.1)`) + cercles pointillés intérieurs |
| Symboles runiques | "Ж" 90px coin haut-gauche, "§" 90px coin bas-droit, opacity 4-5% |
| Embers (braises) | 10 points lumineux `#f5a030` animés (flotteurs 6-10s, tailles 2-4px, box-shadow glow) |
| Accent principal | Bronze `#c67032` · Or sable `#e8c96a` · Orange ember `#f5a030` |
| Texte | Principal `#f0e6d0` · Secondaire `#ddd0b8` · Sable `#e8c96a` · Discret `#9ca3af` |
| Police | Segoe UI (titres en Georgia serif) |

### Status colors (verdict)

| Verdict | Couleur |
|---|---|
| KEEP | `#8ec44a` (vert sauge) |
| PWR-UP | `#f5a030` (orange flamme) |
| SELL | `#d84a3a` (rouge brique) |

## 4. Architecture de la page

Layout grille `170px / 1fr`, max-width 1200px, min-height 620px.

```
┌─────────────┬──────────────────────────────────────────────────┐
│             │ HEADER : [Start B4] · ● État actif               │
│  SIDEBAR    ├──────────────────────────────────────────────────┤
│  170px      │ COUNTERS : 4 cellules (Total · Kept · Sold · PwrUp) │
│             ├──────────────────────────────────────────────────┤
│  · Logo     │ MAIN grid 230/1fr/1fr :                          │
│  · Nav      │  ┌─────────┬──────────────┬──────────────┐       │
│    items    │  │Historique│ Dernière rune│ Meilleure rune│      │
│             │  │ (230px) │ + Verdict    │ + Verdict     │      │
│             │  │ scroll  │              │              │       │
└─────────────┴──────────────────────────────────────────────────┘
```

### 4.1 Sidebar (170px)

- Logo vertical "LUCI2US" (Georgia 20px, gold `#e8c96a`, letter-spacing) + sous-titre "SW BOT" en 9px gris
- Border-bottom `#3d2818`
- Nav items (Scan, Profil, Historique, Stats, Paramètres) :
  - 11px gap icône/label, padding 10/12, radius 5px
  - Hover : background `rgba(232,201,106,.06)`
  - Active : gradient `rgba(198,112,50,.25)` → transparent, border-left 3px `#c67032`, label en `#e8c96a`
  - Icônes SVG 18×18 stroke 1.6, drop-shadow gold quand actif

### 4.2 Header

- **Bouton Start** (B4 — glow pulse)
  - Gradient `#c67032` → `#8b4a1f`, bordure `#e8a050`
  - Shadow multi-couches : inset highlight + outer drop + outer glow orange (18-26px blur)
  - Animation `glowBtn 2.2s ease-in-out infinite` (pulsation du glow)
  - Icône play SVG 13×13 avec drop-shadow
  - Label 13px letter-spacing 1.5
- **Indicateur état** : dot 9×9 `#8ec44a` avec box-shadow glow + animation pulse 1.2s, label "ACTIF" vert

### 4.3 Compteurs (4 cellules)

- Grid 4 colonnes égales, fond gradient bronze foncé, bordure `#5a3d1f`, radius 5px
- Séparateurs verticaux `#3d2818`
- Label 10px uppercase letter-spacing 1
- Valeur 20px Georgia `#e8c96a`
- Cellules : Total · Kept · Sold · PwrUp

### 4.4 Colonne Historique (230px)

- Conteneur fond gradient bronze foncé, bordure `#5a3d1f`, max-height 470px, scroll custom 5px thumb bronze
- Chaque item : grid `36px / 1fr / auto`, padding 6/7, border-bottom `#2d1f14`
- **Icône rune (historique)** : 36×36, juste le logo du set centré (drop-shadow 1px)
- Infos : nom du set + niveau (ex "+9") coloré gold + stat principale
- Tag : KEEP (vert) · SELL (rouge) · PWR (orange), 9px bold uppercase

### 4.5 Cards "Dernière rune" et "Meilleure rune"

Chacune = **rune-card** + **verdict** au-dessous.

#### rune-card

- Padding 13/18, radius 7px, fond `rgba(26,15,7,.9)`
- Bordure + glow coloré selon verdict (KEEP vert · PWR orange · SELL rouge, offset 18px blur)
- **Titre** (rc-title) : 14px bold `#e8b040` centré, text-shadow
- **Body** grid `50px / 1fr / auto` :
  - **Icône** (rc-icon-wrap 62×62) : logo set seul, drop-shadow 2px, étoiles ★★★★★★ 9px gold au-dessus
  - **Stat principale** (rc-main) : 17px `#f0e6d0` centré (ex "ATQ +22")
  - **Right** : badge grade (bronze `#a05a2a` / violet hero `#8a3aab`) + badge mana (`#5a2e14` avec icône mana.png 12×12 + valeur)
- **Subs** : 4 sub-stats 11px `#d8ccab`
- **Set bonus** : ligne séparée border-top `#2d1f14`, texte vert `#9cc848`

#### verdict (dessous)

- Fond gradient coloré selon verdict (keep/powerup/sell), bordure colorée correspondante
- Padding 8/11, gap 10px, flex align-items center
- **Badge verdict** : 11px bold 900 padding 4/10, couleurs miroir du tag historique
- **v-eff** (flex 1) : 3 lignes
  - **Score** : icône rune.png 14×14 + "Score 215" en gold 11px bold
  - **SWOP** 98.3% (max 112.4%)
  - **S2US** 127.4% (max 145.0%)

## 5. Assets requis

### Locaux (déjà dans le projet ou à ajouter dans `assets/icons/`)
- Icônes SVG nav (inline dans le code)

### Distants (fetch au build ou bundle en local dans `assets/swarfarm/`)
Source : `https://raw.githubusercontent.com/swarfarm/swarfarm/master/herders/static/herders/images/`

| Asset | Chemin |
|---|---|
| Logos de set | `runes/{endure,violent,swift,fatal,rage,blade,focus,despair,will,nemesis,vampire,guard,revenge,nemesis,energy,fight,determination,enhance,accuracy,tolerance,shield}.png` |
| Icône mana | `items/mana.png` |
| Icône rune (Score) | `icons/rune.png` |

**Recommandation** : bundler les assets swarfarm en local dans `assets/swarfarm/` pour éviter la dépendance réseau au runtime.

## 6. Découpage composants PySide6

Un widget = un fichier, responsabilités isolées :

```
ui/scan/
├── scan_page.py            # Page racine, orchestre les sous-widgets
├── header_bar.py           # Bouton Start B4 + indicateur état
├── counters_bar.py         # 4 compteurs
├── history_list.py         # QScrollArea + HistoryItem
├── history_item.py         # Item ligne historique (36×36 + infos + tag)
├── rune_card.py            # Card rune (titre, body, subs, set bonus)
├── verdict_bar.py          # Badge + Score/SWOP/S2US
└── widgets/
    ├── rune_icon.py        # QLabel chargeant le logo set (36 ou 62)
    ├── mana_badge.py       # Badge mana avec icône
    └── glow_button.py      # Bouton B4 avec animation QPropertyAnimation
```

### Rendu pixel-perfect — stratégie

- **Couleurs, dimensions, paddings** : constantes dans `ui/scan/theme.py` (un seul endroit, miroir du CSS)
- **Animations** : `QPropertyAnimation` + `QGraphicsDropShadowEffect` pour le glow du bouton et les embers
- **Gradients / shadows complexes** : `QPainter.paintEvent` custom sur widgets clés (rune-card border-glow, header ember background)
- **Background radial/linear** : peint dans `paintEvent` de la tab racine (RadialGradient + LinearGradient QBrush)
- **Embers** : 10 `QLabel` animés en opacité + position Y via `QPropertyAnimation` en boucle

## 7. Data flow (inchangé côté logique)

```
SwexBridge ──(raw rune data)──▶ EvaluatorChain
                                     │
                                     ▼
                              S2usFilter (Score, Eff1, Eff2, Gemstone)
                                     │
                                     ▼
                           Verdict (KEEP / PWR-UP / SELL)
                                     │
                                     ▼
                         ScanPage.on_rune_evaluated(rune, verdict)
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
             HistoryList     RuneCard.last     RuneCard.best (si verdict > seuil)
             HistoryDB.save
```

`RuneCard.update(rune, verdict)` reçoit le modèle rune (objet `Rune` existant) + verdict + scores Score/Eff1/Eff2 et met à jour tous les labels.

## 8. Tests

- **Visuel** : comparaison screenshot PySide6 vs mockup v13 (outil pixelmatch ou simple review manuelle diff < 5%)
- **Logique** : les tests existants de `evaluator_chain` / `s2us_filter` couvrent la logique. Ajouter tests widget :
  - `HistoryItem` affiche correctement un set, niveau, stat, tag
  - `RuneCard.update()` réinitialise correctement entre deux runes
  - `VerdictBar` affiche Score + SWOP + S2US avec l'icône rune.png
- Pas de test d'animation (non critique).

## 9. Erreurs et edge cases

- **Asset swarfarm manquant** (set inconnu après update SW) : fallback icône placeholder + log warning
- **Score indisponible** (erreur évaluateur) : afficher "—" à la place du chiffre, ne pas crasher
- **Historique plein** : limité à N items (N = config, défaut 50), scroll auto vers le haut sur nouvelle entrée
- **Bot arrêté** : indicateur état passe en gris "INACTIF", le bouton Start redevient cliquable et son animation `glowBtn` reste active (elle signale "prêt à démarrer"). Le dot vert pulse s'arrête.

## 10. Hors scope

- Migration des autres onglets (Profil, Historique, Stats, Paramètres) — traités dans des specs séparés
- Changement des seuils de verdict ou de la logique Smart Filter
- Support thème clair
- Internationalisation de nouveaux strings (réutilise `i18n.py` existant)

## 11. Référence visuelle autoritaire

`.superpowers/brainstorm/1160-1776439696/content/scan-page-v13.html` — ce fichier est la **source de vérité** pour l'implémentation. Toute ambiguïté se résout en comparant au rendu navigateur de v13.
