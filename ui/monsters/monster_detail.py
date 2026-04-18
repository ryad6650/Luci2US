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

            header_lbl = QLabel(f"SLOT {slot_num}")
            header_lbl.setStyleSheet(
                f"color:{theme.COLOR_GOLD}; font-size:10px; font-weight:700;"
                f" letter-spacing:1px;"
            )
            card_lay.addWidget(header_lbl)

            content = QLabel("Vide")
            content.setObjectName("slot_content")
            content.setWordWrap(True)
            content.setStyleSheet(
                f"color:{theme.COLOR_TEXT_DIM}; font-size:11px;"
            )
            card_lay.addWidget(content)
            card_lay.addStretch()

            self._slot_widgets.append(card)
            row = (slot_num - 1) // 3
            col = (slot_num - 1) % 3
            self._slots_grid.addWidget(card, row, col)

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
