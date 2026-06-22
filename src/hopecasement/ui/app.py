import tkinter.messagebox as mb
from dataclasses import asdict

import customtkinter as ctk

from hopecasement.config import Config, load_config, save_config
from hopecasement.ui.tab_images import ImagesTab
from hopecasement.ui.tab_quotes import QuotesTab
from hopecasement.ui.tab_schedule import ScheduleTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_VERSION = "0.1.0"
_WIN_W, _WIN_H = 680, 560


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"来日窗笺  v{_VERSION}")
        self.geometry(f"{_WIN_W}x{_WIN_H}")
        self.resizable(False, False)
        self._cfg = load_config()
        self._build()

    def _build(self):
        header = ctk.CTkLabel(
            self,
            text="来日窗笺",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        header.pack(pady=(16, 4))

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        tabs.add("句子库")
        tabs.add("背景图")
        tabs.add("换壁纸设置")

        self._tab_quotes = QuotesTab(tabs.tab("句子库"))
        self._tab_quotes.pack(fill="both", expand=True)

        self._tab_images = ImagesTab(tabs.tab("背景图"))
        self._tab_images.pack(fill="both", expand=True)
        self._tab_images.load_config(self._cfg)

        self._tab_schedule = ScheduleTab(tabs.tab("换壁纸设置"))
        self._tab_schedule.pack(fill="both", expand=True)
        self._tab_schedule.load_config(self._cfg)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(btn_row, text="立即换壁纸", width=140, command=self._change_now).pack(side="left")
        ctk.CTkButton(btn_row, text="保存设置", width=140, command=self._save).pack(side="right")

    def _collect_config(self) -> Config:
        values = {}
        values.update(self._tab_images.get_config_values())
        values.update(self._tab_schedule.get_config_values())
        base = asdict(self._cfg)
        base.update(values)
        return Config(**base)

    def _save(self):
        try:
            self._tab_quotes.save()
            cfg = self._collect_config()
            save_config(cfg)
            self._cfg = cfg
        except Exception as e:
            mb.showerror("保存失败", str(e))
            return
        try:
            from hopecasement.scheduler import apply_schedule
            apply_schedule(cfg)
            mb.showinfo("保存成功", "设置已保存，换壁纸计划已更新。")
        except RuntimeError as e:
            mb.showwarning("计划更新失败", f"设置已保存。\n换壁纸计划未能更新：\n{e}")

    def _change_now(self):
        self._tab_quotes.save()
        cfg = self._collect_config()
        save_config(cfg)
        self._cfg = cfg
        try:
            from hopecasement.changer import change_wallpaper
            change_wallpaper()
        except FileNotFoundError as e:
            mb.showwarning("没有背景图", str(e))
        except Exception as e:
            mb.showerror("出错了", str(e))


def run_ui() -> None:
    App().mainloop()
