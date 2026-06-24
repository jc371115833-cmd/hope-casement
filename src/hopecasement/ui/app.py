import re
import threading
import tkinter.messagebox as mb
from dataclasses import asdict
from pathlib import Path

import customtkinter as ctk

from hopecasement import __version__
from hopecasement.config import Config, load_config, save_config
from hopecasement.ui.tab_images import ImagesTab
from hopecasement.ui.tab_quotes import QuotesTab
from hopecasement.ui.tab_schedule import ScheduleTab

ctk.set_appearance_mode("light")
ctk.set_default_color_theme(str(Path(__file__).parent / "theme.json"))
_WIN_W, _WIN_H = 680, 640
_ICON_PATH = Path(__file__).parent / "hopecasement.ico"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"来日窗笺  v{__version__}")
        self.geometry(f"{_WIN_W}x{_WIN_H}")
        self.resizable(True, True)
        self._cfg = load_config()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Map>", self._on_restore)
        self._apply_window_icon()
        self.after(0, self._apply_titlebar_color)
        # CustomTkinter sets its own icon shortly after creation; re-apply to win the race.
        self.after(300, self._apply_window_icon)
        self.after(2000, self._poll_external_changes)

    def _apply_window_icon(self) -> None:
        if _ICON_PATH.exists():
            try:
                self.iconbitmap(str(_ICON_PATH))
            except Exception:
                pass

    def _poll_external_changes(self) -> None:
        try:
            self._tab_quotes.poll_reload()
            self._tab_images.poll_reload()
        except Exception:
            pass
        self.after(2000, self._poll_external_changes)

    def _on_restore(self, event=None) -> None:
        # CustomTkinter doesn't repaint its canvas-based widgets after a minimize/
        # restore, leaving them black. Only react to the toplevel's own Map event.
        if event is not None and event.widget is not self:
            return
        self.after(0, self._force_redraw)

    def _force_redraw(self) -> None:
        """A 1px geometry nudge forces every CTk canvas to redraw itself."""
        try:
            geo = self.geometry()  # logical "WxH+X+Y"
            m = re.match(r"(\d+)x(\d+)(.*)", geo)
            if not m:
                return
            w, h, rest = int(m.group(1)), int(m.group(2)), m.group(3)
            self.geometry(f"{w}x{h + 1}{rest}")
            self.update_idletasks()
            self.geometry(geo)
            # The geometry nudge can miss some widgets; re-setting the appearance
            # mode makes CTk redraw every registered widget.
            ctk.set_appearance_mode(ctk.get_appearance_mode())
            self._apply_titlebar_color()
        except Exception:
            pass

    def _apply_titlebar_color(self) -> None:
        try:
            import ctypes
            hwnd = self.winfo_id()
            # Ensure light-mode title bar icons (black text/icons)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(0)), 4)
            # Set caption background to match window bg: #F7F6F3 → COLORREF 0x00F3F6F7
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(ctypes.c_int(0x00F3F6F7)), 4)
        except Exception:
            pass

    def _build(self):
        # No in-window title — the window title bar already shows the app name.

        # Pack the button row at the bottom first so it always reserves its
        # space and never gets squeezed out by the expanding tabview.
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=16, pady=(0, 16))
        self._change_btn = ctk.CTkButton(btn_row, text="立即换壁纸", width=140, command=self._change_now)
        self._change_btn.pack(side="left")
        ctk.CTkButton(btn_row, text="保存设置", width=140, command=self._save).pack(side="right")
        self._status_label = ctk.CTkLabel(
            btn_row, text="", text_color="#5A8F5A", font=ctk.CTkFont(size=13))
        self._status_label.pack(side="left", padx=16)
        self._status_token = 0

        tabs = ctk.CTkTabview(self)
        tabs.pack(side="top", fill="both", expand=True, padx=16, pady=(0, 8))

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

        tabs.set("换壁纸设置")

    def _flash_status(self, text: str) -> None:
        """Show a brief non-modal confirmation next to the buttons, then clear it."""
        self._status_token += 1
        token = self._status_token
        self._status_label.configure(text=text)
        self.after(2500, lambda: self._status_token == token and self._status_label.configure(text=""))

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
            self._flash_status("✓ 已保存")
        except RuntimeError as e:
            mb.showwarning("计划更新失败", f"设置已保存。\n换壁纸计划未能更新：\n{e}")

    def _change_now(self):
        # Read widget values on the UI thread, then render + set the wallpaper off
        # it so the window never freezes during the (~1s) image work.
        try:
            self._tab_quotes.save()
            cfg = self._collect_config()
        except Exception as e:
            mb.showerror("出错了", str(e))
            return
        self._change_btn.configure(state="disabled", text="更换中…")
        # Worker only sets a plain attribute (GIL-atomic); the UI thread polls it.
        # Tkinter isn't thread-safe, so the worker never touches widgets.
        self._change_result: tuple[str, str] | None = None
        threading.Thread(target=self._change_worker, args=(cfg,), daemon=True).start()
        self.after(80, self._poll_change)

    def _change_worker(self, cfg: Config) -> None:
        try:
            from hopecasement.changer import change_wallpaper
            change_wallpaper(cfg)
            self._change_result = ("ok", "")
        except FileNotFoundError as e:
            self._change_result = ("nobg", str(e))
        except Exception as e:
            self._change_result = ("error", str(e))

    def _poll_change(self) -> None:
        if self._change_result is None:
            self.after(80, self._poll_change)
            return
        kind, msg = self._change_result
        self._change_btn.configure(state="normal", text="立即换壁纸")
        if kind == "nobg":
            mb.showwarning("没有背景图", msg)
        elif kind == "error":
            mb.showerror("出错了", msg)
        else:
            self._flash_status("✓ 已更换壁纸")


    def _has_unsaved_changes(self) -> bool:
        try:
            return (
                asdict(self._collect_config()) != asdict(self._cfg)
                or self._tab_quotes.has_changes()
            )
        except Exception:
            return False

    def _on_close(self) -> None:
        if self._has_unsaved_changes():
            answer = mb.askyesnocancel(
                "未保存的修改",
                "有未保存的修改，是否保存后退出？\n\n【是】保存并退出，【否】直接退出。",
            )
            if answer is None:
                return
            if answer:
                try:
                    self._tab_quotes.save()
                    cfg = self._collect_config()
                    save_config(cfg)
                    self._cfg = cfg
                except Exception as e:
                    mb.showerror("保存失败", str(e))
                    return
        self.destroy()


def run_ui() -> None:
    App().mainloop()
