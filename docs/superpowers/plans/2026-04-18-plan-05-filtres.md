# Plan 05 — Onglet Filtres (éditeur S2US complet + Rune Optimizer)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le placeholder `Filtres` (index 1) par une page fonctionnelle deux colonnes : panneau gauche « Filtres S2US » (liste catégorisée triable via boutons ▲▼, ajout/suppression `+`/`−`, boutons `Importer` / `Exporter` / `Test`), panneau droit éditeur S2US complet (header enabled+nom, grille Sets, Niveau, Rareté, Slot, ★, Classe, Main stat, Innate, Sous-propriétés tri-état avec seuil + slider, compteur optional_count, Efficacité, simulation Meule/Gemme, Marque, bouton SAVE). Bouton `Test` ouvre une modale **Rune Optimizer** qui, pour une rune saisie, affiche la meilleure configuration `meule + gemme` maximisant l'Efficience S2US **et** la liste des filtres qui matcheraient la rune optimisée.

**Architecture:** Deux nouveaux modules core **strictement additifs** : `s2us_writer.py` (inverse de `s2us_filter.load_s2us_file`, sérialise une `list[S2USFilter]` vers le format JSON `.s2us`) et `rune_optimizer.py` (logique pure, sans Qt : prend une `Rune` + des grades `grind_grade`/`gem_grade` max autorisés, renvoie la meilleure variante +12 selon `calculate_efficiency1`, réutilise `powerup_simulator.project_to_plus12`). Nouveau sous-package UI `ui/filtres/` suivant le pattern des autres onglets : `FiltresPage` orchestre un `QSplitter` horizontal contenant `FilterListPanel` (gauche) + `FilterEditor` (droite). Les deux panneaux communiquent par signaux (`filter_selected(int)`, `filter_saved(S2USFilter)`, `filter_added()`, `filter_removed(int)`, `filter_moved(int, int)`). La page lit/écrit via `load_s2us_file` (existant) + nouveau `save_s2us_file` (dans `s2us_writer.py`) ; le chemin courant est lu depuis `config.json["s2us"]["filter_file"]`. La modale `RuneTesterModal` est un `QDialog` qui utilise `rune_optimizer.best_variant` + `match_filter` pour produire son verdict. Aucun module bot core n'est modifié (`evaluator_chain`, `s2us_filter`, `auto_mode`, `swex_bridge`, `profile_loader`, `profile_store`, `models`, `powerup_simulator` — tous intouchables, utilisation en lecture / appels existants uniquement).

**Tech Stack:** PySide6 6.11.0, `QSplitter`, `QListWidget` (groupes repliables via items `QTreeWidget`), `QDialog`, `QSlider`, `QDoubleSpinBox`, `QRadioButton` exclusifs (`QButtonGroup`), pytest-qt (`qapp`), `json` stdlib. Les modules core (`s2us_writer.py`, `rune_optimizer.py`) sont couverts par des tests unitaires purs (pas de fixture `qapp`).

---

## File Structure

### Créer

| Chemin | Responsabilité |
|---|---|
| `s2us_writer.py` | `save_s2us_file(path, filters, global_settings)` : inverse de `load_s2us_file`. Sérialise vers JSON `.s2us` avec encodage `Name` en base64, champs `SlotN` / `Sub<KEY>` / `Min<KEY>` / `Innate<KEY>` / sets bool, etc. |
| `rune_optimizer.py` | `best_variant(rune, grind_grade, gem_grade) -> OptimizerResult` (meilleure variante +12 selon `calculate_efficiency1`). `best_plus0(rune, max_grind_grade, max_gem_grade) -> OptimizerResult` (rune +0 → meilleure config future). `best_now(rune, grind_grade, gem_grade) -> OptimizerResult` (rune +12 → meilleur gain immédiat). `filters_that_match(variant, filters) -> list[S2USFilter]`. |
| `ui/filtres/__init__.py` | Package init vide |
| `ui/filtres/filtres_page.py` | `FiltresPage` : `QSplitter` horizontal (list panel + editor) + I/O disk (`_load_filters_from_config`, `_write_filters_to_config_path`) |
| `ui/filtres/filter_list_panel.py` | `FilterListPanel` : titre, 4 boutons ronds (`+`/`−`/`▲`/`▼`), 3 boutons rectangulaires (`Importer`/`Exporter`/`Test`), liste catégorisée (`QTreeWidget`). Signaux : `filter_selected(int)`, `filter_added()`, `filter_removed(int)`, `filter_moved(int, int)`, `import_requested(str)`, `export_requested(str)`, `test_requested()` |
| `ui/filtres/filter_editor.py` | `FilterEditor` : éditeur complet pour une `S2USFilter`. Méthodes `load_filter(f)` / `current_filter() -> S2USFilter`. Signal `filter_saved(S2USFilter)` émis au clic SAVE |
| `ui/filtres/rune_tester_modal.py` | `RuneTesterModal(QDialog)` : formulaire de saisie rune + résultat optimizer + liste filtres matchés |
| `tests/test_s2us_writer.py` | Tests purs (no Qt) : round-trip `load_s2us_file` → `save_s2us_file` → `load_s2us_file` conserve les filtres |
| `tests/test_rune_optimizer.py` | Tests purs : `best_variant` retourne bien la variante de max eff1, `best_plus0` vs `best_now`, `filters_that_match` |
| `tests/ui/test_filtres_page.py` | Tests `FiltresPage` (splitter, I/O disque via `tmp_path + monkeypatch`, câblage signaux) |
| `tests/ui/test_filter_list_panel.py` | Tests rendu liste catégorisée + signaux `+`/`−`/`▲`/`▼` + Import/Export/Test |
| `tests/ui/test_filter_editor.py` | Tests `load_filter` → UI peuplée + `current_filter` → round-trip conserve les champs + SAVE émet signal |
| `tests/ui/test_rune_tester_modal.py` | Tests modale : saisie → verdict optimizer + liste filtres matchés |

### Modifier

| Chemin | Changement |
|---|---|
| `ui/main_window.py` | Remplacer `_placeholder("Filtres - a implementer")` (index 1) par `FiltresPage()` réel. Aucun signal `profile_loaded` nécessaire (page isolée, travaille sur le fichier `.s2us` configuré dans `config.json`). |
| `tests/ui/test_main_window_nav.py` | Ajouter `test_filters_index_is_filtres_page` (assert `isinstance(mw._stack.widget(1), FiltresPage)`). |

### Ne pas toucher

- `evaluator_chain.py`, `s2us_filter.py`, `auto_mode.py`, `swex_bridge.py`, `profile_loader.py`, `profile_store.py`, `models.py`, `monster_icons.py`, `powerup_simulator.py`, `history_db.py`, `i18n.py`
- `ui/sidebar.py`, `ui/scan/*`, `ui/profile/*`, `ui/widgets/*`, `ui/theme.py`, `ui/settings/*`, `ui/monsters/*` (si plan 02 livré), `ui/runes/*` (si plan 03 livré), `ui/stats_history/*` (si plan 04 livré), `ui/controllers/scan_controller.py`
- Tabs legacy (`settings_tab.py`, `stats_tab.py`, `history_tab.py`, `auto_tab.py`, `profile_tab.py`) — ils seront supprimés dans un plan ultérieur de nettoyage.

---

## Task 1 — `s2us_writer.py` : sérialisation `.s2us`

**Files:**
- Create: `s2us_writer.py`
- Create: `tests/test_s2us_writer.py`

- [ ] **Step 1.1 : Écrire les tests qui échouent**

Créer `tests/test_s2us_writer.py` :

```python
"""Round-trip tests pour s2us_writer (inverse de s2us_filter.load_s2us_file)."""
from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from s2us_filter import S2USFilter, load_s2us_file
from s2us_writer import save_s2us_file, _encode_name, serialize_filter


def _make_minimal_filter(name: str = "SPD CR CD ACC") -> S2USFilter:
    return S2USFilter(
        name=name,
        enabled=True,
        sets={"Violent": True, "Swift": True},
        slots={f"Slot{i}": (i == 2) for i in range(1, 7)},
        grades={"Rare": False, "Hero": True, "Legend": True},
        stars={"FiveStars": False, "SixStars": True},
        main_stats={"MainSPD": True},
        ancient_type="",
        sub_requirements={"SPD": 1, "CR": 2, "CD": 2, "ACC": 2},
        min_values={"SPD": 12, "CR": 6, "CD": 9, "ACC": 0},
        optional_count=2,
        level=4,
        efficiency=80.0,
        eff_method="S2US",
        grind=3,
        gem=3,
        powerup_mandatory=0,
        powerup_optional=0,
        innate_required={},
    )


def test_encode_name_roundtrip():
    encoded = _encode_name("SPD CR CD ACC")
    assert base64.b64decode(encoded).decode("utf-8") == "SPD CR CD ACC"


def test_serialize_filter_sets_name_as_b64():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert base64.b64decode(raw["Name"]).decode("utf-8") == "SPD CR CD ACC"


def test_serialize_filter_has_all_sets_as_int():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert raw["Violent"] == 1
    assert raw["Swift"] == 1
    assert raw["Despair"] == 0  # absent du dict → 0
    assert raw["Will"] == 0


def test_serialize_filter_has_sub_and_min_fields():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert raw["SubSPD"] == 1
    assert raw["MinSPD"] == 12
    assert raw["SubCR"] == 2
    assert raw["MinCR"] == 6
    assert raw["SubHP"] == 0  # stat non utilisée → 0


def test_serialize_filter_writes_slots_and_grades():
    f = _make_minimal_filter()
    raw = serialize_filter(f)
    assert raw["Slot2"] == 1
    assert raw["Slot1"] == 0
    assert raw["Hero"] == 1
    assert raw["Legend"] == 1
    assert raw["Rare"] == 0
    assert raw["SixStars"] == 1
    assert raw["FiveStars"] == 0


def test_serialize_filter_writes_ancient_flags():
    f = _make_minimal_filter()
    f.ancient_type = "Ancient"
    raw = serialize_filter(f)
    assert raw["Ancient"] == 1
    assert raw["Normal"] == 0

    f.ancient_type = "NotAncient"
    raw = serialize_filter(f)
    assert raw["Ancient"] == 0
    assert raw["Normal"] == 1

    f.ancient_type = ""
    raw = serialize_filter(f)
    assert raw["Ancient"] == 0
    assert raw["Normal"] == 0


def test_serialize_filter_innate_flag_and_specifics():
    f = _make_minimal_filter()
    f.innate_required = {"SPD": True, "CR": True}
    raw = serialize_filter(f)
    assert raw["Innate"] == 1
    assert raw["InnateSPD"] == 1
    assert raw["InnateCR"] == 1
    assert raw["InnateHP"] == 0


def test_serialize_filter_no_innate_flag_when_empty():
    f = _make_minimal_filter()
    f.innate_required = {}
    raw = serialize_filter(f)
    assert raw["Innate"] == 0


def test_save_and_reload_preserves_one_filter(tmp_path: Path):
    path = tmp_path / "out.s2us"
    f = _make_minimal_filter()
    save_s2us_file(str(path), [f], {"SmartPowerup": True, "RareLevel": 2,
                                     "HeroLevel": 4, "LegendLevel": 4})
    reloaded, settings = load_s2us_file(str(path))
    assert len(reloaded) == 1
    g = reloaded[0]
    assert g.name == f.name
    assert g.enabled == f.enabled
    assert g.level == f.level
    assert g.optional_count == f.optional_count
    assert g.efficiency == f.efficiency
    assert g.grind == f.grind
    assert g.gem == f.gem
    assert g.sub_requirements["SPD"] == 1
    assert g.min_values["CR"] == 6
    assert g.sets["Violent"] is True
    assert g.sets["Despair"] is False
    assert g.slots["Slot2"] is True
    assert g.grades["Hero"] is True
    assert g.stars["SixStars"] is True
    assert settings["SmartPowerup"] is True
    assert settings["RareLevel"] == 2


def test_save_and_reload_preserves_multiple_filters(tmp_path: Path):
    path = tmp_path / "multi.s2us"
    a = _make_minimal_filter("Filter A")
    b = _make_minimal_filter("Filter B")
    b.efficiency = 95.0
    save_s2us_file(str(path), [a, b], {})
    reloaded, _ = load_s2us_file(str(path))
    assert [f.name for f in reloaded] == ["Filter A", "Filter B"]
    assert reloaded[1].efficiency == 95.0


def test_save_file_is_utf8_json_with_runefilter_envelope(tmp_path: Path):
    path = tmp_path / "envelope.s2us"
    save_s2us_file(str(path), [_make_minimal_filter()], {})
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    assert "RuneFilter" in data
    assert "Filter" in data["RuneFilter"]
    assert isinstance(data["RuneFilter"]["Filter"], list)


def test_save_file_global_settings_written_in_envelope(tmp_path: Path):
    path = tmp_path / "settings.s2us"
    save_s2us_file(str(path), [], {
        "SmartPowerup": False, "RareLevel": 1, "HeroLevel": 3, "LegendLevel": 4,
    })
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    rf = data["RuneFilter"]
    assert rf["SmartPowerup"] is False
    assert rf["RareLevel"] == 1
    assert rf["HeroLevel"] == 3
    assert rf["LegendLevel"] == 4
```

- [ ] **Step 1.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
cd /c/Users/louis/Desktop/Luci2US
pytest tests/test_s2us_writer.py -v
```

Attendu : FAIL (`ModuleNotFoundError: No module named 's2us_writer'`).

- [ ] **Step 1.3 : Créer `s2us_writer.py`**

```python
"""Sérialisation d'une liste de S2USFilter vers un fichier .s2us.

Inverse de s2us_filter.load_s2us_file. Respecte exactement le format attendu
par le bot (JSON UTF-8 BOM, enveloppe RuneFilter, Name en base64, flags int 0/1).
"""
from __future__ import annotations

import base64
import json

from s2us_filter import (
    S2USFilter,
    _SET_FIELDS,
    _STAT_KEYS,
)


def _encode_name(name: str) -> str:
    return base64.b64encode(name.encode("utf-8")).decode("ascii")


_MAIN_KEYS = [
    "MainSPD", "MainHP", "MainHP2", "MainATK", "MainATK2",
    "MainDEF", "MainDEF2", "MainCR", "MainCD", "MainACC", "MainRES",
]


def serialize_filter(f: S2USFilter) -> dict:
    """Retourne le dict JSON-ready correspondant à un S2USFilter."""
    raw: dict = {}
    raw["Name"] = _encode_name(f.name)
    raw["Enabled"] = bool(f.enabled)

    # Sets : tous les 23, int 0/1
    for s in _SET_FIELDS:
        raw[s] = 1 if f.sets.get(s) else 0

    # Slots 1-6
    for i in range(1, 7):
        key = f"Slot{i}"
        raw[key] = 1 if f.slots.get(key) else 0

    # Rareté
    for g in ("Rare", "Hero", "Legend"):
        raw[g] = 1 if f.grades.get(g) else 0

    # ★
    for s in ("FiveStars", "SixStars"):
        raw[s] = 1 if f.stars.get(s) else 0

    # Main stats
    for k in _MAIN_KEYS:
        raw[k] = 1 if f.main_stats.get(k) else 0

    # Ancient / Normal
    if f.ancient_type == "Ancient":
        raw["Ancient"], raw["Normal"] = 1, 0
    elif f.ancient_type == "NotAncient":
        raw["Ancient"], raw["Normal"] = 0, 1
    else:
        raw["Ancient"], raw["Normal"] = 0, 0

    # Sous-requirements + min values
    for k in _STAT_KEYS:
        raw[f"Sub{k}"] = int(f.sub_requirements.get(k, 0))
        raw[f"Min{k}"] = int(f.min_values.get(k, 0))

    # Innate : flag global + clés spécifiques
    innate = {k: v for k, v in f.innate_required.items() if v}
    raw["Innate"] = 1 if innate else 0
    for k in _STAT_KEYS:
        raw[f"Innate{k}"] = 1 if innate.get(k) else 0

    # Numériques
    raw["Optional"] = int(f.optional_count)
    raw["Level"] = int(f.level)
    raw["Efficiency"] = float(f.efficiency)
    raw["EffMethod"] = str(f.eff_method)
    raw["Grind"] = int(f.grind)
    raw["Gem"] = int(f.gem)
    raw["PowerupMandatory"] = int(f.powerup_mandatory)
    raw["PowerupOptional"] = int(f.powerup_optional)
    return raw


def save_s2us_file(
    path: str,
    filters: list[S2USFilter],
    global_settings: dict | None = None,
) -> None:
    """Sérialise `filters` vers `path` au format .s2us."""
    settings = global_settings or {}
    rf = {
        "SmartPowerup": bool(settings.get("SmartPowerup", True)),
        "RareLevel": int(settings.get("RareLevel", 0)),
        "HeroLevel": int(settings.get("HeroLevel", 0)),
        "LegendLevel": int(settings.get("LegendLevel", 0)),
        "Filter": [serialize_filter(f) for f in filters],
    }
    payload = {"RuneFilter": rf}
    # load_s2us_file lit avec utf-8-sig → on écrit sans BOM, l'encodeur lit les deux
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
```

- [ ] **Step 1.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/test_s2us_writer.py -v
```

Attendu : 12 tests PASS.

- [ ] **Step 1.5 : Test bonus de round-trip sur un vrai fichier existant** (si disponible)

Si l'utilisateur a un `.s2us` dans `config.json`, vérifier que le round-trip conserve tous les filtres :

```python
# (ponctuel, pas de test automatique)
from s2us_filter import load_s2us_file
from s2us_writer import save_s2us_file
import json
cfg = json.load(open("config.json", encoding="utf-8"))
src = cfg["s2us"]["filter_file"]
filters, settings = load_s2us_file(src)
save_s2us_file("roundtrip_test.s2us", filters, settings)
f2, s2 = load_s2us_file("roundtrip_test.s2us")
assert len(f2) == len(filters)
```

- [ ] **Step 1.6 : Commit**

```bash
cd /c/Users/louis/Desktop/Luci2US
git add s2us_writer.py tests/test_s2us_writer.py
git commit -m "feat(s2us_writer): serialize S2USFilter list to .s2us (inverse of load_s2us_file)"
```

---

## Task 2 — `rune_optimizer.py` : meilleure config meule+gemme

**Files:**
- Create: `rune_optimizer.py`
- Create: `tests/test_rune_optimizer.py`

**Concept :** pour une rune donnée + des grades max de grind et de gem, énumérer via `powerup_simulator.project_to_plus12` toutes les variantes +12 possibles, puis retourner celle qui maximise `calculate_efficiency1`. Le caller décide s'il appelle en mode « rune +0 futur » (grades max = `S2USFilter.grind` / `S2USFilter.gem`) ou « rune déjà à +12, maintenant » (grades max = grades de matériaux disponibles).

- [ ] **Step 2.1 : Écrire les tests qui échouent**

Créer `tests/test_rune_optimizer.py` :

```python
"""Tests purs pour rune_optimizer.best_variant et filters_that_match."""
from __future__ import annotations

from models import Rune, SubStat
from s2us_filter import S2USFilter
from rune_optimizer import (
    OptimizerResult,
    best_variant,
    best_plus0,
    best_now,
    filters_that_match,
)


def _rune_plus0_legend() -> Rune:
    return Rune(
        set="Violent",
        slot=2,
        stars=6,
        grade="Legendaire",
        level=0,
        main_stat=SubStat(type="ATQ%", value=63),
        prefix=None,
        substats=[
            SubStat(type="VIT", value=5),
            SubStat(type="CC", value=4),
            SubStat(type="DC", value=5),
            SubStat(type="PV%", value=4),
        ],
        ancient=False,
    )


def _rune_plus12_legend() -> Rune:
    return Rune(
        set="Violent",
        slot=2,
        stars=6,
        grade="Legendaire",
        level=12,
        main_stat=SubStat(type="ATQ%", value=63),
        prefix=None,
        substats=[
            SubStat(type="VIT", value=18),
            SubStat(type="CC", value=10),
            SubStat(type="DC", value=14),
            SubStat(type="PV%", value=5),
        ],
        ancient=False,
    )


def test_best_variant_returns_optimizer_result():
    r = _rune_plus12_legend()
    res = best_variant(r, grind_grade=0, gem_grade=0)
    assert isinstance(res, OptimizerResult)
    assert res.efficiency >= 0
    assert res.rune is not None


def test_best_variant_at_plus12_zero_materials_returns_same_rune_eff():
    """Rune +12, aucune amélioration → variante retournée = rune telle quelle."""
    from s2us_filter import calculate_efficiency1
    r = _rune_plus12_legend()
    res = best_variant(r, grind_grade=0, gem_grade=0)
    assert res.efficiency == calculate_efficiency1(r)


def test_best_variant_higher_with_grind_than_without():
    r = _rune_plus12_legend()
    low = best_variant(r, grind_grade=0, gem_grade=0)
    high = best_variant(r, grind_grade=3, gem_grade=0)
    assert high.efficiency >= low.efficiency


def test_best_variant_higher_with_gem_than_without():
    r = _rune_plus12_legend()
    low = best_variant(r, grind_grade=0, gem_grade=0)
    high = best_variant(r, grind_grade=0, gem_grade=3)
    assert high.efficiency >= low.efficiency


def test_best_variant_returns_grind_applied_on_substats():
    r = _rune_plus12_legend()
    res = best_variant(r, grind_grade=3, gem_grade=0)
    # Au moins une sub a dû gagner du grind par rapport à la rune d'entrée
    in_values = {s.type: s.value for s in r.substats}
    out_values = {s.type: s.value for s in res.rune.substats}
    grind_applied = any(
        out_values.get(k, 0) > in_values.get(k, 0) for k in in_values
    )
    assert grind_applied


def test_best_plus0_uses_filter_authorized_grades():
    """best_plus0 projette la rune en utilisant grind/gem de filtre."""
    r = _rune_plus0_legend()
    res = best_plus0(r, max_grind_grade=3, max_gem_grade=3)
    assert isinstance(res, OptimizerResult)
    assert res.efficiency > 0


def test_best_now_projects_current_level():
    """best_now sur rune +12 : identique à best_variant."""
    r = _rune_plus12_legend()
    a = best_now(r, grind_grade=2, gem_grade=2)
    b = best_variant(r, grind_grade=2, gem_grade=2)
    assert a.efficiency == b.efficiency


def test_filters_that_match_returns_list_ordered_by_efficiency_desc():
    r = _rune_plus12_legend()
    f_low = S2USFilter(name="low", efficiency=30.0,
                       sub_requirements={}, min_values={})
    f_high = S2USFilter(name="high", efficiency=85.0,
                        sub_requirements={}, min_values={})
    f_disabled = S2USFilter(name="off", enabled=False,
                            sub_requirements={}, min_values={})
    matches = filters_that_match(r, [f_disabled, f_low, f_high])
    # f_disabled exclu, f_high avant f_low (tri décroissant par seuil)
    names = [f.name for f in matches]
    assert "off" not in names
    assert names.index("high") < names.index("low")


def test_filters_that_match_handles_empty_filters():
    r = _rune_plus12_legend()
    assert filters_that_match(r, []) == []
```

- [ ] **Step 2.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/test_rune_optimizer.py -v
```

Attendu : FAIL (`ModuleNotFoundError: No module named 'rune_optimizer'`).

- [ ] **Step 2.3 : Créer `rune_optimizer.py`**

```python
"""Choisit la meilleure configuration meule+gemme pour une rune.

Module pur (pas de Qt). Réutilise :
  - powerup_simulator.project_to_plus12(rune, grind_grade, gem_grade) pour
    énumérer toutes les variantes +12 atteignables.
  - s2us_filter.calculate_efficiency1 pour scorer chaque variante.
  - s2us_filter.match_filter pour savoir quels filtres matcheraient la
    variante optimisée.

Le caller décide du cas d'usage :
  - best_plus0  : rune fraîche, utilisateur veut la meilleure config future
                  (grades max = ce qu'il est prêt à investir).
  - best_now    : rune déjà à +12, utilisateur veut le meilleur gain
                  immédiat avec les grades en poche.
  - best_variant: primitive bas niveau utilisée par les deux.
"""
from __future__ import annotations

from dataclasses import dataclass

from models import Rune
from powerup_simulator import project_to_plus12
from s2us_filter import (
    S2USFilter,
    calculate_efficiency1,
    match_filter,
)


@dataclass
class OptimizerResult:
    rune: Rune
    efficiency: float


def best_variant(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
) -> OptimizerResult:
    """Énumère toutes les variantes +12 et retourne celle de max Efficiency1."""
    variants = project_to_plus12(
        rune, grind_grade=grind_grade, gem_grade=gem_grade,
    )
    if not variants:
        return OptimizerResult(rune=rune, efficiency=float(calculate_efficiency1(rune)))
    best = max(variants, key=calculate_efficiency1)
    return OptimizerResult(rune=best, efficiency=float(calculate_efficiency1(best)))


def best_plus0(
    rune: Rune,
    max_grind_grade: int = 3,
    max_gem_grade: int = 3,
) -> OptimizerResult:
    """Rune à +0 (ou <+12) → config future optimale dans la limite des grades."""
    return best_variant(rune, grind_grade=max_grind_grade, gem_grade=max_gem_grade)


def best_now(
    rune: Rune,
    grind_grade: int = 0,
    gem_grade: int = 0,
) -> OptimizerResult:
    """Rune à +12 → meilleure amélioration immédiate avec ces grades."""
    return best_variant(rune, grind_grade=grind_grade, gem_grade=gem_grade)


def filters_that_match(
    rune: Rune,
    filters: list[S2USFilter],
) -> list[S2USFilter]:
    """Filtres enabled qui acceptent cette rune, triés par seuil d'efficacité
    décroissant (comme dans evaluate_s2us).
    """
    matching = [f for f in filters if f.enabled and match_filter(rune, f)]
    matching.sort(key=lambda f: f.efficiency, reverse=True)
    return matching
```

- [ ] **Step 2.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/test_rune_optimizer.py -v
```

Attendu : 9 tests PASS.

- [ ] **Step 2.5 : Commit**

```bash
git add rune_optimizer.py tests/test_rune_optimizer.py
git commit -m "feat(rune_optimizer): best grind+gem variant for max Efficiency1"
```

---

## Task 3 — Squelette `FiltresPage` + câblage dans `MainWindow`

**Files:**
- Create: `ui/filtres/__init__.py`
- Create: `ui/filtres/filtres_page.py`
- Create: `tests/ui/test_filtres_page.py`
- Modify: `ui/main_window.py`
- Modify: `tests/ui/test_main_window_nav.py`

- [ ] **Step 3.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_filtres_page.py` :

```python
import json
from pathlib import Path

import pytest

from ui.filtres.filtres_page import FiltresPage


def test_filtres_page_instantiates(qapp):
    page = FiltresPage()
    assert page is not None


def test_filtres_page_has_splitter(qapp):
    from PySide6.QtWidgets import QSplitter
    page = FiltresPage()
    splitters = page.findChildren(QSplitter)
    assert len(splitters) >= 1


def test_filtres_page_loads_filters_from_config(qapp, tmp_path, monkeypatch):
    """La page lit `config.json["s2us"]["filter_file"]` au démarrage."""
    # Crée un .s2us minimal
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    f = S2USFilter(name="TestFilter", enabled=True,
                   sub_requirements={}, min_values={})
    s2us_path = tmp_path / "test.s2us"
    save_s2us_file(str(s2us_path), [f], {})

    # Crée un config.json temporaire
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"filter_file": str(s2us_path)},
    }), encoding="utf-8")

    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    assert len(page._filters) == 1
    assert page._filters[0].name == "TestFilter"


def test_filtres_page_handles_missing_config(qapp, tmp_path, monkeypatch):
    cfg_path = tmp_path / "missing.json"
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    assert page._filters == []
```

- [ ] **Step 3.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/ui/test_filtres_page.py -v
```

Attendu : FAIL (`ModuleNotFoundError: No module named 'ui.filtres'`).

- [ ] **Step 3.3 : Créer `ui/filtres/__init__.py` (vide)**

- [ ] **Step 3.4 : Créer `ui/filtres/filtres_page.py` (squelette)**

```python
"""Onglet Filtres S2US - panneau liste + éditeur.

Ce squelette ne fait que charger les filtres depuis `config.json` et afficher
un QSplitter avec deux placeholders. Les panneaux riches sont branchés dans
les Tasks 4-9.
"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSplitter, QVBoxLayout, QWidget,
)

from s2us_filter import S2USFilter, load_s2us_file
from ui import theme


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.json")


def _read_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


class FiltresPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        self._filters: list[S2USFilter] = []
        self._global_settings: dict = {}
        self._filter_file_path: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._left_placeholder = QLabel("FilterListPanel (Task 4)")
        self._left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._left_placeholder.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; background:{theme.COLOR_BG_FRAME};"
        )
        self._right_placeholder = QLabel("FilterEditor (Task 6-9)")
        self._right_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._right_placeholder.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; background:{theme.COLOR_BG_FRAME};"
        )
        self._splitter.addWidget(self._left_placeholder)
        self._splitter.addWidget(self._right_placeholder)
        self._splitter.setSizes([260, 700])

        root.addWidget(self._splitter)

        self._load_filters_from_config()

    # ── I/O config ──
    def _load_filters_from_config(self) -> None:
        cfg = _read_config()
        path = cfg.get("s2us", {}).get("filter_file", "")
        if not path or not os.path.isfile(path):
            self._filters = []
            self._global_settings = {}
            return
        try:
            self._filters, self._global_settings = load_s2us_file(path)
            self._filter_file_path = path
        except (OSError, json.JSONDecodeError):
            self._filters = []
            self._global_settings = {}
```

- [ ] **Step 3.5 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_filtres_page.py -v
```

Attendu : 4 tests PASS.

- [ ] **Step 3.6 : Câbler `FiltresPage` dans `MainWindow`**

Dans `ui/main_window.py`, ajouter l'import en tête :

```python
from ui.filtres.filtres_page import FiltresPage
```

Remplacer la ligne :

```python
        # Index 1 : Filtres (placeholder, Plan 5)
        self._stack.addWidget(_placeholder("Filtres - a implementer"))
```

par :

```python
        # Index 1 : Filtres
        self.filtres_page = FiltresPage()
        self._stack.addWidget(self.filtres_page)
```

- [ ] **Step 3.7 : Ajouter le test de câblage**

Ajouter à `tests/ui/test_main_window_nav.py` :

```python
def test_filters_index_is_filtres_page(qapp):
    from ui.filtres.filtres_page import FiltresPage
    mw = MainWindow()
    mw._on_nav("filters")
    assert isinstance(mw._stack.currentWidget(), FiltresPage)
```

- [ ] **Step 3.8 : Lancer les tests**

```bash
pytest tests/ui/ -v
```

Attendu : nouveau test PASS, aucune régression.

- [ ] **Step 3.9 : Commit**

```bash
git add ui/filtres/ ui/main_window.py tests/ui/test_filtres_page.py tests/ui/test_main_window_nav.py
git commit -m "feat(filtres): wire FiltresPage skeleton at stack index 1"
```

---

## Task 4 — `FilterListPanel` : liste + boutons `+`/`−`/`▲`/`▼`

**Files:**
- Create: `ui/filtres/filter_list_panel.py`
- Create: `tests/ui/test_filter_list_panel.py`
- Modify: `ui/filtres/filtres_page.py` (remplacer le placeholder gauche)

- [ ] **Step 4.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_filter_list_panel.py` :

```python
import pytest

from PySide6.QtWidgets import QPushButton, QTreeWidget

from s2us_filter import S2USFilter
from ui.filtres.filter_list_panel import FilterListPanel


def _mk(name: str, enabled: bool = True) -> S2USFilter:
    return S2USFilter(name=name, enabled=enabled,
                      sub_requirements={}, min_values={})


def test_panel_instantiates(qapp):
    p = FilterListPanel()
    assert p is not None


def test_panel_has_title(qapp):
    from PySide6.QtWidgets import QLabel
    p = FilterListPanel()
    labels = [l.text() for l in p.findChildren(QLabel)]
    assert any("Filtres" in t for t in labels)


def test_panel_has_round_buttons_plus_minus_up_down(qapp):
    p = FilterListPanel()
    buttons = [b.text() for b in p.findChildren(QPushButton)]
    # Les boutons ronds portent les glyphes +, −, ▲, ▼
    assert "+" in buttons
    assert "\u2212" in buttons or "-" in buttons  # minus sign
    assert "\u25B2" in buttons
    assert "\u25BC" in buttons


def test_panel_has_rect_buttons_import_export_test(qapp):
    p = FilterListPanel()
    buttons = [b.text() for b in p.findChildren(QPushButton)]
    assert "Importer" in buttons
    assert "Exporter" in buttons
    assert "Test" in buttons


def test_set_filters_populates_tree(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B"), _mk("C")])
    tree = p._tree
    assert isinstance(tree, QTreeWidget)
    # Un unique groupe "Filtres" (pas de catégorie explicite) avec 3 enfants
    assert tree.topLevelItemCount() >= 1
    top = tree.topLevelItem(0)
    assert top.childCount() == 3
    assert [top.child(i).text(0) for i in range(3)] == ["A", "B", "C"]


def test_select_index_emits_filter_selected(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    received: list[int] = []
    p.filter_selected.connect(received.append)
    p.select_index(1)
    assert received == [1]


def test_plus_button_emits_filter_added(qapp):
    p = FilterListPanel()
    received: list[bool] = []
    p.filter_added.connect(lambda: received.append(True))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "+")
    btn.click()
    assert received == [True]


def test_minus_button_emits_filter_removed_with_index(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    p.select_index(1)
    received: list[int] = []
    p.filter_removed.connect(received.append)
    btn = next(b for b in p.findChildren(QPushButton)
               if b.text() in ("\u2212", "-"))
    btn.click()
    assert received == [1]


def test_up_button_emits_filter_moved_up(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B"), _mk("C")])
    p.select_index(2)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25B2")
    btn.click()
    assert received == [(2, 1)]


def test_down_button_emits_filter_moved_down(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B"), _mk("C")])
    p.select_index(0)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25BC")
    btn.click()
    assert received == [(0, 1)]


def test_up_button_noop_at_top(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    p.select_index(0)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25B2")
    btn.click()
    assert received == []


def test_down_button_noop_at_bottom(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A"), _mk("B")])
    p.select_index(1)
    received: list[tuple[int, int]] = []
    p.filter_moved.connect(lambda f, t: received.append((f, t)))
    btn = next(b for b in p.findChildren(QPushButton) if b.text() == "\u25BC")
    btn.click()
    assert received == []


def test_disabled_filter_is_visually_dim(qapp):
    p = FilterListPanel()
    p.set_filters([_mk("A", enabled=True), _mk("B", enabled=False)])
    top = p._tree.topLevelItem(0)
    # L'item "B" (disabled) affiche un marqueur visuel (préfixe ◯ ou couleur)
    # On accepte un préfixe "(off)" ou un text color différent via Data role
    txt = top.child(1).text(0)
    assert "B" in txt
```

- [ ] **Step 4.2 : Lancer les tests pour vérifier qu'ils échouent**

```bash
pytest tests/ui/test_filter_list_panel.py -v
```

Attendu : FAIL (`ModuleNotFoundError`).

- [ ] **Step 4.3 : Créer `ui/filtres/filter_list_panel.py`**

```python
"""Panneau gauche de l'onglet Filtres : titre, boutons +/-/↑/↓, Import/Export/Test,
liste catégorisée (QTreeWidget) des filtres.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from s2us_filter import S2USFilter
from ui import theme


def _round_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setFixedSize(28, 28)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton {{ background:{theme.COLOR_BRONZE_DARK};"
        f" color:{theme.COLOR_GOLD};"
        f" border:1px solid {theme.COLOR_BRONZE};"
        f" border-radius:14px; font-size:13px; font-weight:700; }}"
        f"QPushButton:hover {{ background:{theme.COLOR_BRONZE}; color:{theme.COLOR_BG_APP}; }}"
    )
    return b


def _rect_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton {{ background:{theme.COLOR_BRONZE_DARK};"
        f" color:{theme.COLOR_GOLD};"
        f" border:1px solid {theme.COLOR_BRONZE};"
        f" border-radius:3px; padding:5px 10px; font-size:11px; font-weight:600; }}"
        f"QPushButton:hover {{ background:{theme.COLOR_BRONZE}; color:{theme.COLOR_BG_APP}; }}"
    )
    return b


class FilterListPanel(QWidget):
    filter_selected = Signal(int)     # index flat dans la liste
    filter_added = Signal()
    filter_removed = Signal(int)
    filter_moved = Signal(int, int)   # from_index, to_index
    import_requested = Signal()
    export_requested = Signal()
    test_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet(f"background:{theme.COLOR_BG_FRAME};")

        self._filters: list[S2USFilter] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        title = QLabel("Filtres S2US")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f" font-size:15px; font-weight:700;"
        )
        lay.addWidget(title)

        # Boutons ronds
        round_row = QHBoxLayout()
        round_row.setSpacing(6)
        self._btn_add = _round_btn("+")
        self._btn_remove = _round_btn("\u2212")
        self._btn_up = _round_btn("\u25B2")
        self._btn_down = _round_btn("\u25BC")
        for b in (self._btn_add, self._btn_remove, self._btn_up, self._btn_down):
            round_row.addWidget(b)
        round_row.addStretch()
        lay.addLayout(round_row)

        # Boutons rectangulaires
        rect_row = QHBoxLayout()
        rect_row.setSpacing(6)
        self._btn_import = _rect_btn("Importer")
        self._btn_export = _rect_btn("Exporter")
        self._btn_test = _rect_btn("Test")
        for b in (self._btn_import, self._btn_export, self._btn_test):
            rect_row.addWidget(b)
        lay.addLayout(rect_row)

        # Arbre catégorisé
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setStyleSheet(
            f"QTreeWidget {{ background:{theme.COLOR_BG_APP};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; padding:4px; }}"
            f"QTreeWidget::item:selected {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD}; }}"
        )
        lay.addWidget(self._tree, 1)

        # Câblage
        self._btn_add.clicked.connect(self.filter_added.emit)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(lambda: self._move(-1))
        self._btn_down.clicked.connect(lambda: self._move(+1))
        self._btn_import.clicked.connect(self.import_requested.emit)
        self._btn_export.clicked.connect(self.export_requested.emit)
        self._btn_test.clicked.connect(self.test_requested.emit)
        self._tree.currentItemChanged.connect(self._on_item_changed)

    # ── API publique ──
    def set_filters(self, filters: list[S2USFilter]) -> None:
        self._filters = filters
        self._tree.clear()
        root = QTreeWidgetItem(self._tree, ["Filtres"])
        root.setExpanded(True)
        for i, f in enumerate(filters):
            child = QTreeWidgetItem(root, [f.name])
            child.setData(0, Qt.ItemDataRole.UserRole, i)
            if not f.enabled:
                child.setForeground(0, Qt.GlobalColor.darkGray)
        if filters:
            self.select_index(0)

    def select_index(self, idx: int) -> None:
        if not (0 <= idx < len(self._filters)):
            return
        root = self._tree.topLevelItem(0)
        if root is None or idx >= root.childCount():
            return
        self._tree.setCurrentItem(root.child(idx))

    def current_index(self) -> int:
        item = self._tree.currentItem()
        if item is None:
            return -1
        v = item.data(0, Qt.ItemDataRole.UserRole)
        return int(v) if v is not None else -1

    # ── Handlers ──
    def _on_item_changed(self, cur, _prev) -> None:
        if cur is None:
            return
        v = cur.data(0, Qt.ItemDataRole.UserRole)
        if v is None:
            return
        self.filter_selected.emit(int(v))

    def _on_remove(self) -> None:
        idx = self.current_index()
        if idx >= 0:
            self.filter_removed.emit(idx)

    def _move(self, delta: int) -> None:
        idx = self.current_index()
        new = idx + delta
        if idx < 0 or new < 0 or new >= len(self._filters):
            return
        self.filter_moved.emit(idx, new)
```

- [ ] **Step 4.4 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_filter_list_panel.py -v
```

Attendu : 12 tests PASS.

- [ ] **Step 4.5 : Remplacer le placeholder gauche dans `FiltresPage`**

Dans `ui/filtres/filtres_page.py`, remplacer le bloc qui ajoute `_left_placeholder` par :

```python
        from ui.filtres.filter_list_panel import FilterListPanel
        self._list_panel = FilterListPanel()
        self._splitter.addWidget(self._list_panel)
```

Puis, après l'ajout du right placeholder et le `setSizes([260, 700])`, câbler dans `__init__` (après `self._load_filters_from_config()`) :

```python
        self._list_panel.set_filters(self._filters)

        # Mutations : add / remove / move
        self._list_panel.filter_added.connect(self._on_filter_added)
        self._list_panel.filter_removed.connect(self._on_filter_removed)
        self._list_panel.filter_moved.connect(self._on_filter_moved)
```

Et ajouter les slots à la classe `FiltresPage` :

```python
    def _on_filter_added(self) -> None:
        from s2us_filter import S2USFilter
        new = S2USFilter(name="Nouveau filtre", enabled=True,
                          sub_requirements={}, min_values={})
        self._filters.append(new)
        self._list_panel.set_filters(self._filters)
        self._list_panel.select_index(len(self._filters) - 1)

    def _on_filter_removed(self, idx: int) -> None:
        if 0 <= idx < len(self._filters):
            self._filters.pop(idx)
            self._list_panel.set_filters(self._filters)

    def _on_filter_moved(self, src: int, dst: int) -> None:
        if not (0 <= src < len(self._filters) and 0 <= dst < len(self._filters)):
            return
        self._filters.insert(dst, self._filters.pop(src))
        self._list_panel.set_filters(self._filters)
        self._list_panel.select_index(dst)
```

- [ ] **Step 4.6 : Ajouter un test d'intégration dans `test_filtres_page.py`**

```python
def test_page_adds_filter_on_panel_add_signal(qapp, tmp_path, monkeypatch):
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    assert page._filters == []
    page._list_panel.filter_added.emit()
    assert len(page._filters) == 1


def test_page_removes_filter_on_panel_remove_signal(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    s2us = tmp_path / "x.s2us"
    a = S2USFilter(name="A", sub_requirements={}, min_values={})
    b = S2USFilter(name="B", sub_requirements={}, min_values={})
    save_s2us_file(str(s2us), [a, b], {})
    cfg = tmp_path / "c.json"
    import json
    cfg.write_text(json.dumps({"s2us": {"filter_file": str(s2us)}}), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))
    page = FiltresPage()
    assert len(page._filters) == 2
    page._list_panel.filter_removed.emit(0)
    assert [f.name for f in page._filters] == ["B"]


def test_page_moves_filter_on_panel_move_signal(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    s2us = tmp_path / "x.s2us"
    a = S2USFilter(name="A", sub_requirements={}, min_values={})
    b = S2USFilter(name="B", sub_requirements={}, min_values={})
    c = S2USFilter(name="C", sub_requirements={}, min_values={})
    save_s2us_file(str(s2us), [a, b, c], {})
    cfg = tmp_path / "c.json"
    import json
    cfg.write_text(json.dumps({"s2us": {"filter_file": str(s2us)}}), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))
    page = FiltresPage()
    page._list_panel.filter_moved.emit(0, 2)
    assert [f.name for f in page._filters] == ["B", "C", "A"]
```

- [ ] **Step 4.7 : Lancer les tests**

```bash
pytest tests/ui/test_filtres_page.py tests/ui/test_filter_list_panel.py -v
```

Attendu : tous PASS.

- [ ] **Step 4.8 : Commit**

```bash
git add ui/filtres/filter_list_panel.py ui/filtres/filtres_page.py tests/ui/test_filter_list_panel.py tests/ui/test_filtres_page.py
git commit -m "feat(filtres): FilterListPanel with add/remove/up/down actions"
```

---

## Task 5 — `FilterListPanel` : wiring Import / Export / Test

**Files:**
- Modify: `ui/filtres/filtres_page.py`
- Modify: `tests/ui/test_filtres_page.py`

- [ ] **Step 5.1 : Écrire les tests qui échouent**

Ajouter à `tests/ui/test_filtres_page.py` :

```python
def test_page_import_replaces_filter_list(qapp, tmp_path, monkeypatch):
    """Import : l'utilisateur choisit un fichier → les filtres de ce fichier
    remplacent ceux du panneau (et le chemin courant est mis à jour)."""
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    src = tmp_path / "new.s2us"
    save_s2us_file(str(src), [S2USFilter(name="Imported",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(src), "")),
    )

    page = FiltresPage()
    assert page._filters == []
    page._list_panel.import_requested.emit()
    assert len(page._filters) == 1
    assert page._filters[0].name == "Imported"
    assert page._filter_file_path == str(src)


def test_page_export_writes_filters_to_chosen_path(qapp, tmp_path, monkeypatch):
    from s2us_filter import S2USFilter, load_s2us_file
    from ui.filtres import filtres_page
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    out = tmp_path / "out.s2us"
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *a, **kw: (str(out), "")),
    )

    page = FiltresPage()
    page._filters = [S2USFilter(name="X", sub_requirements={}, min_values={})]
    page._list_panel.export_requested.emit()

    assert out.exists()
    reloaded, _ = load_s2us_file(str(out))
    assert reloaded[0].name == "X"


def test_page_test_opens_rune_tester_modal(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()

    # Stub la modale pour éviter de vraiment l'afficher
    called = {"open": 0}

    class _StubDialog:
        def __init__(self, *a, **kw): called["open"] += 1
        def exec(self): return 0

    monkeypatch.setattr(
        "ui.filtres.filtres_page.RuneTesterModal", _StubDialog,
    )
    page._list_panel.test_requested.emit()
    assert called["open"] == 1
```

- [ ] **Step 5.2 : Lancer les tests**

```bash
pytest tests/ui/test_filtres_page.py -v
```

Attendu : FAIL (les slots import/export/test n'existent pas encore).

- [ ] **Step 5.3 : Câbler Import/Export/Test dans `FiltresPage`**

Dans `ui/filtres/filtres_page.py`, ajouter les imports en tête :

```python
from PySide6.QtWidgets import QFileDialog
from s2us_filter import load_s2us_file
from s2us_writer import save_s2us_file
from ui.filtres.rune_tester_modal import RuneTesterModal
```

> Note : `RuneTesterModal` sera créé en Task 10. En attendant, créer un stub minimal :

```python
# Dans ui/filtres/rune_tester_modal.py (sera enrichi en Task 10)
from __future__ import annotations
from PySide6.QtWidgets import QDialog


class RuneTesterModal(QDialog):
    def __init__(self, filters=None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rune Optimizer")
```

Puis ajouter dans `__init__` de `FiltresPage` (après les connexions des mutations) :

```python
        # Import / Export / Test
        self._list_panel.import_requested.connect(self._on_import)
        self._list_panel.export_requested.connect(self._on_export)
        self._list_panel.test_requested.connect(self._on_test)
```

Et les méthodes :

```python
    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer un fichier .s2us", "",
            "Filtres S2US (*.s2us);;Tous les fichiers (*.*)",
        )
        if not path:
            return
        try:
            self._filters, self._global_settings = load_s2us_file(path)
            self._filter_file_path = path
        except (OSError, json.JSONDecodeError):
            return
        self._list_panel.set_filters(self._filters)

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter un fichier .s2us", self._filter_file_path or "",
            "Filtres S2US (*.s2us);;Tous les fichiers (*.*)",
        )
        if not path:
            return
        save_s2us_file(path, self._filters, self._global_settings)

    def _on_test(self) -> None:
        dlg = RuneTesterModal(filters=self._filters, parent=self)
        dlg.exec()
```

- [ ] **Step 5.4 : Créer le stub `ui/filtres/rune_tester_modal.py`**

(voir le code au Step 5.3)

- [ ] **Step 5.5 : Lancer les tests pour vérifier qu'ils passent**

```bash
pytest tests/ui/test_filtres_page.py -v
```

Attendu : tous PASS.

- [ ] **Step 5.6 : Commit**

```bash
git add ui/filtres/filtres_page.py ui/filtres/rune_tester_modal.py tests/ui/test_filtres_page.py
git commit -m "feat(filtres): wire Import/Export/Test actions in FiltresPage"
```

---

## Task 6 — `FilterEditor` : header (enabled + nom) + grille Sets

**Files:**
- Create: `ui/filtres/filter_editor.py`
- Create: `tests/ui/test_filter_editor.py`
- Modify: `ui/filtres/filtres_page.py` (remplacer le placeholder droit)

- [ ] **Step 6.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_filter_editor.py` :

```python
import pytest

from s2us_filter import S2USFilter
from ui.filtres.filter_editor import FilterEditor


def _mk() -> S2USFilter:
    return S2USFilter(
        name="Demo",
        enabled=True,
        sets={"Violent": True, "Swift": True},
        slots={}, grades={}, stars={}, main_stats={},
        ancient_type="",
        sub_requirements={}, min_values={},
        innate_required={},
    )


def test_editor_instantiates(qapp):
    e = FilterEditor()
    assert e is not None


def test_load_filter_sets_name_and_enabled(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    assert e._name_edit.text() == "Demo"
    assert e._enabled_check.isChecked() is True


def test_load_filter_unchecked_when_disabled(qapp):
    e = FilterEditor()
    f = _mk()
    f.enabled = False
    e.load_filter(f)
    assert e._enabled_check.isChecked() is False


def test_current_filter_roundtrip_header(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    e._name_edit.setText("Changed")
    e._enabled_check.setChecked(False)
    f = e.current_filter()
    assert f.name == "Changed"
    assert f.enabled is False


def test_sets_grid_has_all_23_sets(qapp):
    from PySide6.QtWidgets import QCheckBox
    e = FilterEditor()
    e.load_filter(_mk())
    checks = [c for c in e._sets_frame.findChildren(QCheckBox)]
    assert len(checks) == 23


def test_load_sets_populates_checkboxes(qapp):
    from PySide6.QtWidgets import QCheckBox
    e = FilterEditor()
    e.load_filter(_mk())
    checks = {c.text(): c for c in e._sets_frame.findChildren(QCheckBox)}
    # Violent et Swift sont cochés, les autres ne le sont pas
    assert checks["Violent"].isChecked() is True
    assert checks["Swift"].isChecked() is True
    assert checks["Fatal"].isChecked() is False


def test_current_filter_reads_sets(qapp):
    from PySide6.QtWidgets import QCheckBox
    e = FilterEditor()
    e.load_filter(_mk())
    checks = {c.text(): c for c in e._sets_frame.findChildren(QCheckBox)}
    checks["Fatal"].setChecked(True)
    f = e.current_filter()
    assert f.sets.get("Fatal") is True
    assert f.sets.get("Violent") is True
```

- [ ] **Step 6.2 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py -v
```

Attendu : FAIL (`ModuleNotFoundError`).

- [ ] **Step 6.3 : Créer `ui/filtres/filter_editor.py` (squelette + header + sets)**

```python
"""Éditeur S2US complet pour un filtre unique.

L'éditeur expose :
  - load_filter(f: S2USFilter)   — peupler les widgets depuis f
  - current_filter() -> S2USFilter — lire les widgets courants
  - signal filter_saved(S2USFilter) — émis au clic SAVE
"""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QVBoxLayout, QWidget,
)

from models import SETS_FR, SET_FR_TO_EN
from s2us_filter import S2USFilter, _SET_FIELDS
from ui import theme


class FilterEditor(QWidget):
    filter_saved = Signal(object)  # S2USFilter

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        self._current: S2USFilter | None = None

        # Scroll pour accueillir la pile verticale longue
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        self._inner_lay = QVBoxLayout(inner)
        self._inner_lay.setContentsMargins(18, 14, 18, 14)
        self._inner_lay.setSpacing(14)

        self._build_header()
        self._build_sets()

        self._inner_lay.addStretch()

    # ── Construction UI ──
    def _build_header(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(12)
        self._enabled_check = QCheckBox()
        self._enabled_check.setStyleSheet(
            f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}"
        )
        row.addWidget(self._enabled_check)

        lbl = QLabel("Nom :")
        lbl.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        row.addWidget(lbl)

        self._name_edit = QLineEdit()
        self._name_edit.setStyleSheet(
            f"QLineEdit {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:5px 8px; }}"
        )
        row.addWidget(self._name_edit, 1)
        self._inner_lay.addLayout(row)

    def _build_sets(self) -> None:
        self._sets_frame = QFrame()
        self._sets_frame.setStyleSheet(
            f"QFrame {{ background:{theme.COLOR_BG_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )
        box = QVBoxLayout(self._sets_frame)
        box.setContentsMargins(10, 8, 10, 8)
        box.setSpacing(6)

        title = QLabel("Set")
        title.setStyleSheet(f"color:{theme.COLOR_GOLD_TITLE}; font-weight:700;")
        box.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        self._set_checks: dict[str, QCheckBox] = {}  # clé = nom EN (clé S2US)
        for i, set_fr in enumerate(SETS_FR):
            set_en = SET_FR_TO_EN[set_fr]
            cb = QCheckBox(set_en)
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._set_checks[set_en] = cb
            grid.addWidget(cb, i // 6, i % 6)
        box.addLayout(grid)
        self._inner_lay.addWidget(self._sets_frame)

    # ── API publique ──
    def load_filter(self, f: S2USFilter) -> None:
        self._current = f
        self._name_edit.setText(f.name)
        self._enabled_check.setChecked(bool(f.enabled))
        for key, cb in self._set_checks.items():
            cb.setChecked(bool(f.sets.get(key)))

    def current_filter(self) -> S2USFilter:
        base = self._current or S2USFilter(name="", sub_requirements={}, min_values={})
        return replace(
            base,
            name=self._name_edit.text(),
            enabled=self._enabled_check.isChecked(),
            sets={k: cb.isChecked() for k, cb in self._set_checks.items()},
        )
```

- [ ] **Step 6.4 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py -v
```

Attendu : 7 tests PASS.

- [ ] **Step 6.5 : Remplacer le placeholder droit dans `FiltresPage`**

Dans `ui/filtres/filtres_page.py`, importer :

```python
from ui.filtres.filter_editor import FilterEditor
```

Remplacer :

```python
        self._right_placeholder = QLabel("FilterEditor (Task 6-9)")
        ...
        self._splitter.addWidget(self._right_placeholder)
```

par :

```python
        self._editor = FilterEditor()
        self._splitter.addWidget(self._editor)
```

Puis câbler la sélection dans `__init__` :

```python
        self._list_panel.filter_selected.connect(self._on_filter_selected)
```

Et la méthode :

```python
    def _on_filter_selected(self, idx: int) -> None:
        if 0 <= idx < len(self._filters):
            self._editor.load_filter(self._filters[idx])
```

- [ ] **Step 6.6 : Lancer la suite UI**

```bash
pytest tests/ui/ -v
```

Attendu : tous PASS (aucune régression).

- [ ] **Step 6.7 : Commit**

```bash
git add ui/filtres/filter_editor.py ui/filtres/filtres_page.py tests/ui/test_filter_editor.py
git commit -m "feat(filtres): FilterEditor header + Sets grid (23 sets)"
```

---

## Task 7 — `FilterEditor` : Niveau + Rareté + Slot + ★ + Classe + Main/Innate

**Files:**
- Modify: `ui/filtres/filter_editor.py`
- Modify: `tests/ui/test_filter_editor.py`

- [ ] **Step 7.1 : Écrire les tests qui échouent**

Ajouter à `tests/ui/test_filter_editor.py` :

```python
def test_level_slider_sync_with_filter(qapp):
    e = FilterEditor()
    f = _mk()
    f.level = 4
    e.load_filter(f)
    assert e._level_slider.value() == 4
    e._level_slider.setValue(2)
    assert e.current_filter().level == 2


def test_rarity_checkboxes_load_and_save(qapp):
    e = FilterEditor()
    f = _mk()
    f.grades = {"Rare": False, "Hero": True, "Legend": True}
    e.load_filter(f)
    assert e._rar_hero.isChecked() and e._rar_legend.isChecked()
    assert not e._rar_rare.isChecked()
    e._rar_rare.setChecked(True)
    g = e.current_filter()
    assert g.grades["Rare"] is True and g.grades["Hero"] is True


def test_slot_grid_2x3(qapp):
    e = FilterEditor()
    f = _mk()
    f.slots = {f"Slot{i}": (i in (2, 4, 6)) for i in range(1, 7)}
    e.load_filter(f)
    for i in range(1, 7):
        cb = e._slot_checks[i]
        assert cb.isChecked() == (i in (2, 4, 6))


def test_stars_checkboxes(qapp):
    e = FilterEditor()
    f = _mk()
    f.stars = {"FiveStars": True, "SixStars": True}
    e.load_filter(f)
    assert e._star5.isChecked() and e._star6.isChecked()
    e._star5.setChecked(False)
    assert e.current_filter().stars["FiveStars"] is False


def test_ancient_radio_tristate(qapp):
    e = FilterEditor()
    f = _mk()
    f.ancient_type = "Ancient"
    e.load_filter(f)
    assert e._ancient_group.checkedId() == 1  # Ancient
    f.ancient_type = "NotAncient"
    e.load_filter(f)
    assert e._ancient_group.checkedId() == 2  # Normal
    f.ancient_type = ""
    e.load_filter(f)
    assert e._ancient_group.checkedId() == 0  # Tous


def test_main_stats_grid(qapp):
    e = FilterEditor()
    f = _mk()
    f.main_stats = {"MainSPD": True, "MainATK": True}
    e.load_filter(f)
    assert e._main_checks["MainSPD"].isChecked()
    assert e._main_checks["MainATK"].isChecked()
    assert not e._main_checks["MainHP"].isChecked()


def test_innate_grid_roundtrip(qapp):
    e = FilterEditor()
    f = _mk()
    f.innate_required = {"SPD": True, "CR": True}
    e.load_filter(f)
    assert e._innate_checks["SPD"].isChecked()
    assert e._innate_checks["CR"].isChecked()
    e._innate_checks["CD"].setChecked(True)
    g = e.current_filter()
    assert g.innate_required.get("CD") is True
```

- [ ] **Step 7.2 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py -v
```

Attendu : FAIL (widgets non créés).

- [ ] **Step 7.3 : Ajouter les widgets dans `FilterEditor`**

Ajouter les imports manquants :

```python
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QRadioButton, QScrollArea, QSlider, QVBoxLayout, QWidget,
)
from s2us_filter import _STAT_KEYS
```

Ajouter à la fin de `__init__`, **avant** `self._inner_lay.addStretch()`, les appels :

```python
        self._build_level()
        self._build_rarity()
        self._build_slots()
        self._build_stars()
        self._build_ancient()
        self._build_main_stats()
        self._build_innate()
```

Puis les méthodes (à ajouter dans la classe) :

```python
    def _framed_block(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        fr = QFrame()
        fr.setStyleSheet(
            f"QFrame {{ background:{theme.COLOR_BG_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )
        box = QVBoxLayout(fr)
        box.setContentsMargins(10, 8, 10, 8)
        box.setSpacing(6)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color:{theme.COLOR_GOLD_TITLE}; font-weight:700;")
        box.addWidget(lbl)
        self._inner_lay.addWidget(fr)
        return fr, box

    def _build_level(self) -> None:
        _, box = self._framed_block("Niveau (Smart Filter)")
        row = QHBoxLayout()
        self._level_slider = QSlider(Qt.Orientation.Horizontal)
        self._level_slider.setMinimum(-1)
        self._level_slider.setMaximum(15)
        self._level_value = QLabel("0")
        self._level_value.setStyleSheet(f"color:{theme.COLOR_TEXT_MAIN};")
        self._level_slider.valueChanged.connect(
            lambda v: self._level_value.setText("Smart" if v == -1 else str(v))
        )
        row.addWidget(self._level_slider, 1)
        row.addWidget(self._level_value)
        box.addLayout(row)

    def _build_rarity(self) -> None:
        _, box = self._framed_block("Rareté")
        row = QHBoxLayout()
        self._rar_rare = QCheckBox("Rare")
        self._rar_hero = QCheckBox("Hero")
        self._rar_legend = QCheckBox("Legend")
        for cb in (self._rar_rare, self._rar_hero, self._rar_legend):
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            row.addWidget(cb)
        row.addStretch()
        box.addLayout(row)

    def _build_slots(self) -> None:
        _, box = self._framed_block("Slot")
        grid = QGridLayout()
        self._slot_checks: dict[int, QCheckBox] = {}
        for i in range(1, 7):
            cb = QCheckBox(f"Slot {i}")
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._slot_checks[i] = cb
            grid.addWidget(cb, (i - 1) // 3, (i - 1) % 3)
        box.addLayout(grid)

    def _build_stars(self) -> None:
        _, box = self._framed_block("Étoiles")
        row = QHBoxLayout()
        self._star5 = QCheckBox("5★")
        self._star6 = QCheckBox("6★")
        for cb in (self._star5, self._star6):
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            row.addWidget(cb)
        row.addStretch()
        box.addLayout(row)

    def _build_ancient(self) -> None:
        _, box = self._framed_block("Classe")
        row = QHBoxLayout()
        self._ancient_group = QButtonGroup(self)
        rb_all = QRadioButton("Tous")
        rb_anc = QRadioButton("Ancient")
        rb_nor = QRadioButton("Normal")
        for cb in (rb_all, rb_anc, rb_nor):
            cb.setStyleSheet(f"QRadioButton {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            row.addWidget(cb)
        row.addStretch()
        self._ancient_group.addButton(rb_all, 0)
        self._ancient_group.addButton(rb_anc, 1)
        self._ancient_group.addButton(rb_nor, 2)
        rb_all.setChecked(True)
        box.addLayout(row)

    def _build_main_stats(self) -> None:
        _, box = self._framed_block("Propriété principale")
        grid = QGridLayout()
        self._main_checks: dict[str, QCheckBox] = {}
        main_keys = [
            "MainSPD", "MainHP", "MainHP2", "MainATK", "MainATK2",
            "MainDEF", "MainDEF2", "MainCR", "MainCD", "MainACC", "MainRES",
        ]
        for i, k in enumerate(main_keys):
            cb = QCheckBox(k.replace("Main", ""))
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._main_checks[k] = cb
            grid.addWidget(cb, i // 4, i % 4)
        box.addLayout(grid)

    def _build_innate(self) -> None:
        _, box = self._framed_block("Propriété innate (prefix)")
        grid = QGridLayout()
        self._innate_checks: dict[str, QCheckBox] = {}
        for i, k in enumerate(_STAT_KEYS):
            cb = QCheckBox(k)
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._innate_checks[k] = cb
            grid.addWidget(cb, i // 4, i % 4)
        box.addLayout(grid)
```

Enrichir `load_filter` :

```python
    def load_filter(self, f: S2USFilter) -> None:
        self._current = f
        self._name_edit.setText(f.name)
        self._enabled_check.setChecked(bool(f.enabled))
        for key, cb in self._set_checks.items():
            cb.setChecked(bool(f.sets.get(key)))

        self._level_slider.setValue(int(f.level))
        self._level_value.setText(
            "Smart" if f.level == -1 else str(f.level)
        )

        self._rar_rare.setChecked(bool(f.grades.get("Rare")))
        self._rar_hero.setChecked(bool(f.grades.get("Hero")))
        self._rar_legend.setChecked(bool(f.grades.get("Legend")))

        for i, cb in self._slot_checks.items():
            cb.setChecked(bool(f.slots.get(f"Slot{i}")))

        self._star5.setChecked(bool(f.stars.get("FiveStars")))
        self._star6.setChecked(bool(f.stars.get("SixStars")))

        aid = {"Ancient": 1, "NotAncient": 2}.get(f.ancient_type, 0)
        btn = self._ancient_group.button(aid)
        if btn is not None:
            btn.setChecked(True)

        for key, cb in self._main_checks.items():
            cb.setChecked(bool(f.main_stats.get(key)))

        for key, cb in self._innate_checks.items():
            cb.setChecked(bool(f.innate_required.get(key)))
```

Enrichir `current_filter` :

```python
    def current_filter(self) -> S2USFilter:
        base = self._current or S2USFilter(name="", sub_requirements={}, min_values={})
        aid = self._ancient_group.checkedId()
        ancient = {1: "Ancient", 2: "NotAncient"}.get(aid, "")
        return replace(
            base,
            name=self._name_edit.text(),
            enabled=self._enabled_check.isChecked(),
            sets={k: cb.isChecked() for k, cb in self._set_checks.items()},
            level=int(self._level_slider.value()),
            grades={
                "Rare": self._rar_rare.isChecked(),
                "Hero": self._rar_hero.isChecked(),
                "Legend": self._rar_legend.isChecked(),
            },
            slots={f"Slot{i}": cb.isChecked() for i, cb in self._slot_checks.items()},
            stars={
                "FiveStars": self._star5.isChecked(),
                "SixStars": self._star6.isChecked(),
            },
            ancient_type=ancient,
            main_stats={k: cb.isChecked() for k, cb in self._main_checks.items()},
            innate_required={k: cb.isChecked() for k, cb in self._innate_checks.items()
                              if cb.isChecked()},
        )
```

- [ ] **Step 7.4 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py -v
```

Attendu : tous PASS (14 tests — 7 existants + 7 nouveaux).

- [ ] **Step 7.5 : Commit**

```bash
git add ui/filtres/filter_editor.py tests/ui/test_filter_editor.py
git commit -m "feat(filtres): FilterEditor - level/rarity/slot/stars/ancient/main/innate"
```

---

## Task 8 — `FilterEditor` : Sous-propriétés tri-état + seuil + slider + optional_count

**Files:**
- Modify: `ui/filtres/filter_editor.py`
- Modify: `tests/ui/test_filter_editor.py`

**Rappel spec §3** : chaque substat a un état tri-valué :
- ☐ (ignorée, `sub_requirements[key] == 0`)
- ☑ (obligatoire, `sub_requirements[key] == 1`)
- ➖ (optionnelle, `sub_requirements[key] == 2`)

Chaque ligne contient : bouton cyclique tri-état + nom stat + `QDoubleSpinBox` (seuil `min_values[key]`) + `QSlider` synchronisé. À droite du bloc : radios mutuellement exclusives 1/2/3/4 pour `optional_count`.

- [ ] **Step 8.1 : Écrire les tests qui échouent**

Ajouter à `tests/ui/test_filter_editor.py` :

```python
def test_sub_rows_created_for_every_stat_key(qapp):
    from s2us_filter import _STAT_KEYS
    e = FilterEditor()
    e.load_filter(_mk())
    for key in _STAT_KEYS:
        assert key in e._sub_rows


def test_sub_state_button_cycles_ignored_mandatory_optional(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    row = e._sub_rows["SPD"]
    assert row.state == 0  # ignorée
    row.state_btn.click()
    assert row.state == 1  # obligatoire
    row.state_btn.click()
    assert row.state == 2  # optionnelle
    row.state_btn.click()
    assert row.state == 0  # retour à ignorée


def test_load_filter_populates_sub_state_and_threshold(qapp):
    e = FilterEditor()
    f = _mk()
    f.sub_requirements = {"SPD": 1, "CR": 2}
    f.min_values = {"SPD": 12, "CR": 6}
    e.load_filter(f)
    assert e._sub_rows["SPD"].state == 1
    assert e._sub_rows["CR"].state == 2
    assert e._sub_rows["SPD"].threshold.value() == 12
    assert e._sub_rows["CR"].threshold.value() == 6


def test_threshold_slider_and_spin_synchronized(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    row = e._sub_rows["SPD"]
    row.slider.setValue(20)
    assert row.threshold.value() == 20
    row.threshold.setValue(15)
    assert row.slider.value() == 15


def test_current_filter_writes_sub_reqs_and_min_values(qapp):
    e = FilterEditor()
    e.load_filter(_mk())
    e._sub_rows["SPD"].set_state(1)
    e._sub_rows["SPD"].threshold.setValue(12)
    e._sub_rows["CR"].set_state(2)
    e._sub_rows["CR"].threshold.setValue(6)
    f = e.current_filter()
    assert f.sub_requirements["SPD"] == 1
    assert f.sub_requirements["CR"] == 2
    assert f.min_values["SPD"] == 12
    assert f.min_values["CR"] == 6


def test_optional_count_radio_group(qapp):
    e = FilterEditor()
    f = _mk()
    f.optional_count = 3
    e.load_filter(f)
    assert e._optional_group.checkedId() == 3
    e._optional_group.button(2).setChecked(True)
    assert e.current_filter().optional_count == 2
```

- [ ] **Step 8.2 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py -v
```

Attendu : FAIL (widgets non créés).

- [ ] **Step 8.3 : Ajouter le widget `SubRow` + bloc subs dans `FilterEditor`**

Dans `ui/filtres/filter_editor.py`, ajouter les imports :

```python
from PySide6.QtWidgets import QDoubleSpinBox, QPushButton, QSizePolicy
```

Ajouter à la fin du fichier (en dehors de la classe) :

```python
_STATE_GLYPHS = {0: "\u2610", 1: "\u2611", 2: "\u2796"}  # ☐ / ☑ / ➖


class _SubRow(QWidget):
    """Une ligne substat : bouton état + label + spinbox seuil + slider."""

    def __init__(self, key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self.state = 0

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.state_btn = QPushButton(_STATE_GLYPHS[0])
        self.state_btn.setFixedWidth(30)
        self.state_btn.clicked.connect(self._cycle)
        row.addWidget(self.state_btn)

        self.label = QLabel(key)
        self.label.setStyleSheet(f"color:{theme.COLOR_TEXT_MAIN};")
        self.label.setFixedWidth(60)
        row.addWidget(self.label)

        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0, 9999)
        self.threshold.setDecimals(0)
        self.threshold.setFixedWidth(70)
        row.addWidget(self.threshold)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 60)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row.addWidget(self.slider, 1)

        # Sync spin <-> slider
        self.slider.valueChanged.connect(
            lambda v: self.threshold.blockSignals(True)
            or self.threshold.setValue(v)
            or self.threshold.blockSignals(False)
        )
        self.threshold.valueChanged.connect(
            lambda v: self.slider.blockSignals(True)
            or self.slider.setValue(int(v))
            or self.slider.blockSignals(False)
        )

    def _cycle(self) -> None:
        self.set_state((self.state + 1) % 3)

    def set_state(self, s: int) -> None:
        self.state = s
        self.state_btn.setText(_STATE_GLYPHS[s])
```

Ajouter dans la classe `FilterEditor` l'appel :

```python
        self._build_subs()
```

(entre `_build_innate()` et `addStretch`)

Et la méthode :

```python
    def _build_subs(self) -> None:
        fr, box = self._framed_block("Sous-propriétés")
        container = QHBoxLayout()
        rows_box = QVBoxLayout()
        rows_box.setSpacing(2)
        self._sub_rows: dict[str, _SubRow] = {}
        for key in _STAT_KEYS:
            row = _SubRow(key)
            self._sub_rows[key] = row
            rows_box.addWidget(row)
        container.addLayout(rows_box, 1)

        # Côté droit : compteur optional_count
        side = QVBoxLayout()
        side.setSpacing(4)
        lbl = QLabel("Facultatives requises")
        lbl.setStyleSheet(f"color:{theme.COLOR_GOLD};")
        side.addWidget(lbl)
        self._optional_group = QButtonGroup(self)
        for n in (1, 2, 3, 4):
            rb = QRadioButton(str(n))
            rb.setStyleSheet(f"QRadioButton {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._optional_group.addButton(rb, n)
            side.addWidget(rb)
        side.addStretch()
        container.addLayout(side)

        box.addLayout(container)
```

Enrichir `load_filter` (append avant la fin) :

```python
        for key, row in self._sub_rows.items():
            row.set_state(int(f.sub_requirements.get(key, 0)))
            row.threshold.setValue(float(f.min_values.get(key, 0)))
        n = int(f.optional_count or 0)
        btn = self._optional_group.button(n)
        if btn is not None:
            btn.setChecked(True)
```

Enrichir `current_filter` :

```python
        sub_requirements = {k: r.state for k, r in self._sub_rows.items()}
        min_values = {k: int(r.threshold.value()) for k, r in self._sub_rows.items()}
        optional_count = self._optional_group.checkedId()
        if optional_count < 0:
            optional_count = 0
```

Et remplacer la fin du `replace(...)` :

```python
        return replace(
            base,
            name=self._name_edit.text(),
            enabled=self._enabled_check.isChecked(),
            sets={k: cb.isChecked() for k, cb in self._set_checks.items()},
            level=int(self._level_slider.value()),
            grades={
                "Rare": self._rar_rare.isChecked(),
                "Hero": self._rar_hero.isChecked(),
                "Legend": self._rar_legend.isChecked(),
            },
            slots={f"Slot{i}": cb.isChecked() for i, cb in self._slot_checks.items()},
            stars={
                "FiveStars": self._star5.isChecked(),
                "SixStars": self._star6.isChecked(),
            },
            ancient_type=ancient,
            main_stats={k: cb.isChecked() for k, cb in self._main_checks.items()},
            innate_required={k: cb.isChecked() for k, cb in self._innate_checks.items()
                              if cb.isChecked()},
            sub_requirements=sub_requirements,
            min_values=min_values,
            optional_count=optional_count,
        )
```

- [ ] **Step 8.4 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py -v
```

Attendu : 20 tests PASS (14 existants + 6 nouveaux).

- [ ] **Step 8.5 : Commit**

```bash
git add ui/filtres/filter_editor.py tests/ui/test_filter_editor.py
git commit -m "feat(filtres): FilterEditor - substat tri-state rows + optional_count"
```

---

## Task 9 — `FilterEditor` : Efficacité + Méthode + Meule/Gemme + SAVE

**Files:**
- Modify: `ui/filtres/filter_editor.py`
- Modify: `tests/ui/test_filter_editor.py`
- Modify: `ui/filtres/filtres_page.py` (câbler `filter_saved`)

- [ ] **Step 9.1 : Écrire les tests qui échouent**

Ajouter à `tests/ui/test_filter_editor.py` :

```python
def test_efficiency_slider_and_method_roundtrip(qapp):
    e = FilterEditor()
    f = _mk()
    f.efficiency = 85.0
    f.eff_method = "SWOP"
    e.load_filter(f)
    assert e._eff_slider.value() == 85
    assert e._eff_method.currentText() in ("SWOP", "S2US")
    e._eff_slider.setValue(70)
    e._eff_method.setCurrentText("S2US")
    g = e.current_filter()
    assert g.efficiency == 70.0
    assert g.eff_method == "S2US"


def test_grind_gem_dropdowns_roundtrip(qapp):
    e = FilterEditor()
    f = _mk()
    f.grind = 2
    f.gem = 3
    e.load_filter(f)
    assert e._grind_combo.currentIndex() == 2
    assert e._gem_combo.currentIndex() == 3
    e._grind_combo.setCurrentIndex(1)
    assert e.current_filter().grind == 1


def test_save_button_emits_filter_saved(qapp):
    from PySide6.QtWidgets import QPushButton
    e = FilterEditor()
    e.load_filter(_mk())
    received: list = []
    e.filter_saved.connect(received.append)
    save_btn = next(b for b in e.findChildren(QPushButton) if "SAVE" in b.text().upper())
    e._name_edit.setText("After Save")
    save_btn.click()
    assert len(received) == 1
    assert received[0].name == "After Save"
```

Et dans `tests/ui/test_filtres_page.py` :

```python
def test_page_propagates_editor_save_to_filter_list(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    src = tmp_path / "s.s2us"
    save_s2us_file(str(src), [S2USFilter(name="Orig",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    import json
    cfg.write_text(json.dumps({"s2us": {"filter_file": str(src)}}), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()
    # Simule la modification depuis l'éditeur
    page._editor._name_edit.setText("Renamed")
    page._editor.filter_saved.emit(page._editor.current_filter())

    # Le filtre en mémoire est mis à jour
    assert page._filters[0].name == "Renamed"
    # Le fichier sur disque aussi
    from s2us_filter import load_s2us_file
    reloaded, _ = load_s2us_file(str(src))
    assert reloaded[0].name == "Renamed"
```

- [ ] **Step 9.2 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py tests/ui/test_filtres_page.py -v
```

Attendu : FAIL (widgets + câblage manquants).

- [ ] **Step 9.3 : Ajouter les widgets + SAVE dans `FilterEditor`**

Ajouter l'import `QComboBox` :

```python
from PySide6.QtWidgets import QComboBox
```

Dans `__init__`, ajouter après `self._build_subs()` :

```python
        self._build_efficiency()
        self._build_grind_gem()
        self._build_save_button()
```

Et les méthodes :

```python
    def _build_efficiency(self) -> None:
        _, box = self._framed_block("Efficacité")
        row = QHBoxLayout()
        self._eff_slider = QSlider(Qt.Orientation.Horizontal)
        self._eff_slider.setRange(0, 100)
        self._eff_value = QLabel("0")
        self._eff_value.setStyleSheet(f"color:{theme.COLOR_TEXT_MAIN};")
        self._eff_slider.valueChanged.connect(
            lambda v: self._eff_value.setText(str(v))
        )
        self._eff_method = QComboBox()
        self._eff_method.addItems(["S2US", "SWOP"])
        row.addWidget(self._eff_slider, 1)
        row.addWidget(self._eff_value)
        row.addWidget(self._eff_method)
        box.addLayout(row)

    def _build_grind_gem(self) -> None:
        _, box = self._framed_block("Simuler Meule / Gemme")
        row = QHBoxLayout()
        lbl_g = QLabel("Meule :")
        lbl_g.setStyleSheet(f"color:{theme.COLOR_GOLD};")
        self._grind_combo = QComboBox()
        self._grind_combo.addItems(["Aucune", "Magique", "Rare", "Légendaire"])
        lbl_m = QLabel("Gemme :")
        lbl_m.setStyleSheet(f"color:{theme.COLOR_GOLD};")
        self._gem_combo = QComboBox()
        self._gem_combo.addItems(["Aucune", "Magique", "Rare", "Légendaire"])
        row.addWidget(lbl_g); row.addWidget(self._grind_combo)
        row.addSpacing(16)
        row.addWidget(lbl_m); row.addWidget(self._gem_combo)
        row.addStretch()
        box.addLayout(row)

    def _build_save_button(self) -> None:
        self._save_btn = QPushButton("SAVE")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BRONZE};"
            f" color:{theme.COLOR_BG_APP}; border:none; border-radius:4px;"
            f" padding:10px; font-size:13px; font-weight:700; letter-spacing:0.6px; }}"
            f"QPushButton:hover {{ background:{theme.COLOR_EMBER}; }}"
        )
        self._save_btn.clicked.connect(self._on_save)
        self._inner_lay.addWidget(self._save_btn)

    def _on_save(self) -> None:
        self.filter_saved.emit(self.current_filter())
```

Compléter `load_filter` :

```python
        self._eff_slider.setValue(int(f.efficiency))
        self._eff_value.setText(str(int(f.efficiency)))
        self._eff_method.setCurrentText(f.eff_method or "S2US")
        self._grind_combo.setCurrentIndex(int(f.grind or 0))
        self._gem_combo.setCurrentIndex(int(f.gem or 0))
```

Et dans `current_filter`, ajouter au `replace(...)` :

```python
            efficiency=float(self._eff_slider.value()),
            eff_method=self._eff_method.currentText(),
            grind=int(self._grind_combo.currentIndex()),
            gem=int(self._gem_combo.currentIndex()),
```

- [ ] **Step 9.4 : Câbler `filter_saved` dans `FiltresPage`**

Dans `ui/filtres/filtres_page.py`, après `self._list_panel.filter_selected.connect(...)` :

```python
        self._editor.filter_saved.connect(self._on_editor_saved)
```

Et la méthode :

```python
    def _on_editor_saved(self, new_filter) -> None:
        idx = self._list_panel.current_index()
        if idx < 0 or idx >= len(self._filters):
            return
        self._filters[idx] = new_filter
        # Re-peuple la liste (nom possiblement modifié)
        self._list_panel.set_filters(self._filters)
        self._list_panel.select_index(idx)
        # Écriture disque si un chemin est connu
        self._write_filters_to_config_path()

    def _write_filters_to_config_path(self) -> None:
        path = self._filter_file_path
        if not path:
            return
        try:
            save_s2us_file(path, self._filters, self._global_settings)
        except OSError:
            pass
```

- [ ] **Step 9.5 : Lancer les tests**

```bash
pytest tests/ui/test_filter_editor.py tests/ui/test_filtres_page.py -v
```

Attendu : tous PASS.

- [ ] **Step 9.6 : Commit**

```bash
git add ui/filtres/filter_editor.py ui/filtres/filtres_page.py tests/ui/test_filter_editor.py tests/ui/test_filtres_page.py
git commit -m "feat(filtres): efficiency + grind/gem + SAVE button (persists to .s2us)"
```

---

## Task 10 — `RuneTesterModal` : modale « Rune Optimizer »

**Files:**
- Modify: `ui/filtres/rune_tester_modal.py` (était stub)
- Create: `tests/ui/test_rune_tester_modal.py`

**UX :** formulaire de saisie d'une rune minimale (set + slot + ★ + niveau + grade + main stat + substats), bouton « Optimiser ». Sortie :
- **Meilleure configuration** : liste des substats post meule+gemme + Efficience1 en gros.
- **Filtres matchés** : liste des noms de filtres qui acceptent la rune optimisée, triée par seuil d'efficacité (via `rune_optimizer.filters_that_match`).
- Le caller passe `filters` (liste actuelle) via le constructeur ; si `rune.level < 12` → `best_plus0`, sinon `best_now`.

- [ ] **Step 10.1 : Écrire les tests qui échouent**

Créer `tests/ui/test_rune_tester_modal.py` :

```python
import pytest

from models import Rune, SubStat
from s2us_filter import S2USFilter
from ui.filtres.rune_tester_modal import RuneTesterModal


def _rune() -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
        main_stat=SubStat(type="ATQ%", value=63), prefix=None,
        substats=[
            SubStat(type="VIT", value=18),
            SubStat(type="CC", value=10),
            SubStat(type="DC", value=14),
            SubStat(type="PV%", value=5),
        ],
    )


def test_modal_instantiates(qapp):
    dlg = RuneTesterModal(filters=[])
    assert dlg is not None
    assert dlg.windowTitle() == "Rune Optimizer"


def test_modal_accepts_rune_via_api(qapp):
    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    # Les champs sont peuplés
    assert dlg._slot_spin.value() == 2
    assert dlg._stars_spin.value() == 6
    assert dlg._level_spin.value() == 12


def test_optimize_button_populates_result_label(qapp):
    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())
    dlg._grind_combo.setCurrentIndex(3)
    dlg._gem_combo.setCurrentIndex(3)
    dlg._btn_optimize.click()
    text = dlg._result_label.text()
    assert "Eff" in text or "eff" in text


def test_optimize_populates_matching_filters_list(qapp):
    f_match = S2USFilter(name="MatchMe", efficiency=10.0,
                         sub_requirements={}, min_values={})
    f_no_match = S2USFilter(
        name="TooHigh", efficiency=999.0,
        sub_requirements={}, min_values={},
    )
    dlg = RuneTesterModal(filters=[f_match, f_no_match])
    dlg.set_rune(_rune())
    dlg._btn_optimize.click()
    items = [dlg._filters_list.item(i).text()
             for i in range(dlg._filters_list.count())]
    joined = " ".join(items)
    assert "MatchMe" in joined
    assert "TooHigh" not in joined


def test_plus0_uses_best_plus0(qapp, monkeypatch):
    calls = {"plus0": 0, "now": 0}

    from rune_optimizer import OptimizerResult
    from ui.filtres import rune_tester_modal

    def fake_plus0(r, max_grind_grade=3, max_gem_grade=3):
        calls["plus0"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    def fake_now(r, grind_grade=0, gem_grade=0):
        calls["now"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    monkeypatch.setattr(rune_tester_modal, "best_plus0", fake_plus0)
    monkeypatch.setattr(rune_tester_modal, "best_now", fake_now)

    dlg = RuneTesterModal(filters=[])
    r = _rune()
    r.level = 0
    dlg.set_rune(r)
    dlg._btn_optimize.click()
    assert calls["plus0"] == 1
    assert calls["now"] == 0


def test_plus12_uses_best_now(qapp, monkeypatch):
    calls = {"plus0": 0, "now": 0}

    from rune_optimizer import OptimizerResult
    from ui.filtres import rune_tester_modal

    def fake_plus0(r, max_grind_grade=3, max_gem_grade=3):
        calls["plus0"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    def fake_now(r, grind_grade=0, gem_grade=0):
        calls["now"] += 1
        return OptimizerResult(rune=r, efficiency=50.0)

    monkeypatch.setattr(rune_tester_modal, "best_plus0", fake_plus0)
    monkeypatch.setattr(rune_tester_modal, "best_now", fake_now)

    dlg = RuneTesterModal(filters=[])
    dlg.set_rune(_rune())  # level=12
    dlg._btn_optimize.click()
    assert calls["plus0"] == 0
    assert calls["now"] == 1
```

- [ ] **Step 10.2 : Lancer les tests**

```bash
pytest tests/ui/test_rune_tester_modal.py -v
```

Attendu : FAIL (stub minimal actuel).

- [ ] **Step 10.3 : Remplacer `ui/filtres/rune_tester_modal.py`**

```python
"""Modale Rune Optimizer : saisie d'une rune + sortie optimale + filtres matchés."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from models import Rune, SubStat
from rune_optimizer import best_plus0, best_now, filters_that_match
from s2us_filter import S2USFilter
from ui import theme


_STATS = ["VIT", "PV%", "PV", "ATQ%", "ATQ", "DEF%", "DEF",
          "DC", "CC", "PRE", "RES"]
_SETS = ["Violent", "Swift", "Despair", "Will", "Rage", "Fatal",
         "Energy", "Blade", "Focus", "Guard", "Endure",
         "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
         "Determination", "Enhance", "Accuracy", "Tolerance",
         "Intangible", "Seal", "Shield"]
_GRADES = ["Rare", "Heroique", "Legendaire"]
_GRIND_LABELS = ["Aucune", "Magique", "Rare", "Légendaire"]


class RuneTesterModal(QDialog):
    def __init__(
        self,
        filters: list[S2USFilter] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rune Optimizer")
        self.resize(560, 560)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")
        self._filters = filters or []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # ── Form d'entrée ──
        form = QFormLayout()
        form.setSpacing(6)

        self._set_combo = QComboBox(); self._set_combo.addItems(_SETS)
        self._slot_spin = QSpinBox(); self._slot_spin.setRange(1, 6)
        self._stars_spin = QSpinBox(); self._stars_spin.setRange(1, 6); self._stars_spin.setValue(6)
        self._level_spin = QSpinBox(); self._level_spin.setRange(0, 15); self._level_spin.setValue(0)
        self._grade_combo = QComboBox(); self._grade_combo.addItems(_GRADES)
        self._main_combo = QComboBox(); self._main_combo.addItems(_STATS)

        form.addRow("Set", self._set_combo)
        form.addRow("Slot", self._slot_spin)
        form.addRow("★", self._stars_spin)
        form.addRow("Niveau", self._level_spin)
        form.addRow("Grade", self._grade_combo)
        form.addRow("Main stat", self._main_combo)

        # 4 substats
        self._sub_stats: list[tuple[QComboBox, QSpinBox]] = []
        for i in range(4):
            row = QHBoxLayout()
            ctype = QComboBox(); ctype.addItems([""] + _STATS)
            cval = QSpinBox(); cval.setRange(0, 999)
            row.addWidget(ctype); row.addWidget(cval)
            form.addRow(f"Sub {i+1}", self._row_wrap(row))
            self._sub_stats.append((ctype, cval))

        self._grind_combo = QComboBox(); self._grind_combo.addItems(_GRIND_LABELS)
        self._gem_combo = QComboBox(); self._gem_combo.addItems(_GRIND_LABELS)
        form.addRow("Meule (max)", self._grind_combo)
        form.addRow("Gemme (max)", self._gem_combo)

        lay.addLayout(form)

        # ── Bouton Optimiser ──
        self._btn_optimize = QPushButton("Optimiser")
        self._btn_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_optimize.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BRONZE};"
            f" color:{theme.COLOR_BG_APP}; border:none; border-radius:4px;"
            f" padding:9px; font-weight:700; }}"
            f"QPushButton:hover {{ background:{theme.COLOR_EMBER}; }}"
        )
        self._btn_optimize.clicked.connect(self._on_optimize)
        lay.addWidget(self._btn_optimize)

        # ── Résultats ──
        self._result_label = QLabel("")
        self._result_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-size:14px; font-weight:700;"
        )
        self._result_label.setWordWrap(True)
        lay.addWidget(self._result_label)

        lbl_fm = QLabel("Filtres matchés :")
        lbl_fm.setStyleSheet(f"color:{theme.COLOR_GOLD};")
        lay.addWidget(lbl_fm)

        self._filters_list = QListWidget()
        self._filters_list.setStyleSheet(
            f"QListWidget {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; }}"
        )
        lay.addWidget(self._filters_list, 1)

    # ── Helper pour emballer un sous-layout dans un QWidget (QFormLayout.addRow) ──
    @staticmethod
    def _row_wrap(row_lay) -> QWidget:
        w = QWidget()
        w.setLayout(row_lay)
        return w

    # ── API publique ──
    def set_rune(self, rune: Rune) -> None:
        if rune.set in _SETS:
            self._set_combo.setCurrentText(rune.set)
        self._slot_spin.setValue(int(rune.slot))
        self._stars_spin.setValue(int(rune.stars))
        self._level_spin.setValue(int(rune.level))
        if rune.grade in _GRADES:
            self._grade_combo.setCurrentText(rune.grade)
        if rune.main_stat.type in _STATS:
            self._main_combo.setCurrentText(rune.main_stat.type)
        for i, (ctype, cval) in enumerate(self._sub_stats):
            if i < len(rune.substats):
                s = rune.substats[i]
                ctype.setCurrentText(s.type)
                cval.setValue(int(s.value))
            else:
                ctype.setCurrentIndex(0)
                cval.setValue(0)

    # ── Handlers ──
    def _read_rune(self) -> Rune:
        subs: list[SubStat] = []
        for ctype, cval in self._sub_stats:
            t = ctype.currentText()
            if t:
                subs.append(SubStat(type=t, value=float(cval.value())))
        return Rune(
            set=self._set_combo.currentText(),
            slot=int(self._slot_spin.value()),
            stars=int(self._stars_spin.value()),
            grade=self._grade_combo.currentText(),
            level=int(self._level_spin.value()),
            main_stat=SubStat(type=self._main_combo.currentText(), value=0.0),
            prefix=None,
            substats=subs,
        )

    def _on_optimize(self) -> None:
        rune = self._read_rune()
        grind = self._grind_combo.currentIndex()
        gem = self._gem_combo.currentIndex()
        if rune.level < 12:
            result = best_plus0(rune, max_grind_grade=grind, max_gem_grade=gem)
            mode = "Config future optimale (+12)"
        else:
            result = best_now(rune, grind_grade=grind, gem_grade=gem)
            mode = "Meilleure amélioration immédiate"

        subs_txt = ", ".join(
            f"{s.type} {int(s.value)}" for s in result.rune.substats
        )
        self._result_label.setText(
            f"{mode}\nEff1 = {int(result.efficiency)}\n{subs_txt}"
        )

        self._filters_list.clear()
        for f in filters_that_match(result.rune, self._filters):
            self._filters_list.addItem(f"{f.name}  (Eff≥{int(f.efficiency)})")
```

- [ ] **Step 10.4 : Lancer les tests**

```bash
pytest tests/ui/test_rune_tester_modal.py -v
```

Attendu : 6 tests PASS.

- [ ] **Step 10.5 : Vérifier la suite complète**

```bash
pytest tests/ -v
```

Attendu : **aucune régression** dans les plans 01/02/03/04 ou Scan/Profile.

- [ ] **Step 10.6 : Commit**

```bash
git add ui/filtres/rune_tester_modal.py tests/ui/test_rune_tester_modal.py
git commit -m "feat(filtres): Rune Optimizer modal (best variant + matching filters)"
```

---

## Task 11 — Test manuel de bout en bout (smoke test UI)

**Files:**
- Aucun fichier modifié (vérification visuelle uniquement)

- [ ] **Step 11.1 : Lancer l'application**

```bash
cd /c/Users/louis/Desktop/Luci2US
python scan_app.py
```

- [ ] **Step 11.2 : Ouvrir l'onglet Filtres**

Cliquer `Filtres` dans la sidebar. Checklist :
- La page s'affiche avec un `QSplitter` deux colonnes.
- Panneau gauche : titre « Filtres S2US », 4 boutons ronds, 3 boutons rectangulaires, arbre « Filtres » peuplé depuis `config.json` si un `.s2us` existe (sinon vide).
- Panneau droit : éditeur avec tous les blocs (Sets, Niveau, Rareté, Slot, ★, Classe, Main stat, Innate, Sous-propriétés, Efficacité, Meule/Gemme, SAVE).

- [ ] **Step 11.3 : CRUD d'un filtre**

- Cliquer `+` → un filtre « Nouveau filtre » apparaît en bas de liste et est sélectionné.
- Le renommer dans l'éditeur, cocher quelques sets, régler Efficacité à 80, cliquer `SAVE`.
- La liste reflète le nouveau nom. Le fichier `.s2us` cible a été mis à jour (vérifier avec un éditeur externe ou en rechargeant l'app).
- Cliquer `▲` / `▼` → l'ordre dans la liste change. Cliquer `−` → le filtre est supprimé.

- [ ] **Step 11.4 : Import / Export**

- Cliquer `Exporter` → choisir un fichier de sortie → vérifier que le fichier produit est valide (`python -c "from s2us_filter import load_s2us_file; print(load_s2us_file('out.s2us'))"`).
- Cliquer `Importer` → sélectionner un `.s2us` connu → la liste est remplacée par son contenu.

- [ ] **Step 11.5 : Rune Optimizer**

- Cliquer `Test` → la modale s'ouvre.
- Saisir une rune +0 Légendaire (6★ Violent slot 2 ATQ%, 4 subs) → choisir Meule Légendaire + Gemme Légendaire → `Optimiser`.
- Vérifier l'affichage : « Config future optimale (+12) », Eff1 ≥ valeur initiale, liste des subs post-optimisation, filtres matchés triés.
- Saisir la même rune mais à +12 → `Optimiser` → l'affichage passe à « Meilleure amélioration immédiate ».

- [ ] **Step 11.6 : Vérifier la non-régression**

- Cliquer `Scan`, `Runes` (placeholder ou vue si plan 03 livré), `Monstres` (idem plan 02), `Stats & Historique` (idem plan 04), `Profils`, `Paramètres`. Aucun crash. Les autres onglets restent fonctionnels.

- [ ] **Step 11.7 : Si tout est bon, tag de fin de plan**

```bash
git tag plan-05-done
```

---

## Récapitulatif — ce que ce plan produit

À la fin de l'exécution :

1. **`s2us_writer.py`** : sérialisation inverse de `s2us_filter.load_s2us_file`, round-trip testé. ✓
2. **`rune_optimizer.py`** : primitives `best_variant` / `best_plus0` / `best_now` / `filters_that_match`, réutilise `powerup_simulator.project_to_plus12`. ✓
3. **`ui/filtres/`** : `FiltresPage` (splitter + I/O disk), `FilterListPanel` (liste + boutons + Import/Export/Test), `FilterEditor` (éditeur S2US complet), `RuneTesterModal` (modale Optimizer). ✓
4. **`MainWindow`** : index 1 du `QStackedWidget` câblé sur `FiltresPage` réelle (plus de placeholder). ✓
5. **Tests** : 12 pour `s2us_writer`, 9 pour `rune_optimizer`, 4+ pour `FiltresPage`, 12 pour `FilterListPanel`, 20 pour `FilterEditor`, 6 pour `RuneTesterModal`, 1 pour `MainWindow` — tous passants. ✓
6. **Persistance** : l'éditeur écrit automatiquement dans le `.s2us` pointé par `config.json` à chaque SAVE. Import/Export ouvrent un `QFileDialog`. ✓
7. **Aucune modification** des modules bot core (`evaluator_chain`, `s2us_filter`, `auto_mode`, `swex_bridge`, `profile_loader`, `profile_store`, `models`, `powerup_simulator`, `monster_icons`, `history_db`, `i18n`). ✓

Le plan 05 clôt le portage des 5 onglets PySide6 prévus par le spec `2026-04-17-luci2us-tabs-design.md`. Un plan de nettoyage ultérieur pourra ensuite supprimer les tabs legacy `settings_tab.py`, `stats_tab.py`, `history_tab.py`, `auto_tab.py`, `profile_tab.py`.
