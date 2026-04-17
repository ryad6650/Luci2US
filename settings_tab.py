"""Settings Tab – configuration panel for Luci2US."""

from __future__ import annotations

import json
import os
from tkinter import filedialog

import customtkinter as ctk

from i18n import t, set_language, get_language
from monster_icons import download_icons_async
from s2us_filter import load_s2us_file, S2USFilter

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, config: dict) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._filters: list[S2USFilter] = []
        self._global_settings: dict = {}
        self._build_ui()

    # ── UI ──

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Section 1: Filtres S2US ──
        s2us_frame = ctk.CTkFrame(self)
        s2us_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        s2us_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            s2us_frame, text=t("filters_s2us"),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        self._btn_import = ctk.CTkButton(
            s2us_frame, text=t("import_s2us"), width=200,
            command=self._import_s2us,
        )
        self._btn_import.grid(row=1, column=0, padx=12, pady=4, sticky="w")

        self._lbl_filter_count = ctk.CTkLabel(
            s2us_frame, text=t("no_filters"),
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        )
        self._lbl_filter_count.grid(row=1, column=1, padx=12, pady=4, sticky="w")

        self._lbl_filter_names = ctk.CTkLabel(
            s2us_frame, text="",
            font=ctk.CTkFont(size=11), text_color="#6b7280",
            justify="left", anchor="w",
        )
        self._lbl_filter_names.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")

        self._smart_powerup_var = ctk.BooleanVar(value=True)
        self._chk_smart = ctk.CTkCheckBox(
            s2us_frame, text=t("smart_powerup"),
            variable=self._smart_powerup_var,
        )
        self._chk_smart.grid(row=3, column=0, columnspan=2, padx=12, pady=(4, 10), sticky="w")

        row += 1

        # ── Section 2: SWEX ──
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

        # Load existing filters from config
        self._load_existing_filters()

    # ── Actions ──

    def _import_s2us(self) -> None:
        path = filedialog.askopenfilename(
            title=t("import_s2us"),
            filetypes=[("S2US files", "*.s2us"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            self._filters, self._global_settings = load_s2us_file(path)
        except Exception:
            self._lbl_filter_count.configure(text=t("error"), text_color="#ef4444")
            return

        if "s2us" not in self._config:
            self._config["s2us"] = {}
        self._config["s2us"]["filter_file"] = path
        self._config["s2us"]["global_settings"] = self._global_settings
        self._smart_powerup_var.set(self._global_settings.get("SmartPowerup", True))
        self._update_filter_display()

        from evaluator_chain import reload_filters
        reload_filters()

    def _update_filter_display(self) -> None:
        count = len(self._filters)
        self._lbl_filter_count.configure(
            text=f"{t('filters_loaded')}: {count}",
            text_color="#d1d5db",
        )
        names = [f.name for f in self._filters[:5]]
        suffix = f"  (+{count - 5})" if count > 5 else ""
        self._lbl_filter_names.configure(text=", ".join(names) + suffix)

    def _load_existing_filters(self) -> None:
        filters_cfg = self._config.get("s2us", {})
        path = filters_cfg.get("filter_file", "")
        if path and os.path.isfile(path):
            try:
                self._filters, self._global_settings = load_s2us_file(path)
                self._smart_powerup_var.set(self._global_settings.get("SmartPowerup", True))
                self._update_filter_display()
            except Exception:
                pass

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

        # Update SmartPowerup in global settings
        if self._global_settings:
            self._global_settings["SmartPowerup"] = self._smart_powerup_var.get()
            if "s2us" in self._config and isinstance(self._config["s2us"], dict):
                self._config["s2us"]["global_settings"] = self._global_settings

        # Write to config.json
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

        self._lbl_status.configure(text=t("saved"))
        self.after(2000, lambda: self._lbl_status.configure(text=""))
