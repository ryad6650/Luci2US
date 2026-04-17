"""Stats Tab – matplotlib charts embedded in CustomTkinter."""

from __future__ import annotations

from datetime import datetime, timedelta

import customtkinter as ctk
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from i18n import t
from history_db import init_db

# ── Dark theme colours ────────────────────────────────────────────
_BG = "#1a1a2e"
_FG = "#e0e0e0"
_GRID = "#2a2a40"
_COLORS_VERDICT = {"KEEP": "#22c55e", "SELL": "#ef4444", "POWER-UP": "#f59e0b"}
_COLORS_GRADE = {
    "Legendaire": "#f59e0b",
    "Heroique": "#a855f7",
    "Rare": "#3b82f6",
    "Magique": "#22c55e",
    "Normal": "#9ca3af",
}
_BAR_COLOR = "#6366f1"


class StatsTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, config: dict) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._conn = init_db(config.get("db_path", "history.db"))
        self._canvases: list[FigureCanvasTkAgg] = []
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Row 0: period selector
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._period_var = ctk.StringVar(value=t("period_all"))
        periods = [
            t("period_today"),
            t("period_7d"),
            t("period_30d"),
            t("period_all"),
        ]
        period_menu = ctk.CTkOptionMenu(
            toolbar,
            values=periods,
            variable=self._period_var,
            width=160,
            command=lambda _: self.refresh(),
        )
        period_menu.grid(row=0, column=0, padx=12, pady=8)

        # Row 1: scrollable chart area
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure((0, 1), weight=1)

        # Placeholder label shown when there's no data
        self._no_data_label = ctk.CTkLabel(
            self._scroll,
            text=t("stats_no_data"),
            font=ctk.CTkFont(size=15),
            text_color="#6b7280",
        )

    # ── Data helpers ──────────────────────────────────────────────

    def _period_range(self) -> tuple[str, str]:
        now = datetime.now()
        end = now.strftime("%Y-%m-%d 23:59:59")
        label = self._period_var.get()
        if label == t("period_today"):
            start = now.strftime("%Y-%m-%d 00:00:00")
        elif label == t("period_7d"):
            start = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        elif label == t("period_30d"):
            start = (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
        else:
            start = "2000-01-01 00:00:00"
        return start, end

    def _fetch_runes(self) -> list[dict]:
        start, end = self._period_range()
        rows = self._conn.execute(
            'SELECT "set", slot, stars, grade, verdict, score '
            "FROM runes r JOIN sessions s ON r.session_id = s.id "
            "WHERE s.start_time >= ? AND s.start_time <= ? "
            "ORDER BY r.id",
            (start, end),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Refresh (called on tab switch / period change) ────────────

    def refresh(self) -> None:
        # Destroy previous canvases
        for c in self._canvases:
            c.get_tk_widget().destroy()
        self._canvases.clear()
        self._no_data_label.grid_forget()

        runes = self._fetch_runes()
        if not runes:
            self._no_data_label.grid(row=0, column=0, columnspan=2, pady=60)
            return

        charts = [
            (self._chart_verdicts, 0, 0),
            (self._chart_efficiency, 0, 1),
            (self._chart_sets, 1, 0),
            (self._chart_grades, 1, 1),
        ]
        for builder, row, col in charts:
            fig = builder(runes)
            canvas = FigureCanvasTkAgg(fig, master=self._scroll)
            widget = canvas.get_tk_widget()
            widget.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            canvas.draw()
            self._canvases.append(canvas)

    # ── Chart builders ────────────────────────────────────────────

    def _make_figure(self, title: str) -> Figure:
        fig = Figure(figsize=(3.6, 2.8), dpi=100)
        fig.patch.set_facecolor(_BG)
        fig.suptitle(title, color=_FG, fontsize=11, fontweight="bold")
        return fig

    def _chart_verdicts(self, runes: list[dict]) -> Figure:
        counts: dict[str, int] = {}
        for r in runes:
            v = r["verdict"]
            counts[v] = counts.get(v, 0) + 1

        fig = self._make_figure(t("chart_verdicts"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(_BG)

        labels = list(counts.keys())
        sizes = list(counts.values())
        colors = [_COLORS_VERDICT.get(l, "#6b7280") for l in labels]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
            startangle=140,
            textprops={"color": _FG, "fontsize": 9},
        )
        for at in autotexts:
            at.set_fontsize(8)
        fig.tight_layout(rect=[0, 0, 1, 0.92])
        return fig

    def _chart_efficiency(self, runes: list[dict]) -> Figure:
        scores = [r["score"] for r in runes if r["score"] is not None]

        fig = self._make_figure(t("chart_efficiency"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(_BG)

        if not scores:
            ax.text(
                0.5, 0.5, t("no_data"),
                ha="center", va="center", color="#6b7280", fontsize=12,
                transform=ax.transAxes,
            )
            return fig

        bins = list(range(0, 110, 10))
        ax.hist(scores, bins=bins, color=_BAR_COLOR, edgecolor=_BG, rwidth=0.85)
        ax.set_xlabel(t("efficiency"), color=_FG, fontsize=9)
        ax.tick_params(colors=_FG, labelsize=8)
        ax.spines[:].set_color(_GRID)
        fig.tight_layout(rect=[0, 0, 1, 0.92])
        return fig

    def _chart_sets(self, runes: list[dict]) -> Figure:
        counts: dict[str, int] = {}
        for r in runes:
            s = r["set"]
            counts[s] = counts.get(s, 0) + 1
        # Sort descending
        counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

        fig = self._make_figure(t("chart_sets"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(_BG)

        ax.barh(list(counts.keys()), list(counts.values()), color=_BAR_COLOR, height=0.6)
        ax.invert_yaxis()
        ax.tick_params(colors=_FG, labelsize=7)
        ax.spines[:].set_color(_GRID)
        fig.tight_layout(rect=[0, 0, 1, 0.92])
        return fig

    def _chart_grades(self, runes: list[dict]) -> Figure:
        order = ["Legendaire", "Heroique", "Rare", "Magique", "Normal"]
        counts: dict[str, int] = {g: 0 for g in order}
        for r in runes:
            g = r["grade"]
            if g in counts:
                counts[g] += 1
            else:
                counts[g] = counts.get(g, 0) + 1
        # Remove zeros
        counts = {k: v for k, v in counts.items() if v > 0}

        fig = self._make_figure(t("chart_grades"))
        ax = fig.add_subplot(111)
        ax.set_facecolor(_BG)

        labels = list(counts.keys())
        values = list(counts.values())
        colors = [_COLORS_GRADE.get(l, "#6b7280") for l in labels]
        ax.bar(labels, values, color=colors, width=0.6)
        ax.tick_params(colors=_FG, labelsize=8)
        ax.spines[:].set_color(_GRID)
        fig.tight_layout(rect=[0, 0, 1, 0.92])
        return fig
