import os
import tkinter.colorchooser as cc
from collections.abc import Callable

import customtkinter as ctk

from hopecasement.config import Config
from hopecasement.image import get_user_images_dir, scan_user_images
from hopecasement.ui.utils import normalize_hex_color

_SWATCH_W, _SWATCH_H = 116, 72
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

        # ── 背景颜色 ────────────────────────────────────────
        color_header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        color_header.pack(fill="x", padx=4, pady=(4, 2))
        ctk.CTkLabel(color_header, text="纯色背景",
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
        images = scan_user_images()
        folder = get_user_images_dir()
        image_header = ctk.CTkFrame(self._scroll, fg_color="transparent")
        image_header.pack(fill="x", padx=4, pady=(12, 2))
        ctk.CTkLabel(image_header, text="图片背景",
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(image_header, text=f"共 {len(images)} 张",
                     text_color="#9B9A97", font=ctk.CTkFont(size=12)).pack(side="right")

        card = ctk.CTkFrame(self._scroll, fg_color=["#FFFFFF", "#1C1C1E"], corner_radius=6)
        card.pack(fill="x", padx=4, pady=(2, 0))
        ctk.CTkLabel(
            card, text="壁纸从下面文件夹随机选取，把图片放进去即可：",
            text_color="#9B9A97", font=ctk.CTkFont(size=11),
            anchor="w", justify="left",
        ).pack(fill="x", padx=12, pady=(10, 2))
        path_row = ctk.CTkFrame(card, fg_color="transparent")
        path_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(path_row, text=str(folder), anchor="w",
                     font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(path_row, text="打开文件夹", width=90, height=26,
                      command=self._open_folder).pack(side="left", padx=(8, 0))

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

    def _open_folder(self) -> None:
        folder = get_user_images_dir()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(folder)
        except OSError:
            pass

    def _add_color(self) -> None:
        def on_pick(color: str) -> None:
            if color not in self._colors:
                self._colors.append(color)
                self._refresh()
        _ColorPickerDialog(self, on_pick)

    def _delete_color(self, color: str) -> None:
        self._colors = [c for c in self._colors if c.upper() != color.upper()]
        self._refresh()
