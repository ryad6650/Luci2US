"""History Tab – browse past farming sessions and runes."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import customtkinter as ctk

from i18n import t
from history_db import init_db, get_sessions, get_runes_by_session, get_top_runes


class HistoryTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, config: dict) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._conn = init_db(config.get("db_path", "history.db"))
        self._sessions: list[dict] = []
        self._current_view: str = "list"  # "list" or "detail"
        self._build_ui()
        self._load_sessions()

    # ── UI ──

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Row 0: Toolbar (period filter + top runes button) ──
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._period_var = ctk.StringVar(value=t("period_all"))
        periods = [t("period_today"), t("period_7d"), t("period_30d"), t("period_all")]
        period_menu = ctk.CTkOptionMenu(
            toolbar, values=periods, variable=self._period_var,
            width=160, command=lambda _: self._load_sessions(),
        )
        period_menu.grid(row=0, column=0, padx=12, pady=8)

        self._btn_top = ctk.CTkButton(
            toolbar, text=t("top_runes"), width=200,
            fg_color="#1f2937", hover_color="#374151",
            command=self._show_top_runes,
        )
        self._btn_top.grid(row=0, column=1, padx=6, pady=8)

        self._btn_back = ctk.CTkButton(
            toolbar, text=t("back_to_list"), width=100,
            fg_color="#374151", hover_color="#4b5563",
            command=self._show_session_list,
        )
        self._btn_back.grid(row=0, column=2, padx=6, pady=8)
        self._btn_back.grid_remove()

        self._lbl_title = ctk.CTkLabel(
            toolbar, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#9ca3af",
        )
        self._lbl_title.grid(row=0, column=3, padx=12, pady=8, sticky="w")
        toolbar.grid_columnconfigure(3, weight=1)

        # ── Row 1: Content area ──
        self._content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)

    # ── Data loading ──

    def _get_period_filter(self) -> str | None:
        """Return ISO start date for the selected period, or None for all."""
        val = self._period_var.get()
        now = datetime.now()
        if val == t("period_today"):
            return now.strftime("%Y-%m-%d 00:00:00")
        elif val == t("period_7d"):
            return (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        elif val == t("period_30d"):
            return (now - timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
        return None

    def _load_sessions(self) -> None:
        self._sessions = get_sessions(self._conn, limit=200)
        period_start = self._get_period_filter()
        if period_start:
            self._sessions = [
                s for s in self._sessions
                if s.get("start_time", "") >= period_start
            ]
        self._show_session_list()

    # ── Session list view ──

    def _show_session_list(self) -> None:
        self._current_view = "list"
        self._btn_back.grid_remove()
        self._lbl_title.configure(text="")
        self._clear_content()

        if not self._sessions:
            lbl = ctk.CTkLabel(
                self._content, text=t("empty_history"),
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            )
            lbl.grid(row=0, column=0, pady=40)
            return

        # Header row
        headers = [t("date"), t("dungeon"), t("total"), t("keep"), t("sell"), t("duration")]
        col_weights = [3, 2, 1, 1, 1, 2]
        hdr_frame = ctk.CTkFrame(self._content, fg_color="#1f2937", corner_radius=6)
        hdr_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for c, (h, w) in enumerate(zip(headers, col_weights)):
            hdr_frame.grid_columnconfigure(c, weight=w)
            ctk.CTkLabel(
                hdr_frame, text=h,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#d1d5db",
            ).grid(row=0, column=c, padx=8, pady=6, sticky="w")

        # Session rows
        for i, session in enumerate(self._sessions):
            self._build_session_row(i + 1, session)

    def _build_session_row(self, row_idx: int, session: dict) -> None:
        bg = "#1a1a2e" if row_idx % 2 == 0 else "transparent"
        row_frame = ctk.CTkFrame(self._content, fg_color=bg, corner_radius=4)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=1)
        col_weights = [3, 2, 1, 1, 1, 2]
        for c, w in enumerate(col_weights):
            row_frame.grid_columnconfigure(c, weight=w)

        # Date
        start = session.get("start_time", "")
        date_str = start[:16].replace("T", " ") if start else "—"
        ctk.CTkLabel(
            row_frame, text=date_str,
            font=ctk.CTkFont(size=12), text_color="#d1d5db",
        ).grid(row=0, column=0, padx=8, pady=4, sticky="w")

        # Dungeon
        dungeon = session.get("dungeon", "") or "—"
        ctk.CTkLabel(
            row_frame, text=dungeon,
            font=ctk.CTkFont(size=12), text_color="#d1d5db",
        ).grid(row=0, column=1, padx=8, pady=4, sticky="w")

        # Total / Keep / Sell
        for c, key in enumerate(("total", "keep", "sell"), start=2):
            val = session.get(key, 0)
            color = "#22c55e" if key == "keep" else "#ef4444" if key == "sell" else "#d1d5db"
            ctk.CTkLabel(
                row_frame, text=str(val),
                font=ctk.CTkFont(size=12), text_color=color,
            ).grid(row=0, column=c, padx=8, pady=4, sticky="w")

        # Duration
        duration = self._calc_duration(session.get("start_time"), session.get("end_time"))
        ctk.CTkLabel(
            row_frame, text=duration,
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        ).grid(row=0, column=5, padx=8, pady=4, sticky="w")

        # Click to expand
        row_frame.bind("<Button-1>", lambda e, s=session: self._show_session_detail(s))
        for child in row_frame.winfo_children():
            child.bind("<Button-1>", lambda e, s=session: self._show_session_detail(s))

    # ── Session detail view ──

    def _show_session_detail(self, session: dict) -> None:
        self._current_view = "detail"
        self._btn_back.grid()
        self._clear_content()

        sid = session.get("id")
        start = session.get("start_time", "")[:16].replace("T", " ")
        dungeon = session.get("dungeon", "") or "—"
        self._lbl_title.configure(
            text=f"{t('session_runes')} — {dungeon} ({start})"
        )

        runes = get_runes_by_session(self._conn, sid)
        if not runes:
            ctk.CTkLabel(
                self._content, text=t("no_runes"),
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).grid(row=0, column=0, pady=40)
            return

        # Header
        headers = [t("set"), t("slot"), t("stars_col"), t("grade"), t("main_stat"),
                   t("efficiency"), t("verdict")]
        hdr_frame = ctk.CTkFrame(self._content, fg_color="#1f2937", corner_radius=6)
        hdr_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for c, h in enumerate(headers):
            hdr_frame.grid_columnconfigure(c, weight=1)
            ctk.CTkLabel(
                hdr_frame, text=h,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#d1d5db",
            ).grid(row=0, column=c, padx=8, pady=6, sticky="w")

        # Rune rows
        for i, rune in enumerate(runes):
            self._build_rune_row(i + 1, rune)

    def _build_rune_row(self, row_idx: int, rune: dict) -> None:
        bg = "#1a1a2e" if row_idx % 2 == 0 else "transparent"
        row_frame = ctk.CTkFrame(self._content, fg_color=bg, corner_radius=4)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=1)
        for c in range(7):
            row_frame.grid_columnconfigure(c, weight=1)

        vals = [
            rune.get("set", ""),
            str(rune.get("slot", "")),
            str(rune.get("stars", "")),
            rune.get("grade", ""),
            rune.get("main_stat", ""),
            f"{rune.get('score', 0):.1f}%" if rune.get("score") is not None else "—",
            rune.get("verdict", ""),
        ]
        for c, val in enumerate(vals):
            color = "#d1d5db"
            if c == 6:  # verdict
                color = "#22c55e" if val.lower() == "keep" else "#ef4444"
            elif c == 5 and val != "—":  # efficiency
                try:
                    eff = float(val.rstrip("%"))
                    color = "#22c55e" if eff >= 70 else "#f59e0b" if eff >= 50 else "#d1d5db"
                except ValueError:
                    pass
            ctk.CTkLabel(
                row_frame, text=val,
                font=ctk.CTkFont(size=12), text_color=color,
            ).grid(row=0, column=c, padx=8, pady=4, sticky="w")

        # Tooltip-like: show substats on hover? Keep it simple – show reason below
        reason = rune.get("reason", "")
        if reason:
            ctk.CTkLabel(
                row_frame, text=reason,
                font=ctk.CTkFont(size=10), text_color="#6b7280",
            ).grid(row=1, column=0, columnspan=7, padx=8, pady=(0, 2), sticky="w")

    # ── Top runes view ──

    def _show_top_runes(self) -> None:
        self._current_view = "detail"
        self._btn_back.grid()
        self._lbl_title.configure(text=t("top_runes"))
        self._clear_content()

        top = get_top_runes(self._conn, limit=10)
        if not top:
            ctk.CTkLabel(
                self._content, text=t("no_data"),
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).grid(row=0, column=0, pady=40)
            return

        headers = [t("set"), t("slot"), t("stars_col"), t("grade"), t("main_stat"),
                   t("efficiency"), t("verdict"), t("source")]
        hdr_frame = ctk.CTkFrame(self._content, fg_color="#1f2937", corner_radius=6)
        hdr_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for c, h in enumerate(headers):
            hdr_frame.grid_columnconfigure(c, weight=1)
            ctk.CTkLabel(
                hdr_frame, text=h,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#d1d5db",
            ).grid(row=0, column=c, padx=8, pady=6, sticky="w")

        for i, rune in enumerate(top):
            bg = "#1a1a2e" if i % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(self._content, fg_color=bg, corner_radius=4)
            row_frame.grid(row=i + 1, column=0, sticky="ew", pady=1)
            for c in range(8):
                row_frame.grid_columnconfigure(c, weight=1)

            vals = [
                rune.get("set", ""),
                str(rune.get("slot", "")),
                str(rune.get("stars", "")),
                rune.get("grade", ""),
                rune.get("main_stat", ""),
                f"{rune.get('score', 0):.1f}%" if rune.get("score") is not None else "—",
                rune.get("verdict", ""),
                rune.get("source", ""),
            ]
            for c, val in enumerate(vals):
                color = "#d1d5db"
                if c == 5 and val != "—":
                    try:
                        eff = float(val.rstrip("%"))
                        color = "#22c55e" if eff >= 70 else "#f59e0b" if eff >= 50 else "#d1d5db"
                    except ValueError:
                        pass
                elif c == 6:
                    color = "#22c55e" if val.lower() == "keep" else "#ef4444"
                ctk.CTkLabel(
                    row_frame, text=val,
                    font=ctk.CTkFont(size=12), text_color=color,
                ).grid(row=0, column=c, padx=8, pady=4, sticky="w")

    # ── Helpers ──

    def _clear_content(self) -> None:
        for widget in self._content.winfo_children():
            widget.destroy()

    @staticmethod
    def _calc_duration(start: str | None, end: str | None) -> str:
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

    def refresh(self) -> None:
        """Reload data – can be called externally when switching to this tab."""
        self._load_sessions()
