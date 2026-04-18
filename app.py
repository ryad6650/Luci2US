"""Luci2US – main application window."""

from __future__ import annotations

import copy
import json
import os
import sys

import customtkinter as ctk

from i18n import t
from auto_tab import AutoTab
from profile_tab import ProfileTab
from settings_tab import SettingsTab
from history_tab import HistoryTab
from stats_tab import StatsTab
from swex_bridge import detect_drops_dir

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_CONFIG: dict = {
    "db_path": "history.db",
    "lang": "FR",
    "swex": {
        "drops_dir": detect_drops_dir(),
        "poll_interval": 0.5,
    },
    "s2us": {
        "filter_file": "",
        "artifact_eff_threshold": 70,
    },
}


def load_config() -> dict:
    base = copy.deepcopy(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            on_disk = json.load(f)
        for k, v in on_disk.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k].update(v)
            else:
                base[k] = v
    return base


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Luci2US")
        self.geometry("820x520")
        self.minsize(700, 420)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._config = load_config()
        self._tabs: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._active_tab: str = ""

        self._build_layout()
        self._switch_tab("auto")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Layout ──

    def _build_layout(self) -> None:
        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="ns")
        self._sidebar.grid_rowconfigure(10, weight=1)

        logo = ctk.CTkLabel(
            self._sidebar, text="Luci2US",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        logo.grid(row=0, column=0, padx=20, pady=(20, 30))

        tab_defs = ["auto", "settings", "history", "stats", "profile"]
        for i, key in enumerate(tab_defs):
            btn = ctk.CTkButton(
                self._sidebar, text=t(key), width=130, height=34,
                font=ctk.CTkFont(size=13),
                fg_color="transparent", text_color="#d1d5db",
                hover_color="#374151",
                command=lambda k=key: self._switch_tab(k),
            )
            btn.grid(row=i + 1, column=0, padx=12, pady=3)
            self._nav_buttons[key] = btn

        # Main area
        self._main = ctk.CTkFrame(self, fg_color="transparent")
        self._main.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self._main.grid_rowconfigure(0, weight=1)
        self._main.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Build tabs – ProfileTab first so AutoTab can forward profile events
        self._tabs["profile"] = ProfileTab(self._main, self._config)
        self._tabs["settings"] = SettingsTab(self._main, self._config)
        self._tabs["auto"] = AutoTab(
            self._main, self._config,
            on_profile_loaded=self._tabs["profile"].apply_profile_from_dict,
        )
        self._tabs["history"] = HistoryTab(self._main, self._config)
        self._tabs["stats"] = StatsTab(self._main, self._config)

    # ── Navigation ──

    def _switch_tab(self, tab_key: str) -> None:
        if tab_key == self._active_tab:
            return

        # Hide current
        if self._active_tab and self._active_tab in self._tabs:
            self._tabs[self._active_tab].grid_forget()
            self._nav_buttons[self._active_tab].configure(
                fg_color="transparent", text_color="#d1d5db",
            )

        # Show new
        if tab_key == "history":
            self._tabs["history"].refresh()
        elif tab_key == "stats":
            self._tabs["stats"].refresh()
        self._tabs[tab_key].grid(row=0, column=0, sticky="nsew")
        self._nav_buttons[tab_key].configure(
            fg_color="#1f2937", text_color="#ffffff",
        )
        self._active_tab = tab_key


    def _on_close(self) -> None:
        auto_tab = self._tabs.get("auto")
        if auto_tab is not None:
            auto_tab._stop()
        self.destroy()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s: %(message)s")
    app = App()
    app.mainloop()
