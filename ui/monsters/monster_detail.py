"""Vue detail d'un monstre : header + 6 RuneCard (meme visuel que scan) + retour."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

import monster_icons
from models import Monster
from s2us_filter import calculate_efficiency_s2us
from ui import theme
from ui.scan.rune_card import RuneCard, RuneCardStatus


def _rune_efficiency(rune) -> float | None:
    if rune.swex_efficiency is not None:
        return float(rune.swex_efficiency)
    try:
        return float(calculate_efficiency_s2us(rune))
    except Exception:
        return None


def _empty_slot_card(slot_num: int) -> QFrame:
    card = QFrame()
    card.setObjectName(f"empty_slot_{slot_num}")
    card.setStyleSheet(
        f"QFrame#empty_slot_{slot_num} {{ background:rgba(26,15,7,0.6);"
        f" border:1px dashed {theme.COLOR_BORDER_FRAME}; border-radius:7px; }}"
    )
    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 13, 18, 13)
    title = QLabel(f"SLOT {slot_num}")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet(
        f"color:{theme.COLOR_GOLD}; font-size:11px; font-weight:700;"
        f" letter-spacing:1.5px;"
    )
    lay.addWidget(title)
    empty = QLabel("Vide")
    empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
    empty.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:13px;")
    lay.addWidget(empty, 1)
    return card


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

        self._eff_lbl = QLabel("")
        self._eff_lbl.setStyleSheet(
            f"color:{theme.COLOR_KEEP}; font-size:13px; font-weight:600;"
        )
        info.addWidget(self._eff_lbl)

        info.addStretch()
        h_lay.addLayout(info, 1)

        outer.addWidget(header)

        # --- 6 RuneCards (grille 3x2) ---
        self._slots_frame = QFrame()
        self._slots_grid = QGridLayout(self._slots_frame)
        self._slots_grid.setContentsMargins(0, 0, 0, 0)
        self._slots_grid.setHorizontalSpacing(12)
        self._slots_grid.setVerticalSpacing(10)

        # Placeholder containers so we can swap RuneCard / empty card in-place
        self._slot_containers: list[QWidget] = []
        for slot_num in range(1, 7):
            wrap = QWidget()
            wlay = QVBoxLayout(wrap)
            wlay.setContentsMargins(0, 0, 0, 0)
            wlay.setSpacing(0)
            wlay.addWidget(_empty_slot_card(slot_num))
            self._slot_containers.append(wrap)
            row = (slot_num - 1) // 3
            col = (slot_num - 1) % 3
            self._slots_grid.addWidget(wrap, row, col)

        for c in range(3):
            self._slots_grid.setColumnStretch(c, 1)

        outer.addWidget(self._slots_frame, 1)
        outer.addStretch()

    def _replace_slot(self, slot_num: int, widget: QWidget) -> None:
        wrap = self._slot_containers[slot_num - 1]
        lay = wrap.layout()
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        lay.addWidget(widget)

    def set_monster(self, monster: Monster | None) -> None:
        self._monster = monster
        if monster is None:
            self._name_lbl.setText("")
            self._meta_lbl.setText("")
            self._eff_lbl.setText("")
            self._crumb_label.setText("Monstres /")
            self._icon.clear()
            for slot_num in range(1, 7):
                self._replace_slot(slot_num, _empty_slot_card(slot_num))
            return

        self._name_lbl.setText(monster.name)
        self._meta_lbl.setText(
            f"{monster.element} \u00b7 \u2605{monster.stars} \u00b7 Niv {monster.level}"
        )
        self._crumb_label.setText(f"Monstres / {monster.name}")

        try:
            icon_path = monster_icons.get_monster_icon(monster.unit_master_id)
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                self._icon.setPixmap(pix.scaled(
                    96, 96,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
            else:
                self._icon.clear()
        except Exception:
            self._icon.clear()

        by_slot = {r.slot: r for r in monster.equipped_runes}

        effs: list[float] = []
        for slot_num in range(1, 7):
            rune = by_slot.get(slot_num)
            if rune is None:
                self._replace_slot(slot_num, _empty_slot_card(slot_num))
                continue
            card = RuneCard(RuneCardStatus.KEEP)
            card.update_rune(rune, mana=0, set_bonus_text="")
            self._replace_slot(slot_num, card)
            e = _rune_efficiency(rune)
            if e is not None:
                effs.append(e)

        if effs:
            self._eff_lbl.setText(f"Eff moyenne : {sum(effs) / len(effs):.1f}%")
        else:
            self._eff_lbl.setText("Eff moyenne : -")
