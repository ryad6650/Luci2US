# Plan 02 — Onglet Monstres (liste + push page détail)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le placeholder `Monstres` par un onglet fonctionnel : liste des monstres du compte (photo + nom + ★ + niveau + élément + Eff moyenne) avec barre de filtres (élément / ★ / nom) et push page détail plein écran (image + stats + 6 slots de runes). Câblé sur le signal `ScanController.profile_loaded`.

**Architecture:** Nouveau sous-package `ui/monsters/` suivant le pattern de `ui/scan/` et `ui/profile/`. `MonstersPage` est un `QStackedWidget` interne à 2 indices : 0 = `MonsterList` (vue liste), 1 = `MonsterDetail` (vue détail). La page reçoit les données via `apply_profile(profile: dict, saved_at: float)` appelée par un signal du `ScanController`. Aucun changement des modules bot core (`profile_loader`, `swex_bridge`, `models`, `monster_icons`).

**Tech Stack:** PySide6 6.11.0, pytest-qt (`qapp`), `ui.theme`, `monster_icons` (existant, fournit `get_monster_icon(unit_master_id) -> Path` et `download_icons_async`).

---

## File Structure

### Créer

| Chemin | Responsabilité |
|---|---|
| `ui/monsters/__init__.py` | Package init vide |
| `ui/monsters/monsters_page.py` | `MonstersPage` : QStackedWidget interne (liste/détail) + slot `apply_profile` |
| `ui/monsters/monster_list.py` | `MonsterList` : barre de filtres + vue scrollable + bouton refresh icônes |
| `ui/monsters/monster_detail.py` | `MonsterDetail` : header (image + stats) + 6 slots de runes + bouton retour |
| `tests/ui/test_monsters_page.py` | Tests `MonstersPage` (stack + apply_profile) |
| `tests/ui/test_monster_list.py` | Tests `MonsterList` (rendu + filtres + tri) |
| `tests/ui/test_monster_detail.py` | Tests `MonsterDetail` (header + slots + retour) |

### Modifier

| Chemin | Changement |
|---|---|
| `ui/main_window.py` | Remplacer `_placeholder("Monstres - a implementer")` (index 3) par `MonstersPage` réel + connexion signal `profile_loaded` |

### Ne pas toucher

- `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `swex_bridge.py`, `profile_loader.py`, `profile_store.py`, `models.py`
- `monster_icons.py` (utilisé en lecture uniquement via `get_monster_icon` + `download_icons_async`)
- `ui/sidebar.py`, `ui/scan/*`, `ui/profile/*`, `ui/widgets/*`, `ui/theme.py`, `ui/settings/*`
- Tabs legacy (`stats_tab.py`, `history_tab.py`, `auto_tab.py`, `profile_tab.py`, `settings_tab.py`)

---

## Task 1 — Squelette `MonstersPage` (QStackedWidget interne + apply_profile no-op)

**Files:**
- Create: `ui/monsters/__init__.py`
- Create: `ui/monsters/monsters_page.py`
- Create: `tests/ui/test_monsters_page.py`

- [ ] **Step 1.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_monsters_page.py` :

```python
from ui.monsters.monsters_page import MonstersPage


def test_monsters_page_instantiates(qapp):
    page = MonstersPage()
    assert page is not None


def test_monsters_page_has_internal_stack_with_2_views(qapp):
    page = MonstersPage()
    assert page._stack.count() == 2


def test_monsters_page_starts_on_list_view(qapp):
    page = MonstersPage()
    assert page._stack.currentIndex() == 0


def test_apply_profile_accepts_monster_list(qapp):
    from models import Monster
    page = MonstersPage()
    profile = {"monsters": [
        Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211),
    ]}
    page.apply_profile(profile, saved_at=0.0)
    # Liste doit contenir 1 monstre apres apply
    assert len(page._list._rows) == 1


def test_apply_profile_empty_list_ok(qapp):
    page = MonstersPage()
    page.apply_profile({"monsters": []}, saved_at=0.0)
    assert len(page._list._rows) == 0
```

- [ ] **Step 1.2 : Lancer le test pour verifier qu'il echoue**

```bash
cd /c/Users/louis/Desktop/Luci2US
pytest tests/ui/test_monsters_page.py -v
```

Attendu : FAIL avec `ModuleNotFoundError: No module named 'ui.monsters'`.

- [ ] **Step 1.3 : Creer `ui/monsters/__init__.py` (vide)**

Fichier vide.

- [ ] **Step 1.4 : Creer un stub minimal `ui/monsters/monster_list.py`**

```python
"""Stub temporaire - sera complete en Task 2."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout


class MonsterList(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list = []
        QVBoxLayout(self)

    def set_monsters(self, monsters: list) -> None:
        self._rows = list(monsters)
```

- [ ] **Step 1.5 : Creer un stub minimal `ui/monsters/monster_detail.py`**

```python
"""Stub temporaire - sera complete en Task 6-7."""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout


class MonsterDetail(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        QVBoxLayout(self)

    def set_monster(self, monster) -> None:
        self._monster = monster
```

- [ ] **Step 1.6 : Creer `ui/monsters/monsters_page.py`**

```python
"""Monstres tab - QStackedWidget interne (liste/detail)."""
from __future__ import annotations

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ui.monsters.monster_detail import MonsterDetail
from ui.monsters.monster_list import MonsterList


class MonstersPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._stack = QStackedWidget()
        self._list = MonsterList()
        self._detail = MonsterDetail()
        self._stack.addWidget(self._list)
        self._stack.addWidget(self._detail)
        lay.addWidget(self._stack)

    def apply_profile(self, profile: dict, saved_at: float) -> None:
        monsters = profile.get("monsters", [])
        self._list.set_monsters(monsters)
        self._stack.setCurrentIndex(0)  # retour a la liste a chaque refresh
```

- [ ] **Step 1.7 : Lancer les tests pour verifier qu'ils passent**

```bash
pytest tests/ui/test_monsters_page.py -v
```

Attendu : 5 tests PASS.

- [ ] **Step 1.8 : Commit**

```bash
git add ui/monsters/ tests/ui/test_monsters_page.py
git commit -m "feat(monsters): MonstersPage skeleton with internal QStackedWidget"
```

---

## Task 2 — `MonsterList` : rendu des lignes (photo + nom + ★ + niveau + élément + Eff moyenne)

**Files:**
- Modify: `ui/monsters/monster_list.py`
- Create: `tests/ui/test_monster_list.py`

- [ ] **Step 2.1 : Ecrire les tests qui echouent**

Creer `tests/ui/test_monster_list.py` :

```python
from models import Monster, Rune, SubStat
from ui.monsters.monster_list import MonsterList


def _rune(slot: int, eff: float = 100.0) -> Rune:
    return Rune(
        set="Violent", slot=slot, stars=6, grade="Legend", level=12,
        main_stat=SubStat(type="ATQ%", value=63.0),
        prefix=None, substats=[],
        swex_efficiency=eff,
    )


def _monster(name: str, element: str = "Vent", stars: int = 6, level: int = 40,
             runes: list | None = None) -> Monster:
    return Monster(name=name, element=element, stars=stars, level=level,
                   unit_master_id=1, equipped_runes=runes or [])


def test_list_renders_one_row_per_monster(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("Lushen"), _monster("Bella"), _monster("Khmun")])
    assert len(ml._rows) == 3


def test_row_displays_name_stars_level_element(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("Lushen", element="Vent", stars=6, level=40)])
    row = ml._rows[0]
    texts = [lbl.text() for lbl in row.findChildren(__import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel)]
    joined = " | ".join(texts)
    assert "Lushen" in joined
    assert "6" in joined  # stars
    assert "40" in joined  # level
    assert "Vent" in joined


def test_eff_moyenne_computed_from_equipped_runes(qapp):
    ml = MonsterList()
    mon = _monster("Lushen", runes=[_rune(1, 100.0), _rune(2, 80.0), _rune(3, 120.0)])
    ml.set_monsters([mon])
    row = ml._rows[0]
    # Eff moyenne = (100 + 80 + 120) / 3 = 100.0
    assert abs(row._eff_avg - 100.0) < 0.01


def test_eff_moyenne_ignores_missing_swex_efficiency(qapp):
    ml = MonsterList()
    r1 = _rune(1, 100.0)
    r2 = _rune(2, 80.0)
    r2.swex_efficiency = None  # slot sans eff calculee
    mon = _monster("Lushen", runes=[r1, r2])
    ml.set_monsters([mon])
    row = ml._rows[0]
    assert abs(row._eff_avg - 100.0) < 0.01  # seul r1 compte


def test_eff_moyenne_zero_when_no_runes(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("Bare", runes=[])])
    assert ml._rows[0]._eff_avg == 0.0


def test_set_monsters_clears_previous_rows(qapp):
    ml = MonsterList()
    ml.set_monsters([_monster("A"), _monster("B")])
    assert len(ml._rows) == 2
    ml.set_monsters([_monster("C")])
    assert len(ml._rows) == 1
```

- [ ] **Step 2.2 : Lancer les tests pour verifier qu'ils echouent**

```bash
pytest tests/ui/test_monster_list.py -v
```

Attendu : FAIL sur `AttributeError: '_eff_avg'` ou rendering absent.

- [ ] **Step 2.3 : Remplacer completement `ui/monsters/monster_list.py`**

```python
"""Liste des monstres : barre filtres (Task 3) + lignes scrollables."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from models import Monster
from ui import theme


def _avg_efficiency(monster: Monster) -> float:
    """Moyenne arithmetique des swex_efficiency des runes equipees, slots sans eff ignores."""
    effs = [r.swex_efficiency for r in monster.equipped_runes if r.swex_efficiency is not None]
    if not effs:
        return 0.0
    return sum(effs) / len(effs)


class _MonsterRow(QFrame):
    clicked = Signal(object)  # emet le Monster

    def __init__(self, monster: Monster, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._monster = monster
        self._eff_avg = _avg_efficiency(monster)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"_MonsterRow {{ background:rgba(26,15,7,0.6);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:4px; }}"
            f"_MonsterRow:hover {{ background:rgba(198,112,50,0.2);"
            f" border:1px solid {theme.COLOR_BRONZE}; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(14)

        # Photo (48x48 placeholder pour l'instant, Task 4 charge l'icone Swarfarm)
        self._icon = QLabel()
        self._icon.setFixedSize(48, 48)
        self._icon.setStyleSheet(
            f"background:{theme.COLOR_BG_FRAME};"
            f"border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:3px;"
        )
        row.addWidget(self._icon)

        # Nom (flex)
        name = QLabel(monster.name)
        name.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:14px; font-weight:700;"
        )
        row.addWidget(name, 1)

        # Etoiles
        stars = QLabel(f"{'★' * monster.stars} ({monster.stars})")
        stars.setStyleSheet(f"color:{theme.COLOR_GOLD_TITLE}; font-size:12px;")
        row.addWidget(stars)

        # Niveau
        level = QLabel(f"L{monster.level}")
        level.setStyleSheet(f"color:{theme.COLOR_TEXT_MAIN}; font-size:12px;")
        row.addWidget(level)

        # Element
        element = QLabel(monster.element)
        element.setStyleSheet(f"color:{theme.COLOR_BRONZE_LIGHT}; font-size:12px;")
        row.addWidget(element)

        # Eff moyenne
        eff = QLabel(f"Eff moyenne {self._eff_avg:.1f}%")
        eff.setStyleSheet(f"color:{theme.COLOR_KEEP}; font-size:12px; font-weight:600;")
        row.addWidget(eff)

        # Chevron (vers detail)
        chevron = QLabel("\u25B6")  # ▶
        chevron.setStyleSheet(f"color:{theme.COLOR_BRONZE}; font-size:14px;")
        row.addWidget(chevron)

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._monster)
        super().mousePressEvent(ev)


class MonsterList(QWidget):
    monster_clicked = Signal(object)  # re-emet le Monster cliqué

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._rows: list[_MonsterRow] = []
        self._all_monsters: list[Monster] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(8)

        # Zone scrollable
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(4)
        self._rows_layout.addStretch()

        self._scroll.setWidget(self._rows_container)
        outer.addWidget(self._scroll)

    def set_monsters(self, monsters: list[Monster]) -> None:
        """Remplace la liste courante par les monstres fournis."""
        # Purge rows existants
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()
        self._all_monsters = list(monsters)

        # Insere les nouveaux avant le stretch final
        stretch_index = self._rows_layout.count() - 1
        for monster in monsters:
            row = _MonsterRow(monster)
            row.clicked.connect(self.monster_clicked.emit)
            self._rows.append(row)
            self._rows_layout.insertWidget(stretch_index, row)
            stretch_index += 1
```

- [ ] **Step 2.4 : Lancer les tests pour verifier qu'ils passent**

```bash
pytest tests/ui/test_monster_list.py tests/ui/test_monsters_page.py -v
```

Attendu : 11 tests PASS (6 list + 5 page).

- [ ] **Step 2.5 : Commit**

```bash
git add ui/monsters/monster_list.py tests/ui/test_monster_list.py
git commit -m "feat(monsters): MonsterList renders rows with photo/name/stars/level/element/avg-eff"
```

---

## Task 3 — Barre de filtres (Élément / ★ / Nom)

**Files:**
- Modify: `ui/monsters/monster_list.py`
- Modify: `tests/ui/test_monster_list.py`

- [ ] **Step 3.1 : Ajouter les tests qui echouent**

Ajouter a la fin de `tests/ui/test_monster_list.py` :

```python
def test_filter_by_element(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("Lushen", element="Vent"),
        _monster("Laika", element="Feu"),
        _monster("Bella", element="Eau"),
    ])
    ml._element_combo.setCurrentText("Vent")
    assert len(ml._rows) == 1
    assert ml._rows[0]._monster.name == "Lushen"


def test_filter_by_min_stars(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("A", stars=4),
        _monster("B", stars=5),
        _monster("C", stars=6),
    ])
    ml._stars_combo.setCurrentText(">=6")
    assert len(ml._rows) == 1
    assert ml._rows[0]._monster.name == "C"


def test_filter_by_name_substring(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("Lushen"),
        _monster("Laika"),
        _monster("Lupine"),
    ])
    ml._name_search.setText("Lu")
    # Lushen + Lupine
    names = {r._monster.name for r in ml._rows}
    assert names == {"Lushen", "Lupine"}


def test_filter_all_element_shows_all(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("A", element="Vent"),
        _monster("B", element="Feu"),
    ])
    ml._element_combo.setCurrentText("Tous")
    assert len(ml._rows) == 2


def test_filters_combine(qapp):
    ml = MonsterList()
    ml.set_monsters([
        _monster("Laika", element="Feu", stars=6),
        _monster("Laika2", element="Feu", stars=5),
        _monster("Lushen", element="Vent", stars=6),
    ])
    ml._element_combo.setCurrentText("Feu")
    ml._stars_combo.setCurrentText(">=6")
    assert len(ml._rows) == 1
    assert ml._rows[0]._monster.name == "Laika"
```

- [ ] **Step 3.2 : Lancer pour voir FAIL**

```bash
pytest tests/ui/test_monster_list.py -v
```

Attendu : FAIL sur `AttributeError: '_element_combo'`.

- [ ] **Step 3.3 : Ajouter la barre de filtres dans `MonsterList`**

Dans `ui/monsters/monster_list.py`, **ajouter l'import** :

```python
from PySide6.QtWidgets import QComboBox, QLineEdit
```
(fusionner avec l'import existant `from PySide6.QtWidgets import (...)`).

Dans `MonsterList.__init__`, **avant la zone scrollable**, inserer :

```python
        # --- Barre de filtres ---
        filters = QHBoxLayout()
        filters.setSpacing(10)

        self._element_combo = QComboBox()
        self._element_combo.addItems(["Tous", "Eau", "Feu", "Vent", "Lumiere", "Tenebres"])
        self._element_combo.setFixedWidth(120)
        self._element_combo.currentTextChanged.connect(self._refresh_visible)
        filters.addWidget(QLabel("Element :"))
        filters.addWidget(self._element_combo)

        self._stars_combo = QComboBox()
        self._stars_combo.addItems([">=1", ">=2", ">=3", ">=4", ">=5", ">=6"])
        self._stars_combo.setCurrentText(">=1")
        self._stars_combo.setFixedWidth(80)
        self._stars_combo.currentTextChanged.connect(self._refresh_visible)
        filters.addWidget(QLabel("Etoiles :"))
        filters.addWidget(self._stars_combo)

        self._name_search = QLineEdit()
        self._name_search.setPlaceholderText("Rechercher par nom...")
        self._name_search.textChanged.connect(self._refresh_visible)
        filters.addWidget(self._name_search, 1)

        outer.addLayout(filters)
```

**Remplacer** l'ancienne methode `set_monsters` par :

```python
    def set_monsters(self, monsters: list[Monster]) -> None:
        self._all_monsters = list(monsters)
        self._refresh_visible()

    def _refresh_visible(self) -> None:
        # Purge rows actuels
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        # Applique filtres
        elem = self._element_combo.currentText()
        min_stars = int(self._stars_combo.currentText().lstrip(">="))
        name_query = self._name_search.text().strip().lower()

        filtered = []
        for mon in self._all_monsters:
            if elem != "Tous" and mon.element != elem:
                continue
            if mon.stars < min_stars:
                continue
            if name_query and name_query not in mon.name.lower():
                continue
            filtered.append(mon)

        # Insere
        stretch_index = self._rows_layout.count() - 1
        for monster in filtered:
            row = _MonsterRow(monster)
            row.clicked.connect(self.monster_clicked.emit)
            self._rows.append(row)
            self._rows_layout.insertWidget(stretch_index, row)
            stretch_index += 1
```

- [ ] **Step 3.4 : Lancer les tests**

```bash
pytest tests/ui/test_monster_list.py -v
```

Attendu : 11 tests PASS (6 initiaux + 5 filtres).

- [ ] **Step 3.5 : Commit**

```bash
git add ui/monsters/monster_list.py tests/ui/test_monster_list.py
git commit -m "feat(monsters): filter bar (element/stars/name) on MonsterList"
```

---

## Task 4 — Icônes Swarfarm (photo dans chaque ligne) + bouton refresh

**Files:**
- Modify: `ui/monsters/monster_list.py`
- Modify: `tests/ui/test_monster_list.py`

- [ ] **Step 4.1 : Tests qui echouent**

Ajouter a `tests/ui/test_monster_list.py` :

```python
def test_monster_icon_loaded_via_monster_icons(qapp, monkeypatch, tmp_path):
    """Le row doit appeler monster_icons.get_monster_icon(unit_master_id)."""
    from PySide6.QtGui import QPixmap
    import monster_icons
    called_with: list[int] = []

    def fake_get_icon(uid: int):
        called_with.append(uid)
        # Pixmap 1x1 transparent
        p = QPixmap(1, 1)
        p.fill()
        # Sauvegarde dans tmp pour retourner un Path valide
        path = tmp_path / f"{uid}.png"
        p.save(str(path))
        return path

    monkeypatch.setattr(monster_icons, "get_monster_icon", fake_get_icon)

    ml = MonsterList()
    mon = _monster("Lushen")
    mon.unit_master_id = 11211
    ml.set_monsters([mon])
    assert 11211 in called_with


def test_refresh_icons_button_exists(qapp):
    from PySide6.QtWidgets import QPushButton
    ml = MonsterList()
    btns = [b for b in ml.findChildren(QPushButton) if "Refresh" in b.text() or "icones" in b.text().lower()]
    assert len(btns) >= 1
```

- [ ] **Step 4.2 : FAIL**

```bash
pytest tests/ui/test_monster_list.py -v
```

- [ ] **Step 4.3 : Charger l'icone Swarfarm dans `_MonsterRow` + ajouter bouton refresh**

Dans `ui/monsters/monster_list.py`, **ajouter l'import** en haut :

```python
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QPushButton

import monster_icons
```

Dans `_MonsterRow.__init__`, **juste apres la creation de `self._icon`** (avant `row.addWidget(self._icon)`), ajouter :

```python
        # Charger l'icone depuis le cache Swarfarm
        try:
            icon_path = monster_icons.get_monster_icon(monster.unit_master_id)
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self._icon.setPixmap(pix.scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            pass  # placeholder gris (style deja applique)
```

Dans `MonsterList.__init__`, **dans la barre de filtres** (apres `self._name_search`), ajouter :

```python
        self._refresh_btn = QPushButton("Refresh icones Swarfarm")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._on_refresh_icons)
        filters.addWidget(self._refresh_btn)
```

Et ajouter la methode :

```python
    def _on_refresh_icons(self) -> None:
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("Telechargement...")

        def on_done():
            self._refresh_btn.setEnabled(True)
            self._refresh_btn.setText("Refresh icones Swarfarm")
            self._refresh_visible()  # re-render avec nouvelles icones

        monster_icons.download_icons_async(on_done=on_done)
```

- [ ] **Step 4.4 : PASS**

```bash
pytest tests/ui/test_monster_list.py -v
```

Attendu : 13 tests PASS.

- [ ] **Step 4.5 : Commit**

```bash
git add ui/monsters/monster_list.py tests/ui/test_monster_list.py
git commit -m "feat(monsters): Swarfarm icons in rows + refresh button"
```

---

## Task 5 — `MonsterDetail` : header (image + nom/stars/élément/niveau) + bouton retour

**Files:**
- Modify: `ui/monsters/monster_detail.py`
- Create: `tests/ui/test_monster_detail.py`

- [ ] **Step 5.1 : Tests qui echouent**

Creer `tests/ui/test_monster_detail.py` :

```python
from PySide6.QtWidgets import QLabel, QPushButton

from models import Monster, Rune, SubStat
from ui.monsters.monster_detail import MonsterDetail


def _monster(name: str = "Lushen", runes: list | None = None) -> Monster:
    return Monster(
        name=name, element="Vent", stars=6, level=40, unit_master_id=11211,
        equipped_runes=runes or [],
    )


def test_detail_instantiates(qapp):
    assert MonsterDetail() is not None


def test_detail_back_button_exists_and_emits_signal(qapp):
    d = MonsterDetail()
    received: list = []
    d.back_clicked.connect(lambda: received.append(1))
    btns = [b for b in d.findChildren(QPushButton) if "Retour" in b.text()]
    assert len(btns) == 1
    btns[0].click()
    assert received == [1]


def test_set_monster_fills_header(qapp):
    d = MonsterDetail()
    d.set_monster(_monster(name="Lushen"))
    texts = " | ".join(lbl.text() for lbl in d.findChildren(QLabel))
    assert "Lushen" in texts
    assert "Vent" in texts
    assert "40" in texts  # niveau


def test_set_monster_none_shows_empty_state(qapp):
    d = MonsterDetail()
    d.set_monster(None)
    # Ne doit pas crasher. Le header peut etre vide ou afficher un placeholder.
    assert d is not None
```

- [ ] **Step 5.2 : FAIL**

```bash
pytest tests/ui/test_monster_detail.py -v
```

- [ ] **Step 5.3 : Remplacer completement `ui/monsters/monster_detail.py`**

```python
"""Vue detail d'un monstre : header (image + stats) + 6 slots de runes + bouton retour."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

import monster_icons
from models import Monster
from ui import theme


class MonsterDetail(QWidget):
    back_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._monster: Monster | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(12)

        # --- Breadcrumb / Back ---
        crumb = QHBoxLayout()
        crumb.setSpacing(8)
        self._back_btn = QPushButton("< Retour")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{theme.COLOR_BRONZE};"
            f" border:none; font-size:13px; font-weight:600; padding:4px 8px; }}"
            f"QPushButton:hover {{ color:{theme.COLOR_EMBER}; }}"
        )
        self._back_btn.clicked.connect(self.back_clicked.emit)
        crumb.addWidget(self._back_btn)

        self._crumb_label = QLabel("Monstres /")
        self._crumb_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:13px;"
        )
        crumb.addWidget(self._crumb_label)
        crumb.addStretch()
        outer.addLayout(crumb)

        # --- Header ---
        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background:rgba(26,15,7,0.8);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 12, 16, 12)
        h_lay.setSpacing(16)

        self._icon = QLabel()
        self._icon.setFixedSize(96, 96)
        self._icon.setStyleSheet(
            f"background:{theme.COLOR_BG_FRAME};"
            f"border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px;"
        )
        h_lay.addWidget(self._icon)

        info = QVBoxLayout()
        info.setSpacing(4)
        self._name_lbl = QLabel("")
        self._name_lbl.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-size:20px; font-weight:700;"
            f" font-family:'{theme.FONT_TITLE}';"
        )
        info.addWidget(self._name_lbl)

        self._meta_lbl = QLabel("")
        self._meta_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:13px;"
        )
        info.addWidget(self._meta_lbl)
        info.addStretch()
        h_lay.addLayout(info, 1)

        outer.addWidget(header)

        # --- Slots de runes (placeholder, Task 6 remplit) ---
        self._slots_frame = QFrame()
        self._slots_grid = QGridLayout(self._slots_frame)
        self._slots_grid.setContentsMargins(0, 0, 0, 0)
        self._slots_grid.setSpacing(8)
        outer.addWidget(self._slots_frame, 1)

        outer.addStretch()

    def set_monster(self, monster: Monster | None) -> None:
        self._monster = monster
        if monster is None:
            self._name_lbl.setText("")
            self._meta_lbl.setText("")
            self._crumb_label.setText("Monstres /")
            self._icon.clear()
            return

        self._name_lbl.setText(monster.name)
        self._meta_lbl.setText(
            f"{monster.element} \u00b7 \u2605{monster.stars} \u00b7 Niv {monster.level}"
        )
        self._crumb_label.setText(f"Monstres / {monster.name}")

        # Icone
        try:
            icon_path = monster_icons.get_monster_icon(monster.unit_master_id)
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self._icon.setPixmap(pix.scaled(
                    96, 96,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
        except Exception:
            self._icon.clear()
```

- [ ] **Step 5.4 : PASS**

```bash
pytest tests/ui/test_monster_detail.py -v
```

Attendu : 4 tests PASS.

- [ ] **Step 5.5 : Commit**

```bash
git add ui/monsters/monster_detail.py tests/ui/test_monster_detail.py
git commit -m "feat(monsters): MonsterDetail header with icon, name, stars, element, back button"
```

---

## Task 6 — `MonsterDetail` : 6 slots de runes

**Files:**
- Modify: `ui/monsters/monster_detail.py`
- Modify: `tests/ui/test_monster_detail.py`

- [ ] **Step 6.1 : Tests qui echouent**

Ajouter a `tests/ui/test_monster_detail.py` :

```python
def _rune(slot: int, set_name: str = "Violent", main: str = "ATQ%", val: float = 63.0) -> Rune:
    return Rune(
        set=set_name, slot=slot, stars=6, grade="Legend", level=12,
        main_stat=SubStat(type=main, value=val),
        prefix=None, substats=[],
    )


def test_detail_shows_6_slot_cards(qapp):
    d = MonsterDetail()
    runes = [_rune(i) for i in range(1, 7)]
    d.set_monster(_monster(runes=runes))
    # Chaque slot a un cadre identifiable
    assert len(d._slot_widgets) == 6


def test_empty_slot_shows_placeholder(qapp):
    d = MonsterDetail()
    runes = [_rune(1), _rune(3)]  # slots 2/4/5/6 manquants
    d.set_monster(_monster(runes=runes))
    # Les 6 widgets existent quand meme
    assert len(d._slot_widgets) == 6
    # Les slots 2/4/5/6 affichent "Vide"
    texts = [w.findChild(QLabel, "slot_content").text() for w in d._slot_widgets]
    assert "Vide" in texts[1]
    assert "Vide" in texts[3]


def test_filled_slot_shows_set_and_main(qapp):
    d = MonsterDetail()
    runes = [_rune(1, set_name="Violent", main="ATQ%", val=63.0)]
    d.set_monster(_monster(runes=runes))
    content = d._slot_widgets[0].findChild(QLabel, "slot_content").text()
    assert "Violent" in content
    assert "ATQ%" in content
```

- [ ] **Step 6.2 : FAIL**

```bash
pytest tests/ui/test_monster_detail.py -v
```

- [ ] **Step 6.3 : Implementer les 6 slots**

Dans `ui/monsters/monster_detail.py`, **dans `__init__`**, remplacer le bloc `# --- Slots de runes (placeholder, Task 6 remplit) ---` par :

```python
        # --- 6 slots de runes ---
        self._slots_frame = QFrame()
        self._slots_grid = QGridLayout(self._slots_frame)
        self._slots_grid.setContentsMargins(0, 0, 0, 0)
        self._slots_grid.setSpacing(8)

        self._slot_widgets: list[QFrame] = []
        for slot_num in range(1, 7):
            card = QFrame()
            card.setObjectName(f"slot_{slot_num}")
            card.setStyleSheet(
                f"QFrame#slot_{slot_num} {{ background:rgba(26,15,7,0.7);"
                f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
            )
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(10, 8, 10, 8)
            card_lay.setSpacing(4)

            header = QLabel(f"SLOT {slot_num}")
            header.setStyleSheet(
                f"color:{theme.COLOR_GOLD}; font-size:10px; font-weight:700;"
                f" letter-spacing:1px;"
            )
            card_lay.addWidget(header)

            content = QLabel("Vide")
            content.setObjectName("slot_content")
            content.setWordWrap(True)
            content.setStyleSheet(
                f"color:{theme.COLOR_TEXT_DIM}; font-size:11px;"
            )
            card_lay.addWidget(content)
            card_lay.addStretch()

            self._slot_widgets.append(card)
            row = (slot_num - 1) // 3  # 0 pour slots 1-3, 1 pour slots 4-6
            col = (slot_num - 1) % 3
            self._slots_grid.addWidget(card, row, col)

        outer.addWidget(self._slots_frame, 1)
```

Et dans `set_monster`, **apres** `self._crumb_label.setText(...)`, ajouter le remplissage des slots :

```python
        # Remplissage des 6 slots
        by_slot = {r.slot: r for r in monster.equipped_runes}
        for slot_num in range(1, 7):
            content_label = self._slot_widgets[slot_num - 1].findChild(QLabel, "slot_content")
            rune = by_slot.get(slot_num)
            if rune is None:
                content_label.setText("Vide")
                content_label.setStyleSheet(
                    f"color:{theme.COLOR_TEXT_DIM}; font-size:11px;"
                )
            else:
                main = rune.main_stat
                eff = f" \u00b7 Eff {rune.swex_efficiency:.0f}%" if rune.swex_efficiency is not None else ""
                content_label.setText(
                    f"{rune.set} \u2605{rune.stars} +{rune.level}\n"
                    f"{main.type} +{main.value:g}{eff}"
                )
                content_label.setStyleSheet(
                    f"color:{theme.COLOR_TEXT_MAIN}; font-size:11px;"
                )
```

- [ ] **Step 6.4 : PASS**

```bash
pytest tests/ui/test_monster_detail.py -v
```

Attendu : 7 tests PASS (4 initiaux + 3 slots).

- [ ] **Step 6.5 : Commit**

```bash
git add ui/monsters/monster_detail.py tests/ui/test_monster_detail.py
git commit -m "feat(monsters): 6 rune slots in MonsterDetail with fill/empty states"
```

---

## Task 7 — Câbler clic liste → push détail + bouton retour dans `MonstersPage`

**Files:**
- Modify: `ui/monsters/monsters_page.py`
- Modify: `tests/ui/test_monsters_page.py`

- [ ] **Step 7.1 : Tests qui echouent**

Ajouter a `tests/ui/test_monsters_page.py` :

```python
def test_click_on_monster_switches_to_detail(qapp):
    page = MonstersPage()
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211)
    page.apply_profile({"monsters": [mon]}, saved_at=0.0)
    # Simule le clic sur le monstre
    page._list.monster_clicked.emit(mon)
    assert page._stack.currentIndex() == 1
    assert page._detail._monster is mon


def test_back_returns_to_list(qapp):
    page = MonstersPage()
    mon = Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=11211)
    page.apply_profile({"monsters": [mon]}, saved_at=0.0)
    page._list.monster_clicked.emit(mon)
    assert page._stack.currentIndex() == 1
    page._detail.back_clicked.emit()
    assert page._stack.currentIndex() == 0
```

- [ ] **Step 7.2 : FAIL**

- [ ] **Step 7.3 : Cabler les signaux dans `MonstersPage`**

Dans `ui/monsters/monsters_page.py`, **apres** `self._stack.addWidget(self._detail)`, ajouter :

```python
        self._list.monster_clicked.connect(self._on_monster_clicked)
        self._detail.back_clicked.connect(self._on_back)
```

Et ajouter les methodes :

```python
    def _on_monster_clicked(self, monster) -> None:
        self._detail.set_monster(monster)
        self._stack.setCurrentIndex(1)

    def _on_back(self) -> None:
        self._stack.setCurrentIndex(0)
```

- [ ] **Step 7.4 : PASS**

```bash
pytest tests/ui/test_monsters_page.py -v
```

Attendu : 7 tests PASS (5 initiaux + 2 navigation).

- [ ] **Step 7.5 : Commit**

```bash
git add ui/monsters/monsters_page.py tests/ui/test_monsters_page.py
git commit -m "feat(monsters): wire list click -> detail + back -> list"
```

---

## Task 8 — Câbler `MonstersPage` dans `MainWindow` + signal `profile_loaded`

**Files:**
- Modify: `ui/main_window.py`
- Modify: `tests/ui/test_main_window_nav.py`

- [ ] **Step 8.1 : Test qui echoue**

Ajouter a `tests/ui/test_main_window_nav.py` :

```python
def test_monsters_index_is_monsters_page(qapp):
    from ui.monsters.monsters_page import MonstersPage
    mw = MainWindow()
    mw._on_nav("monsters")
    assert isinstance(mw._stack.currentWidget(), MonstersPage)


def test_profile_loaded_signal_feeds_monsters_page(qapp):
    from models import Monster
    mw = MainWindow()
    profile = {
        "wizard_name": "Test", "level": 40,
        "runes": [], "monsters": [
            Monster(name="Lushen", element="Vent", stars=6, level=40, unit_master_id=1),
        ],
        "source": "manual",
    }
    mw.monsters_page.apply_profile(profile, 0.0)
    assert len(mw.monsters_page._list._rows) == 1
```

- [ ] **Step 8.2 : FAIL**

```bash
pytest tests/ui/test_main_window_nav.py -v
```

- [ ] **Step 8.3 : Cabler `MonstersPage` dans `MainWindow`**

Dans `ui/main_window.py`, **ajouter l'import** (avec les autres `from ui...`) :

```python
from ui.monsters.monsters_page import MonstersPage
```

Dans `__init__`, **remplacer la ligne** :

```python
        # Index 3 : Monstres (placeholder, Plan 2)
        self._stack.addWidget(_placeholder("Monstres - a implementer"))
```

par :

```python
        # Index 3 : Monstres
        self.monsters_page = MonstersPage()
        self._stack.addWidget(self.monsters_page)
```

**Cabler le signal profile_loaded**. Apres les autres `self.controller.xxx.connect(...)`, ajouter :

```python
        self.controller.profile_loaded.connect(
            self.monsters_page.apply_profile,
            type=Qt.ConnectionType.QueuedConnection,
        )
```

**Dans `_restore_cached_profile`**, apres `self.profile_page.apply_profile(profile, saved_at)`, ajouter :

```python
        self.monsters_page.apply_profile(profile, saved_at)
```

- [ ] **Step 8.4 : PASS**

```bash
pytest tests/ui/ -v
```

Attendu : tous les tests UI PASS (les 51 existants + 2 nouveaux + 20 des tasks precedentes de ce plan = 73).

- [ ] **Step 8.5 : Commit**

```bash
git add ui/main_window.py tests/ui/test_main_window_nav.py
git commit -m "feat(main-window): wire MonstersPage at index 3 + profile_loaded signal"
```

---

## Task 9 — Smoke test manuel

- [ ] **Step 9.1 : Lancer l'application**

```bash
cd /c/Users/louis/Desktop/Luci2US
python scan_app.py
```

- [ ] **Step 9.2 : Checklist Monstres**

- Cliquer sur `Monstres` dans la sidebar → vue liste vide (pas de profil charge).
- Dans `Profils`, charger un profil manuellement (Import JSON) OU lancer un scan (le signal `profile_loaded` feed la liste).
- Retourner sur `Monstres` → les monstres apparaissent avec icones + nom + etoiles + element + Eff moyenne.
- Taper dans le champ de recherche → la liste se filtre live.
- Selectionner un element → la liste se filtre.
- Selectionner `>=6` → la liste se filtre.
- Combiner filtres → la liste se filtre.
- Cliquer sur un monstre → push sur la vue detail avec image + stats + 6 slots remplis.
- Cliquer `< Retour` → retour a la liste (filtres conserves).
- Cliquer `Refresh icones Swarfarm` → bouton se desactive, texte devient `Telechargement...`, puis retour a l'etat normal une fois fini.

- [ ] **Step 9.3 : Non-regression**

- `Scan` fonctionne toujours.
- `Profils` fonctionne toujours.
- `Parametres` fonctionne toujours.
- `Filtres`, `Runes`, `Stats & Historique` affichent toujours leur placeholder.

- [ ] **Step 9.4 : Tag**

```bash
git tag plan-02-done
```

---

## Récapitulatif — ce que ce plan produit

1. **`MonstersPage`** (QStackedWidget interne liste/detail) cablee sur `ScanController.profile_loaded` ET restauree depuis `_restore_cached_profile`. ✓
2. **`MonsterList`** : barre de filtres (element / ★ / nom) + scroll + Refresh icones Swarfarm. ✓
3. **`MonsterDetail`** : header (icone 96x96 + nom + etoiles + element + niveau) + 6 slots de runes + bouton Retour. ✓
4. **22 tests** couvrant instanciation, rendu, filtres, Eff moyenne, navigation liste↔detail, icones. ✓
5. Aucun changement aux modules bot core. ✓

**Prochain plan :** `Plan 03 — Runes (liste filtree + panneau lateral)`.
