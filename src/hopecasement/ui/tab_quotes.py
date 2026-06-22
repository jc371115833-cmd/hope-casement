import tkinter.filedialog as fd

import customtkinter as ctk

from hopecasement.quotes import _DEFAULT_QUOTES, load_quotes, save_quotes


class QuotesTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()
        self._load()

    def _build(self):
        self.textbox = ctk.CTkTextbox(self, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkButton(btn_row, text="导入 .txt 文件", width=140, command=self._import).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="恢复默认句子", width=140, fg_color="gray40",
                      hover_color="gray30", command=self._restore).pack(side="left")

    def _load(self):
        self._baseline = load_quotes()
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "\n".join(self._baseline))

    def _import(self):
        path = fd.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return
        with open(path, encoding="utf-8", errors="ignore") as f:
            new_lines = [ln.strip() for ln in f if ln.strip()]
        existing = [ln for ln in self.textbox.get("1.0", "end").splitlines() if ln.strip()]
        merged = existing + [ln for ln in new_lines if ln not in existing]
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "\n".join(merged))

    def _restore(self):
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "\n".join(_DEFAULT_QUOTES))

    def has_changes(self) -> bool:
        current = [ln.strip() for ln in self.textbox.get("1.0", "end").splitlines() if ln.strip()]
        return current != self._baseline

    def save(self) -> None:
        lines = [ln.strip() for ln in self.textbox.get("1.0", "end").splitlines() if ln.strip()]
        save_quotes(lines)
        self._baseline = lines
