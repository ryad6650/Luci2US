# Plan 04 — Onglet Stats & Historique Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le placeholder `Stats & Historique` (index 4) par une page fonctionnelle : toolbar de période partagée (`Aujourd'hui / 7j / 30j / Tout`) + `QTabWidget` interne à 2 sous-onglets. Sous-onglet **Stats** : grille 2×2 de cartes (VERDICT, GRADE, SESSIONS/JOUR, TOP RUNES). Sous-onglet **Historique** : liste des sessions (date, durée, total/keep/sell/power-up, eff moyenne) avec push page détail (mini-charts + table des runes scannées). Lecture passive depuis `history.db` via `history_db.py`.

**Architecture:** Nouveau sous-package `ui/stats_history/` suivant le pattern des autres onglets (`ui/scan/`, `ui/profile/`, `ui/settings/`, futur `ui/monsters/`, futur `ui/runes/`). `StatsHistoryPage` est un `QWidget` contenant : (a) un `_PeriodBar` en haut (4 boutons exclusifs) qui émet `period_changed(period_key)`, (b) un `QTabWidget` avec deux pages : `StatsView` et `HistoryView`. Chaque vue expose `refresh(start_iso, end_iso)` et se repeuple depuis `history.db`. Les charts sont rendus en **QPainter custom** (pas de matplotlib, pas de QtCharts) pour cohérence avec les widgets Scan existants (`verdict_bar.py`, `quality_bar.py`) et alignement stylistique v13. Une seule addition additive dans `history_db.py` : `get_sessions_with_stats()` (agrégation `power_up` + `avg_score` via LEFT JOIN). Aucun autre module bot core n'est modifié.

**Tech Stack:** PySide6 6.11.0, `QTabWidget`, `QStackedWidget` (interne Historique), `QPainter` custom, `sqlite3` via `history_db.py`, pytest-qt (`qapp`).

---

## File Structure

### Créer

| Chemin | Responsabilité |
|---|---|
| `ui/stats_history/__init__.py` | Package init vide |
| `ui/stats_history/period_bar.py` | `_PeriodBar` : 4 boutons exclusifs + signal `period_changed(str)` + helper `compute_period_range(key) -> (start_iso, end_iso)` |
| `ui/stats_history/stats_history_page.py` | `StatsHistoryPage` : orchestration (toolbar + QTabWidget Stats/Historique) |
| `ui/stats_history/stats_view.py` | `StatsView` : grille 2×2 de cartes avec 4 charts custom + `refresh(conn, start, end)` |
| `ui/stats_history/charts.py` | Widgets chart custom QPainter : `StackedBarChart`, `GradeBarChart`, `TimelineBarChart`, `TopRunesList` |
| `ui/stats_history/history_view.py` | `HistoryView` : QStackedWidget interne (liste sessions / détail session) + `refresh(conn, start, end)` |
| `ui/stats_history/session_list.py` | `SessionList` : scroll + lignes + signal `session_clicked(int)` |
| `ui/stats_history/session_detail.py` | `SessionDetail` : header + mini-charts Verdict/Grade + table runes + bouton Retour |
| `tests/ui/test_period_bar.py` | Tests `_PeriodBar` (boutons, signal, `compute_period_range`) |
| `tests/ui/test_stats_history_page.py` | Tests `StatsHistoryPage` (toolbar + QTabWidget + dispatch `refresh`) |
| `tests/ui/test_stats_view.py` | Tests `StatsView` (4 cartes, refresh depuis DB temporaire, no-data state) |
| `tests/ui/test_stats_charts.py` | Tests charts (données agrégées correctement, rendu sans crash) |
| `tests/ui/test_history_view.py` | Tests `HistoryView` (stack, navigation liste↔détail, refresh) |
| `tests/ui/test_session_list.py` | Tests `SessionList` (rendu, signal clic, eff moyenne, power-up count) |
| `tests/ui/test_session_detail.py` | Tests `SessionDetail` (header, table runes, bouton retour) |
| `tests/test_history_db_stats.py` | Tests pour la nouvelle fonction `get_sessions_with_stats` |

### Modifier

| Chemin | Changement |
|---|---|
| `history_db.py` | Ajouter **une seule fonction additive** `get_sessions_with_stats(conn, start, end, limit=200)` qui agrège `power_up_count` et `avg_score` via LEFT JOIN runes. Ne rien renommer, ne rien supprimer. |
| `ui/main_window.py` | Remplacer `_placeholder("Stats & Historique - a implementer")` (index 4) par `StatsHistoryPage()` réel. Pas de signal `profile_loaded` nécessaire (page passive sur `history.db`). |
| `tests/ui/test_main_window_nav.py` | Ajouter `test_stats_history_index_is_stats_history_page` |

### Ne pas toucher

- `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `swex_bridge.py`, `profile_loader.py`, `profile_store.py`, `models.py`, `monster_icons.py`
- Fonctions existantes de `history_db.py` (`init_db`, `save_session`, `save_rune`, `get_sessions`, `get_runes_by_session`, `get_stats_by_period`, `get_top_runes`) — aucune modification de signature ou de comportement
- `ui/sidebar.py`, `ui/scan/*`, `ui/profile/*`, `ui/widgets/*`, `ui/theme.py`, `ui/settings/*`, `ui/monsters/*` (si plan 02 livré), `ui/runes/*` (si plan 03 livré)
- Tabs legacy (`stats_tab.py`, `history_tab.py`, `auto_tab.py`, `profile_tab.py`, `settings_tab.py`)

---

## Task 1 — Helper `compute_period_range` + widget `_PeriodBar`

**Files:**
- Create: `ui/stats_history/__init__.py`
- Create: `ui/stats_history/period_bar.py`
- Create: `tests/ui/test_period_bar.py`

- [ ] **Step 1.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_period_bar.py` :

```python
from datetime import datetime

import pytest

from ui.stats_history.period_bar import (
    PeriodBar, compute_period_range, PERIOD_TODAY, PERIOD_7D, PERIOD_30D, PERIOD_ALL,
)


def test_period_keys_are_stable_constants():
    assert PERIOD_TODAY == "today"
    assert PERIOD_7D == "7d"
    assert PERIOD_30D == "30d"
    assert PERIOD_ALL == "all"


def test_compute_range_today():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_TODAY, now=now)
    assert start == "2026-04-18 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_7d_uses_rolling_window():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_7D, now=now)
    assert start == "2026-04-11 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_30d_uses_rolling_window():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_30D, now=now)
    assert start == "2026-03-19 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_all_uses_epoch():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_ALL, now=now)
    assert start == "2000-01-01 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_unknown_key_defaults_to_all():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range("garbage", now=now)
    assert start == "2000-01-01 00:00:00"


def test_period_bar_instantiates(qapp):
    bar = PeriodBar()
    assert bar is not None


def test_period_bar_has_4_buttons(qapp):
    from PySide6.QtWidgets import QPushButton
    bar = PeriodBar()
    btns = bar.findChildren(QPushButton)
    labels = [b.text() for b in btns]
    # Ordre attendu : Aujourd'hui / 7j / 30j / Tout
    assert "Aujourd'hui" in labels
    assert "7j" in labels
    assert "30j" in labels
    assert "Tout" in labels
    assert len(btns) == 4


def test_period_bar_default_selection_is_all(qapp):
    bar = PeriodBar()
    assert bar.current_period() == PERIOD_ALL


def test_period_bar_click_emits_signal(qapp):
    received: list[str] = []
    bar = PeriodBar()
    bar.period_changed.connect(received.append)
    bar._btn_7d.click()
    assert received == [PERIOD_7D]
    assert bar.current_period() == PERIOD_7D


def test_period_bar_buttons_are_exclusive(qapp):
    bar = PeriodBar()
    bar._btn_7d.click()
    assert bar._btn_7d.isChecked() is True
    bar._btn_30d.click()
    assert bar._btn_7d.isChecked() is False
    assert bar._btn_30d.isChecked() is True
```

- [ ] **Step 1.2 : Lancer le test pour vérifier qu'il échoue**

```bash
cd /c/Users/louis/Desktop/Luci2US
pytest tests/ui/test_period_bar.py -v
```

Attendu : FAIL avec `ModuleNotFoundError: No module named 'ui.stats_history'`.

- [ ] **Step 1.3 : Créer `ui/stats_history/__init__.py` (vide)**

Fichier vide.

- [ ] **Step 1.4 : Créer `ui/stats_history/period_bar.py`**

```python
"""Barre de periode partagee (Aujourd'hui / 7j / 30j / Tout) + helper compute_period_range."""
from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

from ui import theme

PERIOD_TODAY = "today"
PERIOD_7D = "7d"
PERIOD_30D = "30d"
PERIOD_ALL = "all"


def compute_period_range(
    key: str, *, now: datetime | None = None
) -> tuple[str, str]:
    """Retourne (start_iso, end_iso) format 'YYYY-MM-DD HH:MM:SS' pour la cle donnee.

    Cle inconnue -> equivalent PERIOD_ALL (debut = 2000-01-01).
    """
    if now is None:
        now = datetime.now()
    end = now.strftime("%Y-%m-%d 23:59:59")

    if key == PERIOD_TODAY:
        start = now.strftime("%Y-%m-%d 00:00:00")
    elif key == PERIOD_7D:
        start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
    elif key == PERIOD_30D:
        start = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    else:
        start = "2000-01-01 00:00:00"
    return start, end


class PeriodBar(QWidget):
    """4 boutons radio-like avec style bronze/or. Emet period_changed(key)."""

    period_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current = PERIOD_ALL

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lay.addStretch()

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self._btn_today = self._make_btn("Aujourd'hui", PERIOD_TODAY)
        self._btn_7d = self._make_btn("7j", PERIOD_7D)
        self._btn_30d = self._make_btn("30j", PERIOD_30D)
        self._btn_all = self._make_btn("Tout", PERIOD_ALL)

        for btn in (self._btn_today, self._btn_7d, self._btn_30d, self._btn_all):
            lay.addWidget(btn)
            self._group.addButton(btn)

        self._btn_all.setChecked(True)

    def _make_btn(self, label: str, period_key: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_SUB};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:4px 12px;"
            f" font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ color:{theme.COLOR_GOLD}; }}"
            f"QPushButton:checked {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD}; border:1px solid {theme.COLOR_BRONZE}; }}"
        )
        btn.clicked.connect(lambda _checked=False, k=period_key: self._on_clicked(k))
        return btn

    def _on_clicked(self, key: str) -> None:
        if self._current == key:
            return
        self._current = key
        self.period_changed.emit(key)

    def current_period(self) -> str:
        return self._current
```

- [ ] **Step 1.5 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_period_bar.py -v
```

Attendu : 10 tests PASS.

- [ ] **Step 1.6 : Commit**

```bash
git add ui/stats_history/__init__.py ui/stats_history/period_bar.py tests/ui/test_period_bar.py
git commit -m "feat(stats-history): PeriodBar widget + compute_period_range helper"
```

---

## Task 2 — Fonction additive `get_sessions_with_stats` dans `history_db.py`

**Files:**
- Modify: `history_db.py`
- Create: `tests/test_history_db_stats.py`

Rappel : le schema `sessions` ne contient pas `power_up_count` ni `avg_score`. Il faut les calculer via LEFT JOIN sur `runes`. Cette fonction remplace un besoin métier spécifique à la nouvelle UI, elle n'est pas utilisée par le legacy.

- [ ] **Step 2.1 : Écrire les tests qui échouent**

Créer `tests/test_history_db_stats.py` :

```python
from __future__ import annotations

import pytest

from history_db import (
    init_db, save_session, save_rune, get_sessions_with_stats,
)


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    yield c
    c.close()


def _populate(conn) -> None:
    # Session 1 : 2 runes KEEP + 1 POWER-UP, scores 80/90/None
    sid1 = save_session(
        conn, start_time="2026-04-18 09:00:00",
        end_time="2026-04-18 09:30:00",
        dungeon="Giant B10", total=3, keep=2, sell=0,
    )
    save_rune(conn, session_id=sid1, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legend", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=80.0)
    save_rune(conn, session_id=sid1, timestamp="2026-04-18 09:15:00",
              rune_set="Fatal", slot=4, stars=6, grade="Legend", level=12,
              main_stat="DC+64", verdict="KEEP", score=90.0)
    save_rune(conn, session_id=sid1, timestamp="2026-04-18 09:20:00",
              rune_set="Energy", slot=6, stars=6, grade="Heroique", level=0,
              main_stat="PV+2448", verdict="POWER-UP", score=None)

    # Session 2 : ancienne, hors periode 7j si ref = 2026-04-18
    sid2 = save_session(
        conn, start_time="2026-03-01 10:00:00",
        end_time="2026-03-01 10:30:00",
        dungeon="Dragon B10", total=1, keep=0, sell=1,
    )
    save_rune(conn, session_id=sid2, timestamp="2026-03-01 10:15:00",
              rune_set="Rage", slot=1, stars=5, grade="Rare", level=0,
              main_stat="ATQ+88", verdict="SELL", score=45.0)


def test_get_sessions_with_stats_returns_all_in_range(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59",
    )
    assert len(rows) == 2


def test_get_sessions_with_stats_filters_by_range(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    assert len(rows) == 1
    assert rows[0]["dungeon"] == "Giant B10"


def test_get_sessions_with_stats_returns_power_up_count(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    assert rows[0]["power_up"] == 1


def test_get_sessions_with_stats_returns_avg_score_ignoring_null(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    # moyenne de 80 et 90, le None etant ignore
    assert rows[0]["avg_score"] == pytest.approx(85.0, abs=0.01)


def test_get_sessions_with_stats_avg_score_null_when_no_scored_runes(conn):
    sid = save_session(
        conn, start_time="2026-04-18 09:00:00", total=0, keep=0, sell=0,
    )
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    assert rows[0]["avg_score"] is None


def test_get_sessions_with_stats_ordered_desc_by_id(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59",
    )
    # Session 1 inseree en premier mais plus recente temporellement → id plus petit mais start_time plus recent
    # Le contrat : ordre DESC par id (comme get_sessions)
    assert rows[0]["id"] > rows[1]["id"]


def test_get_sessions_with_stats_preserves_existing_columns(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59",
    )
    r = rows[0]
    # Toutes les colonnes originales de sessions doivent etre presentes
    for key in ("id", "start_time", "end_time", "dungeon", "total", "keep", "sell"):
        assert key in r


def test_get_sessions_with_stats_respects_limit(conn):
    for i in range(10):
        save_session(
            conn, start_time=f"2026-04-{i+1:02d} 09:00:00",
            total=0, keep=0, sell=0,
        )
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59", limit=3,
    )
    assert len(rows) == 3
```

- [ ] **Step 2.2 : Lancer pour voir FAIL**

```bash
pytest tests/test_history_db_stats.py -v
```

Attendu : FAIL sur `ImportError: cannot import name 'get_sessions_with_stats' from 'history_db'`.

- [ ] **Step 2.3 : Ajouter la fonction dans `history_db.py`**

Ajouter à la fin de `history_db.py`, **après** `get_top_runes` (sans rien modifier d'autre) :

```python
def get_sessions_with_stats(
    conn: sqlite3.Connection, *, start: str, end: str, limit: int = 200,
) -> list[dict]:
    """Retourne les sessions dans [start, end] avec power_up et avg_score agreges.

    - Colonnes sessions originales : id, start_time, end_time, dungeon, total, keep, sell.
    - Colonnes calculees :
        * power_up : nombre de runes avec verdict = 'POWER-UP' dans la session.
        * avg_score : moyenne des `score` non-null des runes de la session (None si aucun).
    - Ordre : DESC par id (plus recentes inserees en premier).
    """
    rows = conn.execute(
        "SELECT s.id, s.start_time, s.end_time, s.dungeon, "
        "       s.total, s.keep, s.sell, "
        "       COALESCE(SUM(CASE WHEN r.verdict = 'POWER-UP' THEN 1 ELSE 0 END), 0) "
        "           AS power_up, "
        "       AVG(r.score) AS avg_score "
        "FROM sessions s "
        "LEFT JOIN runes r ON r.session_id = s.id "
        "WHERE s.start_time >= ? AND s.start_time <= ? "
        "GROUP BY s.id "
        "ORDER BY s.id DESC "
        "LIMIT ?",
        (start, end, limit),
    ).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 2.4 : PASS**

```bash
pytest tests/test_history_db_stats.py -v
```

Attendu : 8 tests PASS.

- [ ] **Step 2.5 : Non-régression des tests existants**

```bash
pytest tests/ -v -x
```

Attendu : tous les tests préexistants continuent de passer (la fonction est strictement additive).

- [ ] **Step 2.6 : Commit**

```bash
git add history_db.py tests/test_history_db_stats.py
git commit -m "feat(history-db): additive get_sessions_with_stats aggregating power_up + avg_score"
```

---

## Task 3 — Squelette `StatsHistoryPage` (toolbar période + QTabWidget vides)

**Files:**
- Create: `ui/stats_history/stats_history_page.py`
- Create: `tests/ui/test_stats_history_page.py`

- [ ] **Step 3.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_stats_history_page.py` :

```python
from __future__ import annotations

from PySide6.QtWidgets import QTabWidget

from ui.stats_history.period_bar import PeriodBar, PERIOD_7D, PERIOD_ALL
from ui.stats_history.stats_history_page import StatsHistoryPage


def test_page_instantiates(qapp):
    p = StatsHistoryPage()
    assert p is not None


def test_page_has_period_bar(qapp):
    p = StatsHistoryPage()
    assert isinstance(p._period_bar, PeriodBar)


def test_page_has_tab_widget_with_2_tabs(qapp):
    p = StatsHistoryPage()
    assert isinstance(p._tabs, QTabWidget)
    assert p._tabs.count() == 2
    assert p._tabs.tabText(0) == "Stats"
    assert p._tabs.tabText(1) == "Historique"


def test_page_default_period_is_all(qapp):
    p = StatsHistoryPage()
    assert p._period_bar.current_period() == PERIOD_ALL


def test_period_change_triggers_dispatch(qapp, monkeypatch):
    p = StatsHistoryPage()
    calls: list[tuple[str, str]] = []

    def fake_stats_refresh(conn, start, end):
        calls.append(("stats", start))

    def fake_history_refresh(conn, start, end):
        calls.append(("history", start))

    monkeypatch.setattr(p._stats_view, "refresh", fake_stats_refresh)
    monkeypatch.setattr(p._history_view, "refresh", fake_history_refresh)

    p._period_bar._btn_7d.click()

    # Les 2 vues doivent etre rafraichies sur changement de periode
    assert ("stats", calls[0][1]) in calls
    assert ("history", calls[1][1]) in calls
    # Le start doit correspondre a 7j
    assert calls[0][1] != "2000-01-01 00:00:00"
```

- [ ] **Step 3.2 : FAIL**

```bash
pytest tests/ui/test_stats_history_page.py -v
```

Attendu : FAIL sur import ou attributs manquants.

- [ ] **Step 3.3 : Créer des stubs minimaux pour les vues**

Créer `ui/stats_history/stats_view.py` (stub temporaire — complet en Task 4/5) :

```python
"""Stub temporaire - complete en Task 4/5."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatsView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Stats - WIP"))

    def refresh(self, conn: sqlite3.Connection, start: str, end: str) -> None:
        pass
```

Créer `ui/stats_history/history_view.py` (stub temporaire — complet en Task 8/9/10) :

```python
"""Stub temporaire - complete en Task 8/9/10."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class HistoryView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Historique - WIP"))

    def refresh(self, conn: sqlite3.Connection, start: str, end: str) -> None:
        pass
```

- [ ] **Step 3.4 : Créer `ui/stats_history/stats_history_page.py`**

```python
"""Page Stats & Historique : toolbar periode partagee + QTabWidget (Stats / Historique)."""
from __future__ import annotations

import os
import sqlite3

from PySide6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from history_db import init_db
from ui import theme
from ui.stats_history.history_view import HistoryView
from ui.stats_history.period_bar import PeriodBar, compute_period_range
from ui.stats_history.stats_view import StatsView


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "history.db")


class StatsHistoryPage(QWidget):
    def __init__(
        self, parent: QWidget | None = None, db_path: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._conn: sqlite3.Connection = init_db(db_path or _DEFAULT_DB_PATH)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        # --- Header (titre + barre periode) ---
        header = QHBoxLayout()
        header.setSpacing(12)

        title = QLabel("Stats & Historique")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:20px; font-weight:700; letter-spacing:0.5px;"
        )
        header.addWidget(title)
        header.addStretch()

        self._period_bar = PeriodBar()
        self._period_bar.period_changed.connect(self._on_period_changed)
        header.addWidget(self._period_bar)

        outer.addLayout(header)

        # --- QTabWidget (Stats / Historique) ---
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            f"QTabWidget::pane {{ border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" background:{theme.COLOR_BG_FRAME}; }}"
            f"QTabBar::tab {{ background:{theme.COLOR_BG_GRAD_LO};"
            f" color:{theme.COLOR_TEXT_SUB}; padding:8px 24px;"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" font-size:12px; font-weight:600; }}"
            f"QTabBar::tab:selected {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD}; }}"
        )

        self._stats_view = StatsView()
        self._history_view = HistoryView()
        self._tabs.addTab(self._stats_view, "Stats")
        self._tabs.addTab(self._history_view, "Historique")
        outer.addWidget(self._tabs, 1)

        # Refresh initial avec periode par defaut (ALL)
        self._dispatch_refresh()

    def _on_period_changed(self, _key: str) -> None:
        self._dispatch_refresh()

    def _dispatch_refresh(self) -> None:
        start, end = compute_period_range(self._period_bar.current_period())
        self._stats_view.refresh(self._conn, start, end)
        self._history_view.refresh(self._conn, start, end)
```

- [ ] **Step 3.5 : PASS**

```bash
pytest tests/ui/test_stats_history_page.py -v
```

Attendu : 5 tests PASS.

- [ ] **Step 3.6 : Commit**

```bash
git add ui/stats_history/stats_history_page.py ui/stats_history/stats_view.py ui/stats_history/history_view.py tests/ui/test_stats_history_page.py
git commit -m "feat(stats-history): StatsHistoryPage shell (period bar + QTabWidget)"
```

---

## Task 4 — Widgets chart custom (`charts.py`) — agrégation + rendu QPainter

**Files:**
- Create: `ui/stats_history/charts.py`
- Create: `tests/ui/test_stats_charts.py`

Quatre widgets charts sont créés ici, tous dans le même fichier car ils partagent des helpers de rendu. Les tests valident l'agrégation (logique data) et l'absence de crash au rendu (QPainter).

- [ ] **Step 4.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_stats_charts.py` :

```python
from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, QPainter

from ui.stats_history.charts import (
    StackedBarChart, GradeBarChart, TimelineBarChart, TopRunesList,
)


def _render(widget) -> QPixmap:
    """Render widget dans un QPixmap pour forcer paintEvent et detecter les crashs."""
    widget.resize(QSize(320, 220))
    widget.show()
    pix = QPixmap(widget.size())
    pix.fill()
    widget.render(pix)
    return pix


# --- StackedBarChart (Verdict KEEP/SELL/POWER-UP) ---

def test_stacked_bar_stores_counts(qapp):
    c = StackedBarChart()
    c.set_counts({"KEEP": 30, "SELL": 60, "POWER-UP": 10})
    assert c._counts == {"KEEP": 30, "SELL": 60, "POWER-UP": 10}


def test_stacked_bar_empty_state_renders(qapp):
    c = StackedBarChart()
    c.set_counts({})
    pix = _render(c)
    assert not pix.isNull()


def test_stacked_bar_renders_without_crash(qapp):
    c = StackedBarChart()
    c.set_counts({"KEEP": 10, "SELL": 20, "POWER-UP": 5})
    pix = _render(c)
    assert not pix.isNull()


def test_stacked_bar_ignores_unknown_verdicts(qapp):
    c = StackedBarChart()
    c.set_counts({"KEEP": 5, "WTF": 99})
    # WTF ne doit pas planter
    pix = _render(c)
    assert not pix.isNull()


# --- GradeBarChart ---

def test_grade_bar_stores_counts_in_fixed_order(qapp):
    c = GradeBarChart()
    c.set_counts({"Legendaire": 4, "Heroique": 12, "Rare": 20, "Magique": 8})
    assert c._ordered[0][0] == "Legendaire"
    assert c._ordered[1][0] == "Heroique"
    assert c._ordered[2][0] == "Rare"
    assert c._ordered[3][0] == "Magique"


def test_grade_bar_renders(qapp):
    c = GradeBarChart()
    c.set_counts({"Legendaire": 4, "Heroique": 12, "Rare": 20, "Magique": 8})
    pix = _render(c)
    assert not pix.isNull()


def test_grade_bar_handles_missing_grades(qapp):
    c = GradeBarChart()
    c.set_counts({"Rare": 5})
    # Les autres grades ne doivent pas crasher le rendu
    pix = _render(c)
    assert not pix.isNull()


# --- TimelineBarChart (Sessions / jour) ---

def test_timeline_aggregates_sessions_by_day(qapp):
    c = TimelineBarChart()
    sessions = [
        {"start_time": "2026-04-18 09:00:00"},
        {"start_time": "2026-04-18 15:00:00"},
        {"start_time": "2026-04-17 10:00:00"},
    ]
    c.set_sessions(sessions)
    assert c._by_day["2026-04-18"] == 2
    assert c._by_day["2026-04-17"] == 1


def test_timeline_renders(qapp):
    c = TimelineBarChart()
    c.set_sessions([
        {"start_time": "2026-04-18 09:00:00"},
        {"start_time": "2026-04-17 10:00:00"},
    ])
    pix = _render(c)
    assert not pix.isNull()


def test_timeline_empty_sessions(qapp):
    c = TimelineBarChart()
    c.set_sessions([])
    pix = _render(c)
    assert not pix.isNull()


def test_timeline_handles_iso_T_format(qapp):
    c = TimelineBarChart()
    c.set_sessions([{"start_time": "2026-04-18T09:00:00"}])
    assert c._by_day["2026-04-18"] == 1


# --- TopRunesList (top 5 par score) ---

def test_top_runes_list_fills_rows(qapp):
    from PySide6.QtWidgets import QLabel
    tr = TopRunesList()
    tr.set_runes([
        {"set": "Violent", "slot": 2, "main_stat": "ATQ%+22", "score": 92.5},
        {"set": "Fatal", "slot": 4, "main_stat": "DC+64", "score": 87.0},
    ])
    texts = [l.text() for l in tr.findChildren(QLabel)]
    joined = " | ".join(texts)
    assert "Violent" in joined
    assert "92.5" in joined or "93" in joined
    assert "Fatal" in joined


def test_top_runes_list_caps_at_5(qapp):
    tr = TopRunesList()
    many = [
        {"set": "Violent", "slot": 1, "main_stat": "ATQ", "score": 100 - i}
        for i in range(10)
    ]
    tr.set_runes(many)
    assert len(tr._rows) == 5


def test_top_runes_list_empty_state(qapp):
    from PySide6.QtWidgets import QLabel
    tr = TopRunesList()
    tr.set_runes([])
    labels = [l.text() for l in tr.findChildren(QLabel)]
    # Placeholder "Aucune donnee" visible
    assert any("Aucune" in t or "—" in t for t in labels)
```

- [ ] **Step 4.2 : FAIL**

```bash
pytest tests/ui/test_stats_charts.py -v
```

Attendu : FAIL sur `ImportError: cannot import name 'StackedBarChart' from 'ui.stats_history.charts'`.

- [ ] **Step 4.3 : Créer `ui/stats_history/charts.py`**

```python
"""Charts custom (QPainter) pour StatsView et SessionDetail.

Quatre widgets :
  - StackedBarChart    : barre horizontale empilee KEEP / POWER-UP / SELL (verdicts).
  - GradeBarChart      : 4 barres verticales par grade.
  - TimelineBarChart   : barres verticales chronologiques (sessions par jour).
  - TopRunesList       : mini-liste texte des 5 meilleures runes (pas un chart peint).

Style aligne v13 : palette bronze/or + couleurs semantiques (COLOR_KEEP, COLOR_SELL, COLOR_POWERUP).
"""
from __future__ import annotations

from collections import OrderedDict

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui import theme


# ── Helpers ─────────────────────────────────────────────────────────

_VERDICT_ORDER = ("KEEP", "POWER-UP", "SELL")
_VERDICT_COLORS = {
    "KEEP": theme.COLOR_KEEP,
    "POWER-UP": theme.COLOR_POWERUP,
    "SELL": theme.COLOR_SELL,
}

_GRADE_ORDER = ("Legendaire", "Heroique", "Rare", "Magique")
_GRADE_COLORS = {
    "Legendaire": theme.COLOR_GRADE_LEGEND_B,
    "Heroique": theme.COLOR_GRADE_HERO_B,
    "Rare": "#3b82f6",
    "Magique": theme.COLOR_KEEP,
}


def _draw_empty(painter: QPainter, rect: QRectF, text: str = "Aucune donnee") -> None:
    painter.setPen(QColor(theme.COLOR_TEXT_DIM))
    painter.setFont(QFont(theme.FONT_UI, 10))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


# ── StackedBarChart (Verdict) ───────────────────────────────────────

class StackedBarChart(QWidget):
    """Barre horizontale empilee KEEP / POWER-UP / SELL avec legende."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._counts: dict[str, int] = {}
        self.setMinimumHeight(120)

    def set_counts(self, counts: dict[str, int]) -> None:
        self._counts = dict(counts)
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(16, 20, -16, -16))
        total = sum(self._counts.get(v, 0) for v in _VERDICT_ORDER)

        if total <= 0:
            _draw_empty(painter, rect)
            return

        # Titre
        painter.setPen(QColor(theme.COLOR_GOLD))
        painter.setFont(QFont(theme.FONT_UI, 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() - 16, rect.width(), 16),
            Qt.AlignmentFlag.AlignLeft, "VERDICT",
        )

        # Barre empilee (hauteur 32)
        bar_rect = QRectF(rect.x(), rect.y() + 8, rect.width(), 32)
        painter.setPen(Qt.PenStyle.NoPen)
        x = bar_rect.x()
        for verdict in _VERDICT_ORDER:
            n = self._counts.get(verdict, 0)
            if n <= 0:
                continue
            w = bar_rect.width() * (n / total)
            painter.setBrush(QBrush(QColor(_VERDICT_COLORS[verdict])))
            painter.drawRect(QRectF(x, bar_rect.y(), w, bar_rect.height()))
            x += w

        # Legende (3 items sous la barre)
        legend_y = bar_rect.bottom() + 18
        painter.setFont(QFont(theme.FONT_UI, 9))
        slot_w = rect.width() / 3
        for i, verdict in enumerate(_VERDICT_ORDER):
            slot_x = rect.x() + i * slot_w
            painter.setBrush(QBrush(QColor(_VERDICT_COLORS[verdict])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(slot_x, legend_y, 10, 10))

            painter.setPen(QColor(theme.COLOR_TEXT_MAIN))
            n = self._counts.get(verdict, 0)
            painter.drawText(
                QRectF(slot_x + 14, legend_y - 2, slot_w - 14, 14),
                Qt.AlignmentFlag.AlignLeft,
                f"{verdict}  {n}",
            )


# ── GradeBarChart ───────────────────────────────────────────────────

class GradeBarChart(QWidget):
    """4 barres verticales par grade (Legendaire / Heroique / Rare / Magique)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ordered: list[tuple[str, int]] = []
        self.setMinimumHeight(160)

    def set_counts(self, counts: dict[str, int]) -> None:
        self._ordered = [(g, counts.get(g, 0)) for g in _GRADE_ORDER]
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(16, 20, -16, -20))

        # Titre
        painter.setPen(QColor(theme.COLOR_GOLD))
        painter.setFont(QFont(theme.FONT_UI, 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() - 16, rect.width(), 16),
            Qt.AlignmentFlag.AlignLeft, "GRADE",
        )

        max_val = max((n for _, n in self._ordered), default=0)
        if max_val <= 0:
            _draw_empty(painter, rect)
            return

        col_w = rect.width() / len(self._ordered)
        base_y = rect.bottom() - 24  # reserve pour label grade
        chart_h = base_y - rect.y() - 14  # reserve pour label valeur

        painter.setPen(Qt.PenStyle.NoPen)
        for i, (grade, n) in enumerate(self._ordered):
            bar_h = chart_h * (n / max_val) if n > 0 else 0
            bar_x = rect.x() + i * col_w + col_w * 0.2
            bar_w = col_w * 0.6
            bar_y = base_y - bar_h
            color = QColor(_GRADE_COLORS.get(grade, theme.COLOR_BRONZE))
            painter.setBrush(QBrush(color))
            painter.drawRect(QRectF(bar_x, bar_y, bar_w, bar_h))

            # Valeur au-dessus
            painter.setPen(QColor(theme.COLOR_TEXT_MAIN))
            painter.setFont(QFont(theme.FONT_UI, 9, QFont.Weight.Bold))
            painter.drawText(
                QRectF(bar_x, bar_y - 14, bar_w, 14),
                Qt.AlignmentFlag.AlignCenter, str(n),
            )
            painter.setPen(Qt.PenStyle.NoPen)

            # Label grade
            painter.setPen(QColor(theme.COLOR_TEXT_DIM))
            painter.setFont(QFont(theme.FONT_UI, 8))
            painter.drawText(
                QRectF(rect.x() + i * col_w, base_y + 4, col_w, 20),
                Qt.AlignmentFlag.AlignCenter, grade[:4],
            )
            painter.setPen(Qt.PenStyle.NoPen)


# ── TimelineBarChart (Sessions / jour) ──────────────────────────────

class TimelineBarChart(QWidget):
    """Barres verticales chronologiques : 1 barre par jour."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._by_day: "OrderedDict[str, int]" = OrderedDict()
        self.setMinimumHeight(160)

    def set_sessions(self, sessions: list[dict]) -> None:
        by_day: dict[str, int] = {}
        for s in sessions:
            st = s.get("start_time", "")
            if not st:
                continue
            # Normalise 'YYYY-MM-DD HH:...' ou 'YYYY-MM-DDTHH:...'
            day = st.replace("T", " ")[:10]
            if not day:
                continue
            by_day[day] = by_day.get(day, 0) + 1
        self._by_day = OrderedDict(sorted(by_day.items()))
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(16, 20, -16, -20))

        painter.setPen(QColor(theme.COLOR_GOLD))
        painter.setFont(QFont(theme.FONT_UI, 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() - 16, rect.width(), 16),
            Qt.AlignmentFlag.AlignLeft, "SESSIONS / JOUR",
        )

        if not self._by_day:
            _draw_empty(painter, rect)
            return

        values = list(self._by_day.values())
        max_val = max(values)
        n_cols = len(values)
        col_w = rect.width() / n_cols
        base_y = rect.bottom() - 18
        chart_h = base_y - rect.y() - 4

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(theme.COLOR_BRONZE)))
        for i, (day, n) in enumerate(self._by_day.items()):
            bar_h = chart_h * (n / max_val) if max_val else 0
            bar_x = rect.x() + i * col_w + col_w * 0.15
            bar_w = col_w * 0.7
            bar_y = base_y - bar_h
            painter.drawRect(QRectF(bar_x, bar_y, bar_w, bar_h))

        # Label debut / fin
        painter.setPen(QColor(theme.COLOR_TEXT_DIM))
        painter.setFont(QFont(theme.FONT_UI, 8))
        first_day = next(iter(self._by_day))
        last_day = list(self._by_day)[-1]
        painter.drawText(
            QRectF(rect.x(), base_y + 2, rect.width() / 2, 14),
            Qt.AlignmentFlag.AlignLeft, first_day,
        )
        painter.drawText(
            QRectF(rect.x() + rect.width() / 2, base_y + 2, rect.width() / 2, 14),
            Qt.AlignmentFlag.AlignRight, last_day,
        )


# ── TopRunesList ────────────────────────────────────────────────────

class TopRunesList(QFrame):
    """Top 5 runes par score. Liste de QLabel, pas un chart peint."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[QWidget] = []
        self.setMinimumHeight(160)
        self.setStyleSheet(
            f"QFrame {{ background:transparent; border:none; }}"
        )

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(16, 20, 16, 16)
        self._lay.setSpacing(4)

        self._title = QLabel("TOP RUNES")
        self._title.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:10px; font-weight:700;"
            f" letter-spacing:1px;"
        )
        self._lay.addWidget(self._title)

        self._empty = QLabel("Aucune donnee")
        self._empty.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-style:italic;"
        )
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lay.addWidget(self._empty)
        self._lay.addStretch()

    def set_runes(self, runes: list[dict]) -> None:
        # Purge rows existants
        for w in self._rows:
            w.setParent(None)
            w.deleteLater()
        self._rows.clear()

        top = sorted(
            [r for r in runes if r.get("score") is not None],
            key=lambda r: r["score"], reverse=True,
        )[:5]

        self._empty.setVisible(not top)

        # Insere avant le stretch final
        stretch_index = self._lay.count() - 1
        for rune in top:
            row = self._make_row(rune)
            self._rows.append(row)
            self._lay.insertWidget(stretch_index, row)
            stretch_index += 1

    def _make_row(self, rune: dict) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(8)

        name = QLabel(f"{rune.get('set', '?')} · Slot {rune.get('slot', '?')}")
        name.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:11px; font-weight:600;"
        )
        h.addWidget(name, 1)

        main = QLabel(str(rune.get("main_stat", "")))
        main.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px;"
        )
        h.addWidget(main)

        score_val = rune.get("score", 0)
        score = QLabel(f"{float(score_val):.1f}")
        score.setStyleSheet(
            f"color:{theme.COLOR_KEEP}; font-size:11px; font-weight:700;"
        )
        h.addWidget(score)
        return w
```

- [ ] **Step 4.4 : PASS**

```bash
pytest tests/ui/test_stats_charts.py -v
```

Attendu : 13 tests PASS.

- [ ] **Step 4.5 : Commit**

```bash
git add ui/stats_history/charts.py tests/ui/test_stats_charts.py
git commit -m "feat(stats-history): custom QPainter charts (stacked/grade/timeline/top-runes)"
```

---

## Task 5 — `StatsView` : grille 2×2 de cartes + refresh depuis DB

**Files:**
- Modify: `ui/stats_history/stats_view.py`
- Create: `tests/ui/test_stats_view.py`

- [ ] **Step 5.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_stats_view.py` :

```python
from __future__ import annotations

import pytest

from history_db import init_db, save_session, save_rune
from ui.stats_history.charts import (
    StackedBarChart, GradeBarChart, TimelineBarChart, TopRunesList,
)
from ui.stats_history.stats_view import StatsView


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    # 3 sessions, 5 runes avec variete de verdicts/grades/scores
    sid1 = save_session(c, start_time="2026-04-18 09:00:00", total=2, keep=2, sell=0)
    save_rune(c, session_id=sid1, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=92.5)
    save_rune(c, session_id=sid1, timestamp="2026-04-18 09:15:00",
              rune_set="Fatal", slot=4, stars=6, grade="Heroique", level=12,
              main_stat="DC+64", verdict="KEEP", score=87.0)

    sid2 = save_session(c, start_time="2026-04-17 10:00:00", total=2, keep=0, sell=1)
    save_rune(c, session_id=sid2, timestamp="2026-04-17 10:05:00",
              rune_set="Rage", slot=1, stars=5, grade="Rare", level=0,
              main_stat="ATQ+88", verdict="SELL", score=45.0)
    save_rune(c, session_id=sid2, timestamp="2026-04-17 10:10:00",
              rune_set="Energy", slot=6, stars=6, grade="Heroique", level=0,
              main_stat="PV+2448", verdict="POWER-UP", score=None)

    yield c
    c.close()


def test_stats_view_instantiates(qapp):
    v = StatsView()
    assert v is not None


def test_stats_view_contains_4_charts(qapp):
    v = StatsView()
    assert isinstance(v._verdict_chart, StackedBarChart)
    assert isinstance(v._grade_chart, GradeBarChart)
    assert isinstance(v._timeline_chart, TimelineBarChart)
    assert isinstance(v._top_runes, TopRunesList)


def test_refresh_populates_verdict_chart(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert v._verdict_chart._counts == {"KEEP": 2, "POWER-UP": 1, "SELL": 1}


def test_refresh_populates_grade_chart(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    counts = dict(v._grade_chart._ordered)
    assert counts["Legendaire"] == 1
    assert counts["Heroique"] == 2
    assert counts["Rare"] == 1
    assert counts["Magique"] == 0


def test_refresh_populates_timeline_chart(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert v._timeline_chart._by_day["2026-04-18"] == 1
    assert v._timeline_chart._by_day["2026-04-17"] == 1


def test_refresh_populates_top_runes(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert len(v._top_runes._rows) == 3  # 92.5, 87.0, 45.0 (None ignore)


def test_refresh_filters_by_period(qapp, conn):
    v = StatsView()
    # Fenetre serree sur 2026-04-18 uniquement
    v.refresh(conn, "2026-04-18 00:00:00", "2026-04-18 23:59:59")
    assert v._verdict_chart._counts.get("SELL", 0) == 0  # session du 17 exclue
    assert v._verdict_chart._counts.get("KEEP", 0) == 2


def test_refresh_empty_period_leaves_empty_charts(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2025-01-01 00:00:00", "2025-01-31 00:00:00")
    assert v._verdict_chart._counts == {}
    assert all(n == 0 for _, n in v._grade_chart._ordered)
    assert len(v._top_runes._rows) == 0
```

- [ ] **Step 5.2 : FAIL**

```bash
pytest tests/ui/test_stats_view.py -v
```

Attendu : FAIL sur `AttributeError: '_verdict_chart'`.

- [ ] **Step 5.3 : Remplacer complètement `ui/stats_history/stats_view.py`**

```python
"""Sous-onglet Stats : grille 2x2 de 4 cartes (Verdict / Grade / Sessions-jour / Top runes)."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QFrame, QGridLayout, QVBoxLayout, QWidget

from ui import theme
from ui.stats_history.charts import (
    GradeBarChart, StackedBarChart, TimelineBarChart, TopRunesList,
)


def _card_frame() -> QFrame:
    """Cartouche bronze/or qui encadre un chart."""
    card = QFrame()
    card.setStyleSheet(
        f"QFrame {{ background:rgba(26,15,7,0.7);"
        f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
    )
    return card


class StatsView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 12, 0, 0)
        outer.setSpacing(0)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(12)

        # 4 cartes (row, col)
        self._verdict_chart = StackedBarChart()
        self._grade_chart = GradeBarChart()
        self._timeline_chart = TimelineBarChart()
        self._top_runes = TopRunesList()

        placements = [
            (self._verdict_chart, 0, 0),
            (self._grade_chart, 0, 1),
            (self._timeline_chart, 1, 0),
            (self._top_runes, 1, 1),
        ]
        for widget, row, col in placements:
            card = _card_frame()
            inner = QVBoxLayout(card)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(widget)
            grid.addWidget(card, row, col)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid, 1)

    def refresh(self, conn: sqlite3.Connection, start: str, end: str) -> None:
        # Recupere toutes les runes de la periode (avec session pour timeline)
        runes = conn.execute(
            'SELECT r."set", r.slot, r.stars, r.grade, r.verdict, '
            "       r.main_stat, r.score "
            "FROM runes r JOIN sessions s ON r.session_id = s.id "
            "WHERE s.start_time >= ? AND s.start_time <= ? "
            "ORDER BY r.id",
            (start, end),
        ).fetchall()
        runes = [dict(r) for r in runes]

        sessions = conn.execute(
            "SELECT start_time FROM sessions "
            "WHERE start_time >= ? AND start_time <= ?",
            (start, end),
        ).fetchall()
        sessions = [dict(s) for s in sessions]

        # Agreger verdicts
        verdict_counts: dict[str, int] = {}
        for r in runes:
            v = r["verdict"]
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
        self._verdict_chart.set_counts(verdict_counts)

        # Agreger grades
        grade_counts: dict[str, int] = {}
        for r in runes:
            g = r["grade"]
            grade_counts[g] = grade_counts.get(g, 0) + 1
        self._grade_chart.set_counts(grade_counts)

        # Timeline sessions/jour
        self._timeline_chart.set_sessions(sessions)

        # Top runes
        self._top_runes.set_runes(runes)
```

- [ ] **Step 5.4 : PASS**

```bash
pytest tests/ui/test_stats_view.py tests/ui/test_stats_charts.py tests/ui/test_stats_history_page.py -v
```

Attendu : 26 tests PASS (8 stats_view + 13 charts + 5 page).

- [ ] **Step 5.5 : Commit**

```bash
git add ui/stats_history/stats_view.py tests/ui/test_stats_view.py
git commit -m "feat(stats-history): StatsView 2x2 grid of charts with DB-backed refresh"
```

---

## Task 6 — `SessionList` : lignes de sessions (date / durée / total / keep / sell / power-up / eff moyenne)

**Files:**
- Create: `ui/stats_history/session_list.py`
- Create: `tests/ui/test_session_list.py`

- [ ] **Step 6.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_session_list.py` :

```python
from __future__ import annotations

from PySide6.QtWidgets import QLabel

from ui.stats_history.session_list import SessionList, format_duration


def test_format_duration_hms():
    assert format_duration("2026-04-18 09:00:00", "2026-04-18 09:30:15") == "30m15s"
    assert format_duration("2026-04-18 09:00:00", "2026-04-18 10:05:00") == "1h05m"


def test_format_duration_missing_returns_dash():
    assert format_duration(None, None) == "—"
    assert format_duration("2026-04-18 09:00:00", None) == "—"
    assert format_duration(None, "2026-04-18 09:30:00") == "—"


def test_format_duration_negative_returns_dash():
    assert format_duration("2026-04-18 10:00:00", "2026-04-18 09:00:00") == "—"


def test_format_duration_handles_T_separator():
    assert format_duration("2026-04-18T09:00:00", "2026-04-18T09:30:15") == "30m15s"


def test_session_list_instantiates(qapp):
    sl = SessionList()
    assert sl is not None


def test_set_sessions_creates_one_row_per_session(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": "2026-04-18 09:30:00",
         "dungeon": "Giant B10", "total": 3, "keep": 2, "sell": 0,
         "power_up": 1, "avg_score": 85.0},
        {"id": 2, "start_time": "2026-04-17 10:00:00", "end_time": "2026-04-17 10:30:00",
         "dungeon": "Dragon B10", "total": 1, "keep": 0, "sell": 1,
         "power_up": 0, "avg_score": 45.0},
    ])
    assert len(sl._rows) == 2


def test_row_shows_dungeon_and_counts(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": "2026-04-18 09:30:00",
         "dungeon": "Giant B10", "total": 3, "keep": 2, "sell": 1,
         "power_up": 1, "avg_score": 85.0},
    ])
    row = sl._rows[0]
    texts = " | ".join(l.text() for l in row.findChildren(QLabel))
    assert "Giant B10" in texts
    assert "3" in texts  # total
    assert "85" in texts or "85.0" in texts  # avg_score


def test_row_shows_dash_when_avg_score_none(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": None,
         "dungeon": "", "total": 0, "keep": 0, "sell": 0,
         "power_up": 0, "avg_score": None},
    ])
    row = sl._rows[0]
    texts = " | ".join(l.text() for l in row.findChildren(QLabel))
    assert "—" in texts


def test_click_emits_session_id(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPointF

    received: list[int] = []
    sl = SessionList()
    sl.session_clicked.connect(received.append)
    sl.set_sessions([
        {"id": 42, "start_time": "2026-04-18 09:00:00", "end_time": "2026-04-18 09:30:00",
         "dungeon": "Giant B10", "total": 3, "keep": 2, "sell": 0,
         "power_up": 1, "avg_score": 85.0},
    ])
    row = sl._rows[0]
    ev = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress, QPointF(10, 10), QPointF(10, 10),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    row.mousePressEvent(ev)
    assert received == [42]


def test_set_sessions_clears_previous(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": None,
         "dungeon": "", "total": 0, "keep": 0, "sell": 0, "power_up": 0, "avg_score": None},
    ])
    sl.set_sessions([])
    assert len(sl._rows) == 0


def test_empty_list_shows_placeholder(qapp):
    sl = SessionList()
    sl.set_sessions([])
    # Placeholder visible (QLabel avec "Aucune" ou assimilable)
    labels = [l.text() for l in sl.findChildren(QLabel)]
    assert any("Aucune" in t for t in labels)
```

- [ ] **Step 6.2 : FAIL**

```bash
pytest tests/ui/test_session_list.py -v
```

Attendu : FAIL sur `ModuleNotFoundError: No module named 'ui.stats_history.session_list'`.

- [ ] **Step 6.3 : Créer `ui/stats_history/session_list.py`**

```python
"""Liste scrollable des sessions. Chaque ligne est cliquable."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ui import theme


def format_duration(start: str | None, end: str | None) -> str:
    if not start or not end:
        return "—"
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        s = start.replace("T", " ")[:19]
        e = end.replace("T", " ")[:19]
        delta = datetime.strptime(e, fmt) - datetime.strptime(s, fmt)
        total_sec = int(delta.total_seconds())
        if total_sec < 0:
            return "—"
        h, rem = divmod(total_sec, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h{m:02d}m"
        return f"{m}m{s:02d}s"
    except (ValueError, TypeError):
        return "—"


class _SessionRow(QFrame):
    clicked = Signal(int)

    def __init__(self, session: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session_id = int(session["id"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"_SessionRow {{ background:rgba(26,15,7,0.6);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
            f"_SessionRow:hover {{ background:rgba(198,112,50,0.2);"
            f" border:1px solid {theme.COLOR_BRONZE}; }}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        start = str(session.get("start_time") or "")
        date_str = start.replace("T", " ")[:16] if start else "—"

        date_lbl = QLabel(date_str)
        date_lbl.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:12px; font-weight:600;"
        )
        date_lbl.setMinimumWidth(130)
        row.addWidget(date_lbl)

        dungeon = session.get("dungeon") or "—"
        dungeon_lbl = QLabel(dungeon)
        dungeon_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:12px;"
        )
        dungeon_lbl.setMinimumWidth(140)
        row.addWidget(dungeon_lbl)

        duration = format_duration(session.get("start_time"), session.get("end_time"))
        dur_lbl = QLabel(duration)
        dur_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:12px;"
        )
        dur_lbl.setMinimumWidth(60)
        row.addWidget(dur_lbl)

        row.addStretch()

        # Compteurs colores
        for label, value, color in (
            ("Scan", session.get("total", 0), theme.COLOR_TEXT_MAIN),
            ("Keep", session.get("keep", 0), theme.COLOR_KEEP),
            ("Sell", session.get("sell", 0), theme.COLOR_SELL),
            ("PwrUp", session.get("power_up", 0), theme.COLOR_POWERUP),
        ):
            lbl = QLabel(f"{label} {value}")
            lbl.setStyleSheet(
                f"color:{color}; font-size:11px; font-weight:600;"
            )
            row.addWidget(lbl)

        avg = session.get("avg_score")
        if avg is None:
            eff_text = "Eff —"
        else:
            eff_text = f"Eff {float(avg):.1f}"
        eff_lbl = QLabel(eff_text)
        eff_lbl.setStyleSheet(
            f"color:{theme.COLOR_BRONZE_LIGHT}; font-size:12px; font-weight:700;"
        )
        eff_lbl.setMinimumWidth(80)
        row.addWidget(eff_lbl)

        chevron = QLabel("\u25B6")  # ▶
        chevron.setStyleSheet(f"color:{theme.COLOR_BRONZE}; font-size:12px;")
        row.addWidget(chevron)

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._session_id)
        super().mousePressEvent(ev)


class SessionList(QWidget):
    session_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[_SessionRow] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._container = QWidget()
        self._lay = QVBoxLayout(self._container)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(4)
        self._lay.addStretch()

        self._scroll.setWidget(self._container)
        outer.addWidget(self._scroll)

        self._empty = QLabel("Aucune session pour cette periode.")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:13px; font-style:italic;"
            f" padding:24px;"
        )
        outer.addWidget(self._empty)
        self._empty.setVisible(True)

    def set_sessions(self, sessions: list[dict]) -> None:
        # Purge rows
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        # Empty state
        self._empty.setVisible(not sessions)
        self._scroll.setVisible(bool(sessions))

        stretch_index = self._lay.count() - 1
        for session in sessions:
            row = _SessionRow(session)
            row.clicked.connect(self.session_clicked.emit)
            self._rows.append(row)
            self._lay.insertWidget(stretch_index, row)
            stretch_index += 1
```

- [ ] **Step 6.4 : PASS**

```bash
pytest tests/ui/test_session_list.py -v
```

Attendu : 11 tests PASS.

- [ ] **Step 6.5 : Commit**

```bash
git add ui/stats_history/session_list.py tests/ui/test_session_list.py
git commit -m "feat(stats-history): SessionList with click-to-detail signal"
```

---

## Task 7 — `SessionDetail` : header + mini-charts + table runes + bouton Retour

**Files:**
- Create: `ui/stats_history/session_detail.py`
- Create: `tests/ui/test_session_detail.py`

- [ ] **Step 7.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_session_detail.py` :

```python
from __future__ import annotations

import pytest

from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget

from history_db import init_db, save_session, save_rune
from ui.stats_history.session_detail import SessionDetail


@pytest.fixture
def conn_with_session(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    sid = save_session(
        c, start_time="2026-04-18 09:00:00", end_time="2026-04-18 09:30:00",
        dungeon="Giant B10", total=3, keep=2, sell=0,
    )
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=92.5, reason="eff>80")
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:15:00",
              rune_set="Fatal", slot=4, stars=6, grade="Heroique", level=12,
              main_stat="DC+64", verdict="KEEP", score=87.0)
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:20:00",
              rune_set="Energy", slot=6, stars=6, grade="Heroique", level=0,
              main_stat="PV+2448", verdict="POWER-UP", score=None)
    yield c, sid
    c.close()


def test_detail_instantiates(qapp):
    d = SessionDetail()
    assert d is not None


def test_detail_has_back_button(qapp):
    d = SessionDetail()
    btns = [b for b in d.findChildren(QPushButton) if "Retour" in b.text()]
    assert len(btns) == 1


def test_back_button_emits_signal(qapp):
    d = SessionDetail()
    received: list = []
    d.back_clicked.connect(lambda: received.append(1))
    btns = [b for b in d.findChildren(QPushButton) if "Retour" in b.text()]
    btns[0].click()
    assert received == [1]


def test_load_session_fills_header(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    texts = " | ".join(l.text() for l in d.findChildren(QLabel))
    assert "Giant B10" in texts
    assert "2026-04-18" in texts


def test_load_session_populates_runes_table(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    table = d.findChild(QTableWidget)
    assert table is not None
    assert table.rowCount() == 3


def test_load_session_table_has_expected_columns(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    table = d.findChild(QTableWidget)
    headers = [
        table.horizontalHeaderItem(i).text()
        for i in range(table.columnCount())
    ]
    for expected in ("Set", "Slot", "Grade", "Main", "Eff", "Verdict"):
        assert expected in headers


def test_load_session_fills_mini_charts(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    # Verdict : KEEP=2, POWER-UP=1
    assert d._verdict_chart._counts == {"KEEP": 2, "POWER-UP": 1}
    # Grade : Legendaire=1, Heroique=2
    counts = dict(d._grade_chart._ordered)
    assert counts["Legendaire"] == 1
    assert counts["Heroique"] == 2


def test_load_session_unknown_id_empty_table(qapp, conn_with_session):
    conn, _sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, 99999)
    table = d.findChild(QTableWidget)
    assert table.rowCount() == 0


def test_load_session_empty_score_shows_dash(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    table = d.findChild(QTableWidget)
    # Chercher la ligne POWER-UP (score None)
    for r in range(table.rowCount()):
        verdict = table.item(r, 5).text()
        if verdict == "POWER-UP":
            eff_cell = table.item(r, 4).text()
            assert eff_cell == "—"
            return
    pytest.fail("POWER-UP row not found")
```

- [ ] **Step 7.2 : FAIL**

```bash
pytest tests/ui/test_session_detail.py -v
```

- [ ] **Step 7.3 : Créer `ui/stats_history/session_detail.py`**

```python
"""Vue detail d'une session : breadcrumb + mini-charts Verdict/Grade + table des runes."""
from __future__ import annotations

import json
import sqlite3

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from history_db import get_runes_by_session
from ui import theme
from ui.stats_history.charts import GradeBarChart, StackedBarChart
from ui.stats_history.session_list import format_duration


_COLS = ["Set", "Slot", "Etoiles", "Grade", "Main", "Eff", "Verdict"]


class SessionDetail(QWidget):
    back_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        # --- Breadcrumb ---
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

        self._crumb = QLabel("Historique /")
        self._crumb.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:13px;"
        )
        crumb.addWidget(self._crumb)
        crumb.addStretch()
        outer.addLayout(crumb)

        # --- Header compact (date + durée + compteurs) ---
        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background:rgba(26,15,7,0.8);"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(14, 10, 14, 10)
        h_lay.setSpacing(16)

        self._title_lbl = QLabel("")
        self._title_lbl.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:15px; font-weight:700;"
        )
        h_lay.addWidget(self._title_lbl)
        h_lay.addStretch()

        self._meta_lbl = QLabel("")
        self._meta_lbl.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:12px;"
        )
        h_lay.addWidget(self._meta_lbl)

        outer.addWidget(header)

        # --- Mini-charts (row horizontal) ---
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        self._verdict_chart = StackedBarChart()
        self._grade_chart = GradeBarChart()
        for chart in (self._verdict_chart, self._grade_chart):
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background:rgba(26,15,7,0.7);"
                f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
            )
            inner = QVBoxLayout(card)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(chart)
            charts_row.addWidget(card, 1)

        outer.addLayout(charts_row)

        # --- Table des runes ---
        self._table = QTableWidget(0, len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setStyleSheet(
            f"QTableWidget {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" gridline-color:{theme.COLOR_BORDER_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; font-size:11px; }}"
            f"QHeaderView::section {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" padding:4px; font-size:11px; font-weight:700; }}"
        )
        outer.addWidget(self._table, 1)

    def load_session(self, conn: sqlite3.Connection, session_id: int) -> None:
        """Charge le header + charts + table pour la session donnee."""
        session_row = conn.execute(
            "SELECT id, start_time, end_time, dungeon, total, keep, sell "
            "FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if session_row is None:
            self._title_lbl.setText("Session introuvable")
            self._meta_lbl.setText("")
            self._crumb.setText("Historique /")
            self._verdict_chart.set_counts({})
            self._grade_chart.set_counts({})
            self._table.setRowCount(0)
            return

        session = dict(session_row)

        # Header
        start = session.get("start_time") or ""
        date_str = start.replace("T", " ")[:16]
        dungeon = session.get("dungeon") or "—"
        self._title_lbl.setText(f"{dungeon} — {date_str}")
        self._crumb.setText(f"Historique / {dungeon}")

        duration = format_duration(session.get("start_time"), session.get("end_time"))
        self._meta_lbl.setText(
            f"Scan {session.get('total', 0)} · "
            f"Keep {session.get('keep', 0)} · "
            f"Sell {session.get('sell', 0)} · "
            f"Duree {duration}"
        )

        # Runes
        runes = get_runes_by_session(conn, session_id)

        verdict_counts: dict[str, int] = {}
        grade_counts: dict[str, int] = {}
        for r in runes:
            verdict_counts[r["verdict"]] = verdict_counts.get(r["verdict"], 0) + 1
            grade_counts[r["grade"]] = grade_counts.get(r["grade"], 0) + 1
        self._verdict_chart.set_counts(verdict_counts)
        self._grade_chart.set_counts(grade_counts)

        self._populate_table(runes)

    def _populate_table(self, runes: list[dict]) -> None:
        self._table.setRowCount(0)
        for r in runes:
            row = self._table.rowCount()
            self._table.insertRow(row)

            score = r.get("score")
            eff_text = f"{float(score):.1f}" if score is not None else "—"

            cells = [
                r.get("set", ""),
                str(r.get("slot", "")),
                str(r.get("stars", "")),
                r.get("grade", ""),
                r.get("main_stat", ""),
                eff_text,
                r.get("verdict", ""),
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Couleur verdict
                if col == 6:
                    if val == "KEEP":
                        item.setForeground(QColor(theme.COLOR_KEEP))
                    elif val == "SELL":
                        item.setForeground(QColor(theme.COLOR_SELL))
                    elif val == "POWER-UP":
                        item.setForeground(QColor(theme.COLOR_POWERUP))
                self._table.setItem(row, col, item)
```

- [ ] **Step 7.4 : PASS**

```bash
pytest tests/ui/test_session_detail.py -v
```

Attendu : 9 tests PASS.

- [ ] **Step 7.5 : Commit**

```bash
git add ui/stats_history/session_detail.py tests/ui/test_session_detail.py
git commit -m "feat(stats-history): SessionDetail with breadcrumb + mini-charts + runes table"
```

---

## Task 8 — `HistoryView` : QStackedWidget interne (liste ↔ détail) + câblage

**Files:**
- Modify: `ui/stats_history/history_view.py`
- Create: `tests/ui/test_history_view.py`

- [ ] **Step 8.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_history_view.py` :

```python
from __future__ import annotations

import pytest

from history_db import init_db, save_session, save_rune
from ui.stats_history.history_view import HistoryView
from ui.stats_history.session_detail import SessionDetail
from ui.stats_history.session_list import SessionList


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    sid = save_session(
        c, start_time="2026-04-18 09:00:00", end_time="2026-04-18 09:30:00",
        dungeon="Giant B10", total=2, keep=2, sell=0,
    )
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=92.5)
    yield c, sid
    c.close()


def test_history_view_instantiates(qapp):
    v = HistoryView()
    assert v is not None


def test_history_view_has_stack_with_2_views(qapp):
    v = HistoryView()
    assert v._stack.count() == 2
    assert isinstance(v._list, SessionList)
    assert isinstance(v._detail, SessionDetail)


def test_history_view_starts_on_list(qapp):
    v = HistoryView()
    assert v._stack.currentIndex() == 0


def test_refresh_populates_list(qapp, conn):
    c, _sid = conn
    v = HistoryView()
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert len(v._list._rows) == 1


def test_refresh_resets_to_list_view(qapp, conn):
    c, sid = conn
    v = HistoryView()
    # Bascule sur detail manuellement
    v._list.session_clicked.emit(sid)
    assert v._stack.currentIndex() == 1
    # Puis refresh (changement de periode) → doit revenir a la liste
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert v._stack.currentIndex() == 0


def test_click_session_switches_to_detail(qapp, conn):
    c, sid = conn
    v = HistoryView()
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    v._list.session_clicked.emit(sid)
    assert v._stack.currentIndex() == 1


def test_back_returns_to_list(qapp, conn):
    c, sid = conn
    v = HistoryView()
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    v._list.session_clicked.emit(sid)
    v._detail.back_clicked.emit()
    assert v._stack.currentIndex() == 0


def test_refresh_empty_period_empty_list(qapp, conn):
    c, _sid = conn
    v = HistoryView()
    v.refresh(c, "2025-01-01 00:00:00", "2025-01-31 00:00:00")
    assert len(v._list._rows) == 0
```

- [ ] **Step 8.2 : FAIL**

```bash
pytest tests/ui/test_history_view.py -v
```

Attendu : FAIL (stub actuel n'a ni `_stack` ni `_list`).

- [ ] **Step 8.3 : Remplacer complètement `ui/stats_history/history_view.py`**

```python
"""Sous-onglet Historique : QStackedWidget interne (liste sessions / detail session)."""
from __future__ import annotations

import sqlite3

from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from history_db import get_sessions_with_stats
from ui.stats_history.session_detail import SessionDetail
from ui.stats_history.session_list import SessionList


class HistoryView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._conn: sqlite3.Connection | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 12, 0, 0)
        outer.setSpacing(0)

        self._stack = QStackedWidget()
        self._list = SessionList()
        self._detail = SessionDetail()
        self._stack.addWidget(self._list)
        self._stack.addWidget(self._detail)
        outer.addWidget(self._stack)

        self._list.session_clicked.connect(self._on_session_clicked)
        self._detail.back_clicked.connect(self._on_back)

    def refresh(self, conn: sqlite3.Connection, start: str, end: str) -> None:
        self._conn = conn
        sessions = get_sessions_with_stats(conn, start=start, end=end)
        self._list.set_sessions(sessions)
        self._stack.setCurrentIndex(0)  # revient a la liste a chaque refresh

    def _on_session_clicked(self, session_id: int) -> None:
        if self._conn is None:
            return
        self._detail.load_session(self._conn, session_id)
        self._stack.setCurrentIndex(1)

    def _on_back(self) -> None:
        self._stack.setCurrentIndex(0)
```

- [ ] **Step 8.4 : PASS**

```bash
pytest tests/ui/test_history_view.py tests/ui/test_stats_history_page.py -v
```

Attendu : 13 tests PASS (8 history_view + 5 page — mais le test de dispatch de la page peut devoir être ajusté car les stubs ne sont plus stubs).

Si `test_period_change_triggers_dispatch` casse parce que `refresh` réel nécessite un `conn`, le test reste valable car il monkeypatch `refresh` → le code réel n'est pas exécuté. Vérifier que le test passe toujours.

- [ ] **Step 8.5 : Commit**

```bash
git add ui/stats_history/history_view.py tests/ui/test_history_view.py
git commit -m "feat(stats-history): HistoryView QStackedWidget list<->detail navigation"
```

---

## Task 9 — Câbler `StatsHistoryPage` dans `MainWindow` (index 4)

**Files:**
- Modify: `ui/main_window.py`
- Modify: `tests/ui/test_main_window_nav.py`

- [ ] **Step 9.1 : Écrire le test qui échoue**

Ajouter à la fin de `tests/ui/test_main_window_nav.py` :

```python
def test_stats_history_index_is_stats_history_page(qapp):
    from ui.stats_history.stats_history_page import StatsHistoryPage
    mw = MainWindow()
    mw._on_nav("stats_history")
    current = mw._stack.currentWidget()
    assert isinstance(current, StatsHistoryPage)
```

- [ ] **Step 9.2 : FAIL**

```bash
pytest tests/ui/test_main_window_nav.py -v
```

Attendu : FAIL sur le placeholder qui n'est pas `StatsHistoryPage`.

- [ ] **Step 9.3 : Modifier `ui/main_window.py`**

Dans `ui/main_window.py`, **ajouter l'import** (groupé avec les autres `from ui...`) :

```python
from ui.stats_history.stats_history_page import StatsHistoryPage
```

Puis, **remplacer** le bloc :

```python
        # Index 4 : Stats & Historique (placeholder, Plan 4)
        self._stack.addWidget(_placeholder("Stats & Historique - a implementer"))
```

par :

```python
        # Index 4 : Stats & Historique
        self.stats_history_page = StatsHistoryPage()
        self._stack.addWidget(self.stats_history_page)
```

Pas de signal `profile_loaded` à connecter : la page lit `history.db` passivement.

- [ ] **Step 9.4 : PASS**

```bash
pytest tests/ui/ -v
```

Attendu : tous les tests UI passent (existants + ~60 nouveaux tests de ce plan).

- [ ] **Step 9.5 : Commit**

```bash
git add ui/main_window.py tests/ui/test_main_window_nav.py
git commit -m "feat(main-window): wire StatsHistoryPage at index 4"
```

---

## Task 10 — Smoke test manuel

- [ ] **Step 10.1 : Lancer l'application**

```bash
cd /c/Users/louis/Desktop/Luci2US
python scan_app.py
```

- [ ] **Step 10.2 : Checklist Stats & Historique**

- Cliquer sur `Stats & Historique` dans la sidebar → la page s'affiche.
- Onglet **Stats** par défaut visible avec les 4 cartes :
  - Carte VERDICT : barre empilée KEEP / POWER-UP / SELL + légende avec compteurs.
  - Carte GRADE : 4 barres (Legendaire, Heroique, Rare, Magique) avec valeurs au-dessus.
  - Carte SESSIONS/JOUR : barres chronologiques + labels date début/fin.
  - Carte TOP RUNES : mini-liste des 5 meilleurs scores (ou "Aucune donnee" si vide).
- Changer la période (`Aujourd'hui` / `7j` / `30j` / `Tout`) → les 4 cartes se rafraîchissent, les valeurs changent.
- Cliquer sur l'onglet **Historique** → liste de sessions visible avec date, dungeon, durée, Scan/Keep/Sell/PwrUp, Eff.
- Si aucune session dans la période → placeholder `Aucune session pour cette periode.`
- Cliquer sur une session → push vers la vue détail :
  - Breadcrumb `< Retour  Historique / Giant B10`.
  - Header avec titre + méta (Scan/Keep/Sell/Durée).
  - 2 mini-charts (Verdict + Grade) spécifiques à la session.
  - Table des runes scannées (Set / Slot / Etoiles / Grade / Main / Eff / Verdict) avec couleurs sur Verdict (vert KEEP, rouge SELL, orange POWER-UP).
- Cliquer `< Retour` → revient à la liste des sessions.
- Changer la période alors qu'on est sur la vue détail → revient automatiquement à la liste.

- [ ] **Step 10.3 : Non-régression**

- `Scan` fonctionne toujours.
- `Profils` fonctionne toujours.
- `Paramètres` fonctionne toujours.
- `Monstres`, `Runes`, `Filtres` affichent toujours leur placeholder (ou leur vraie page si livrée).
- Un scan/un save_session/save_rune existants (via le controleur) alimentent bien l'onglet après navigation `Scan` → `Stats & Historique`.

- [ ] **Step 10.4 : Tag**

```bash
git tag plan-04-done
```

---

## Récapitulatif — ce que ce plan produit

1. **Widget `PeriodBar`** avec 4 boutons exclusifs + helper pur `compute_period_range` (bornes ISO UTF normalisées). ✓
2. **Fonction additive `get_sessions_with_stats`** dans `history_db.py` agrégeant `power_up` + `avg_score` via LEFT JOIN. Aucune modification des fonctions existantes. ✓
3. **`StatsHistoryPage`** : toolbar période partagée + `QTabWidget` (Stats / Historique). Dispatch d'un refresh vers les 2 vues sur changement de période. ✓
4. **4 charts custom QPainter** (`StackedBarChart`, `GradeBarChart`, `TimelineBarChart`, `TopRunesList`) alignés sur la palette v13. ✓
5. **`StatsView`** : grille 2×2 de cartes, refresh SQL direct (runes + sessions) par période. ✓
6. **`SessionList`** : lignes cliquables (date, dungeon, durée, compteurs, Eff) + empty state. ✓
7. **`SessionDetail`** : breadcrumb + header + mini-charts Verdict/Grade + table runes 7 colonnes avec couleurs verdict. ✓
8. **`HistoryView`** : `QStackedWidget` interne (liste ↔ détail) + retour automatique à la liste sur changement de période. ✓
9. **Câblage `MainWindow`** index 4. Aucun signal `profile_loaded` ajouté (page passive sur DB). ✓
10. **~60 tests pytest-qt** couvrant period helper, page shell, 4 charts, stats view, session list, session detail, history view, main window nav, et la nouvelle fonction DB. ✓
11. Aucun changement aux modules bot core. ✓

**Prochain plan :** `Plan 05 — Onglet Filtres (S2US editor + rune optimizer)` — le plus complexe, à traiter en dernier comme prévu par la spec §12.
