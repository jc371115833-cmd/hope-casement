import os
import tkinter.colorchooser as cc
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk

from hopecasement.config import Config
from hopecasement.i18n import t
from hopecasement.image import (
    SUPPORTED_IMAGE_EXTENSIONS,
    get_user_images_dir,
    import_image,
    scan_user_images,
)
from hopecasement.ui.utils import normalize_hex_color

_SWATCH_W, _SWATCH_H = 116, 72
_COLS = 4

# (hex, i18n key) — names are localized at display time.
_RECOMMENDED_COLORS: list[tuple[str, str]] = [
    ("#1A1A2E", "color_midnight"),
    ("#0F2027", "color_ocean"),
    ("#152D32", "color_teal"),
    ("#1F4037", "color_emerald"),
    ("#2D1B69", "color_indigo"),
    ("#1B0036", "color_amethyst"),
    ("#2C1810", "color_espresso"),
    ("#232526", "color_charcoal"),
]


class _ColorPickerDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkBaseClass, on_pick: Callable[[str], None]):
        super().__init__(master)
        self.title(t("cp_title"))
        self.resizable(False, False)
        self._on_pick = on_pick
        self._build()
        self.grab_set()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=t("cp_recommended"), font=ctk.CTkFont(weight="bold")).pack(
            padx=20, pady=(14, 8))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=20, pady=(0, 4))

        for idx, (hex_color, name_key) in enumerate(_RECOMMENDED_COLORS):
            row, col = divmod(idx, 4)
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=6, pady=4)
            ctk.CTkButton(
                cell, width=72, height=44,
                text="", fg_color=hex_color, hover_color=hex_color,
                corner_radius=6,
                command=lambda c=hex_color: self._select(c),
            ).pack()
            ctk.CTkLabel(cell, text=t(name_key), font=ctk.CTkFont(size=10)).pack()

        hex_row = ctk.CTkFrame(self, fg_color="transparent")
        hex_row.pack(padx=20, pady=(10, 4))
        ctk.CTkLabel(hex_row, text=t("cp_hex")).pack(side="left")
        self._hex_entry = ctk.CTkEntry(hex_row, width=100, placeholder_text="#RRGGBB")
        self._hex_entry.pack(side="left", padx=(4, 6))
        ctk.CTkButton(hex_row, text=t("cp_add"), width=56,
                      command=self._add_hex).pack(side="left")

        ctk.CTkButton(
            self, text=t("cp_custom"), width=160,
            fg_color="#EEEDE9", hover_color="#E4E3DE", text_color="#37352F",
            command=self._custom,
        ).pack(padx=20, pady=(6, 16))

    def _select(self, color: str) -> None:
        self._on_pick(color.upper())
        self.destroy()

    def _add_hex(self) -> None:
        color = normalize_hex_color(self._hex_entry.get())
        if color:
            self._on_pick(color)
            self.destroy()
        else:
            self._hex_entry.delete(0, "end")
            self._hex_entry.configure(placeholder_text=t("cp_format_error"))

    def _custom(self) -> None:
        self.grab_release()
        result = cc.askcolor(title=t("cp_custom_title"))
        hex_color = result[1]
        if hex_color:
            self._on_pick(hex_color.upper())
        self.destroy()


class ImagesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._colors: list[str] = []
        self._images_dir: str = ""
        self._dir_mtime_seen: float = 0.0
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self._scroll = scroll

    def load_config(self, cfg: Config) -> None:
        self._colors = list(cfg.background_colors)
        self._images_dir = cfg.images_dir
        self._refresh()

    def get_config_values(self) -> dict:
        return {"background_colors": list(self._colors), "images_dir": self._images_dir}

    def _refresh(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()

        # ── 背景颜色 ────────────────────────────────────────
        color_header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        color_header.pack(fill="x", padx=4, pady=(4, 2))
        ctk.CTkLabel(color_header, text=t("img_solid"),
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(color_header, text=t("img_add_color"), width=75, height=26,
                      command=self._add_color).pack(side="left", padx=(12, 0))

        color_grid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        color_grid.pack(fill="x", padx=4)

        for idx, color in enumerate(self._colors):
            row, col = divmod(idx, _COLS)
            cell = ctk.CTkFrame(color_grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=6, pady=6)
            self._make_swatch(cell, color)

        # ── 背景图片 ────────────────────────────────────────
        images = scan_user_images(self._images_dir)
        folder = get_user_images_dir(self._images_dir)
        self._dir_mtime_seen = self._dir_mtime()
        image_header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        image_header.pack(fill="x", padx=4, pady=(12, 2))
        ctk.CTkLabel(image_header, text=t("img_image"),
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(image_header, text=t("img_add_image"), width=85, height=26,
                      command=self._add_image).pack(side="left", padx=(12, 0))
        ctk.CTkButton(image_header, text=t("img_change_folder"), width=95, height=26,
                      command=self._change_folder).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(image_header, text=t("img_count").format(n=len(images)),
                     text_color="#9B9A97", font=ctk.CTkFont(size=12)).pack(side="right")

        card = ctk.CTkFrame(self._scroll, fg_color=["#FFFFFF", "#1C1C1E"], corner_radius=6)
        card.pack(fill="x", padx=4, pady=(2, 0))
        ctk.CTkLabel(
            card, text=t("img_folder_hint"),
            text_color="#9B9A97", font=ctk.CTkFont(size=11),
            anchor="w", justify="left",
        ).pack(fill="x", padx=12, pady=(10, 2))
        path_row = ctk.CTkFrame(card, fg_color="transparent")
        path_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(path_row, text=str(folder), anchor="w",
                     font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_row, text=t("open_folder"), width=90, height=26,
                      command=self._open_folder).pack(side="left", padx=(8, 0))

    def _make_swatch(self, cell: ctk.CTkFrame, color: str) -> None:
        swatch = ctk.CTkFrame(cell, width=_SWATCH_W, height=_SWATCH_H,
                               fg_color=color, corner_radius=6)
        swatch.pack()
        swatch.pack_propagate(False)
        ctk.CTkLabel(swatch, text=color.upper(), text_color="white",
                      font=ctk.CTkFont(size=11)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkButton(
            cell, text=t("delete"), width=80, height=22,
            fg_color="#EEEDE9", hover_color="#E4E3DE", text_color="#37352F", font=ctk.CTkFont(size=11),
            command=lambda c=color: self._delete_color(c),
        ).pack(pady=(3, 0))

    def _open_folder(self) -> None:
        folder = get_user_images_dir(self._images_dir)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(folder)
        except OSError as exc:
            mb.showerror(t("dlg_error"), str(exc))

    def _add_image(self) -> None:
        paths = fd.askopenfilenames(
            title=t("img_pick_images"),
            filetypes=[
                (t("img_ft_images"), " ".join(f"*{e}" for e in SUPPORTED_IMAGE_EXTENSIONS)),
            ],
        )
        if not paths:
            return
        dest = get_user_images_dir(self._images_dir)
        try:
            for filename in paths:
                import_image(Path(filename), dest)
        except OSError as exc:
            mb.showerror(t("dlg_error"), str(exc))
        self._refresh()

    def _change_folder(self) -> None:
        chosen = fd.askdirectory(title=t("img_pick_folder"))
        if not chosen:
            return
        default = get_user_images_dir()
        # An empty images_dir means "use the default folder"
        self._images_dir = "" if Path(chosen) == default else chosen
        self._refresh()

    def _dir_mtime(self) -> float:
        d = get_user_images_dir(self._images_dir)
        try:
            return d.stat().st_mtime
        except OSError:
            return 0.0

    def poll_reload(self) -> None:
        """Re-scan if the folder changed on disk (external add/remove)."""
        if self._dir_mtime() != self._dir_mtime_seen:
            self._refresh()

    def _add_color(self) -> None:
        def on_pick(color: str) -> None:
            if color not in self._colors:
                self._colors.append(color)
                self._refresh()
        _ColorPickerDialog(self, on_pick)

    def _delete_color(self, color: str) -> None:
        self._colors = [c for c in self._colors if c.upper() != color.upper()]
        self._refresh()
