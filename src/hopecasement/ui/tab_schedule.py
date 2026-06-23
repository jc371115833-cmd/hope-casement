import re
import tkinter.colorchooser as cc

import customtkinter as ctk

from hopecasement.config import Config
from hopecasement.renderer import DEFAULT_FONT_FILE, FONT_CHOICES, available_fonts
from hopecasement.ui.utils import normalize_hex_color

_FONT_NAME_BY_FILE = {f: name for name, f in FONT_CHOICES.items()}

_ALIGN_BY_LABEL = {"左对齐": "left", "居中": "center", "右对齐": "right"}
_ALIGN_LABEL_BY_VALUE = {v: k for k, v in _ALIGN_BY_LABEL.items()}

_FONT_SIZE_OPTIONS    = ["2%", "3%", "4%", "5%", "6%", "7%", "8%", "10%", "12%", "15%"]
_LINE_SPACING_OPTIONS = ["1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.75", "2.0", "2.5", "3.0"]
_TEXT_WIDTH_OPTIONS   = ["40%", "50%", "60%", "65%", "70%", "75%", "80%", "85%", "90%", "95%", "100%"]
_OPACITY_OPTIONS      = ["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"]


def _parse_opacity(s: str) -> int:
    try:
        return max(0, min(100, int(s.strip().rstrip("%"))))
    except ValueError:
        return 0


def _parse_int(s: str, default: int) -> int:
    try:
        return int(s)
    except ValueError:
        return default


def _fmt_float(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _parse_font_size(s: str) -> float:
    try:
        v = float(s.strip().rstrip("%"))
        return round(max(1.0, min(20.0, v)), 2)
    except ValueError:
        return 4.0


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


def _parse_time(s: str) -> str:
    s = s.strip()
    if re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", s):
        return s
    return "08:00"


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
        style_header = ctk.CTkFrame(scroll, fg_color="transparent")
        style_header.grid(row=row, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 2))
        ctk.CTkLabel(style_header, text="文字样式", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(style_header, text="恢复默认", width=72, height=24,
                      fg_color="transparent", border_width=1,
                      border_color="#B0AFA8", text_color="#37352F",
                      hover_color="#EEEDE9", font=ctk.CTkFont(size=12),
                      command=self._reset_text_style).pack(side="left", padx=(12, 0))
        row += 1

        # 显示文字 + 字号 / 行间距 / 文本宽度 — 同一行
        trio = ctk.CTkFrame(scroll, fg_color="transparent")
        trio.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=6)
        self._show_text_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(trio, text="显示文字", variable=self._show_text_var,
                        command=self._toggle_text_style).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(trio, text="字号").pack(side="left", padx=(0, 4))
        self._font_size_box = ctk.CTkComboBox(trio, values=_FONT_SIZE_OPTIONS, width=90)
        self._font_size_box.set("4%")
        self._font_size_box.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(trio, text="行间距").pack(side="left", padx=(0, 4))
        self._line_spacing_box = ctk.CTkComboBox(trio, values=_LINE_SPACING_OPTIONS, width=75)
        self._line_spacing_box.set("1.4")
        self._line_spacing_box.pack(side="left")

        self._font_size_box._entry.bind(
            "<FocusOut>", lambda e: self._font_size_box.set(f"{_fmt_float(_parse_font_size(self._font_size_box.get()))}%"))
        self._line_spacing_box._entry.bind(
            "<FocusOut>", lambda e: self._line_spacing_box.set(_fmt_float(_parse_line_spacing(self._line_spacing_box.get()))))
        row += 1

        # 字体 + 文字颜色 + 阴影颜色 — 同一行
        color_row = ctk.CTkFrame(scroll, fg_color="transparent")
        color_row.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=6)

        ctk.CTkLabel(color_row, text="字体").pack(side="left", padx=(0, 4))
        self._font_box = ctk.CTkComboBox(
            color_row, values=list(available_fonts().keys()), width=110, state="readonly")
        self._font_box.set("微软雅黑")
        self._font_box.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(color_row, text="文字颜色").pack(side="left", padx=(0, 6))
        self._font_color_swatch = ctk.CTkFrame(
            color_row, width=28, height=28, fg_color="#FFFFFF", corner_radius=4,
            cursor="hand2")
        self._font_color_swatch.pack(side="left", padx=(0, 4))
        self._font_color_swatch.pack_propagate(False)
        self._font_color_swatch.bind("<Button-1>", lambda e: self._pick_font_color())
        self._font_color_entry = ctk.CTkEntry(color_row, width=84)
        self._font_color_entry.insert(0, "#FFFFFF")
        self._font_color_entry.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(color_row, text="阴影颜色").pack(side="left", padx=(0, 6))
        self._shadow_color_swatch = ctk.CTkFrame(
            color_row, width=28, height=28, fg_color="#000000", corner_radius=4,
            cursor="hand2")
        self._shadow_color_swatch.pack(side="left", padx=(0, 4))
        self._shadow_color_swatch.pack_propagate(False)
        self._shadow_color_swatch.bind("<Button-1>", lambda e: self._pick_shadow_color())
        self._shadow_color_entry = ctk.CTkEntry(color_row, width=84)
        self._shadow_color_entry.insert(0, "#000000")
        self._shadow_color_entry.pack(side="left")

        for entry, swatch in [
            (self._font_color_entry, self._font_color_swatch),
            (self._shadow_color_entry, self._shadow_color_swatch),
        ]:
            entry.bind("<FocusOut>", lambda e, en=entry, sw=swatch: self._apply_color(en, sw))
            entry.bind("<Return>",   lambda e, en=entry, sw=swatch: self._apply_color(en, sw))
        row += 1

        # 文字背景：衬底颜色 + 透明度 — 同一行
        textbg_row = ctk.CTkFrame(scroll, fg_color="transparent")
        textbg_row.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=6)
        ctk.CTkLabel(textbg_row, text="文字背景").pack(side="left", padx=(0, 6))
        self._text_bg_color_swatch = ctk.CTkFrame(
            textbg_row, width=28, height=28, fg_color="#000000", corner_radius=4,
            cursor="hand2")
        self._text_bg_color_swatch.pack(side="left", padx=(0, 4))
        self._text_bg_color_swatch.pack_propagate(False)
        self._text_bg_color_swatch.bind("<Button-1>", lambda e: self._pick_text_bg_color())
        self._text_bg_color_entry = ctk.CTkEntry(textbg_row, width=88)
        self._text_bg_color_entry.insert(0, "#000000")
        self._text_bg_color_entry.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(textbg_row, text="不透明度").pack(side="left", padx=(0, 6))
        self._text_bg_opacity_box = ctk.CTkComboBox(textbg_row, values=_OPACITY_OPTIONS, width=75)
        self._text_bg_opacity_box.set("30%")
        self._text_bg_opacity_box.pack(side="left")
        self._text_bg_opacity_box._entry.bind(
            "<FocusOut>", lambda e: self._text_bg_opacity_box.set(f"{_parse_opacity(self._text_bg_opacity_box.get())}%"))
        self._text_bg_color_entry.bind(
            "<FocusOut>", lambda e: self._apply_color(self._text_bg_color_entry, self._text_bg_color_swatch))
        self._text_bg_color_entry.bind(
            "<Return>", lambda e: self._apply_color(self._text_bg_color_entry, self._text_bg_color_swatch))
        row += 1

        # 对齐方式
        label("对齐方式", row)
        self._align_seg = ctk.CTkSegmentedButton(scroll, values=list(_ALIGN_BY_LABEL.keys()))
        self._align_seg.set("居中")
        self._align_seg.grid(row=row, column=1, sticky="w", pady=6)
        row += 1

        # 文字位置 + 文本宽度 — 同一行
        pos_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        pos_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=6)
        ctk.CTkLabel(pos_frame, text="文字位置").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(pos_frame, text="横").pack(side="left")
        self._text_x_entry = ctk.CTkEntry(pos_frame, width=46, justify="center")
        self._text_x_entry.insert(0, "50")
        self._text_x_entry.pack(side="left", padx=(4, 2))
        ctk.CTkLabel(pos_frame, text="%", text_color="gray").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(pos_frame, text="纵").pack(side="left")
        self._text_y_entry = ctk.CTkEntry(pos_frame, width=46, justify="center")
        self._text_y_entry.insert(0, "88")
        self._text_y_entry.pack(side="left", padx=(4, 2))
        ctk.CTkLabel(pos_frame, text="%（左上为0）",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(pos_frame, text="文本宽度").pack(side="left", padx=(0, 4))
        self._text_width_box = ctk.CTkComboBox(pos_frame, values=_TEXT_WIDTH_OPTIONS, width=72)
        self._text_width_box.set("75%")
        self._text_width_box.pack(side="left")
        self._text_width_box._entry.bind(
            "<FocusOut>", lambda e: self._text_width_box.set(f"{_parse_text_width(self._text_width_box.get())}%"))
        row += 1

        self._text_style_widgets = [
            self._font_box,
            self._font_size_box, self._line_spacing_box, self._text_width_box,
            self._font_color_entry, self._shadow_color_entry,
            self._text_bg_color_entry, self._text_bg_opacity_box,
            self._align_seg,
            self._text_x_entry, self._text_y_entry,
        ]

        # --- 换壁纸计划 ---
        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 2))
        ctk.CTkLabel(header_frame, text="换壁纸计划", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(header_frame, text="  （可多选）",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(side="left")
        row += 1

        self._startup_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(scroll, text="开机时换", variable=self._startup_var).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        row += 1

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

        self._daily_var = ctk.BooleanVar(value=False)
        daily_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        daily_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=4, pady=4)
        ctk.CTkCheckBox(daily_frame, text="每天", variable=self._daily_var).pack(side="left")
        self._daily_entry = ctk.CTkEntry(daily_frame, width=72, justify="center")
        self._daily_entry.insert(0, "08:00")
        self._daily_entry.pack(side="left", padx=4)
        ctk.CTkLabel(daily_frame, text="换一次").pack(side="left")
        self._daily_entry.bind("<FocusOut>", lambda e: self._normalize_daily_entry())

    def _normalize_daily_entry(self) -> None:
        normalized = _parse_time(self._daily_entry.get())
        self._daily_entry.delete(0, "end")
        self._daily_entry.insert(0, normalized)

    def _toggle_text_style(self) -> None:
        state = "normal" if self._show_text_var.get() else "disabled"
        for w in self._text_style_widgets:
            w.configure(state=state)

    def _reset_text_style(self) -> None:
        d = Config()
        self._show_text_var.set(d.show_text)
        self._font_box.set(_FONT_NAME_BY_FILE.get(d.font_file, "微软雅黑"))
        self._font_size_box.set(f"{d.font_size}%")
        self._line_spacing_box.set(f"{d.line_spacing:.2g}")
        self._text_width_box.set(f"{int(d.text_width_ratio * 100)}%")
        self._font_color_entry.delete(0, "end")
        self._font_color_entry.insert(0, d.font_color)
        self._font_color_swatch.configure(fg_color=d.font_color)
        self._shadow_color_entry.delete(0, "end")
        self._shadow_color_entry.insert(0, d.shadow_color)
        self._shadow_color_swatch.configure(fg_color=d.shadow_color)
        self._text_bg_color_entry.delete(0, "end")
        self._text_bg_color_entry.insert(0, d.text_bg_color)
        self._text_bg_color_swatch.configure(fg_color=d.text_bg_color)
        self._text_bg_opacity_box.set(f"{d.text_bg_opacity}%")
        self._align_seg.set(_ALIGN_LABEL_BY_VALUE.get(d.text_align, "居中"))
        self._text_x_entry.delete(0, "end")
        self._text_x_entry.insert(0, str(d.text_x))
        self._text_y_entry.delete(0, "end")
        self._text_y_entry.insert(0, str(d.text_y))
        self._toggle_text_style()

    def _apply_color(self, entry: ctk.CTkEntry, swatch: ctk.CTkFrame) -> None:
        color = normalize_hex_color(entry.get())
        if color:
            entry.delete(0, "end")
            entry.insert(0, color)
            swatch.configure(fg_color=color)

    def _pick_font_color(self) -> None:
        if not self._show_text_var.get():
            return
        current = normalize_hex_color(self._font_color_entry.get()) or "#FFFFFF"
        color = cc.askcolor(color=current, title="文字颜色")[1]
        if color:
            color = color.upper()
            self._font_color_entry.delete(0, "end")
            self._font_color_entry.insert(0, color)
            self._font_color_swatch.configure(fg_color=color)

    def _pick_shadow_color(self) -> None:
        if not self._show_text_var.get():
            return
        current = normalize_hex_color(self._shadow_color_entry.get()) or "#000000"
        color = cc.askcolor(color=current, title="阴影颜色")[1]
        if color:
            color = color.upper()
            self._shadow_color_entry.delete(0, "end")
            self._shadow_color_entry.insert(0, color)
            self._shadow_color_swatch.configure(fg_color=color)

    def _pick_text_bg_color(self) -> None:
        if not self._show_text_var.get():
            return
        current = normalize_hex_color(self._text_bg_color_entry.get()) or "#000000"
        color = cc.askcolor(color=current, title="文字背景颜色")[1]
        if color:
            color = color.upper()
            self._text_bg_color_entry.delete(0, "end")
            self._text_bg_color_entry.insert(0, color)
            self._text_bg_color_swatch.configure(fg_color=color)

    def load_config(self, cfg: Config) -> None:
        self._show_text_var.set(cfg.show_text)
        self._toggle_text_style()
        self._font_box.set(_FONT_NAME_BY_FILE.get(cfg.font_file, "微软雅黑"))
        self._font_size_box.set(f"{_fmt_float(cfg.font_size)}%")
        self._line_spacing_box.set(_fmt_float(cfg.line_spacing))
        self._text_width_box.set(f"{int(cfg.text_width_ratio * 100)}%")
        self._font_color_entry.delete(0, "end")
        self._font_color_entry.insert(0, cfg.font_color)
        self._font_color_swatch.configure(fg_color=cfg.font_color)
        self._shadow_color_entry.delete(0, "end")
        self._shadow_color_entry.insert(0, cfg.shadow_color)
        self._shadow_color_swatch.configure(fg_color=cfg.shadow_color)
        self._text_bg_color_entry.delete(0, "end")
        self._text_bg_color_entry.insert(0, cfg.text_bg_color)
        self._text_bg_color_swatch.configure(fg_color=cfg.text_bg_color)
        self._text_bg_opacity_box.set(f"{cfg.text_bg_opacity}%")
        self._align_seg.set(_ALIGN_LABEL_BY_VALUE.get(cfg.text_align, "居中"))
        self._text_x_entry.delete(0, "end")
        self._text_x_entry.insert(0, str(cfg.text_x))
        self._text_y_entry.delete(0, "end")
        self._text_y_entry.insert(0, str(cfg.text_y))
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
            "show_text": self._show_text_var.get(),
            "font_file": FONT_CHOICES.get(self._font_box.get(), DEFAULT_FONT_FILE),
            "font_size": _parse_font_size(self._font_size_box.get()),
            "line_spacing": _parse_line_spacing(self._line_spacing_box.get()),
            "text_width_ratio": _parse_text_width(self._text_width_box.get()) / 100,
            "font_color": normalize_hex_color(self._font_color_entry.get()) or "#FFFFFF",
            "shadow_color": normalize_hex_color(self._shadow_color_entry.get()) or "#000000",
            "text_bg_color": normalize_hex_color(self._text_bg_color_entry.get()) or "#000000",
            "text_bg_opacity": _parse_opacity(self._text_bg_opacity_box.get()),
            "text_align": _ALIGN_BY_LABEL.get(self._align_seg.get(), "center"),
            "text_x": max(0, min(100, _parse_int(self._text_x_entry.get(), 50))),
            "text_y": max(0, min(100, _parse_int(self._text_y_entry.get(), 88))),
            "schedule_modes": modes,
            "interval_hours": max(0, _parse_int(self._interval_hours_entry.get(), 0)),
            "interval_minutes": max(0, min(59, _parse_int(self._interval_minutes_entry.get(), 0))),
            "daily_time": _parse_time(self._daily_entry.get()),
        }
