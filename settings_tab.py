"""Settings Tab – configuration panel for Luci2US."""

from __future__ import annotations

import json
import os
from tkinter import filedialog

import customtkinter as ctk

from i18n import t, set_language, get_language
from monster_icons import download_icons_async

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, config: dict) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._config.setdefault("swlens", {"keep_threshold": 230})
        self._build_ui()

    # ── UI ──

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Section SWEX ──
        swex_frame = ctk.CTkFrame(self)
        swex_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        swex_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            swex_frame, text=t("swex_section"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=12, pady=(10, 6), sticky="w")

        ctk.CTkLabel(
            swex_frame, text=t("drops_dir"),
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        ).grid(row=1, column=0, padx=12, pady=4, sticky="w")

        swex_cfg = self._config.get("swex", {})
        self._drops_dir_var = ctk.StringVar(value=swex_cfg.get("drops_dir", ""))
        self._entry_drops = ctk.CTkEntry(
            swex_frame, textvariable=self._drops_dir_var, width=350,
        )
        self._entry_drops.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        self._btn_browse_drops = ctk.CTkButton(
            swex_frame, text=t("browse"), width=90,
            command=self._browse_drops,
        )
        self._btn_browse_drops.grid(row=1, column=2, padx=(4, 12), pady=(4, 10))

        row += 1

        # ── Section 3: Icones monstres ──
        icons_frame = ctk.CTkFrame(self)
        icons_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        icons_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            icons_frame, text=t("icons_section"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        self._btn_refresh_icons = ctk.CTkButton(
            icons_frame, text=t("refresh_icons"), width=250,
            command=self._refresh_icons,
        )
        self._btn_refresh_icons.grid(row=1, column=0, padx=12, pady=(4, 10), sticky="w")

        self._lbl_icons_status = ctk.CTkLabel(
            icons_frame, text="",
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        )
        self._lbl_icons_status.grid(row=1, column=1, padx=12, pady=(4, 10), sticky="w")

        row += 1

        # ── Section 4: Langue ──
        lang_frame = ctk.CTkFrame(self)
        lang_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        lang_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            lang_frame, text=t("language"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._lang_var = ctk.StringVar(value=self._config.get("lang", get_language()))
        self._dropdown_lang = ctk.CTkOptionMenu(
            lang_frame, values=["FR", "EN"],
            variable=self._lang_var, width=100,
        )
        self._dropdown_lang.grid(row=0, column=1, padx=12, pady=10, sticky="w")

        row += 1

        # ── Bouton Sauvegarder ──
        self._btn_save = ctk.CTkButton(
            self, text=t("save"), width=160, height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#22c55e", hover_color="#16a34a",
            command=self._save,
        )
        self._btn_save.grid(row=row, column=0, pady=(4, 0), sticky="w")

        self._lbl_status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="#22c55e",
        )
        self._lbl_status.grid(row=row, column=0, padx=(180, 0), pady=(4, 0), sticky="w")

    # ── Actions ──

    def _refresh_icons(self) -> None:
        self._btn_refresh_icons.configure(state="disabled")
        self._lbl_icons_status.configure(
            text=t("icons_downloading"), text_color="#60a5fa",
        )

        def on_progress(done: int, total: int) -> None:
            text = t("icons_progress").replace("{done}", str(done)).replace("{total}", str(total))
            self.after(0, self._lbl_icons_status.configure, {"text": text})

        def on_done() -> None:
            self.after(0, self._lbl_icons_status.configure, {
                "text": t("icons_done"), "text_color": "#22c55e",
            })
            self.after(0, self._btn_refresh_icons.configure, {"state": "normal"})
            self.after(3000, lambda: self._lbl_icons_status.configure(text=""))

        download_icons_async(on_progress=on_progress, on_done=on_done)

    def _browse_drops(self) -> None:
        directory = filedialog.askdirectory(title=t("drops_dir"))
        if directory:
            self._drops_dir_var.set(directory)

    def _save(self) -> None:
        # Update config
        self._config["lang"] = self._lang_var.get()
        set_language(self._lang_var.get())

        if "swex" not in self._config:
            self._config["swex"] = {}
        self._config["swex"]["drops_dir"] = self._drops_dir_var.get()

        # Write to config.json
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

        self._lbl_status.configure(text=t("saved"))
        self.after(2000, lambda: self._lbl_status.configure(text=""))
