import os
import re
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from contextlib import contextmanager
from pathlib import Path

import customtkinter as ctk

from hopecasement.i18n import quote_count, t
from hopecasement.quotes import default_quotes, load_quotes, quotes_path, save_quotes

_NUM_FG = "#9B9A97"
_NUM_RE = re.compile(r"^\d+\.\s")
_SHIFT = 0x1
_FILE_SIZE_WARN = 200

_HEADING_RE = re.compile(r"^#{1,6}\s")
_LIST_PREFIX_RE = re.compile(r"^(?:\d+[\.\)]\s+|[-*+]\s+)")
_INLINE_MD_SUBS = [
    (re.compile(r"!\[.*?\]\(.*?\)"),      ""),      # images → remove
    (re.compile(r"\[([^\]]+)\]\(.*?\)"),  r"\1"),   # links → keep text
    (re.compile(r"\*{3}(.+?)\*{3}"),      r"\1"),   # ***bold italic***
    (re.compile(r"\*{2}(.+?)\*{2}"),      r"\1"),   # **bold**
    (re.compile(r"_{2}(.+?)_{2}"),        r"\1"),   # __bold__
    (re.compile(r"\*(.+?)\*"),            r"\1"),   # *italic*
    (re.compile(r"_(.+?)_"),              r"\1"),   # _italic_
    (re.compile(r"~~(.+?)~~"),            r"\1"),   # ~~strikethrough~~
    (re.compile(r"`(.+?)`"),              r"\1"),   # `code`
]


def _strip_num(line: str) -> str:
    return _NUM_RE.sub("", line)


def _strip_inline_md(text: str) -> str:
    for pattern, repl in _INLINE_MD_SUBS:
        text = pattern.sub(repl, text)
    return text.strip()


def _parse_import_line(line: str) -> str | None:
    """Return quote text from one import line, or None to skip."""
    line = line.strip()
    if not line or _HEADING_RE.match(line):
        return None
    line = _LIST_PREFIX_RE.sub("", line, count=1)
    return _strip_inline_md(line) or None


class QuotesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._renumbering = False
        self._hint_on = False
        self._hint_text = t("q_placeholder")
        self._baseline: list[str] = []
        self._build()
        self._load()

    def _build(self) -> None:
        # Pack the button row first (side="bottom") so it always reserves space
        # and never gets squeezed out by the expanding text frame.
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(btn_row, text=t("q_import"), width=120,
                      command=self._import).pack(side="left")
        ctk.CTkButton(
            btn_row, text=t("q_open_file"), width=96,
            fg_color="transparent", border_width=1, border_color="#B0AFA8",
            hover_color="#EEEDE9", text_color="#37352F",
            command=self._open_file,
        ).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(btn_row, text=t("q_len_hint"),
                     text_color="#9B9A97", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 0))
        # Count sits at the far right; the rarely-used restore is a de-emphasized text button beside it.
        self._count_label = ctk.CTkLabel(
            btn_row, text="", text_color="#9B9A97", font=ctk.CTkFont(size=12))
        self._count_label.pack(side="right")
        ctk.CTkButton(
            btn_row, text=t("q_restore"), width=120, height=28,
            fg_color="transparent", border_width=1, border_color="#B0AFA8",
            hover_color="#EEEDE9", text_color="#37352F",
            font=ctk.CTkFont(size=12), command=self._restore,
        ).pack(side="right", padx=(0, 12))

        text_frame = ctk.CTkFrame(
            self, corner_radius=8, border_width=1,
            border_color=["#D8D6D0", "#3A3A3C"],
            fg_color=["#FFFFFF", "#1C1C1E"],
        )
        text_frame.pack(side="top", fill="both", expand=True, padx=8, pady=(8, 4))

        scrollbar = ctk.CTkScrollbar(text_frame)
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)

        self._text = tk.Text(
            text_frame,
            wrap="char",
            font=("Microsoft YaHei UI", 15),
            bg="#FFFFFF",
            fg="#37352F",
            selectbackground="#DCE9DC",
            selectforeground="#37352F",
            insertbackground="#37352F",
            relief="flat",
            bd=0,
            padx=12,
            pady=10,
            spacing3=4,
            yscrollcommand=scrollbar.set,
            undo=True,
        )
        scrollbar.configure(command=self._text.yview)
        self._text.pack(fill="both", expand=True, padx=2, pady=2)

        self._text.tag_configure("num", foreground=_NUM_FG)
        self._text.tag_configure("hint", foreground="#B8B7B4")

        self._text.bind("<FocusIn>",       self._on_focus_in)
        self._text.bind("<Return>",        self._on_return)
        self._text.bind("<BackSpace>",     self._on_backspace)
        self._text.bind("<Delete>",        self._on_delete)
        self._text.bind("<Home>",          self._on_home)
        self._text.bind("<Left>",          self._on_left)
        self._text.bind("<Right>",         self._on_right)
        self._text.bind("<Key>",           self._on_any_key)
        self._text.bind("<KeyRelease>",    self._on_key_release)
        self._text.bind("<<Paste>>",       self._on_paste)
        self._text.bind("<FocusOut>",      self._on_focus_out)
        self._text.bind("<ButtonRelease-1>", self._on_click)
        self._text.bind("<Control-s>",       self._on_ctrl_s)
        self._text.bind("<<Undo>>",          self._on_undo)
        self._text.bind("<<Redo>>",          self._on_undo)

    # ── prefix helpers ─────────────────────────────────────────────────────

    def _prefix_len(self, line: int) -> int:
        m = _NUM_RE.match(self._text.get(f"{line}.0", f"{line}.end"))
        return len(m.group()) if m else 0

    def _clamp_cursor(self) -> None:
        """Push cursor past the gray prefix if it landed inside it."""
        pos = self._text.index("insert")
        line, col = map(int, pos.split("."))
        plen = self._prefix_len(line)
        if col < plen:
            self._text.mark_set("insert", f"{line}.{plen}")

    # ── numbering ──────────────────────────────────────────────────────────

    def _content_empty(self, line: int) -> bool:
        """True if the line has no quote content (blank, or only a locked number)."""
        return not _strip_num(self._text.get(f"{line}.0", f"{line}.end")).strip()

    # ── placeholder hint on the trailing ghost slot ─────────────────────────

    def _clear_hint(self) -> None:
        """Remove the grey placeholder so content logic never sees it. Cosmetic (no undo)."""
        if not self._hint_on:
            return
        self._hint_on = False
        rng = self._text.tag_ranges("hint")
        if rng:
            self._text.config(undo=False)
            self._text.delete(rng[0], rng[1])
            self._text.config(undo=True)

    def _show_hint(self) -> None:
        if self._hint_on:
            return
        last = int(self._text.index("end-1c").split(".")[0])
        if not self._content_empty(last):
            return
        saved = self._text.index("insert")
        self._text.config(undo=False)
        self._text.insert("end-1c", self._hint_text, "hint")
        self._text.config(undo=True)
        self._text.mark_set("insert", saved)
        self._hint_on = True

    def _slot_empty(self) -> bool:
        """True if the trailing slot has no real content (ignoring the placeholder)."""
        last = int(self._text.index("end-1c").split(".")[0])
        text = self._text.get(f"{last}.0", f"{last}.end")
        if self._hint_on and text.endswith(self._hint_text):
            text = text[: -len(self._hint_text)]
        return not _strip_num(text).strip()

    def _update_hint(self) -> None:
        """Hint stays unless the cursor is actually on the (empty) trailing slot."""
        focused = self._text.focus_get() is self._text
        last = int(self._text.index("end-1c").split(".")[0])
        cur_line = int(self._text.index("insert").split(".")[0])
        if (focused and cur_line == last) or not self._slot_empty():
            self._clear_hint()
        else:
            self._show_hint()

    def _ensure_ghost(self) -> None:
        """Keep exactly one empty trailing line — the 'next input' slot users type into.

        Inherits the caller's undo state (renumber toggles it), so it stays cosmetic.
        The insert mark is preserved so appending the ghost never drags the cursor down.
        """
        saved = self._text.index("insert")
        last = int(self._text.index("end-1c").split(".")[0])
        while last >= 2 and self._content_empty(last) and self._content_empty(last - 1):
            self._text.delete(f"{last - 1}.end", f"{last}.end")
            last -= 1
        if not self._content_empty(last):
            self._text.insert("end-1c", "\n")
        self._text.mark_set("insert", saved)

    def _renumber(self, track_undo: bool = False) -> None:
        """Update only changed line prefixes and keep one trailing ghost slot.

        By default undo is disabled so prefix changes don't pollute the undo stack.
        Pass track_undo=True to record them, e.g. so a paste undoes as one unit.
        """
        if self._renumbering:
            return
        self._clear_hint()  # never let the placeholder reach content/ghost logic
        self._renumbering = True
        if not track_undo:
            self._text.config(undo=False)
        try:
            self._ensure_ghost()
            total = int(self._text.index("end-1c").split(".")[0])
            for i in range(1, total + 1):
                line_text = self._text.get(f"{i}.0", f"{i}.end")
                m = _NUM_RE.match(line_text)
                expected = f"{i}. "
                if m:
                    if m.group() != expected:
                        self._text.delete(f"{i}.0", f"{i}.{len(m.group())}")
                        self._text.insert(f"{i}.0", expected)
                else:
                    self._text.insert(f"{i}.0", expected)
            self._reapply_tags()
            self._update_count()
        finally:
            if not track_undo:
                self._text.config(undo=True)
            self._renumbering = False
        self._clamp_cursor()

    @contextmanager
    def _atomic_edit(self):
        """Group a structural edit + its renumber into one undo unit.

        Disables tk's auto separators and brackets the edit with manual ones so a
        single Ctrl+Z reverts the whole thing — never leaving an orphan prefix or line.
        """
        self._text.configure(autoseparators=False)
        self._text.edit_separator()
        try:
            yield
        finally:
            self._renumber(track_undo=True)
            self._text.edit_separator()
            self._text.configure(autoseparators=True)

    def _reapply_tags(self) -> None:
        self._text.tag_remove("num", "1.0", "end")
        for i, line in enumerate(self._text.get("1.0", "end-1c").split("\n"), start=1):
            m = _NUM_RE.match(line)
            if m:
                self._text.tag_add("num", f"{i}.0", f"{i}.{len(m.group())}")

    def _update_count(self) -> None:
        self._count_label.configure(text=quote_count(len(self._get_quotes())))

    # ── event handlers ─────────────────────────────────────────────────────

    def _on_return(self, event) -> str:
        self._clamp_cursor()
        line = int(self._text.index("insert").split(".")[0])
        if self._content_empty(line):
            return "break"  # never create empty items; the ghost slot already waits below
        with self._atomic_edit():
            self._text.insert("insert", "\n")
            new_line = int(self._text.index("insert").split(".")[0])
        prefix = f"{new_line}. "
        self._text.mark_set("insert", f"{new_line}.{len(prefix)}")
        self._text.see("insert")
        return "break"

    def _on_backspace(self, event) -> str | None:
        if self._text.tag_ranges("sel"):
            self._text.after(10, self._renumber)
            return None
        pos = self._text.index("insert")
        line, col = map(int, pos.split("."))
        plen = self._prefix_len(line)
        if col < plen:
            return "break"
        if col == plen:
            if line == 1:
                return "break"
            # Merge: delete newline + this line's prefix to join with prev line
            with self._atomic_edit():
                self._text.delete(f"{line - 1}.end", f"{line}.{plen}")
            return "break"
        return None

    def _on_delete(self, event) -> str | None:
        if self._text.tag_ranges("sel"):
            self._text.after(10, self._renumber)
            return None
        pos = self._text.index("insert")
        line, col = map(int, pos.split("."))
        plen = self._prefix_len(line)
        if col < plen:
            return "break"
        # At end of line: Delete would swallow next line's prefix — handle it
        if self._text.compare("insert", "==", f"{line}.end"):
            total = int(self._text.index("end-1c").split(".")[0])
            if line < total:
                next_plen = self._prefix_len(line + 1)
                with self._atomic_edit():
                    self._text.delete("insert", f"{line + 1}.{next_plen}")
                return "break"
        return None

    def _on_home(self, event) -> str | None:
        if event.state & _SHIFT:
            return None  # Let Tk extend selection normally
        pos = self._text.index("insert")
        line = int(pos.split(".")[0])
        plen = self._prefix_len(line)
        self._text.mark_set("insert", f"{line}.{plen}")
        self._text.see("insert")
        return "break"

    def _on_left(self, event) -> str | None:
        if event.state & _SHIFT:
            return None
        pos = self._text.index("insert")
        line, col = map(int, pos.split("."))
        if col <= self._prefix_len(line):
            if line > 1:
                self._text.mark_set("insert", f"{line - 1}.end")
                self._text.see("insert")
            return "break"
        return None

    def _on_right(self, event) -> str | None:
        if event.state & _SHIFT:
            return None
        pos = self._text.index("insert")
        line, col = map(int, pos.split("."))
        line_end = int(self._text.index(f"{line}.end").split(".")[1])
        if col >= line_end:
            total = int(self._text.index("end-1c").split(".")[0])
            if line < total:
                next_plen = self._prefix_len(line + 1)
                self._text.mark_set("insert", f"{line + 1}.{next_plen}")
                self._text.see("insert")
                return "break"
        return None

    def _on_any_key(self, event) -> None:
        """If a printable character is typed while cursor is in prefix, push past it."""
        if not event.char or event.state & 0x4:  # no char or Ctrl held
            return
        self._clamp_cursor()

    def _on_key_release(self, event) -> None:
        """Maintain the trailing ghost slot as content is typed or deleted."""
        if (event.char and event.char.isprintable()) or event.keysym in ("BackSpace", "Delete"):
            self._renumber()
        self._update_hint()

    def _on_paste(self, event) -> str:
        """Clean clipboard text the same way as 导入 before inserting it."""
        try:
            raw = self._text.clipboard_get()
        except tk.TclError:
            return "break"
        cleaned = [q for ln in raw.splitlines() if (q := _parse_import_line(ln)) is not None]
        if not cleaned:
            return "break"
        with self._atomic_edit():
            if self._text.tag_ranges("sel"):
                self._text.delete("sel.first", "sel.last")
            self._clamp_cursor()
            self._text.insert("insert", "\n".join(cleaned))
        self._text.see("insert")
        return "break"

    def _on_focus_in(self, event) -> None:
        self._text.after_idle(self._update_hint)

    def _on_focus_out(self, event) -> None:
        self._renumber()
        self._text.after_idle(self._update_hint)

    def _on_click(self, event) -> None:
        self._text.after_idle(self._after_pointer)

    def _after_pointer(self) -> None:
        self._clamp_cursor()
        self._update_hint()

    def _on_undo(self, event) -> None:
        # After tk finishes the undo/redo, re-prefix any lines whose numbers shifted
        self._text.after_idle(self._renumber)

    def _on_ctrl_s(self, event) -> str:
        try:
            self.save()
        except (OSError, UnicodeError) as exc:
            mb.showerror(t("dlg_save_failed"), str(exc))
        return "break"

    # ── public API ─────────────────────────────────────────────────────────

    def _get_quotes(self) -> list[str]:
        text = self._text.get("1.0", "end-1c")
        if self._hint_on and text.endswith(self._hint_text):
            text = text[: -len(self._hint_text)]
        return [s for ln in text.split("\n") if (s := _strip_num(ln).strip())]

    def _set_quotes(self, quotes: list[str]) -> None:
        """Insert editor-owned numbering separately from the quote text."""
        self._hint_on = False  # text is about to be wiped; drop any stale placeholder state
        numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(quotes))
        self._text.delete("1.0", "end")
        self._text.insert("1.0", numbered)
        self._reapply_tags()
        self._update_count()

    def _replace_all_undoable(self, quotes: list[str]) -> None:
        """Replace all content as a single undo unit (used by 导入 / 恢复默认)."""
        with self._atomic_edit():
            self._set_quotes(quotes)
        self._text.mark_set("insert", "1.0")
        self._clamp_cursor()
        self._text.see("insert")
        self._text.after_idle(self._update_hint)

    def _disk_mtime(self) -> int:
        try:
            return quotes_path().stat().st_mtime_ns
        except OSError:
            return 0

    def _load(self) -> None:
        self._disk_mtime_seen = self._disk_mtime()
        try:
            self._baseline = load_quotes()
        except (OSError, UnicodeError) as exc:
            mb.showerror(t("dlg_error"), f"{quotes_path()}\n{exc}")
            return
        self._set_quotes(self._baseline)
        self._renumber()  # append the trailing ghost slot
        self._text.edit_reset()  # loaded content is the undo floor
        self._text.after_idle(self._update_hint)

    def poll_reload(self) -> None:
        """Reload from disk if the file changed externally and the UI has no unsaved edits."""
        if self.has_changes() or self._disk_mtime() == self._disk_mtime_seen:
            return
        self._load()

    def _import(self) -> None:
        path = fd.askopenfilename(
            filetypes=[(t("q_ft_textmd"), "*.txt *.md"), (t("q_ft_all"), "*.*")])
        if not path:
            return
        try:
            raw = Path(path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            mb.showerror(t("dlg_error"), str(exc))
            return
        lines = raw.splitlines()
        if len(lines) > _FILE_SIZE_WARN:
            if not mb.askyesno(t("q_large_title"), t("q_large_body").format(n=len(lines))):
                return
        parsed = [q for ln in lines if (q := _parse_import_line(ln)) is not None]
        existing = self._get_quotes()
        existing_set = set(existing)
        new_quotes = [q for q in dict.fromkeys(parsed) if q not in existing_set]
        if new_quotes:
            self._replace_all_undoable(existing + new_quotes)
        mb.showinfo(
            t("q_import_done"),
            t("q_import_done_body").format(
                total=len(parsed), new=len(new_quotes), dup=len(parsed) - len(new_quotes)),
        )

    def _open_file(self) -> None:
        # Persist the current view first so the opened file matches what's shown;
        # external edits then sync back via poll_reload.
        try:
            self.save()
            os.startfile(quotes_path())
        except (OSError, UnicodeError) as exc:
            mb.showerror(t("dlg_error"), str(exc))

    def _restore(self) -> None:
        self._replace_all_undoable(default_quotes())

    def has_changes(self) -> bool:
        return self._get_quotes() != self._baseline

    def save(self) -> None:
        quotes = self._get_quotes()
        if quotes == self._baseline:
            self.poll_reload()
            return
        if quotes_path().exists():
            disk_quotes = load_quotes()
            if disk_quotes != self._baseline and disk_quotes != quotes:
                raise OSError(t("q_edit_conflict"))
        save_quotes(quotes)
        self._baseline = quotes
        self._disk_mtime_seen = self._disk_mtime()
