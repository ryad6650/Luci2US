"""'Skills' tab — numbered skill rows + passive block."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui import theme
from ui.monsters.elements import hex_alpha


@dataclass
class Skill:
    n: int
    name: str
    desc: str
    mult: str = "—"
    cd: int | None = None


class SkillRow(QWidget):
    def __init__(self, skill: Skill, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 12, 0, 12)
        outer.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        badge = QLabel(str(skill.n))
        badge.setFixedSize(32, 32)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"""
            background:{theme.D.ACCENT_DIM};
            border:1px solid {hex_alpha(theme.D.ACCENT, '33')};
            border-radius:8px;
            color:{theme.D.ACCENT};
            font-family:'{theme.D.FONT_MONO}'; font-size:13px; font-weight:700;
            """
        )
        row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        text = QVBoxLayout()
        text.setSpacing(2)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        name = QLabel(skill.name)
        name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600;"
        )
        head.addWidget(name)
        if skill.cd:
            cd = QLabel(f"CD {skill.cd}t")
            cd.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:10px;"
            )
            head.addWidget(cd)
        head.addStretch(1)
        text.addLayout(head)

        desc = QLabel(skill.desc)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px;"
        )
        text.addWidget(desc)
        row.addLayout(text, 1)

        mult_wrap = QVBoxLayout()
        mult_wrap.setSpacing(2)
        mult_wrap.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        mult_lbl = QLabel("MULT")
        mult_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        mult_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:9px; font-weight:700; letter-spacing:1px;"
        )
        mult_wrap.addWidget(mult_lbl)
        mult_val = QLabel(skill.mult or "—")
        mult_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        mult_val.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:12px; font-weight:700;"
        )
        mult_wrap.addWidget(mult_val)
        row.addLayout(mult_wrap)

        outer.addLayout(row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none; margin-top:10px;")
        outer.addWidget(sep)


class SkillsTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._rows_wrap = QVBoxLayout()
        self._rows_wrap.setContentsMargins(0, 0, 0, 0)
        self._rows_wrap.setSpacing(0)
        rows_container = QWidget()
        rows_container.setLayout(self._rows_wrap)
        self._outer.addWidget(rows_container)

        self._passive = QFrame()
        self._passive.setObjectName("PassiveBlock")
        self._passive.setStyleSheet(
            f"""
            #PassiveBlock {{
                background:rgba(255,255,255,0.03);
                border:1px solid {theme.D.BORDER};
                border-radius:10px;
            }}
            """
        )
        pl = QVBoxLayout(self._passive)
        pl.setContentsMargins(14, 14, 14, 14)
        pl.setSpacing(6)
        kicker = QLabel("PASSIF")
        kicker.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:1px;"
        )
        pl.addWidget(kicker)
        self._passive_body = QLabel("")
        self._passive_body.setWordWrap(True)
        self._passive_body.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px;"
        )
        pl.addWidget(self._passive_body)
        self._outer.addSpacing(16)
        self._outer.addWidget(self._passive)
        self._outer.addStretch(1)

    def set_skills(self, skills: list[Skill], passive: str | None) -> None:
        while self._rows_wrap.count():
            it = self._rows_wrap.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        if skills:
            for sk in skills:
                self._rows_wrap.addWidget(SkillRow(sk))
        else:
            empty = QLabel("Aucune donnée de skill disponible pour ce monstre.")
            empty.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:12px; padding:24px 0;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._rows_wrap.addWidget(empty)

        if passive:
            self._passive.setVisible(True)
            self._passive_body.setText(passive)
        else:
            self._passive.setVisible(False)
