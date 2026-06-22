import shutil
import tkinter.colorchooser as cc
import tkinter.filedialog as fd
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from hopecasement.config import Config
from hopecasement.image import SUPPORTED_IMAGE_EXTENSIONS, get_user_images_dir, scan_user_images
from hopecasement.ui.utils import normalize_hex_color

_SWATCH_W, _SWATCH_H = 116, 72
_THUMB_W, _THUMB_H = 116, 72
_COLS = 4

_RECOMMENDED_COLORS: list[tuple[str, str]] = [
    ("#1A1A2E", "深夜蓝"),
    ("#0F2027", "深洋蓝"),
    ("#152D32", "深青碧"),
    ("#1F4037", "深祖母绿"),
    ("#2D1B69", "皇家靛紫"),
    ("#1B0036", "深紫晶"),
    ("#2C1810", "深焙咖"),
    ("#232526", "炭岩灰"),
]


class _ColorPickerDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTkBaseClass, on_pick: Callable[[str], None]):
        super().__init__(master)
        self.title("添加背景颜色")
        self.resizable(False, False)
        self._on_pick = on_pick
        self._build()
        self.grab_set()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="推荐配色", font=ctk.CTkFont(weight="bold")).pack(
            padx=20, pady=(14, 8))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=20, pady=(0, 4))

        for idx, (hex_color, name) in enumerate(_RECOMMENDED_COLORS):
            row, col = divmod(idx, 4)
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=6, pady=4)
            ctk.CTkButton(
                cell, width=72, height=44,
                text="", fg_color=hex_color, hover_color=hex_color,
                corner_radius=6,
                command=lambda c=hex_color: self._select(c),
            ).pack()
            ctk.CTkLabel(cell, text=name, font=ctk.CTkFont(size=10)).pack()

        hex_row = ctk.CTkFrame(self, fg_color="transparent")
        hex_row.pack(padx=20, pady=(10, 4))
        ctk.CTkLabel(hex_row, text="十六进制：").pack(side="left")
        self._hex_entry = ctk.CTkEntry(hex_row, width=100, placeholder_text="#RRGGBB")
        self._hex_entry.pack(side="left", padx=(4, 6))
        ctk.CTkButton(hex_row, text="添加", width=56,
                      command=self._add_hex).pack(side="left")

        ctk.CTkButton(
            self, text="自定义颜色…", width=160,
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
            self._hex_entry.configure(placeholder_text="格式错误")

    def _custom(self) -> None:
        self.grab_release()
        result = cc.askcolor(title="自定义颜色")
        hex_color = result[1]
        if hex_color:
            self._on_pick(hex_color.upper())
        self.destroy()


class ImagesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._colors: list[str] = []
        self._thumbs: list = []
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        self._scroll = scroll

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
        color_header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        color_header.pack(fill="x", padx=4, pady=(4, 2))
        ctk.CTkLabel(color_header, text="背景颜色",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(color_header, text="添加颜色", width=75, height=26,
                      command=self._add_color).pack(side="left", padx=(12, 0))

        color_grid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        color_grid.pack(fill="x", padx=4)

        for idx, color in enumerate(self._colors):
            row, col = divmod(idx, _COLS)
            cell = ctk.CTkFrame(color_grid, fg_color="transparent")
            cell.grid(row=row, column=col, padx=6, pady=6)
            self._make_swatch(cell, color)

        # ── 背景图片 ────────────────────────────────────────
        image_header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        image_header.pack(fill="x", padx=4, pady=(12, 2))
        ctk.CTkLabel(image_header, text="背景图片",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(image_header, text="添加图片", width=75, height=26,
                      command=self._add_image).pack(side="left", padx=(12, 0))

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
            fg_color="#EEEDE9", hover_color="#E4E3DE", text_color="#37352F", font=ctk.CTkFont(size=11),
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
            fg_color="#EEEDE9", hover_color="#E4E3DE", text_color="#37352F", font=ctk.CTkFont(size=11),
            command=lambda p=path: self._delete_image(p),
        ).pack(pady=(3, 0))

    def _add_color(self) -> None:
        def on_pick(color: str) -> None:
            if color not in self._colors:
                self._colors.append(color)
                self._refresh()
        _ColorPickerDialog(self, on_pick)

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
