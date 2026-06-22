import tkinter.colorchooser as cc

import customtkinter as ctk

from hopecasement.config import Config

_POSITIONS = ["top_left", "top_center", "center", "bottom_center", "bottom_right"]
_POSITION_LABELS = ["左上", "顶中", "居中", "底中", "右下"]

_FONT_SIZE_OPTIONS = ["24", "28", "32", "36", "40", "48", "56", "64", "72", "80", "88", "96"]
_LINE_SPACING_OPTIONS = ["1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.75", "2.0", "2.5", "3.0"]
_TEXT_WIDTH_OPTIONS = ["40%", "50%", "60%", "65%", "70%", "75%", "80%", "85%", "90%", "95%", "100%"]


def _parse_int(s: str, default: int) -> int:
    try:
        return int(s)
    except ValueError:
        return default


def _parse_font_size(s: str) -> int:
    try:
        v = int(s.strip())
        return max(12, min(120, v))
    except ValueError:
        return 48


def _parse_line_spacing(s: str) -> float:
    try:
        v = float(s.strip())
        return round(max(1.0, min(3.0, v)), 2)
    except ValueError:
        return 1.4


def _parse_text_width(s: str) -> int:
    try:
        v = int(s.strip().rstrip("%"))
        return max(20, min(100, v))
    except ValueError:
        return 75


class ScheduleTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
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

        trio = ctk.CTkFrame(scroll, fg_color="transparent")
        trio.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=6)
        ctk.CTkLabel(trio, text="字号").pack(side="left", padx=(0, 4))
        self._font_size_box = ctk.CTkComboBox(trio, values=_FONT_SIZE_OPTIONS, width=100)
        self._font_size_box.set("48")
        self._font_size_box.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(trio, text="行间距").pack(side="left", padx=(0, 4))
        self._line_spacing_box = ctk.CTkComboBox(trio, values=_LINE_SPACING_OPTIONS, width=100)
        self._line_spacing_box.set("1.4")
        self._line_spacing_box.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(trio, text="文本宽度").pack(side="left", padx=(0, 4))
        self._text_width_box = ctk.CTkComboBox(trio, values=_TEXT_WIDTH_OPTIONS, width=100)
        self._text_width_box.set("75%")
        self._text_width_box.pack(side="left")
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
        self._position_btn = ctk.CTkSegmentedButton(scroll, values=_POSITION_LABELS,
                                                    command=self._on_position_change)
        self._position_btn.grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        # --- 换壁纸计划 ---
        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 2))
        ctk.CTkLabel(header_frame, text="换壁纸计划", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(header_frame, text="  （可多选，不勾选则手动）",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(side="left")
        row += 1

        self._startup_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(scroll, text="开机时换", variable=self._startup_var).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        row += 1

        # interval row
        self._interval_var = ctk.BooleanVar(value=False)
        interval_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        interval_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ctk.CTkCheckBox(interval_frame, text="每", variable=self._interval_var).pack(side="left")
        self._interval_hours_entry = ctk.CTkEntry(interval_frame, width=40, justify="center")
        self._interval_hours_entry.insert(0, "3")
        self._interval_hours_entry.pack(side="left", padx=(4, 0))
        ctk.CTkLabel(interval_frame, text="小时").pack(side="left", padx=(2, 4))
        self._interval_minutes_entry = ctk.CTkEntry(interval_frame, width=40, justify="center")
        self._interval_minutes_entry.insert(0, "0")
        self._interval_minutes_entry.pack(side="left")
        ctk.CTkLabel(interval_frame, text="分钟换一次").pack(side="left", padx=(2, 0))
        row += 1

        # daily row
        self._daily_var = ctk.BooleanVar(value=False)
        daily_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        daily_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ctk.CTkCheckBox(daily_frame, text="每天", variable=self._daily_var).pack(side="left")
        self._daily_entry = ctk.CTkEntry(daily_frame, width=72, justify="center")
        self._daily_entry.insert(0, "08:00")
        self._daily_entry.pack(side="left", padx=4)
        ctk.CTkLabel(daily_frame, text="换一次").pack(side="left")

    def _on_position_change(self, label: str):
        idx = _POSITION_LABELS.index(label)
        self._position_var.set(_POSITIONS[idx])

    def _pick_font_color(self):
        color = cc.askcolor(color=self._font_color_var.get(), title="文字颜色")[1]
        if color:
            self._font_color_var.set(color.upper())

    def _pick_shadow_color(self):
        color = cc.askcolor(color=self._shadow_color_var.get(), title="阴影颜色")[1]
        if color:
            self._shadow_color_var.set(color.upper())

    def load_config(self, cfg: Config) -> None:
        self._font_size_box.set(str(cfg.font_size))
        self._line_spacing_box.set(f"{cfg.line_spacing:.2g}")
        self._text_width_box.set(f"{int(cfg.text_width_ratio * 100)}%")
        self._font_color_var.set(cfg.font_color)
        self._shadow_color_var.set(cfg.shadow_color)
        self._shadow_offset_var.set(cfg.shadow_offset)
        self._shadow_offset_label.configure(text=str(cfg.shadow_offset))
        if cfg.text_position in _POSITIONS:
            self._position_var.set(cfg.text_position)
            self._position_btn.set(_POSITION_LABELS[_POSITIONS.index(cfg.text_position)])
        self._startup_var.set("startup" in cfg.schedule_modes)
        self._interval_var.set("interval" in cfg.schedule_modes)
        self._daily_var.set("daily" in cfg.schedule_modes)
        self._interval_hours_entry.delete(0, "end")
        self._interval_hours_entry.insert(0, str(cfg.interval_hours))
        self._interval_minutes_entry.delete(0, "end")
        self._interval_minutes_entry.insert(0, str(cfg.interval_minutes))
        self._daily_entry.delete(0, "end")
        self._daily_entry.insert(0, cfg.daily_time)

    def get_config_values(self) -> dict:
        modes = []
        if self._startup_var.get():
            modes.append("startup")
        if self._interval_var.get():
            modes.append("interval")
        if self._daily_var.get():
            modes.append("daily")
        return {
            "font_size": _parse_font_size(self._font_size_box.get()),
            "line_spacing": _parse_line_spacing(self._line_spacing_box.get()),
            "text_width_ratio": _parse_text_width(self._text_width_box.get()) / 100,
            "font_color": self._font_color_var.get(),
            "shadow_color": self._shadow_color_var.get(),
            "shadow_offset": int(self._shadow_offset_var.get()),
            "text_position": self._position_var.get(),
            "schedule_modes": modes,
            "interval_hours": max(0, _parse_int(self._interval_hours_entry.get(), 0)),
            "interval_minutes": max(0, min(59, _parse_int(self._interval_minutes_entry.get(), 0))),
            "daily_time": self._daily_entry.get().strip() or "08:00",
        }
