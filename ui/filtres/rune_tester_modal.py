"""Modale Rune Optimizer : saisie d'une rune + sortie optimale + filtres matches."""
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


_STATS_DISPLAY = ["SPD", "HP%", "HP", "ATK%", "ATK", "DEF%", "DEF",
                  "CD", "CR", "ACC", "RES"]
_DISPLAY_TO_FR = {
    "SPD": "VIT", "HP%": "PV%", "HP": "PV",
    "ATK%": "ATQ%", "ATK": "ATQ",
    "DEF%": "DEF%", "DEF": "DEF",
    "CD": "DC", "CR": "CC", "ACC": "PRE", "RES": "RES",
}
_FR_TO_DISPLAY = {v: k for k, v in _DISPLAY_TO_FR.items()}
_FIXED_MAIN_BY_SLOT = {1: "ATK", 3: "DEF", 5: "HP"}
_SETS = ["Violent", "Swift", "Despair", "Will", "Rage", "Fatal",
         "Energy", "Blade", "Focus", "Guard", "Endure",
         "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
         "Determination", "Enhance", "Accuracy", "Tolerance",
         "Intangible", "Seal", "Shield"]
_GRADES = ["Rare", "Heroique", "Legendaire"]
_GRIND_LABELS = ["Aucune", "Magique", "Rare", "Legendaire"]


class RuneTesterModal(QDialog):
    def __init__(
        self,
        filters: list[S2USFilter] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rune Optimizer")
        self.resize(560, 560)
        self.setStyleSheet(
            f"QDialog {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            f" stop:0 {theme.COLOR_BG_GRAD_HI},"
            f" stop:1 {theme.COLOR_BG_GRAD_LO});"
            f" border: 1px solid {theme.COLOR_BORDER_FRAME}; }}"
            f"QLabel {{ color:{theme.COLOR_TEXT_MAIN}; background: transparent; }}"
            f"QComboBox, QSpinBox {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:3px 6px; }}"
        )
        self._filters = filters or []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(6)

        self._set_combo = QComboBox()
        self._set_combo.addItems(_SETS)
        self._slot_spin = QSpinBox()
        self._slot_spin.setRange(1, 6)
        self._stars_spin = QSpinBox()
        self._stars_spin.setRange(1, 6)
        self._stars_spin.setValue(6)
        self._level_spin = QSpinBox()
        self._level_spin.setRange(0, 15)
        self._level_spin.setValue(0)
        self._grade_combo = QComboBox()
        self._grade_combo.addItems(_GRADES)
        self._main_combo = QComboBox()
        self._main_combo.addItems(_STATS_DISPLAY)

        form.addRow("Set", self._set_combo)
        form.addRow("Slot", self._slot_spin)
        form.addRow("\u2605", self._stars_spin)
        form.addRow("Niveau", self._level_spin)
        form.addRow("Grade", self._grade_combo)
        form.addRow("Main stat", self._main_combo)

        self._slot_spin.valueChanged.connect(self._on_slot_changed)
        self._on_slot_changed(self._slot_spin.value())

        self._sub_stats: list[tuple[QComboBox, QSpinBox]] = []
        for i in range(4):
            row = QHBoxLayout()
            ctype = QComboBox()
            ctype.addItems([""] + _STATS_DISPLAY)
            cval = QSpinBox()
            cval.setRange(0, 999)
            row.addWidget(ctype)
            row.addWidget(cval)
            form.addRow(f"Sub {i+1}", self._row_wrap(row))
            self._sub_stats.append((ctype, cval))

        self._grind_combo = QComboBox()
        self._grind_combo.addItems(_GRIND_LABELS)
        self._gem_combo = QComboBox()
        self._gem_combo.addItems(_GRIND_LABELS)
        form.addRow("Meule (max)", self._grind_combo)
        form.addRow("Gemme (max)", self._gem_combo)

        lay.addLayout(form)

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

        self._result_label = QLabel("")
        self._result_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-size:14px; font-weight:700;"
        )
        self._result_label.setWordWrap(True)
        lay.addWidget(self._result_label)

        lbl_fm = QLabel("Filtres matches :")
        lbl_fm.setStyleSheet(f"color:{theme.COLOR_GOLD};")
        lay.addWidget(lbl_fm)

        self._filters_list = QListWidget()
        self._filters_list.setStyleSheet(
            f"QListWidget {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; }}"
        )
        lay.addWidget(self._filters_list, 1)

    def _on_slot_changed(self, slot: int) -> None:
        forced = _FIXED_MAIN_BY_SLOT.get(int(slot))
        if forced is None:
            self._main_combo.setEnabled(True)
            return
        self._main_combo.setCurrentText(forced)
        self._main_combo.setEnabled(False)

    @staticmethod
    def _row_wrap(row_lay) -> QWidget:
        w = QWidget()
        w.setLayout(row_lay)
        return w

    def set_rune(self, rune: Rune) -> None:
        if rune.set in _SETS:
            self._set_combo.setCurrentText(rune.set)
        self._slot_spin.setValue(int(rune.slot))
        self._stars_spin.setValue(int(rune.stars))
        self._level_spin.setValue(int(rune.level))
        if rune.grade in _GRADES:
            self._grade_combo.setCurrentText(rune.grade)
        main_disp = _FR_TO_DISPLAY.get(rune.main_stat.type, rune.main_stat.type)
        if main_disp in _STATS_DISPLAY:
            self._main_combo.setCurrentText(main_disp)
        for i, (ctype, cval) in enumerate(self._sub_stats):
            if i < len(rune.substats):
                s = rune.substats[i]
                ctype.setCurrentText(_FR_TO_DISPLAY.get(s.type, s.type))
                cval.setValue(int(s.value))
            else:
                ctype.setCurrentIndex(0)
                cval.setValue(0)

    def _read_rune(self) -> Rune:
        subs: list[SubStat] = []
        for ctype, cval in self._sub_stats:
            t = ctype.currentText()
            if t:
                subs.append(SubStat(
                    type=_DISPLAY_TO_FR.get(t, t),
                    value=float(cval.value()),
                ))
        main_disp = self._main_combo.currentText()
        return Rune(
            set=self._set_combo.currentText(),
            slot=int(self._slot_spin.value()),
            stars=int(self._stars_spin.value()),
            grade=self._grade_combo.currentText(),
            level=int(self._level_spin.value()),
            main_stat=SubStat(
                type=_DISPLAY_TO_FR.get(main_disp, main_disp),
                value=0.0,
            ),
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
            mode = "Meilleure amelioration immediate"

        subs_txt = ", ".join(
            f"{_FR_TO_DISPLAY.get(s.type, s.type)} {int(s.value)}"
            for s in result.rune.substats
        )
        self._result_label.setText(
            f"{mode}\nEff1 = {int(result.efficiency)}\n{subs_txt}"
        )

        self._filters_list.clear()
        for f in filters_that_match(result.rune, self._filters):
            self._filters_list.addItem(
                f"{f.name}  (Eff\u2265{int(f.efficiency)})"
            )
