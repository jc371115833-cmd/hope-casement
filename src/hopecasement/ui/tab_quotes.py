import re
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from pathlib import Path

import customtkinter as ctk

from hopecasement.quotes import DEFAULT_QUOTES, load_quotes, save_quotes

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
    line = _strip_inline_md(line)
    return line if line else None


class QuotesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._renumbering = False
        self._build()
        self._load()

    def _build(self) -> None:
        # Pack the button row first (side="bottom") so it always reserves space
        # and never gets squeezed out by the expanding text frame.
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(btn_row, text="导入 .txt 文件", width=140,
                      command=self._import).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_row, text="恢复默认句子", width=140,
            fg_color="#EEEDE9", hover_color="#E4E3DE", text_color="#37352F",
            command=self._restore,
        ).pack(side="left")
        self._count_label = ctk.CTkLabel(
            btn_row, text="", text_color="#9B9A97", font=ctk.CTkFont(size=12))
        self._count_label.pack(side="right")

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

        self._text.bind("<Return>",        self._on_return)
        self._text.bind("<BackSpace>",     self._on_backspace)
        self._text.bind("<Delete>",        self._on_delete)
        self._text.bind("<Home>",          self._on_home)
        self._text.bind("<Left>",          self._on_left)
        self._text.bind("<Right>",         self._on_right)
        self._text.bind("<Key>",           self._on_any_key)
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

    def _renumber(self) -> None:
        """Update only changed line prefixes; undo=False so content undo is unaffected."""
        if self._renumbering:
            return
        self._renumbering = True
        self._text.config(undo=False)
        try:
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
            self._text.config(undo=True)
            self._renumbering = False
        self._clamp_cursor()

    def _reapply_tags(self) -> None:
        self._text.tag_remove("num", "1.0", "end")
        for i, line in enumerate(self._text.get("1.0", "end-1c").split("\n"), start=1):
            m = _NUM_RE.match(line)
            if m:
                self._text.tag_add("num", f"{i}.0", f"{i}.{len(m.group())}")

    def _update_count(self) -> None:
        self._count_label.configure(text=f"共 {len(self._get_quotes())} 句")

    # ── event handlers ─────────────────────────────────────────────────────

    def _on_return(self, event) -> str:
        self._text.edit_separator()
        self._text.insert("insert", "\n")
        new_line = int(self._text.index("insert").split(".")[0])
        self._renumber()
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
            self._text.edit_separator()
            self._text.delete(f"{line - 1}.end", f"{line}.{plen}")
            self._renumber()
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
                self._text.edit_separator()
                self._text.delete("insert", f"{line + 1}.{next_plen}")
                self._renumber()
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

    def _on_paste(self, event) -> None:
        def finish():
            self._renumber()
            self._text.mark_set("insert", "end-1c")
            self._text.see("insert")
        self._text.after(10, finish)

    def _on_focus_out(self, event) -> None:
        self._renumber()

    def _on_click(self, event) -> None:
        self._text.after_idle(self._clamp_cursor)

    def _on_undo(self, event) -> None:
        # After tk finishes the undo/redo, re-prefix any lines whose numbers shifted
        self._text.after_idle(self._renumber)

    def _on_ctrl_s(self, event) -> str:
        self.save()
        return "break"

    # ── public API ─────────────────────────────────────────────────────────

    def _get_quotes(self) -> list[str]:
        lines = self._text.get("1.0", "end-1c").split("\n")
        return [s for ln in lines if (s := _strip_num(ln).strip())]

    def _set_quotes(self, quotes: list[str]) -> None:
        numbered = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(quotes))
        self._text.delete("1.0", "end")
        self._text.insert("1.0", numbered)
        self._reapply_tags()
        self._update_count()

    def _load(self) -> None:
        self._baseline = load_quotes()
        self._set_quotes(self._baseline)
        self._text.edit_reset()  # loaded content is the undo floor

    def _import(self) -> None:
        path = fd.askopenfilename(
            filetypes=[("文本 / Markdown", "*.txt *.md"), ("所有文件", "*.*")])
        if not path:
            return
        raw = Path(path).read_text(encoding="utf-8", errors="ignore")
        lines = raw.splitlines()
        if len(lines) > _FILE_SIZE_WARN:
            if not mb.askyesno("文件较大", f"文件共 {len(lines)} 行，确认导入？"):
                return
        parsed = [q for ln in lines if (q := _parse_import_line(ln)) is not None]
        existing = self._get_quotes()
        existing_set = set(existing)
        new_quotes = [q for q in parsed if q not in existing_set]
        self._set_quotes(existing + new_quotes)
        mb.showinfo(
            "导入完成",
            f"共识别 {len(parsed)} 句，新增 {len(new_quotes)} 句，去重 {len(parsed) - len(new_quotes)} 句。",
        )

    def _restore(self) -> None:
        self._set_quotes(list(DEFAULT_QUOTES))

    def has_changes(self) -> bool:
        return self._get_quotes() != self._baseline

    def save(self) -> None:
        quotes = self._get_quotes()
        save_quotes(quotes)
        self._baseline = quotes
