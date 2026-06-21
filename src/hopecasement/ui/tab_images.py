import shutil
import tkinter.filedialog as fd
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from hopecasement.image import (
    SUPPORTED_IMAGE_EXTENSIONS,
    _get_builtin_images_dir,
    _get_user_images_dir,
    _scan,
)

_THUMB_W, _THUMB_H = 120, 90
_COLS = 4


class ImagesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._thumbs: list = []  # keep references to prevent GC
        self._build()
        self.refresh()

    def _build(self):
        self._grid = ctk.CTkScrollableFrame(self)
        self._grid.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(btn_row, text="添加背景图...", width=160, command=self._add).pack(side="left")

    def refresh(self):
        for w in self._grid.winfo_children():
            w.destroy()
        self._thumbs.clear()

        builtin = _scan(_get_builtin_images_dir())
        user = _scan(_get_user_images_dir())

        all_items = [(p, False) for p in builtin] + [(p, True) for p in user]

        for idx, (path, deletable) in enumerate(all_items):
            row, col = divmod(idx, _COLS)
            cell = ctk.CTkFrame(self._grid)
            cell.grid(row=row, column=col, padx=6, pady=6)
            self._add_thumb(cell, path, deletable)

    def _add_thumb(self, cell: ctk.CTkFrame, path: Path, deletable: bool):
        try:
            img = Image.open(path)
            img.thumbnail((_THUMB_W, _THUMB_H))
            ctk_img = ctk.CTkImage(light_image=img, size=(_THUMB_W, _THUMB_H))
        except Exception:
            ctk_img = None

        if ctk_img:
            self._thumbs.append(ctk_img)
            ctk.CTkLabel(cell, image=ctk_img, text="").pack()

        label_text = path.name if deletable else f"[内置] {path.name}"
        ctk.CTkLabel(cell, text=label_text, font=("", 10), wraplength=_THUMB_W).pack()

        if deletable:
            ctk.CTkButton(
                cell, text="删除", width=80, height=22,
                fg_color="gray40", hover_color="gray30",
                font=("", 11),
                command=lambda p=path: self._delete(p),
            ).pack(pady=(2, 0))

    def _add(self):
        paths = fd.askopenfilenames(
            title="选择背景图",
            filetypes=[
                ("图片文件", " ".join(f"*{e}" for e in SUPPORTED_IMAGE_EXTENSIONS)),
                ("所有文件", "*.*"),
            ],
        )
        dest = _get_user_images_dir()
        for p in paths:
            shutil.copy2(p, dest / Path(p).name)
        self.refresh()

    def _delete(self, path: Path):
        path.unlink(missing_ok=True)
        self.refresh()
