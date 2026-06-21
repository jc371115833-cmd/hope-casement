import shutil
import tkinter.colorchooser as cc
import tkinter.filedialog as fd
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from hopecasement.config import Config
from hopecasement.image import SUPPORTED_IMAGE_EXTENSIONS, get_user_images_dir, scan_user_images

_SWATCH_W, _SWATCH_H = 116, 72
_THUMB_W, _THUMB_H = 116, 72
_COLS = 4


class ImagesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._colors: list[str] = []
        self._thumbs: list = []
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        self._scroll = scroll

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(btn_row, text="添加颜色…", width=120,
                      command=self._add_color).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="添加图片…", width=120,
                      command=self._add_image).pack(side="left")

    def load_config(self, cfg: Config) -> None:
        self._colors = list(cfg.background_colors)
        self._refresh()

    def get_config_values(self) -> dict:
        return {"background_colors": list(self._colors)}

    def _refresh(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        self._thumbs.clear()

        # ── 背景颜色 ────────────────────────────────────────
        ctk.CTkLabel(self._scroll, text="背景颜色",
                     font=ctk.CTkFont(weight="bold"), anchor="w").pack(
            fill="x", padx=4, pady=(4, 2))

        color_grid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        color_grid.pack(fill="x", padx=4)

        for idx, color in enumerate(self._colors):
            row, col = divmod(idx, _COLS)
            cell = ctk.CTkFrame(color_grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=6, pady=6)
            self._make_swatch(cell, color)

        # ── 背景图片 ────────────────────────────────────────
        ctk.CTkLabel(self._scroll, text="背景图片",
                     font=ctk.CTkFont(weight="bold"), anchor="w").pack(
            fill="x", padx=4, pady=(12, 2))

        image_grid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        image_grid.pack(fill="x", padx=4)

        for idx, path in enumerate(scan_user_images()):
            row, col = divmod(idx, _COLS)
            cell = ctk.CTkFrame(image_grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=6, pady=6)
            self._make_thumb(cell, path)

    def _make_swatch(self, cell: ctk.CTkFrame, color: str) -> None:
        swatch = ctk.CTkFrame(cell, width=_SWATCH_W, height=_SWATCH_H,
                               fg_color=color, corner_radius=6)
        swatch.pack()
        swatch.pack_propagate(False)
        ctk.CTkLabel(swatch, text=color.upper(), text_color="white",
                      font=ctk.CTkFont(size=11)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkButton(
            cell, text="删除", width=80, height=22,
            fg_color="gray40", hover_color="gray30", font=ctk.CTkFont(size=11),
            command=lambda c=color: self._delete_color(c),
        ).pack(pady=(3, 0))

    def _make_thumb(self, cell: ctk.CTkFrame, path: Path) -> None:
        try:
            img = Image.open(path)
            img.thumbnail((_THUMB_W, _THUMB_H))
            ctk_img = ctk.CTkImage(light_image=img, size=(_THUMB_W, _THUMB_H))
            self._thumbs.append(ctk_img)
            ctk.CTkLabel(cell, image=ctk_img, text="").pack()
        except Exception:
            ctk.CTkLabel(cell, text="?", width=_THUMB_W, height=_THUMB_H).pack()

        ctk.CTkLabel(cell, text=path.name, font=ctk.CTkFont(size=10),
                      wraplength=_THUMB_W).pack()
        ctk.CTkButton(
            cell, text="删除", width=80, height=22,
            fg_color="gray40", hover_color="gray30", font=ctk.CTkFont(size=11),
            command=lambda p=path: self._delete_image(p),
        ).pack(pady=(3, 0))

    def _add_color(self) -> None:
        result = cc.askcolor(title="选择背景颜色")
        hex_color = result[1]
        if hex_color:
            hex_color = hex_color.upper()
            if hex_color not in [c.upper() for c in self._colors]:
                self._colors.append(hex_color)
                self._refresh()

    def _delete_color(self, color: str) -> None:
        self._colors = [c for c in self._colors if c.upper() != color.upper()]
        self._refresh()

    def _add_image(self) -> None:
        paths = fd.askopenfilenames(
            title="选择背景图",
            filetypes=[
                ("图片文件", " ".join(f"*{e}" for e in SUPPORTED_IMAGE_EXTENSIONS)),
                ("所有文件", "*.*"),
            ],
        )
        dest = get_user_images_dir()
        for p in paths:
            shutil.copy2(p, dest / Path(p).name)
        self._refresh()

    def _delete_image(self, path: Path) -> None:
        path.unlink(missing_ok=True)
        self._refresh()
