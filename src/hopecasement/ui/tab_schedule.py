import os
import tkinter.colorchooser as cc

import customtkinter as ctk

from hopecasement.config import Config

_POSITIONS = ["top_left", "top_center", "center", "bottom_center", "bottom_right"]
_POSITION_LABELS = ["左上", "顶中", "居中", "底中", "右下"]
_MODES = ["manual", "startup", "interval", "daily"]


class ScheduleTab(ctk.CTkFrame):
    def __init__(self, master, on_preview, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_preview = on_preview
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)
        scroll.columnconfigure(1, weight=1)

        row = 0

        def label(text, r):
            ctk.CTkLabel(scroll, text=text, anchor="w").grid(
                row=r, column=0, sticky="w", padx=(4, 12), pady=6)

        # --- 文字样式 ---
        ctk.CTkLabel(scroll, text="文字样式", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2))
        row += 1

        label("字号", row)
        self._font_size_var = ctk.IntVar(value=48)
        size_row = ctk.CTkFrame(scroll, fg_color="transparent")
        size_row.grid(row=row, column=1, sticky="ew", pady=6)
        self._font_size_label = ctk.CTkLabel(size_row, text="48", width=32)
        self._font_size_label.pack(side="right")
        ctk.CTkSlider(size_row, from_=24, to=96, variable=self._font_size_var,
                      command=lambda v: self._font_size_label.configure(text=str(int(v)))
                      ).pack(side="left", fill="x", expand=True)
        row += 1

        label("文字颜色", row)
        self._font_color_var = ctk.StringVar(value="#FFFFFF")
        self._font_color_btn = ctk.CTkButton(scroll, textvariable=self._font_color_var,
                                              width=100, command=self._pick_font_color)
        self._font_color_btn.grid(row=row, column=1, sticky="w", pady=6)
        row += 1

        label("阴影颜色", row)
        self._shadow_color_var = ctk.StringVar(value="#000000")
        self._shadow_color_btn = ctk.CTkButton(scroll, textvariable=self._shadow_color_var,
                                                width=100, command=self._pick_shadow_color)
        self._shadow_color_btn.grid(row=row, column=1, sticky="w", pady=6)
        row += 1

        label("阴影偏移", row)
        self._shadow_offset_var = ctk.IntVar(value=2)
        shadow_row = ctk.CTkFrame(scroll, fg_color="transparent")
        shadow_row.grid(row=row, column=1, sticky="ew", pady=6)
        self._shadow_offset_label = ctk.CTkLabel(shadow_row, text="2", width=24)
        self._shadow_offset_label.pack(side="right")
        ctk.CTkSlider(shadow_row, from_=0, to=8, number_of_steps=8,
                      variable=self._shadow_offset_var,
                      command=lambda v: self._shadow_offset_label.configure(text=str(int(v)))
                      ).pack(side="left", fill="x", expand=True)
        row += 1

        label("文字位置", row)
        self._position_var = ctk.StringVar(value="bottom_center")
        ctk.CTkSegmentedButton(scroll, values=_POSITION_LABELS,
                                command=self._on_position_change,
                                ).grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        ctk.CTkButton(scroll, text="预览效果", width=120, command=self._on_preview).grid(
            row=row, column=1, sticky="w", pady=(4, 12))
        row += 1

        # --- 换壁纸计划 ---
        ctk.CTkLabel(scroll, text="换壁纸计划", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 2))
        row += 1

        self._mode_var = ctk.StringVar(value="manual")

        def radio(text, mode, r):
            ctk.CTkRadioButton(scroll, text=text, variable=self._mode_var,
                                value=mode, command=self._on_mode_change
                                ).grid(row=r, column=0, columnspan=2, sticky="w", padx=4, pady=4)

        radio("手动（不自动切换）", "manual", row); row += 1
        radio("开机时换", "startup", row); row += 1

        # interval row
        interval_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        interval_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ctk.CTkRadioButton(interval_frame, text="每", variable=self._mode_var,
                           value="interval", command=self._on_mode_change).pack(side="left")
        self._interval_entry = ctk.CTkEntry(interval_frame, width=48, justify="center")
        self._interval_entry.insert(0, "3")
        self._interval_entry.pack(side="left", padx=4)
        ctk.CTkLabel(interval_frame, text="小时换一次").pack(side="left")
        row += 1

        # daily row
        daily_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        daily_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ctk.CTkRadioButton(daily_frame, text="每天", variable=self._mode_var,
                           value="daily", command=self._on_mode_change).pack(side="left")
        self._daily_entry = ctk.CTkEntry(daily_frame, width=72, justify="center")
        self._daily_entry.insert(0, "08:00")
        self._daily_entry.pack(side="left", padx=4)
        ctk.CTkLabel(daily_frame, text="换一次").pack(side="left")

    def _on_position_change(self, label: str):
        idx = _POSITION_LABELS.index(label)
        self._position_var.set(_POSITIONS[idx])

    def _on_mode_change(self):
        pass  # mode_var already updated by radio button

    def _pick_font_color(self):
        color = cc.askcolor(color=self._font_color_var.get(), title="文字颜色")[1]
        if color:
            self._font_color_var.set(color.upper())

    def _pick_shadow_color(self):
        color = cc.askcolor(color=self._shadow_color_var.get(), title="阴影颜色")[1]
        if color:
            self._shadow_color_var.set(color.upper())

    def load_config(self, cfg: Config):
        self._font_size_var.set(cfg.font_size)
        self._font_size_label.configure(text=str(cfg.font_size))
        self._font_color_var.set(cfg.font_color)
        self._shadow_color_var.set(cfg.shadow_color)
        self._shadow_offset_var.set(cfg.shadow_offset)
        self._shadow_offset_label.configure(text=str(cfg.shadow_offset))
        if cfg.text_position in _POSITIONS:
            self._position_var.set(cfg.text_position)
        self._mode_var.set(cfg.schedule_mode)
        self._interval_entry.delete(0, "end")
        self._interval_entry.insert(0, str(cfg.interval_hours))
        self._daily_entry.delete(0, "end")
        self._daily_entry.insert(0, cfg.daily_time)

    def get_config_values(self) -> dict:
        return {
            "font_size": int(self._font_size_var.get()),
            "font_color": self._font_color_var.get(),
            "shadow_color": self._shadow_color_var.get(),
            "shadow_offset": int(self._shadow_offset_var.get()),
            "text_position": self._position_var.get(),
            "schedule_mode": self._mode_var.get(),
            "interval_hours": max(1, int(self._interval_entry.get() or 3)),
            "daily_time": self._daily_entry.get() or "08:00",
        }
