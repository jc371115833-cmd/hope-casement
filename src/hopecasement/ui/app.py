import re
import threading
import tkinter.messagebox as mb
from dataclasses import asdict
from pathlib import Path

import customtkinter as ctk

from hopecasement import __version__, i18n, single_instance
from hopecasement.config import Config, load_config, save_config
from hopecasement.i18n import t
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
        self.title(f"{i18n.app_name()}  v{__version__}")
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
        self._change_btn = ctk.CTkButton(btn_row, text=t("change_now"), width=140, command=self._change_now)
        self._change_btn.pack(side="left")
        ctk.CTkButton(btn_row, text=t("save"), width=140, command=self._save).pack(side="right")
        self._status_label = ctk.CTkLabel(
            btn_row, text="", text_color="#5A8F5A", font=ctk.CTkFont(size=13))
        self._status_label.pack(side="left", padx=16)
        self._status_token = 0

        tabs = ctk.CTkTabview(self)
        tabs.pack(side="top", fill="both", expand=True, padx=16, pady=(0, 8))

        name_quotes, name_images, name_schedule = t("tab_quotes"), t("tab_images"), t("tab_schedule")
        tabs.add(name_quotes)
        tabs.add(name_images)
        tabs.add(name_schedule)

        self._tab_quotes = QuotesTab(tabs.tab(name_quotes))
        self._tab_quotes.pack(fill="both", expand=True)

        self._tab_images = ImagesTab(tabs.tab(name_images))
        self._tab_images.pack(fill="both", expand=True)
        self._tab_images.load_config(self._cfg)

        self._tab_schedule = ScheduleTab(tabs.tab(name_schedule))
        self._tab_schedule.pack(fill="both", expand=True)
        self._tab_schedule.load_config(self._cfg)

        tabs.set(name_schedule)

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
            mb.showerror(t("dlg_save_failed"), str(e))
            return
        try:
            from hopecasement.scheduler import apply_schedule
            apply_schedule(cfg)
            self._flash_status(t("status_saved"))
        except RuntimeError as e:
            mb.showwarning(t("dlg_schedule_failed"), t("dlg_schedule_failed_body").format(err=e))

    def _change_now(self):
        # Read widget values on the UI thread, then render + set the wallpaper off
        # it so the window never freezes during the (~1s) image work.
        try:
            self._tab_quotes.save()
            cfg = self._collect_config()
        except Exception as e:
            mb.showerror(t("dlg_error"), str(e))
            return
        self._change_btn.configure(state="disabled", text=t("changing"))
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
        self._change_btn.configure(state="normal", text=t("change_now"))
        if kind == "nobg":
            mb.showwarning(t("dlg_nobg"), msg)
        elif kind == "error":
            mb.showerror(t("dlg_error"), msg)
        else:
            self._flash_status(t("status_changed"))


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
            answer = mb.askyesnocancel(t("dlg_unsaved"), t("dlg_unsaved_body"))
            if answer is None:
                return
            if answer:
                try:
                    self._tab_quotes.save()
                    cfg = self._collect_config()
                    save_config(cfg)
                    self._cfg = cfg
                except Exception as e:
                    mb.showerror(t("dlg_save_failed"), str(e))
                    return
        self.destroy()


def run_ui() -> None:
    # Resolve language once: saved config → installer's choice → system language.
    cfg = load_config()
    lang = cfg.language or i18n.installer_language() or i18n.system_language()
    i18n.set_language(lang)
    if cfg.language != lang:
        cfg.language = lang
        save_config(cfg)

    # Keep a single window: focus the existing one and bail if already running.
    if single_instance.already_running():
        single_instance.focus_existing(f"{i18n.app_name()}  v{__version__}")
        return

    App().mainloop()
