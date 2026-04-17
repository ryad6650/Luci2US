# Plan 01 — Fondations (sidebar 7 items + wiring MainWindow) + onglet Paramètres

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Étendre la sidebar Luci2US à 7 items dans l'ordre final, câbler tous les slots du `QStackedWidget` du `MainWindow` (placeholders pour les 4 tabs à venir), et implémenter l'onglet Paramètres minimaliste (Langue + SWEX drops dir + Save).

**Architecture:** Suit le pattern existant `ui/scan/` et `ui/profile/` — nouveau sous-package `ui/settings/` avec un seul widget `SettingsPage`. La sidebar expose une nouvelle clé par item (`filters`, `runes`, `monsters`, `stats_history`, `settings`). `MainWindow` ajoute les 5 pages au `QStackedWidget` (4 placeholders + `SettingsPage` réel) et étend son mapping `_on_nav`. Aucune modification des modules core intouchables (`evaluator_chain`, `s2us_filter`, `auto_mode`, `swex_bridge`).

**Tech Stack:** PySide6 6.11.0, pytest-qt (fixture `qapp`), `i18n.py` existant, `config.json` existant. Tous les tests dans `tests/ui/`.

---

## File Structure

### Créer

| Chemin | Responsabilité |
|---|---|
| `ui/settings/__init__.py` | Package init vide |
| `ui/settings/settings_page.py` | Widget `SettingsPage` : Langue + SWEX drops_dir + bouton Save |
| `tests/ui/test_sidebar.py` | Tests du nouveau NAV_ITEMS à 7 items + signal `nav_changed` |
| `tests/ui/test_main_window_nav.py` | Tests du mapping `_on_nav` étendu à 7 clés |
| `tests/ui/test_settings_page.py` | Tests de chargement/sauvegarde de `config.json` |

### Modifier

| Chemin | Changement |
|---|---|
| `ui/sidebar.py` | `NAV_ITEMS` étendu à 7 items dans l'ordre : scan / filters / runes / monsters / stats_history / profile / settings |
| `ui/main_window.py` | 5 nouvelles pages ajoutées au `QStackedWidget` (4 placeholders + `SettingsPage`), `_on_nav` mappe 7 clés |

### Ne pas toucher

- `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `swex_bridge.py`, `profile_loader.py`, `profile_store.py`
- `ui/controllers/scan_controller.py`, `ui/scan/*`, `ui/profile/*`, `ui/widgets/*`, `ui/theme.py`
- Tabs legacy `settings_tab.py`, `stats_tab.py`, `history_tab.py`, `auto_tab.py`, `profile_tab.py` (supprimés plus tard, après validation globale)

---

## Task 1 — Étendre la sidebar à 7 items

**Files:**
- Create: `tests/ui/test_sidebar.py`
- Modify: `ui/sidebar.py:10-16`

- [ ] **Step 1.1 : Écrire le test qui échoue**

Créer `tests/ui/test_sidebar.py` :

```python
from ui.sidebar import Sidebar, NAV_ITEMS


def test_nav_items_order_and_keys():
    keys = [k for k, _ in NAV_ITEMS]
    assert keys == [
        "scan",
        "filters",
        "runes",
        "monsters",
        "stats_history",
        "profile",
        "settings",
    ]


def test_nav_items_labels_french():
    labels = [label for _, label in NAV_ITEMS]
    assert any("Scan" in l for l in labels)
    assert any("Filtres" in l for l in labels)
    assert any("Runes" in l for l in labels)
    assert any("Monstres" in l for l in labels)
    assert any("Stats" in l for l in labels)
    assert any("Profils" in l for l in labels)
    assert any("Parametres" in l for l in labels)


def test_sidebar_instantiates_with_all_buttons(qapp):
    sb = Sidebar()
    for key, _ in NAV_ITEMS:
        assert key in sb._buttons, f"missing button for key {key}"


def test_sidebar_emits_nav_changed(qapp):
    sb = Sidebar()
    received: list[str] = []
    sb.nav_changed.connect(received.append)
    sb._on_click("runes")
    assert received == ["runes"]


def test_sidebar_active_highlighting(qapp):
    sb = Sidebar()
    sb.set_active("monsters")
    assert sb._buttons["monsters"].isChecked() is True
    assert sb._buttons["scan"].isChecked() is False
```

- [ ] **Step 1.2 : Lancer le test pour vérifier qu'il échoue**

```bash
cd /c/Users/louis/Desktop/Luci2US
pytest tests/ui/test_sidebar.py -v
```

Attendu : FAIL sur `test_nav_items_order_and_keys` (les clés actuelles sont `scan/settings/history/stats/profile`, pas les 7 nouvelles).

- [ ] **Step 1.3 : Modifier `ui/sidebar.py` — nouveau NAV_ITEMS**

Remplacer le bloc `NAV_ITEMS` (lignes 10-16) :

```python
NAV_ITEMS = [
    ("scan",          "\u25C9  Scan"),
    ("filters",       "\u25A3  Filtres"),
    ("runes",         "\u2726  Runes"),
    ("monsters",      "\u2618  Monstres"),
    ("stats_history", "\u2261  Stats & Historique"),
    ("profile",       "\u25CE  Profils"),
    ("settings",      "\u2699  Parametres"),
]
```

Aucune autre modification nécessaire dans ce fichier — la boucle `for key, label in NAV_ITEMS` consomme déjà la structure.

- [ ] **Step 1.4 : Lancer le test pour vérifier qu'il passe**

```bash
pytest tests/ui/test_sidebar.py -v
```

Attendu : 5 tests PASS.

- [ ] **Step 1.5 : Commit**

```bash
cd /c/Users/louis/Desktop/Luci2US
git add ui/sidebar.py tests/ui/test_sidebar.py
git commit -m "feat(sidebar): extend nav to 7 items (filters/runes/monsters/stats_history/settings)"
```

---

## Task 2 — Étendre le mapping `_on_nav` du MainWindow

**Files:**
- Create: `tests/ui/test_main_window_nav.py`
- Modify: `ui/main_window.py:98-100` (ligne de mapping), `ui/main_window.py:55-58` (ajout de pages au stack)

- [ ] **Step 2.1 : Écrire le test qui échoue**

Créer `tests/ui/test_main_window_nav.py` :

```python
from ui.main_window import MainWindow


def test_stack_has_7_pages(qapp):
    mw = MainWindow()
    assert mw._stack.count() == 7


def test_on_nav_maps_all_7_keys(qapp):
    mw = MainWindow()
    expected = {
        "scan":          0,
        "filters":       1,
        "runes":         2,
        "monsters":      3,
        "stats_history": 4,
        "profile":       5,
        "settings":      6,
    }
    for key, index in expected.items():
        mw._on_nav(key)
        assert mw._stack.currentIndex() == index, f"{key} -> {mw._stack.currentIndex()} expected {index}"


def test_on_nav_unknown_key_defaults_to_scan(qapp):
    mw = MainWindow()
    mw._on_nav("does-not-exist")
    assert mw._stack.currentIndex() == 0
```

- [ ] **Step 2.2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/ui/test_main_window_nav.py -v
```

Attendu : FAIL (stack n'a que 5 pages actuellement, mapping ne contient pas les nouvelles clés).

- [ ] **Step 2.3 : Modifier `ui/main_window.py` — ajouter les 5 pages au stack**

Dans `__init__`, remplacer le bloc lignes 52-58 (création du stack + ajout des pages) par :

```python
        self._stack = QStackedWidget()
        self.scan_page = ScanPage()
        self.profile_page = ProfilePage()

        # Index 0 : Scan
        self._stack.addWidget(self.scan_page)
        # Index 1 : Filtres (placeholder, Plan 5)
        self._stack.addWidget(_placeholder("Filtres - a implementer"))
        # Index 2 : Runes (placeholder, Plan 3)
        self._stack.addWidget(_placeholder("Runes - a implementer"))
        # Index 3 : Monstres (placeholder, Plan 2)
        self._stack.addWidget(_placeholder("Monstres - a implementer"))
        # Index 4 : Stats & Historique (placeholder, Plan 4)
        self._stack.addWidget(_placeholder("Stats & Historique - a implementer"))
        # Index 5 : Profils
        self._stack.addWidget(self.profile_page)
        # Index 6 : Paramètres (wiré dans Task 7)
        self._stack.addWidget(_placeholder("Parametres - wiring dans Task 7"))

        bg_lay.addWidget(self._stack)
```

Puis, remplacer `_on_nav` (lignes 98-100) par :

```python
    def _on_nav(self, key: str) -> None:
        index = {
            "scan":          0,
            "filters":       1,
            "runes":         2,
            "monsters":      3,
            "stats_history": 4,
            "profile":       5,
            "settings":      6,
        }.get(key, 0)
        self._stack.setCurrentIndex(index)
```

- [ ] **Step 2.4 : Lancer le test pour vérifier qu'il passe**

```bash
pytest tests/ui/test_main_window_nav.py -v
```

Attendu : 3 tests PASS.

- [ ] **Step 2.5 : Vérifier que les tests existants du MainWindow ne régressent pas**

```bash
pytest tests/ui/ -v
```

Attendu : tous les tests UI PASS (aucun test existant ne doit casser).

- [ ] **Step 2.6 : Commit**

```bash
git add ui/main_window.py tests/ui/test_main_window_nav.py
git commit -m "feat(main-window): wire 7 nav slots with placeholders for new tabs"
```

---

## Task 3 — Squelette de `SettingsPage` (instanciation)

**Files:**
- Create: `ui/settings/__init__.py`
- Create: `ui/settings/settings_page.py`
- Create: `tests/ui/test_settings_page.py`

- [ ] **Step 3.1 : Écrire le test qui échoue (instanciation minimale)**

Créer `tests/ui/test_settings_page.py` :

```python
from ui.settings.settings_page import SettingsPage


def test_settings_page_instantiates(qapp):
    page = SettingsPage()
    assert page is not None


def test_settings_page_has_title(qapp):
    page = SettingsPage()
    # Le titre "Parametres" doit etre present dans un QLabel enfant
    from PySide6.QtWidgets import QLabel
    labels = page.findChildren(QLabel)
    texts = [l.text() for l in labels]
    assert any("Parametres" in t for t in texts)
```

- [ ] **Step 3.2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : FAIL avec `ModuleNotFoundError: No module named 'ui.settings'`.

- [ ] **Step 3.3 : Créer `ui/settings/__init__.py` (vide)**

Créer un fichier vide :

```python
```

- [ ] **Step 3.4 : Créer `ui/settings/settings_page.py` (squelette)**

```python
"""Parametres tab - langue + chemin SWEX drops + bouton Save."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ui import theme


class SettingsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(18)

        title = QLabel("Parametres")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:22px; font-weight:700; letter-spacing:0.5px;"
        )
        lay.addWidget(title)

        lay.addStretch()
```

- [ ] **Step 3.5 : Lancer le test pour vérifier qu'il passe**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : 2 tests PASS.

- [ ] **Step 3.6 : Commit**

```bash
git add ui/settings/ tests/ui/test_settings_page.py
git commit -m "feat(settings): add SettingsPage skeleton with title"
```

---

## Task 4 — Dropdown Langue (chargement depuis config.json)

**Files:**
- Modify: `ui/settings/settings_page.py` (ajouter dropdown + lecture config)
- Modify: `tests/ui/test_settings_page.py` (ajouter tests)

- [ ] **Step 4.1 : Écrire les tests qui échouent**

Ajouter à la fin de `tests/ui/test_settings_page.py` :

```python
import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Cree un config.json temporaire et patche le chemin dans le module."""
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({
            "lang": "EN",
            "swex": {"drops_dir": "C:/tmp/drops"},
        }),
        encoding="utf-8",
    )
    from ui.settings import settings_page
    monkeypatch.setattr(settings_page, "_CONFIG_PATH", str(cfg))
    return cfg


def test_language_dropdown_loaded_from_config(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    assert page._lang_combo.currentText() == "EN"


def test_language_dropdown_defaults_to_FR_when_missing(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({}), encoding="utf-8")
    from ui.settings import settings_page
    monkeypatch.setattr(settings_page, "_CONFIG_PATH", str(cfg))
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    assert page._lang_combo.currentText() == "FR"


def test_language_dropdown_has_fr_and_en(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    items = [page._lang_combo.itemText(i) for i in range(page._lang_combo.count())]
    assert items == ["FR", "EN"]
```

- [ ] **Step 4.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : FAIL (3 nouveaux tests) sur `AttributeError: 'SettingsPage' object has no attribute '_lang_combo'`.

- [ ] **Step 4.3 : Implémenter dropdown Langue**

Remplacer complètement `ui/settings/settings_page.py` par :

```python
"""Parametres tab - langue + chemin SWEX drops + bouton Save."""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from ui import theme


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.json")


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


class SettingsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        cfg = _load_config()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(18)

        title = QLabel("Parametres")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:22px; font-weight:700; letter-spacing:0.5px;"
        )
        lay.addWidget(title)

        # ── Langue ──
        lang_row = QHBoxLayout()
        lang_row.setSpacing(12)

        lang_label = QLabel("Langue")
        lang_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:13px; font-weight:600;"
        )
        lang_row.addWidget(lang_label)

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["FR", "EN"])
        self._lang_combo.setCurrentText(cfg.get("lang", "FR"))
        self._lang_combo.setFixedWidth(100)
        self._lang_combo.setStyleSheet(
            f"QComboBox {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:4px 8px; font-size:12px; }}"
        )
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()

        lay.addLayout(lang_row)
        lay.addStretch()
```

- [ ] **Step 4.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : 5 tests PASS (les 2 existants + 3 nouveaux).

- [ ] **Step 4.5 : Commit**

```bash
git add ui/settings/settings_page.py tests/ui/test_settings_page.py
git commit -m "feat(settings): language dropdown loaded from config.json"
```

---

## Task 5 — Input SWEX drops_dir + bouton Parcourir

**Files:**
- Modify: `ui/settings/settings_page.py`
- Modify: `tests/ui/test_settings_page.py`

- [ ] **Step 5.1 : Écrire les tests qui échouent**

Ajouter à la fin de `tests/ui/test_settings_page.py` :

```python
def test_drops_dir_loaded_from_config(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    assert page._drops_edit.text() == "C:/tmp/drops"


def test_drops_dir_empty_when_missing(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({}), encoding="utf-8")
    from ui.settings import settings_page
    monkeypatch.setattr(settings_page, "_CONFIG_PATH", str(cfg))
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    assert page._drops_edit.text() == ""


def test_drops_dir_has_browse_button(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    from PySide6.QtWidgets import QPushButton
    page = SettingsPage()
    buttons = [b.text() for b in page.findChildren(QPushButton)]
    assert any("Parcourir" in t for t in buttons)
```

- [ ] **Step 5.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : FAIL sur `AttributeError: '_drops_edit'`.

- [ ] **Step 5.3 : Ajouter le champ SWEX drops dir + bouton Parcourir**

Dans `ui/settings/settings_page.py`, ajouter les imports en haut :

```python
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)
```

Puis, dans `__init__`, juste avant le `lay.addStretch()` final, insérer :

```python
        # ── SWEX drops dir ──
        swex_label = QLabel("SWEX - Dossier des drops")
        swex_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:13px; font-weight:600;"
        )
        lay.addWidget(swex_label)

        swex_row = QHBoxLayout()
        swex_row.setSpacing(8)

        self._drops_edit = QLineEdit()
        self._drops_edit.setText(cfg.get("swex", {}).get("drops_dir", ""))
        self._drops_edit.setStyleSheet(
            f"QLineEdit {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:6px 8px; font-size:12px; }}"
        )
        swex_row.addWidget(self._drops_edit, 1)

        browse_btn = QPushButton("Parcourir")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_drops)
        browse_btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD};"
            f" border:1px solid {theme.COLOR_BRONZE};"
            f" border-radius:3px; padding:6px 14px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{theme.COLOR_BRONZE}; color:{theme.COLOR_BG_APP}; }}"
        )
        swex_row.addWidget(browse_btn)

        lay.addLayout(swex_row)
```

Ajouter la méthode `_browse_drops` dans la classe :

```python
    def _browse_drops(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier des drops SWEX", self._drops_edit.text()
        )
        if directory:
            self._drops_edit.setText(directory)
```

- [ ] **Step 5.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : 8 tests PASS (les 5 existants + 3 nouveaux).

- [ ] **Step 5.5 : Commit**

```bash
git add ui/settings/settings_page.py tests/ui/test_settings_page.py
git commit -m "feat(settings): SWEX drops_dir field with browse button"
```

---

## Task 6 — Bouton Save (écriture de config.json)

**Files:**
- Modify: `ui/settings/settings_page.py`
- Modify: `tests/ui/test_settings_page.py`

- [ ] **Step 6.1 : Écrire les tests qui échouent**

Ajouter à la fin de `tests/ui/test_settings_page.py` :

```python
def test_save_writes_language_and_drops_dir(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    page._lang_combo.setCurrentText("FR")
    page._drops_edit.setText("D:/new/drops")
    page._save()
    saved = json.loads(tmp_config.read_text(encoding="utf-8"))
    assert saved["lang"] == "FR"
    assert saved["swex"]["drops_dir"] == "D:/new/drops"


def test_save_preserves_other_config_keys(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({
            "lang": "FR",
            "swex": {"drops_dir": "C:/x", "poll_interval": 0.5},
            "s2us": {"filter_file": "C:/y.s2us"},
        }),
        encoding="utf-8",
    )
    from ui.settings import settings_page
    monkeypatch.setattr(settings_page, "_CONFIG_PATH", str(cfg))
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    page._lang_combo.setCurrentText("EN")
    page._save()
    saved = json.loads(cfg.read_text(encoding="utf-8"))
    assert saved["lang"] == "EN"
    assert saved["swex"]["poll_interval"] == 0.5
    assert saved["s2us"]["filter_file"] == "C:/y.s2us"


def test_save_button_exists_and_triggers_save(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    from PySide6.QtWidgets import QPushButton
    page = SettingsPage()
    save_btns = [b for b in page.findChildren(QPushButton) if "Sauvegarder" in b.text()]
    assert len(save_btns) == 1
    page._lang_combo.setCurrentText("EN")
    save_btns[0].click()
    saved = json.loads(tmp_config.read_text(encoding="utf-8"))
    assert saved["lang"] == "EN"
```

- [ ] **Step 6.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : FAIL sur `AttributeError: 'SettingsPage' object has no attribute '_save'`.

- [ ] **Step 6.3 : Implémenter Save**

Dans `ui/settings/settings_page.py`, juste avant `lay.addStretch()` final, ajouter :

```python
        # ── Bouton Save ──
        save_btn = QPushButton("Sauvegarder")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        save_btn.setFixedWidth(160)
        save_btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BRONZE};"
            f" color:{theme.COLOR_BG_APP};"
            f" border:none; border-radius:4px;"
            f" padding:10px 18px; font-size:13px; font-weight:700; letter-spacing:0.5px; }}"
            f"QPushButton:hover {{ background:{theme.COLOR_EMBER}; }}"
        )
        lay.addWidget(save_btn)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"color:{theme.COLOR_KEEP}; font-size:11px; font-style:italic;"
        )
        lay.addWidget(self._status_label)
```

Ajouter la méthode `_save` dans la classe :

```python
    def _save(self) -> None:
        cfg = _load_config()
        cfg["lang"] = self._lang_combo.currentText()
        cfg.setdefault("swex", {})
        cfg["swex"]["drops_dir"] = self._drops_edit.text()
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        self._status_label.setText("Sauvegarde.")
```

- [ ] **Step 6.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_settings_page.py -v
```

Attendu : 11 tests PASS (les 8 existants + 3 nouveaux).

- [ ] **Step 6.5 : Commit**

```bash
git add ui/settings/settings_page.py tests/ui/test_settings_page.py
git commit -m "feat(settings): Save button writes language and drops_dir to config.json"
```

---

## Task 7 — Câbler `SettingsPage` dans `MainWindow` (remplacer le placeholder)

**Files:**
- Modify: `ui/main_window.py`
- Modify: `tests/ui/test_main_window_nav.py`

- [ ] **Step 7.1 : Écrire le test qui échoue**

Ajouter à la fin de `tests/ui/test_main_window_nav.py` :

```python
def test_settings_index_is_settings_page(qapp):
    from ui.settings.settings_page import SettingsPage
    mw = MainWindow()
    mw._on_nav("settings")
    current = mw._stack.currentWidget()
    assert isinstance(current, SettingsPage)
```

- [ ] **Step 7.2 : Lancer le test pour vérifier qu'il échoue**

```bash
pytest tests/ui/test_main_window_nav.py::test_settings_index_is_settings_page -v
```

Attendu : FAIL — `currentWidget()` est un `QLabel` (placeholder), pas `SettingsPage`.

- [ ] **Step 7.3 : Câbler SettingsPage dans MainWindow**

Dans `ui/main_window.py`, ajouter l'import en tête :

```python
from ui.settings.settings_page import SettingsPage
```

Dans `__init__`, remplacer la ligne :

```python
        self._stack.addWidget(_placeholder("Parametres - wiring dans Task 7"))
```

par :

```python
        self.settings_page = SettingsPage()
        self._stack.addWidget(self.settings_page)
```

- [ ] **Step 7.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_main_window_nav.py -v
```

Attendu : 4 tests PASS (les 3 existants + le nouveau).

- [ ] **Step 7.5 : Vérifier la suite complète**

```bash
pytest tests/ -v
```

Attendu : tous les tests passent, aucune régression (les tests legacy matplotlib peuvent être skipped s'ils existent, mais rien ne doit casser).

- [ ] **Step 7.6 : Commit**

```bash
git add ui/main_window.py tests/ui/test_main_window_nav.py
git commit -m "feat(main-window): wire SettingsPage at index 6 (settings key)"
```

---

## Task 8 — Test manuel de bout en bout (smoke test UI)

**Files:**
- Aucun fichier modifié (vérification visuelle uniquement)

- [ ] **Step 8.1 : Lancer l'application**

```bash
cd /c/Users/louis/Desktop/Luci2US
python scan_app.py
```

- [ ] **Step 8.2 : Vérifier la sidebar**

Checklist visuelle :
- La sidebar affiche 7 items dans l'ordre : Scan · Filtres · Runes · Monstres · Stats & Historique · Profils · Parametres.
- Cliquer sur chaque item change le contenu de la zone principale.
- L'item actif a la bordure gauche bronze + fond légèrement doré.

- [ ] **Step 8.3 : Vérifier les placeholders**

- `Filtres`, `Runes`, `Monstres`, `Stats & Historique` → affichent le texte placeholder « XXX - a implementer ».

- [ ] **Step 8.4 : Vérifier l'onglet Paramètres**

- Cliquer `Parametres` → voir le titre, le dropdown Langue (avec la valeur courante de `config.json`), le champ SWEX drops dir (pré-rempli), le bouton `Parcourir` et le bouton `Sauvegarder`.
- Changer la langue de FR à EN puis cliquer `Sauvegarder` → le message « Sauvegarde. » s'affiche en vert.
- Ouvrir `config.json` dans un éditeur externe → vérifier que `"lang": "EN"` a bien été écrit.
- Remettre la langue à FR et sauvegarder à nouveau.

- [ ] **Step 8.5 : Vérifier la non-régression du Scan**

- Cliquer `Scan` → la page Scan s'affiche correctement (header, compteurs à 0, historique vide, etc.).
- Cliquer `Profils` → la page Profils s'affiche correctement (le profil mis en cache est restauré si présent).

- [ ] **Step 8.6 : Si tout est bon, tag de fin de plan**

```bash
git tag plan-01-done
```

---

## Récapitulatif — ce que ce plan produit

À la fin de l'exécution :

1. **Sidebar** étendue à 7 items dans l'ordre final. ✓
2. **MainWindow** câble 7 pages dans son `QStackedWidget` (4 placeholders + Scan + Profil + Paramètres réel). ✓
3. **Onglet Paramètres** complet : Langue + SWEX drops dir + Save → `config.json`. ✓
4. **11 tests** Paramètres + **8 tests** Sidebar/MainWindow, tous passants. ✓
5. **Scan** et **Profil** fonctionnent sans régression. ✓
6. Aucune modification des modules core intouchables. ✓

L'app est **livrable dans cet état** : l'utilisateur a déjà une sidebar complète et un onglet Paramètres fonctionnel ; les 4 tabs restants (Filtres, Runes, Monstres, Stats & Historique) affichent un placeholder qui sera remplacé par les plans suivants.

**Prochain plan :** `Plan 02 — Monstres (liste + push page détail)`.
