"""Profile Tab – load and browse a SWEX profile export."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk
from PIL import Image

from i18n import t
from models import Monster, Rune
from monster_icons import get_monster_icon
from profile_loader import load_profile_from_dict, load_profile_from_file
from swlens import rl_score


class ProfileTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, config: dict) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._monsters: list[Monster] = []
        self._all_runes: list[Rune] = []
        self._filtered: list[Monster] = []
        self._selected_monster: Monster | None = None
        self._sort_key: str = "name"
        self._sort_reverse: bool = False
        self._profile_source: str = ""
        self._profile_name: str = ""
        self._profile_date: str = ""
        self._icon_cache: dict[int, ctk.CTkImage] = {}
        self._build_ui()

    # ── UI ──

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Row 0: Indicator + Load button + summary ──
        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.grid_columnconfigure(2, weight=1)

        # Profile indicator (name + date + source)
        self._lbl_indicator = ctk.CTkLabel(
            top, text=t("no_profile"),
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#9ca3af",
        )
        self._lbl_indicator.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._btn_load = ctk.CTkButton(
            top, text=t("load_profile_manual"), width=220,
            command=self._load_profile,
        )
        self._btn_load.grid(row=0, column=1, padx=12, pady=10, sticky="w")

        self._lbl_summary = ctk.CTkLabel(
            top, text="",
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        )
        self._lbl_summary.grid(row=0, column=2, padx=12, pady=10, sticky="w")

        # ── Row 1: Filters ──
        filt_frame = ctk.CTkFrame(self)
        filt_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filters())
        self._entry_search = ctk.CTkEntry(
            filt_frame, textvariable=self._search_var,
            placeholder_text=t("search_monster"), width=200,
        )
        self._entry_search.grid(row=0, column=0, padx=(12, 6), pady=6)

        elements = [t("all_elements"), "Eau", "Feu", "Vent", "Lumiere", "Tenebres"]
        self._element_var = ctk.StringVar(value=t("all_elements"))
        self._dropdown_element = ctk.CTkOptionMenu(
            filt_frame, values=elements, variable=self._element_var,
            width=110, command=lambda _: self._apply_filters(),
        )
        self._dropdown_element.grid(row=0, column=1, padx=6, pady=6)

        ctk.CTkLabel(filt_frame, text=t("min_stars"), font=ctk.CTkFont(size=12)).grid(
            row=0, column=2, padx=(12, 4), pady=6,
        )
        self._stars_var = ctk.StringVar(value="1")
        self._dropdown_stars = ctk.CTkOptionMenu(
            filt_frame, values=["1", "2", "3", "4", "5", "6"],
            variable=self._stars_var, width=60,
            command=lambda _: self._apply_filters(),
        )
        self._dropdown_stars.grid(row=0, column=3, padx=6, pady=6)

        # ── Row 2: Split pane – monster list | rune detail ──
        split = ctk.CTkFrame(self, fg_color="transparent")
        split.grid(row=2, column=0, sticky="nsew")
        split.grid_columnconfigure(0, weight=3)
        split.grid_columnconfigure(1, weight=2)
        split.grid_rowconfigure(0, weight=1)

        # Left: monster table
        left = ctk.CTkFrame(split)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Header row (col 0 = icon placeholder, cols 1-6 = sortable)
        hdr = ctk.CTkFrame(left, fg_color="#1f2937", height=30)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, minsize=52)
        hdr.grid_columnconfigure((1, 2, 3, 4, 5, 6), weight=1)
        # Empty header for icon column
        ctk.CTkLabel(hdr, text="", width=48).grid(row=0, column=0, padx=2)
        headers = [
            ("name", t("name")),
            ("element", t("element")),
            ("stars", t("stars_col")),
            ("level", t("level_col")),
            ("sets", t("sets_equipped")),
            ("eff", t("avg_eff")),
        ]
        for col, (key, label) in enumerate(headers, start=1):
            btn = ctk.CTkButton(
                hdr, text=label, fg_color="transparent",
                hover_color="#374151", height=28,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#d1d5db",
                command=lambda k=key: self._toggle_sort(k),
            )
            btn.grid(row=0, column=col, sticky="ew", padx=1)

        self._monster_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._monster_scroll.grid(row=1, column=0, sticky="nsew")
        self._monster_scroll.grid_columnconfigure(0, minsize=52)
        self._monster_scroll.grid_columnconfigure((1, 2, 3, 4, 5, 6), weight=1)

        # Right: rune detail
        self._detail_frame = ctk.CTkFrame(split)
        self._detail_frame.grid(row=0, column=1, sticky="nsew")
        self._detail_frame.grid_columnconfigure(0, weight=1)

        self._lbl_detail_title = ctk.CTkLabel(
            self._detail_frame, text=t("equipped_runes"),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._lbl_detail_title.grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        self._detail_scroll = ctk.CTkScrollableFrame(
            self._detail_frame, fg_color="transparent",
        )
        self._detail_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self._detail_frame.grid_rowconfigure(1, weight=1)

    # ── Actions ──

    def _load_profile(self) -> None:
        path = filedialog.askopenfilename(
            title=t("load_profile"),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        try:
            profile = load_profile_from_file(path)
        except Exception:
            self._lbl_summary.configure(text=t("error"), text_color="#ef4444")
            return

        self._apply_profile(profile)

    def apply_profile_from_dict(self, data: dict) -> None:
        """Called from the SWEX bridge callback (auto-detected login)."""
        try:
            profile = load_profile_from_dict(data)
        except Exception:
            return
        self.after(0, self._apply_profile, profile)

    def _apply_profile(self, profile: dict) -> None:
        """Apply a parsed profile dict to the tab."""
        self._monsters = profile["monsters"]
        self._all_runes = profile["runes"]
        self._profile_source = profile.get("source", "manual")
        self._profile_name = profile["wizard_name"]
        self._profile_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Update indicator
        source_label = (
            t("profile_source_auto") if self._profile_source == "auto"
            else t("profile_source_manual")
        )
        indicator = f"{self._profile_name}  —  {self._profile_date}  {source_label}"
        self._lbl_indicator.configure(text=indicator, text_color="#60a5fa")

        # Update summary
        summary = (
            f"{t('wizard_name')}: {profile['wizard_name']}  |  "
            f"{t('wizard_level')}: {profile['level']}  |  "
            f"{t('monster_count')}: {len(self._monsters)}  |  "
            f"{t('rune_count')}: {len(self._all_runes)}"
        )
        self._lbl_summary.configure(text=summary, text_color="#d1d5db")
        self._apply_filters()

    # ── Filtering & sorting ──

    def _apply_filters(self) -> None:
        query = self._search_var.get().lower().strip()
        elem = self._element_var.get()
        min_stars = int(self._stars_var.get())

        filtered = self._monsters
        if query:
            filtered = [m for m in filtered if query in m.name.lower()]
        if elem != t("all_elements"):
            filtered = [m for m in filtered if m.element == elem]
        if min_stars > 1:
            filtered = [m for m in filtered if m.stars >= min_stars]

        self._filtered = self._sort_monsters(filtered)
        self._render_monster_list()

    def _toggle_sort(self, key: str) -> None:
        if self._sort_key == key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_key = key
            self._sort_reverse = False
        self._apply_filters()

    def _sort_monsters(self, monsters: list[Monster]) -> list[Monster]:
        key = self._sort_key
        if key == "name":
            return sorted(monsters, key=lambda m: m.name.lower(), reverse=self._sort_reverse)
        elif key == "element":
            return sorted(monsters, key=lambda m: m.element, reverse=self._sort_reverse)
        elif key == "stars":
            return sorted(monsters, key=lambda m: m.stars, reverse=self._sort_reverse)
        elif key == "level":
            return sorted(monsters, key=lambda m: m.level, reverse=self._sort_reverse)
        elif key == "eff":
            return sorted(monsters, key=lambda m: self._avg_eff(m), reverse=self._sort_reverse)
        elif key == "sets":
            return sorted(monsters, key=lambda m: self._sets_text(m), reverse=self._sort_reverse)
        return monsters

    # ── Rendering ──

    def _render_monster_list(self) -> None:
        for w in self._monster_scroll.winfo_children():
            w.destroy()

        for i, mon in enumerate(self._filtered):
            bg = "#1f2937" if i % 2 == 0 else "transparent"
            row_frame = ctk.CTkFrame(self._monster_scroll, fg_color=bg, height=48)
            row_frame.grid(row=i, column=0, columnspan=7, sticky="ew", pady=1)
            row_frame.grid_columnconfigure(0, minsize=52)
            row_frame.grid_columnconfigure((1, 2, 3, 4, 5, 6), weight=1)
            row_frame.bind("<Button-1>", lambda e, m=mon: self._select_monster(m))

            # Icon (lazy: loaded on render only for visible rows)
            icon_img = self._get_ctk_icon(mon.unit_master_id)
            icon_lbl = ctk.CTkLabel(row_frame, text="", image=icon_img, width=48)
            icon_lbl.grid(row=0, column=0, padx=2, pady=2)
            icon_lbl.bind("<Button-1>", lambda e, m=mon: self._select_monster(m))

            values = [
                mon.name,
                mon.element,
                str(mon.stars),
                str(mon.level),
                self._sets_text(mon),
                f"{self._avg_eff(mon):.1f}%",
            ]
            for col, val in enumerate(values, start=1):
                lbl = ctk.CTkLabel(
                    row_frame, text=val, font=ctk.CTkFont(size=11),
                    text_color="#d1d5db", anchor="w",
                )
                lbl.grid(row=0, column=col, padx=6, pady=2, sticky="w")
                lbl.bind("<Button-1>", lambda e, m=mon: self._select_monster(m))

    def _select_monster(self, mon: Monster) -> None:
        self._selected_monster = mon
        self._render_rune_detail(mon)

    def _render_rune_detail(self, mon: Monster) -> None:
        for w in self._detail_scroll.winfo_children():
            w.destroy()

        self._lbl_detail_title.configure(
            text=f"  {t('equipped_runes')} — {mon.name} ({mon.stars}* {mon.element})",
            image=self._get_ctk_icon(mon.unit_master_id), compound="left",
        )

        if not mon.equipped_runes:
            ctk.CTkLabel(
                self._detail_scroll, text=t("no_data"),
                text_color="#6b7280",
            ).grid(row=0, column=0, padx=12, pady=12)
            return

        for i, rune in enumerate(mon.equipped_runes):
            eff = rl_score(rune).total
            frame = ctk.CTkFrame(self._detail_scroll, fg_color="#1f2937")
            frame.grid(row=i, column=0, sticky="ew", pady=2, padx=4)
            frame.grid_columnconfigure(0, weight=1)

            header = (
                f"Slot {rune.slot}  |  {rune.set}  |  "
                f"{rune.stars}* {rune.grade}  |  +{rune.level}  |  "
                f"{t('efficiency')}: {eff:.1f}%"
            )
            ctk.CTkLabel(
                frame, text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#f9fafb",
            ).grid(row=0, column=0, padx=8, pady=(6, 2), sticky="w")

            main_text = f"Main: {rune.main_stat.type} +{rune.main_stat.value}"
            if rune.prefix:
                main_text += f"  |  Prefix: {rune.prefix.type} +{rune.prefix.value}"
            ctk.CTkLabel(
                frame, text=main_text,
                font=ctk.CTkFont(size=11), text_color="#9ca3af",
            ).grid(row=1, column=0, padx=8, pady=1, sticky="w")

            subs_parts = []
            for sub in rune.substats:
                grind = f"(+{sub.grind_value})" if sub.grind_value else ""
                subs_parts.append(f"{sub.type} +{sub.value}{grind}")
            if subs_parts:
                ctk.CTkLabel(
                    frame, text="  |  ".join(subs_parts),
                    font=ctk.CTkFont(size=11), text_color="#6b7280",
                ).grid(row=2, column=0, padx=8, pady=(1, 6), sticky="w")

    # ── Helpers ──

    def _get_ctk_icon(self, unit_master_id: int) -> ctk.CTkImage:
        """Return a cached 48x48 CTkImage for a monster icon."""
        if unit_master_id in self._icon_cache:
            return self._icon_cache[unit_master_id]
        icon_path = get_monster_icon(unit_master_id)
        try:
            pil_img = Image.open(icon_path).resize((48, 48), Image.LANCZOS)
        except Exception:
            pil_img = Image.new("RGBA", (48, 48), (128, 128, 128, 80))
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
        self._icon_cache[unit_master_id] = ctk_img
        return ctk_img

    @staticmethod
    def _avg_eff(mon: Monster) -> float:
        if not mon.equipped_runes:
            return 0.0
        total = sum(rl_score(r).total for r in mon.equipped_runes)
        return total / len(mon.equipped_runes)

    @staticmethod
    def _sets_text(mon: Monster) -> str:
        if not mon.equipped_runes:
            return "-"
        sets = sorted(set(r.set for r in mon.equipped_runes))
        return ", ".join(sets)
