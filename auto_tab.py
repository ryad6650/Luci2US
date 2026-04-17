"""Auto Tab – main automation panel for Luci2US."""

from __future__ import annotations

import time
import threading
from typing import Callable, TYPE_CHECKING

import customtkinter as ctk

from auto_mode import AutoMode, State, SessionStats
from i18n import t
from models import Rune, Verdict

if TYPE_CHECKING:
    pass

STATE_COLORS: dict[State, str] = {
    State.IDLE: "#6b7280",
    State.SCANNING: "#22c55e",
    State.ANALYZING: "#f59e0b",
    State.PAUSED: "#3b82f6",
    State.ERROR: "#ef4444",
}

STATE_I18N: dict[State, str] = {
    State.IDLE: "idle",
    State.SCANNING: "scanning",
    State.ANALYZING: "analyzing",
    State.PAUSED: "paused",
    State.ERROR: "error",
}

# ── Couleurs in-game ──

_BG_CARD = "#2d1f14"
_BG_CARD_BORDER = "#4a3728"
_GOLD_TITLE = "#e8c96a"
_GOLD_STARS = "#f0a030"
_CREAM = "#f0e6d0"
_CREAM_SUB = "#ddd0b8"
_GREEN_SET = "#8ec44a"
_INNATE_COLOR = "#a0a0a0"

_GRADE_COLORS: dict[str, str] = {
    "Legendaire": "#e2a039",
    "Heroique": "#c36de4",
    "Rare": "#55a8e8",
    "Magique": "#55c855",
    "Normal": "#b0b0b0",
}

_GRADE_BG: dict[str, str] = {
    "Legendaire": "#c67032",
    "Heroique": "#8a3aab",
    "Rare": "#2e6ea8",
    "Magique": "#2e8a2e",
    "Normal": "#5a5a5a",
}

# Noms d'affichage des stats (comme in-game)
_STAT_DISPLAY: dict[str, tuple[str, bool]] = {
    "PV%": ("PV", True),
    "PV": ("PV", False),
    "ATQ%": ("ATQ", True),
    "ATQ": ("ATQ", False),
    "DEF%": ("DEF", True),
    "DEF": ("DEF", False),
    "VIT": ("VIT", False),
    "CC": ("Taux critique", True),
    "DC": ("Dégâts critique", True),
    "PRE": ("Précision", True),
    "RES": ("Résistance", True),
}

# Bonus de set (simplifié)
_SET_BONUS: dict[str, str] = {
    "Energie": "2 Set : PV +15%",
    "Garde": "2 Set : DEF +15%",
    "Rapide": "4 Set : VIT +25%",
    "Lame": "2 Set : TC +12%",
    "Concentration": "2 Set : PRE +20%",
    "Endurance": "2 Set : RES +20%",
    "Fatal": "4 Set : ATQ +35%",
    "Desespoir": "4 Set : Étourdissement 25%",
    "Vampire": "4 Set : Drain 35%",
    "Will": "2 Set : Immunité 1 tour",
    "Violent": "4 Set : Tour additionnel",
    "Nemesis": "2 Set : Barre ATB +4%",
    "Vengeance": "2 Set : Contre-attaque 15%",
    "Destruction": "2 Set : Ignore 30% PV max",
    "Combat": "2 Set : ATQ +8% alliés",
    "Determination": "2 Set : DEF +8% alliés",
    "Amelioration": "2 Set : PV +8% alliés",
    "Precision": "2 Set : PRE +10% alliés",
    "Tolerance": "2 Set : RES +10% alliés",
    "Rage": "4 Set : DC +40%",
    "Bouclier": "2 Set : Bouclier 15% PV",
    "Intangible": "2 Set : Intangible 1 tour",
    "Sceau": "2 Set : Sceau 1 tour",
    "Immemorial": "2 Set : Immemorial",
}


def _format_stat(stat_type: str, value: float) -> str:
    """Format a stat like the in-game display: 'ATQ +22' or 'PV +6%'."""
    display_name, is_pct = _STAT_DISPLAY.get(stat_type, (stat_type, False))
    val_int = int(value)
    if is_pct:
        return f"{display_name} +{val_int}%"
    return f"{display_name} +{val_int}"


# ── RuneCard Widget ──

class RuneCard(ctk.CTkFrame):
    """Widget reproduisant l'affichage in-game d'une rune."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=_BG_CARD,
            border_color=_BG_CARD_BORDER,
            border_width=2,
            corner_radius=10,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self._sub_labels: list[ctk.CTkLabel] = []
        self._verdict_frame: ctk.CTkFrame | None = None
        self._build()

    def _build(self) -> None:
        # Title: "Rune Endurance (1)"
        self._lbl_title = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=_GOLD_TITLE,
        )
        self._lbl_title.grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 2), sticky="w")

        # Row 1: Stars + Main stat + Grade badge
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)

        self._lbl_stars = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=14),
            text_color=_GOLD_STARS,
        )
        self._lbl_stars.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self._lbl_main = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=_CREAM,
        )
        self._lbl_main.grid(row=0, column=1, sticky="w")

        self._lbl_grade = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#fff5e0",
            corner_radius=6,
            padx=10, pady=2,
        )
        self._lbl_grade.grid(row=0, column=2, padx=(8, 0), sticky="e")

        # Level
        self._lbl_level = ctk.CTkLabel(
            info_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color="#c8b890",
        )
        self._lbl_level.grid(row=1, column=2, padx=(8, 0), sticky="e")

        # Innate/prefix
        self._lbl_innate = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=_INNATE_COLOR,
        )
        self._lbl_innate.grid(row=2, column=0, columnspan=2, padx=16, pady=(2, 0), sticky="w")

        # Substats container
        self._subs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._subs_frame.grid(row=3, column=0, columnspan=2, padx=16, pady=(2, 2), sticky="w")

        # Set bonus
        self._lbl_set_bonus = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=_GREEN_SET,
        )
        self._lbl_set_bonus.grid(row=4, column=0, columnspan=2, padx=12, pady=(4, 4), sticky="w")

        # Verdict bar (bottom)
        self._verdict_frame = ctk.CTkFrame(self, fg_color="transparent", height=28)
        self._verdict_frame.grid(row=5, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="ew")
        self._verdict_frame.grid_columnconfigure(1, weight=1)

        self._lbl_verdict = ctk.CTkLabel(
            self._verdict_frame, text="",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self._lbl_verdict.grid(row=0, column=0, sticky="w")

        self._lbl_eff = ctk.CTkLabel(
            self._verdict_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color="#c8b890",
        )
        self._lbl_eff.grid(row=0, column=1, padx=(8, 0), sticky="w")

        # Initially hidden
        self._empty = True
        self._lbl_empty = ctk.CTkLabel(
            self, text=t("no_data"),
            font=ctk.CTkFont(size=12),
            text_color="#6b7280",
        )
        self._lbl_empty.grid(row=6, column=0, columnspan=2, padx=12, pady=20)
        self._hide_rune_rows()

    def _hide_rune_rows(self) -> None:
        for w in (self._lbl_title, self._lbl_innate, self._subs_frame,
                  self._lbl_set_bonus, self._verdict_frame):
            w.grid_remove()
        # Hide info_frame row
        for child in self.grid_slaves(row=1):
            child.grid_remove()

    def _show_rune_rows(self) -> None:
        self._lbl_empty.grid_remove()
        self._lbl_title.grid()
        # Re-show info frame
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child not in (self._subs_frame, self._verdict_frame):
                if child.grid_info() == {}:
                    child.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="ew")
                    break
        self._lbl_innate.grid()
        self._subs_frame.grid()
        self._lbl_set_bonus.grid()
        self._verdict_frame.grid()

    def update_rune(self, rune: Rune, verdict: Verdict | None = None) -> None:
        if self._empty:
            self._empty = False
            self._show_rune_rows()

        # Title
        self._lbl_title.configure(text=f"Rune {rune.set} ({rune.slot})")

        # Stars
        star_text = "\u2605" * rune.stars
        self._lbl_stars.configure(text=star_text)

        # Main stat
        self._lbl_main.configure(text=_format_stat(rune.main_stat.type, rune.main_stat.value))

        # Grade badge
        grade_bg = _GRADE_BG.get(rune.grade, "#5a5a5a")
        grade_text = rune.grade.replace("Legendaire", "Légendaire").replace("Heroique", "Héroïque")
        self._lbl_grade.configure(text=grade_text, fg_color=grade_bg)

        # Level
        if rune.level > 0:
            self._lbl_level.configure(text=f"+{rune.level}")
        else:
            self._lbl_level.configure(text="")

        # Innate / prefix
        if rune.prefix:
            innate_text = _format_stat(rune.prefix.type, rune.prefix.value)
            self._lbl_innate.configure(text=f"({innate_text})")
            self._lbl_innate.grid()
        else:
            self._lbl_innate.grid_remove()

        # Clear old substats
        for lbl in self._sub_labels:
            lbl.destroy()
        self._sub_labels.clear()

        # Substats
        for i, sub in enumerate(rune.substats):
            text = _format_stat(sub.type, sub.value)
            if sub.grind_value > 0:
                text += f" (+{int(sub.grind_value)})"
            lbl = ctk.CTkLabel(
                self._subs_frame, text=text,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=_CREAM_SUB,
            )
            lbl.grid(row=i, column=0, sticky="w", pady=0)
            self._sub_labels.append(lbl)

        # Set bonus
        bonus = _SET_BONUS.get(rune.set, "")
        if bonus:
            self._lbl_set_bonus.configure(text=bonus)
            self._lbl_set_bonus.grid()
        else:
            self._lbl_set_bonus.grid_remove()

        # Verdict
        if verdict:
            decision = verdict.decision
            if decision == "KEEP":
                v_color = "#22c55e"
                v_text = "KEEP"
            elif decision == "POWER-UP":
                v_color = "#f59e0b"
                v_text = "POWER-UP"
            else:
                v_color = "#ef4444"
                v_text = "SELL"
            self._lbl_verdict.configure(text=v_text, text_color=v_color)

            eff_text = ""
            if verdict.details:
                d = verdict.details
                swop = f"SWOP: {d['eff_swop']:.1f}%"
                swop_max = f"(max {d['max_swop']:.1f}%)" if "max_swop" in d else ""
                s2us = f"S2US: {d['eff_s2us']:.1f}%"
                s2us_max = f"(max {d['max_s2us']:.1f}%)" if "max_s2us" in d else ""
                eff_text = f"{swop} {swop_max}  |  {s2us} {s2us_max}"
            elif verdict.score is not None:
                eff_text = f"Eff: {verdict.score:.1f}%"
            self._lbl_eff.configure(text=eff_text)

    def update_from_dict(self, data: dict) -> None:
        """Update card from a best_rune dict (session stats)."""
        if self._empty:
            self._empty = False
            self._show_rune_rows()

        self._lbl_title.configure(text=f"Rune {data.get('set', '?')} ({data.get('slot', '?')})")
        stars = data.get("stars", 6)
        self._lbl_stars.configure(text="\u2605" * stars)
        self._lbl_main.configure(text="")
        grade = data.get("grade", "Normal")
        grade_bg = _GRADE_BG.get(grade, "#5a5a5a")
        grade_text = grade.replace("Legendaire", "Légendaire").replace("Heroique", "Héroïque")
        self._lbl_grade.configure(text=grade_text, fg_color=grade_bg)
        self._lbl_level.configure(text="")
        self._lbl_innate.grid_remove()

        for lbl in self._sub_labels:
            lbl.destroy()
        self._sub_labels.clear()

        bonus = _SET_BONUS.get(data.get("set", ""), "")
        self._lbl_set_bonus.configure(text=bonus)

        score = data.get("score")
        score_text = f"Eff: {score:.1f}%" if score else ""
        self._lbl_eff.configure(text=score_text)
        self._lbl_verdict.configure(
            text=data.get("reason", ""),
            text_color="#f59e0b",
        )


class AutoTab(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkBaseClass,
        config: dict,
        on_profile_loaded: Callable[[dict], None] | None = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._running = False
        self._start_ts: float | None = None
        self._timer_thread: threading.Thread | None = None

        self._auto_mode = AutoMode(
            config=config,
            on_state_change=self._on_state_change,
            on_rune_processed=self._on_rune_processed,
            on_session_update=self._on_session_update,
            on_profile_loaded=on_profile_loaded,
        )

        self._build_ui()

    # ── UI Construction ──

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Row 0: Start/Stop + State
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky="ew")
        ctrl_frame.grid_columnconfigure(1, weight=1)

        self._btn_toggle = ctk.CTkButton(
            ctrl_frame, text=t("start"), width=140, height=40,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#22c55e", hover_color="#16a34a",
            command=self._toggle,
        )
        self._btn_toggle.grid(row=0, column=0, padx=(0, 16))

        self._lbl_state = ctk.CTkLabel(
            ctrl_frame, text=t("idle"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=STATE_COLORS[State.IDLE],
        )
        self._lbl_state.grid(row=0, column=1, sticky="w")

        # Row 1: Counters
        counter_frame = ctk.CTkFrame(self)
        counter_frame.grid(row=1, column=0, columnspan=2, pady=(0, 12), sticky="ew", padx=0)
        counter_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._counters: dict[str, ctk.CTkLabel] = {}
        counter_defs = [
            ("runes_scanned", "0"),
            ("keep", "0"),
            ("sell", "0"),
            ("mana_earned", "0"),
            ("session_time", "00:00"),
        ]
        for col, (key, default) in enumerate(counter_defs):
            lbl_title = ctk.CTkLabel(
                counter_frame, text=t(key),
                font=ctk.CTkFont(size=11), text_color="#9ca3af",
            )
            lbl_title.grid(row=0, column=col, padx=8, pady=(8, 0))
            lbl_val = ctk.CTkLabel(
                counter_frame, text=default,
                font=ctk.CTkFont(size=18, weight="bold"),
            )
            lbl_val.grid(row=1, column=col, padx=8, pady=(0, 8))
            self._counters[key] = lbl_val

        # Row 2 left: Last rune card
        left_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        left_wrapper.grid(row=2, column=0, sticky="nsew", padx=(0, 6), pady=0)
        left_wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_wrapper, text=t("last_rune"),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#9ca3af",
        ).grid(row=0, column=0, padx=4, pady=(0, 4), sticky="w")

        self._card_last = RuneCard(left_wrapper)
        self._card_last.grid(row=1, column=0, sticky="nsew")

        # Row 2 right: Best rune card
        right_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        right_wrapper.grid(row=2, column=1, sticky="nsew", padx=(6, 0), pady=0)
        right_wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right_wrapper, text=t("best_rune"),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#9ca3af",
        ).grid(row=0, column=0, padx=4, pady=(0, 4), sticky="w")

        self._card_best = RuneCard(right_wrapper)
        self._card_best.grid(row=1, column=0, sticky="nsew")

    # ── Actions ──

    def _toggle(self) -> None:
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        self._running = True
        self._start_ts = time.time()
        self._btn_toggle.configure(
            text=t("stop"), fg_color="#ef4444", hover_color="#dc2626",
        )
        self._auto_mode.start()
        self._timer_thread = threading.Thread(target=self._tick_timer, daemon=True)
        self._timer_thread.start()

    def _stop(self) -> None:
        self._running = False
        self._auto_mode.stop()
        self._btn_toggle.configure(
            text=t("start"), fg_color="#22c55e", hover_color="#16a34a",
        )
        self._start_ts = None

    # ── Callbacks (called from AutoMode threads → schedule on main) ──

    def _on_state_change(self, state: State) -> None:
        self.after(0, self._update_state, state)

    def _update_state(self, state: State) -> None:
        self._lbl_state.configure(
            text=t(STATE_I18N.get(state, "idle")),
            text_color=STATE_COLORS.get(state, "#6b7280"),
        )

    def _on_rune_processed(self, rune: Rune, verdict: Verdict) -> None:
        self.after(0, self._update_last_rune, rune, verdict)

    def _update_last_rune(self, rune: Rune, verdict: Verdict) -> None:
        self._card_last.update_rune(rune, verdict)

    def _on_session_update(self, stats: SessionStats) -> None:
        self.after(0, self._update_counters, stats)

    def _update_counters(self, stats: SessionStats) -> None:
        self._counters["runes_scanned"].configure(text=str(stats.total_runes))
        self._counters["keep"].configure(text=str(stats.keep))
        self._counters["sell"].configure(text=str(stats.sell))
        self._counters["mana_earned"].configure(text=f"{stats.mana_estimate:,}")

        if stats.best_rune:
            self._card_best.update_from_dict(stats.best_rune)

    # ── Timer ──

    def _tick_timer(self) -> None:
        while self._running and self._start_ts is not None:
            elapsed = int(time.time() - self._start_ts)
            mins, secs = divmod(elapsed, 60)
            hrs, mins = divmod(mins, 60)
            if hrs:
                txt = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                txt = f"{mins:02d}:{secs:02d}"
            self.after(0, self._counters["session_time"].configure, {"text": txt})
            time.sleep(1)
