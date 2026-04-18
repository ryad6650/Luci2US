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
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from models import SETS_FR, SET_FR_TO_EN
from s2us_filter import S2USFilter, _STAT_KEYS
from ui import theme


class FilterEditor(QWidget):
    filter_saved = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        self._current: S2USFilter | None = None

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
        self._build_level()
        self._build_rarity()
        self._build_slots()
        self._build_stars()
        self._build_ancient()
        self._build_main_stats()
        self._build_innate()
        self._build_subs()
        self._build_efficiency()
        self._build_grind_gem()
        self._build_save_button()

        self._inner_lay.addStretch()

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
        _, box = self._framed_block("Rarete")
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
        _, box = self._framed_block("Etoiles")
        row = QHBoxLayout()
        self._star5 = QCheckBox("5\u2605")
        self._star6 = QCheckBox("6\u2605")
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
        _, box = self._framed_block("Propriete principale")
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
        _, box = self._framed_block("Propriete innate (prefix)")
        grid = QGridLayout()
        self._innate_checks: dict[str, QCheckBox] = {}
        for i, k in enumerate(_STAT_KEYS):
            cb = QCheckBox(k)
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._innate_checks[k] = cb
            grid.addWidget(cb, i // 4, i % 4)
        box.addLayout(grid)

    def _build_efficiency(self) -> None:
        _, box = self._framed_block("Efficacite")
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
        self._grind_combo.addItems(["Aucune", "Magique", "Rare", "Legendaire"])
        lbl_m = QLabel("Gemme :")
        lbl_m.setStyleSheet(f"color:{theme.COLOR_GOLD};")
        self._gem_combo = QComboBox()
        self._gem_combo.addItems(["Aucune", "Magique", "Rare", "Legendaire"])
        row.addWidget(lbl_g)
        row.addWidget(self._grind_combo)
        row.addSpacing(16)
        row.addWidget(lbl_m)
        row.addWidget(self._gem_combo)
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

    def _build_subs(self) -> None:
        _, box = self._framed_block("Sous-proprietes")
        container = QHBoxLayout()
        rows_box = QVBoxLayout()
        rows_box.setSpacing(2)
        self._sub_rows: dict[str, _SubRow] = {}
        for key in _STAT_KEYS:
            row = _SubRow(key)
            self._sub_rows[key] = row
            rows_box.addWidget(row)
        container.addLayout(rows_box, 1)

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
        self._set_checks: dict[str, QCheckBox] = {}
        for i, set_fr in enumerate(SETS_FR):
            set_en = SET_FR_TO_EN[set_fr]
            cb = QCheckBox(set_en)
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._set_checks[set_en] = cb
            grid.addWidget(cb, i // 6, i % 6)
        box.addLayout(grid)
        self._inner_lay.addWidget(self._sets_frame)

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

        for key, row in self._sub_rows.items():
            row.set_state(int(f.sub_requirements.get(key, 0)))
            row.threshold.setValue(float(f.min_values.get(key, 0)))
        n = int(f.optional_count or 0)
        btn = self._optional_group.button(n)
        if btn is not None:
            btn.setChecked(True)

        self._eff_slider.setValue(int(f.efficiency))
        self._eff_value.setText(str(int(f.efficiency)))
        self._eff_method.setCurrentText(f.eff_method or "S2US")
        self._grind_combo.setCurrentIndex(int(f.grind or 0))
        self._gem_combo.setCurrentIndex(int(f.gem or 0))

    def current_filter(self) -> S2USFilter:
        base = self._current or S2USFilter(name="", sub_requirements={}, min_values={})
        aid = self._ancient_group.checkedId()
        ancient = {1: "Ancient", 2: "NotAncient"}.get(aid, "")
        sub_requirements = {k: r.state for k, r in self._sub_rows.items()}
        min_values = {k: int(r.threshold.value()) for k, r in self._sub_rows.items()}
        optional_count = self._optional_group.checkedId()
        if optional_count < 0:
            optional_count = 0
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
            efficiency=float(self._eff_slider.value()),
            eff_method=self._eff_method.currentText(),
            grind=int(self._grind_combo.currentIndex()),
            gem=int(self._gem_combo.currentIndex()),
        )


_STATE_GLYPHS = {0: "\u2610", 1: "\u2611", 2: "\u2796"}


class _SubRow(QWidget):
    """Une ligne substat : bouton etat + label + spinbox seuil + slider."""

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

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.threshold.valueChanged.connect(self._on_threshold_changed)

    def _on_slider_changed(self, v: int) -> None:
        self.threshold.blockSignals(True)
        self.threshold.setValue(v)
        self.threshold.blockSignals(False)

    def _on_threshold_changed(self, v: float) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(int(v))
        self.slider.blockSignals(False)

    def _cycle(self) -> None:
        self.set_state((self.state + 1) % 3)

    def set_state(self, s: int) -> None:
        self.state = s
        self.state_btn.setText(_STATE_GLYPHS[s])
