#!/usr/bin/env python3
# VEXLang Editor Pro — dojebany edytor dla VEXLang

import sys, os, io, json, threading, zipfile, subprocess, tempfile, shutil, re as _re, time, random as _random
from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.font import Font
from urllib.request import urlopen, Request

# ── ukryj konsole ──
try:
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except: pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vexlang import Lexer, Parser, Interpreter, SLOWA_KLUCZOWE, VERSION as VEX_VER

VERSION = "1.1.0"
GITHUB_REPO = "wk12100lol-prog/vexlang"

# ── VEXHACK NEON PALETTE ──
BG = "#0a0c14"
BG2 = "#0f1220"
BG3 = "#151830"
CARD = "#141726"
CARD2 = "#1a1d35"
TEXT = "#c8ccd4"
TEXT_DIM = "#6a6f85"
PINK = "#ff6b9d"
GREEN = "#00ffa3"
ORANGE = "#ffa640"
BLUE = "#40bfff"
PURPLE = "#a855f7"
CYAN = "#22d3ee"
RED = "#ef4444"
YELLOW = "#eab308"
BORDER = "#1e2240"
BORDER2 = "#2a2f55"

FONT_NAME = "JetBrains Mono"
FONT_FALLBACK = "Consolas"
FONT_SIZE = 13

# ── UTILS ──

def _font(size=FONT_SIZE, bold=False):
    return Font(family=FONT_NAME, size=size, weight="bold" if bold else "normal")

def _btn(parent, text, cmd, bg=PINK, fg=BG, w=None):
    b = Button(parent, text=text, bg=bg, fg=fg, font=_font(10, True),
               border=0, padx=14, pady=4, cursor="hand2", command=cmd)
    if w: b.config(width=w)
    def on_enter(e): b.config(bg=fg, fg=bg)
    def on_leave(e): b.config(bg=bg, fg=fg)
    b.bind("<Enter>", on_enter)
    b.bind("<Leave>", on_leave)
    return b

def _lbl(parent, text, color=TEXT_DIM, size=10, bold=False):
    l = Label(parent, text=text, bg=BG, fg=color, font=_font(size, bold))
    return l

def _separator(parent, color=BORDER):
    f = Frame(parent, height=1, bg=color)
    return f

# ── THEME WRAPPER ──
class ThemedText(Text):
    def __init__(self, master, **kw):
        kw.setdefault("bg", BG)
        kw.setdefault("fg", TEXT)
        kw.setdefault("font", _font())
        kw.setdefault("insertbackground", PINK)
        kw.setdefault("border", 0)
        kw.setdefault("padx", 12)
        kw.setdefault("pady", 8)
        kw.setdefault("relief", FLAT)
        kw.setdefault("wrap", NONE)
        kw.setdefault("undo", True)
        kw.setdefault("selectbackground", "#3a1a40")
        kw.setdefault("selectforeground", TEXT)
        super().__init__(master, **kw)
        self._setup_tags()

    def _setup_tags(self):
        self.tag_config("keyword", foreground=PINK, font=_font(bold=True))
        self.tag_config("string", foreground=GREEN)
        self.tag_config("comment", foreground="#4a4d5e", font=_font(bold=False))
        self.tag_config("number", foreground=ORANGE)
        self.tag_config("builtin", foreground=BLUE)
        self.tag_config("error", foreground=RED, underline=True)


class ThemedCanvas(Canvas):
    def __init__(self, master, **kw):
        kw.setdefault("bg", BG)
        kw.setdefault("border", 0)
        kw.setdefault("highlightthickness", 0)
        super().__init__(master, **kw)


# ═══════════════════════════════════════
#  GŁÓWNY EDYTOR
# ═══════════════════════════════════════

class VEXLangEditor:
    def __init__(self):
        self.root = Tk()
        self.root.title(f"VEXLang Editor v{VERSION}")
        self.root.geometry("1100x720")
        self.root.configure(bg=BG)
        self.root.minsize(800, 500)
        self._ustaw_ikone()

        # stan
        self._pliki = {}  # {path: content_snapshot}
        self._karty = []  # list of path
        self._aktywna_karta = None
        self._zmieniony = False
        self._wyniki_wyszukiwania = []
        self._szukaj_idx = -1

        self._build_ui()
        self._bind_events()
        self._highlight_timer = None

        # domyślna karta
        self._nowa_karta()

        # auto-update
        self.root.after(2000, self._sprawdz_aktualizacje)

        # animacja cząsteczek tła
        self._animuj_czastki()

    def _ustaw_ikone(self):
        try:
            self.root.iconbitmap(default="")
        except: pass

    # ══════════════════════════════════
    #  UI
    # ══════════════════════════════════

    def _build_ui(self):
        # ── HEADER ──
        header = Frame(self.root, bg=BG, height=48)
        header.pack(fill=X)
        header.pack_propagate(False)

        # logo / tytuł
        logo_frame = Frame(header, bg=BG)
        logo_frame.pack(side=LEFT, padx=16, pady=8)
        Canvas(logo_frame, width=28, height=28, bg=BG, highlightthickness=0).pack(side=LEFT)
        # symulowane logo – kółko
        c = Canvas(logo_frame, width=28, height=28, bg=BG, highlightthickness=0)
        c.create_oval(2, 2, 26, 26, outline=PINK, width=2, fill="")
        c.create_oval(7, 7, 21, 21, outline=GREEN, width=2, fill="")
        c.pack(side=LEFT)
        _lbl(logo_frame, " VEXLang", PINK, 14, True).pack(side=LEFT, padx=6)

        # przyciski toolbar
        tb = Frame(header, bg=BG)
        tb.pack(side=LEFT, padx=20)

        self._run_btn = _btn(tb, "▶ Uruchom", self._uruchom, PINK)
        self._run_btn.pack(side=LEFT, padx=2)

        self._stop_btn = _btn(tb, "■ Stop", self._stop_exec, RED, w=6)
        self._stop_btn.pack(side=LEFT, padx=2)

        self._repl_btn = _btn(tb, "💻 REPL", self._uruchom_repl, GREEN)
        self._repl_btn.pack(side=LEFT, padx=2)

        self._find_btn = _btn(tb, "🔍 Szukaj", self._pokaz_szukaj, BLUE)
        self._find_btn.pack(side=LEFT, padx=2)

        self._save_btn = _btn(tb, "💾 Zapisz", self._zapisz, ORANGE)
        self._save_btn.pack(side=LEFT, padx=2)

        # update label
        self._update_lbl = Label(header, text="", bg=BG, fg=TEXT_DIM, font=_font(9))
        self._update_lbl.pack(side=RIGHT, padx=12)

        # separator
        _separator(self.root).pack(fill=X)

        # ── SZUKAJ BAR ──
        self._find_frame = Frame(self.root, bg=BG, height=0)
        self._find_frame.pack(fill=X)
        self._find_frame.pack_propagate(False)
        self._find_visible = False

        find_inner = Frame(self._find_frame, bg=CARD, padx=8, pady=4)
        find_inner.pack(fill=X, padx=8, pady=2)
        _lbl(find_inner, "🔍", TEXT_DIM, 12).pack(side=LEFT, padx=2)
        self._find_entry = Entry(find_inner, bg=BG2, fg=TEXT, font=_font(11),
                                 insertbackground=PINK, border=0, relief=FLAT, width=30)
        self._find_entry.pack(side=LEFT, padx=4, fill=X, expand=True)
        self._find_entry.bind("<Return>", lambda e: self._szukaj())
        self._find_entry.bind("<KeyRelease>", lambda e: self._szukaj())

        _btn(find_inner, "⬆", lambda: self._szukaj_wstecz(), BG3).pack(side=LEFT, padx=1)
        _btn(find_inner, "⬇", lambda: self._szukaj(), BG3).pack(side=LEFT, padx=1)
        self._find_count = _lbl(find_inner, "", TEXT_DIM, 9)
        self._find_count.pack(side=LEFT, padx=6)
        _btn(find_inner, "✕", self._ukryj_szukaj, RED).pack(side=LEFT, padx=4)

        self._find_frame.config(height=0)
        self._find_frame.pack_forget()

        # ── GŁÓWNY OBSZAR ──
        main = Frame(self.root, bg=BG)
        main.pack(fill=BOTH, expand=True)

        # zakładki plików
        self._tab_bar = Frame(main, bg=BG2, height=32)
        self._tab_bar.pack(fill=X)
        self._tab_bar.pack_propagate(False)

        self._tab_container = Frame(self._tab_bar, bg=BG2)
        self._tab_container.pack(side=LEFT, fill=X, expand=True, padx=4)

        # przycisk nowa karta
        _btn(self._tab_bar, "+", self._nowa_karta, BG3, TEXT).pack(side=RIGHT, padx=4)

        # obszar kodu + numery + scroll
        editor_area = Frame(main, bg=BG)
        editor_area.pack(fill=BOTH, expand=True)

        # lewy pasek (numery + fold)
        self._gutter = Canvas(editor_area, width=50, bg=BG2, highlightthickness=0)
        self._gutter.pack(side=LEFT, fill=Y)

        # edytor
        self._text = ThemedText(editor_area, width=80)
        self._text.pack(side=LEFT, fill=BOTH, expand=True)

        # scrollbar
        sc_s = Frame(editor_area, bg=BG2, width=12)
        sc_s.pack(side=RIGHT, fill=Y)
        self._scroll = Scrollbar(sc_s, command=self._text.yview, bg=BG2, troughcolor=BG,
                                  activebackground=PINK, border=0, width=10)
        self._scroll.pack(fill=Y, expand=True)
        self._text.config(yscrollcommand=self._scroll.set)

        # separator
        _separator(self.root, BORDER).pack(fill=X)

        # ── OUTPUT ──
        out_frame = Frame(self.root, bg=BG, height=180)
        out_frame.pack(fill=X)
        out_frame.pack_propagate(False)

        # nagłówek outputu
        out_header = Frame(out_frame, bg=BG2, height=28)
        out_header.pack(fill=X)
        out_header.pack_propagate(False)

        self._out_tabs = {}
        for name, color in [("OUTPUT", GREEN), ("BŁĘDY", RED), ("REPL", BLUE)]:
            tab = Frame(out_header, bg=BG2, cursor="hand2")
            tab.pack(side=LEFT, padx=2, pady=2)
            lbl = Label(tab, text=name, bg=BG2, fg=TEXT_DIM, font=_font(9, True), padx=10)
            lbl.pack()
            lbl.bind("<Button-1>", lambda e, n=name: self._switch_out_tab(n))
            tab.bind("<Button-1>", lambda e, n=name: self._switch_out_tab(n))
            self._out_tabs[name] = {"frame": tab, "label": lbl, "color": color}

        self._clear_out_btn = Label(out_header, text="✕", bg=BG2, fg=TEXT_DIM,
                                     font=_font(9), cursor="hand2")
        self._clear_out_btn.pack(side=RIGHT, padx=8)
        self._clear_out_btn.bind("<Button-1>", lambda e: self._czysc_output())
        self._clear_out_btn.bind("<Enter>", lambda e: self._clear_out_btn.config(fg=RED))
        self._clear_out_btn.bind("<Leave>", lambda e: self._clear_out_btn.config(fg=TEXT_DIM))

        # output text
        self._output = ThemedText(out_frame, height=6, state=DISABLED, wrap=WORD)
        self._output.pack(fill=BOTH, expand=True)
        self._output.tag_config("out_std", foreground=TEXT)
        self._output.tag_config("out_err", foreground=RED)
        self._output.tag_config("out_ok", foreground=GREEN)
        self._output.tag_config("out_info", foreground=BLUE)

        # ── STATUS BAR ──
        status = Frame(self.root, bg=BG2, height=24)
        status.pack(fill=X)
        status.pack_propagate(False)

        self._status_line = Label(status, text="Ln 1, Col 1", bg=BG2, fg=TEXT_DIM, font=_font(9))
        self._status_line.pack(side=LEFT, padx=10)

        self._status_file = Label(status, text="", bg=BG2, fg=TEXT_DIM, font=_font(9))
        self._status_file.pack(side=RIGHT, padx=10)

        self._status_encoding = Label(status, text="UTF-8", bg=BG2, fg=TEXT_DIM, font=_font(9))
        self._status_encoding.pack(side=RIGHT, padx=10)

        # wybierz pierwszy tab output
        self._active_out_tab = "OUTPUT"
        self._switch_out_tab("OUTPUT")

        # ── tło z cząsteczkami ──
        self._particle_canvas = ThemedCanvas(self.root)
        self._particle_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._particle_canvas.lower()

    # ══════════════════════════════════
    #  ZAKŁADKI PLIKÓW
    # ══════════════════════════════════

    def _nowa_karta(self, path=None):
        tab_frame = Frame(self._tab_container, bg=CARD2, cursor="hand2")
        # zamknij
        close_lbl = Label(tab_frame, text="✕", bg=CARD2, fg=TEXT_DIM, font=_font(9), padx=2)
        close_lbl.pack(side=RIGHT)
        close_lbl.bind("<Button-1>", lambda e, p=path: self._zamknij_karte(p))
        close_lbl.bind("<Enter>", lambda e: close_lbl.config(fg=RED))
        close_lbl.bind("<Leave>", lambda e: close_lbl.config(fg=TEXT_DIM))
        # nazwa
        name = os.path.basename(path) if path else "bez nazwy.vex"
        name_lbl = Label(tab_frame, text=name, bg=CARD2, fg=TEXT_DIM, font=_font(9), padx=6)
        name_lbl.pack(side=RIGHT)
        name_lbl.bind("<Button-1>", lambda e, p=path: self._przelacz_karte(p))
        tab_frame.bind("<Button-1>", lambda e, p=path: self._przelacz_karte(p))

        tab_frame.pack(side=LEFT, padx=1, pady=2)

        tid = path or f"_new_{len(self._karty)}"
        self._pliki[tid] = {"frame": tab_frame, "name_lbl": name_lbl, "close": close_lbl,
                            "path": path, "content": "", "saved": True}
        self._karty.append(tid)
        self._przelacz_karte(tid)
        return tid

    def _przelacz_karte(self, tid):
        if tid == self._aktywna_karta:
            return
        # zapisz bieżący stan
        if self._aktywna_karta:
            self._pliki[self._aktywna_karta]["content"] = self._text.get("1.0", "end-1c")
            self._pliki[self._aktywna_karta]["saved"] = not self._zmieniony
            # odznacz
            d = self._pliki[self._aktywna_karta]
            d["frame"].config(bg=BG2)
            d["name_lbl"].config(bg=BG2, fg=TEXT_DIM)
            d["close"].config(bg=BG2)
        # przełącz
        self._aktywna_karta = tid
        d = self._pliki[tid]
        d["frame"].config(bg=CARD2)
        d["name_lbl"].config(bg=CARD2, fg=PINK)
        d["close"].config(bg=CARD2)
        self._text.delete("1.0", END)
        self._text.insert("1.0", d["content"])
        self._zmieniony = not d["saved"]
        self._plik = d["path"]
        self._aktualizuj_tytul()
        self._aktualizuj_status()
        self._highlight()
        self._text.edit_modified(False)
        self._text.edit_reset()

    def _zamknij_karte(self, tid):
        if len(self._karty) <= 1:
            return
        if tid == self._aktywna_karta:
            # zapisz stan
            self._pliki[tid]["content"] = self._text.get("1.0", "end-1c")
        self._pliki[tid]["frame"].destroy()
        self._karty.remove(tid)
        del self._pliki[tid]
        if tid == self._aktywna_karta:
            # przełącz na pierwszą
            self._przelacz_karte(self._karty[0])

    # ══════════════════════════════════
    #  ZDARZENIA
    # ══════════════════════════════════

    def _bind_events(self):
        self._text.bind("<KeyRelease>", self._on_change)
        self._text.bind("<<Modified>>", lambda e: self._text.edit_modified(False))
        self._text.bind("<Control-n>", lambda e: self._nowa_karta())
        self._text.bind("<Control-o>", lambda e: self._otworz())
        self._text.bind("<Control-s>", lambda e: self._zapisz())
        self._text.bind("<Control-S>", lambda e: self._zapisz())
        self._text.bind("<Control-f>", lambda e: self._pokaz_szukaj())
        self._text.bind("<F3>", lambda e: self._szukaj())
        self._text.bind("<Shift-F3>", lambda e: self._szukaj_wstecz())
        self._text.bind("<F5>", lambda e: self._uruchom())
        self._text.bind("<F6>", lambda e: self._uruchom_repl())
        self._text.bind("<Tab>", lambda e: self._wciecie(e))
        self._text.bind("<Shift-Tab>", lambda e: self._odwciecie(e))
        self._text.bind("<ButtonRelease-1>", lambda e: self._aktualizuj_status())
        self._text.bind("<KeyPress>", lambda e: self.root.after(10, self._aktualizuj_status))

        self.root.bind("<Control-q>", lambda e: self.root.destroy())
        self.root.protocol("WM_DELETE_WINDOW", self._zamknij)

    def _on_change(self, e=None):
        self._zmieniony = True
        self._aktualizuj_tytul()
        if self._aktywna_karta:
            self._pliki[self._aktywna_karta]["saved"] = False
        if self._highlight_timer:
            self.root.after_cancel(self._highlight_timer)
        self._highlight_timer = self.root.after(250, self._highlight)
        self._aktualizuj_linie()

    def _wciecie(self, e):
        self._text.insert(INSERT, "    ")
        return "break"

    def _odwciecie(self, e):
        idx = self._text.index(INSERT)
        line_start = f"{idx.split('.')[0]}.0"
        line_text = self._text.get(line_start, idx)
        if line_text.startswith("    "):
            self._text.delete(line_start, f"{line_start}+4c")
        return "break"

    # ══════════════════════════════════
    #  STATUS BAR
    # ══════════════════════════════════

    def _aktualizuj_status(self):
        try:
            idx = self._text.index(INSERT)
            ln, col = idx.split(".")
            self._status_line.config(text=f"Ln {ln}, Col {int(col) + 1}")
            nazwa = os.path.basename(self._plik) if self._plik else ""
            self._status_file.config(text=nazwa)
        except: pass

    def _aktualizuj_tytul(self):
        nazwa = os.path.basename(self._plik) if self._plik else "bez nazwy"
        znak = " ●" if self._zmieniony else ""
        self._root_title = f"VEXLang Editor — {nazwa}{znak}"
        self.root.title(self._root_title)

    # ══════════════════════════════════
    #  SYNTAX HIGHLIGHT
    # ══════════════════════════════════

    def _highlight(self):
        if not self._aktywna_karta:
            return
        for t in ("keyword", "string", "comment", "number", "builtin", "error"):
            self._text.tag_remove(t, "1.0", END)
        data = self._text.get("1.0", END)
        for i, linia in enumerate(data.split("\n"), 1):
            idx = f"{i}.0"
            # komentarz
            if "#" in linia:
                pos = linia.index("#")
                self._text.tag_add("comment", f"{i}.{pos}", f"{i}.end")
                linia = linia[:pos]
            # stringi
            for m in _find_strings(linia):
                self._text.tag_add("string", f"{i}.{m[0]}", f"{i}.{m[1]}")
            # tokeny
            for tok, start, end in _tokenize_line(linia):
                if tok in SLOWA_KLUCZOWE:
                    self._text.tag_add("keyword", f"{i}.{start}", f"{i}.{end}")
                elif tok in ("dlugosc", "konwert", "losuj", "zaokraglij"):
                    self._text.tag_add("builtin", f"{i}.{start}", f"{i}.{end}")
                elif _is_number(tok):
                    self._text.tag_add("number", f"{i}.{start}", f"{i}.{end}")
        self._aktualizuj_linie()

    def _aktualizuj_linie(self):
        self._gutter.delete("all")
        try:
            ilosc = int(self._text.index("end-1c").split(".")[0])
        except:
            ilosc = 1
        self._gutter.config(height=ilosc * 22)
        h = self._text.winfo_height()
        self._gutter.config(height=max(h, ilosc * 22))
        for i in range(1, ilosc + 1):
            y = (i - 1) * 22 + 4
            self._gutter.create_text(40, y, text=str(i), anchor="e",
                                      fill="#3a3d5e", font=_font(10))
            # kropka dla bieżącej linii
            try:
                cur_line = int(self._text.index(INSERT).split(".")[0])
            except: cur_line = 1
            if i == cur_line:
                self._gutter.create_rectangle(0, y - 2, 50, y + 18,
                                               fill="#1a1d40", outline="", width=0)

    # ══════════════════════════════════
    #  FIND / REPLACE
    # ══════════════════════════════════

    def _pokaz_szukaj(self):
        if self._find_visible:
            self._ukryj_szukaj()
            return
        self._find_frame.pack(fill=X, before=self.root.winfo_children()[3] if len(self.root.winfo_children()) > 3 else None)
        self._find_frame.config(height=32)
        self._find_visible = True
        self._find_entry.focus()
        try:
            sel = self._text.selection_get()
            self._find_entry.delete(0, END)
            self._find_entry.insert(0, sel)
        except: pass
        self._szukaj()

    def _ukryj_szukaj(self):
        self._find_frame.pack_forget()
        self._find_visible = False
        self._text.tag_remove("sel", "1.0", END)

    def _szukaj(self, forward=True):
        query = self._find_entry.get()
        if not query:
            self._find_count.config(text="")
            self._text.tag_remove("sel", "1.0", END)
            return
        self._text.tag_remove("sel", "1.0", END)
        self._wyniki_wyszukiwania = []
        start = "1.0"
        while True:
            pos = self._text.search(query, start, END, nocase=True)
            if not pos: break
            self._wyniki_wyszukiwania.append(pos)
            self._text.tag_add("sel", pos, f"{pos}+{len(query)}c")
            start = f"{pos}+{len(query)}c"
        self._text.tag_config("sel", background=PINK, foreground=BG)
        count = len(self._wyniki_wyszukiwania)
        self._find_count.config(text=f"{count} wyników" if count else "brak")
        if self._wyniki_wyszukiwania:
            if forward:
                self._szukaj_idx = (self._szukaj_idx + 1) % count
            else:
                self._szukaj_idx = (self._szukaj_idx - 1) % count if self._szukaj_idx > 0 else count - 1
            pos = self._wyniki_wyszukiwania[self._szukaj_idx]
            self._text.mark_set(INSERT, pos)
            self._text.see(pos)
            self._text.focus()

    def _szukaj_wstecz(self):
        self._szukaj(forward=False)

    # ══════════════════════════════════
    #  FILE OPERATIONS
    # ══════════════════════════════════

    def _otworz(self):
        fp = filedialog.askopenfilename(filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")])
        if not fp: return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                kod = f.read()
            # dodaj kartę
            tid = self._nowa_karta(fp)
            self._text.delete("1.0", END)
            self._text.insert("1.0", kod)
            self._pliki[tid]["content"] = kod
            self._pliki[tid]["saved"] = True
            self._plik = fp
            self._zmieniony = False
            self._aktualizuj_tytul()
            self._aktualizuj_status()
            self._highlight()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć:\n{e}")

    def _zapisz(self, e=None):
        if not self._aktywna_karta: return
        d = self._pliki[self._aktywna_karta]
        if d["path"]:
            self._zapisz_do(d["path"])
        else:
            self._zapisz_jako()

    def _zapisz_jako(self):
        fp = filedialog.asksaveasfilename(defaultextension=".vex",
                                           filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")])
        if not fp: return
        if self._aktywna_karta:
            self._pliki[self._aktywna_karta]["path"] = fp
            self._plik = fp
        self._zapisz_do(fp)

    def _zapisz_do(self, fp):
        try:
            kod = self._text.get("1.0", "end-1c")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(kod)
            self._zmieniony = False
            if self._aktywna_karta:
                self._pliki[self._aktywna_karta]["saved"] = True
                self._pliki[self._aktywna_karta]["name_lbl"].config(text=os.path.basename(fp))
            self._aktualizuj_tytul()
            self._dodaj_output(f"✓ Zapisano: {os.path.basename(fp)}\n", "out_ok")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać:\n{e}")

    def _zamknij(self):
        if self._zmieniony:
            if not messagebox.askokcancel("Wyjście", "Odrzucić zmiany?"):
                return
        self.root.destroy()

    # ══════════════════════════════════
    #  RUN / EXECUTE
    # ══════════════════════════════════

    def _exec_running(self):
        return hasattr(self, '_exec_thread') and self._exec_thread and self._exec_thread.is_alive()

    def _uruchom(self, e=None):
        if self._exec_running():
            return
        kod = self._text.get("1.0", "end-1c")
        if not kod.strip(): return
        self._switch_out_tab("OUTPUT")
        self._czysc_output()
        self._dodaj_output("═══════════════════════════════════\n", "out_info")
        self._dodaj_output("  ▶ Uruchamianie...\n", "out_info")
        self._dodaj_output("═══════════════════════════════════\n", "out_info")
        self._exec_thread = threading.Thread(target=self._execute_code, args=(kod,), daemon=True)
        self._exec_thread.start()

    def _stop_exec(self):
        if self._exec_running():
            self._exec_thread = None
            self._dodaj_output("■ Przerwano\n", "out_err")

    def _execute_code(self, kod):
        old_out, old_in = sys.stdout, sys.stdin
        buf = io.StringIO()
        err_buf = io.StringIO()
        try:
            sys.stdout = buf
            sys.stdin = io.StringIO()
            interp = Interpreter()
            interp.uruchom(kod)
        except SyntaxError as e:
            err_buf.write(f"Składnia: {e}\n")
        except Exception as e:
            err_buf.write(f"Błąd: {e}\n")
        finally:
            sys.stdout = old_out
            sys.stdin = old_in

        out = buf.getvalue()
        err = err_buf.getvalue()

        self.root.after(0, self._show_result, out, err)

    def _show_result(self, out, err):
        if out:
            self._switch_out_tab("OUTPUT")
            self._dodaj_output(out, "out_std")
        if err:
            self._switch_out_tab("BŁĘDY")
            self._dodaj_output(err, "out_err")
        if out and not err:
            self._dodaj_output("═══════════════════════════════════\n", "out_ok")
            self._dodaj_output("  ✓ Zakończono pomyślnie\n", "out_ok")
            self._dodaj_output("═══════════════════════════════════\n", "out_ok")

    # ── REPL ──

    def _uruchom_repl(self):
        self._switch_out_tab("REPL")
        self._dodaj_output("╔══════════════════════════════════╗\n", "out_info")
        self._dodaj_output("║  VEXLang REPL — wpisz 'exit'    ║\n", "out_info")
        self._dodaj_output("╚══════════════════════════════════╝\n", "out_info")

        self._repl_interp = Interpreter()
        self._repl_input_mode = True
        self._repl_callback = None
        threading.Thread(target=self._repl_loop, daemon=True).start()

    def _repl_loop(self):
        while True:
            inp = self._repl_get_input(">>> ")
            if inp is None: break
            if inp.strip().lower() == "exit":
                self._dodaj_output("Bye!\n", "out_info")
                break
            try:
                self._repl_interp.uruchom(inp)
            except Exception as e:
                err = f"Błąd: {e}\n"
                self.root.after(0, self._dodaj_output, err, "out_err")

    def _repl_get_input(self, prompt):
        import threading as _t
        result = []
        ev = _t.Event()
        self.root.after(0, self._show_repl_input, prompt, result, ev)
        ev.wait()
        return result[0] if result else None

    def _show_repl_input(self, prompt, result, ev):
        # małe okno inputu
        dlg = Toplevel(self.root)
        dlg.title("VEXLang Input")
        dlg.geometry("360x120")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()

        f = Frame(dlg, bg=BG, padx=16, pady=12)
        f.pack(fill=BOTH, expand=True)
        Label(f, text=prompt, bg=BG, fg=TEXT, font=_font(12)).pack(anchor="w")
        ent = Entry(f, bg=BG2, fg=TEXT, font=_font(12), insertbackground=PINK,
                    border=0, relief=FLAT, highlightbackground=BORDER,
                    highlightcolor=PINK, highlightthickness=1)
        ent.pack(fill=X, pady=8)
        ent.focus()

        def ok():
            result.append(ent.get())
            ev.set()
            dlg.destroy()

        ent.bind("<Return>", lambda e: ok())
        Button(f, text="OK", bg=PINK, fg=BG, font=_font(10, True),
               border=0, padx=20, pady=4, command=ok, cursor="hand2").pack()

    def _switch_out_tab(self, name):
        for n, d in self._out_tabs.items():
            d["label"].config(fg=PINK if n == name else TEXT_DIM)
            d["frame"].config(bg=BG2 if n == name else BG2)
        self._active_out_tab = name

    def _dodaj_output(self, tekst, tag="out_std"):
        self._output.config(state=NORMAL)
        self._output.insert(END, tekst, tag)
        self._output.see(END)
        self._output.config(state=DISABLED)

    def _czysc_output(self):
        self._output.config(state=NORMAL)
        self._output.delete("1.0", END)
        self._output.config(state=DISABLED)

    # ══════════════════════════════════
    #  AUTO-UPDATE
    # ══════════════════════════════════

    def _sprawdz_aktualizacje(self):
        self._update_lbl.config(text="")
        threading.Thread(target=self._check_update_thread, daemon=True).start()

    def _check_update_thread(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = Request(url, headers={"User-Agent": "VEXLang", "Accept": "application/json"})
            resp = urlopen(req, timeout=8)
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            cur = VERSION.lstrip("v")
            if self._cmp_ver(tag, cur) > 0:
                self.root.after(0, self._show_update, tag, data.get("body", ""))
        except: pass

    def _cmp_ver(self, a, b):
        pa = [int(x) for x in a.split(".")]
        pb = [int(x) for x in b.split(".")]
        for i in range(max(len(pa), len(pb))):
            va = pa[i] if i < len(pa) else 0
            vb = pb[i] if i < len(pb) else 0
            if va != vb: return va - vb
        return 0

    def _show_update(self, tag, body):
        self._update_lbl.config(text=f"⬇ v{tag}!")
        if messagebox.askyesno("Aktualizacja", f"Dostępna: v{tag}\n\n{body}\n\nPobrać?"):
            self._download_update(tag)

    def _download_update(self, tag):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/v{tag}"
            req = Request(url, headers={"User-Agent": "VEXLang"})
            resp = urlopen(req, timeout=8)
            data = json.loads(resp.read().decode())
            zip_url = None
            for a in data.get("assets", []):
                if a["name"].endswith(".zip"):
                    zip_url = a["browser_download_url"]
                    break
            if not zip_url:
                zip_url = data.get("zipball_url")
            if not zip_url:
                raise Exception("Brak URL")
            req2 = Request(zip_url, headers={"User-Agent": "VEXLang"})
            resp2 = urlopen(req2, timeout=30)
            data_zip = resp2.read()
            base = os.path.dirname(os.path.abspath(__file__))
            with zipfile.ZipFile(io.BytesIO(data_zip)) as z:
                names = z.namelist()
                roots = set()
                for n in names:
                    parts = n.split("/")
                    if len(parts) > 1 and parts[0]: roots.add(parts[0])
                skip_root = len(roots) == 1
                for name in names:
                    if skip_root:
                        parts = name.split("/")
                        if len(parts) > 1: parts = parts[1:]
                        else: continue
                    else:
                        parts = name.split("/")
                    target = os.path.join(base, *parts)
                    if name.endswith("/"):
                        os.makedirs(target, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with open(target, "wb") as f:
                            f.write(z.read(name))
            messagebox.showinfo("OK", f"Zaktualizowano do v{tag}. Uruchom ponownie.")
            self._update_lbl.config(text="")
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się: {e}")

    # ══════════════════════════════════
    #  CZĄSTECZKI TŁA
    # ══════════════════════════════════

    def _animuj_czastki(self):
        self._particles = []
        for _ in range(30):
            self._particles.append({
                "x": _random.random() * 1100,
                "y": _random.random() * 720,
                "vx": (_random.random() - 0.5) * 0.3,
                "vy": (_random.random() - 0.5) * 0.3,
                "r": _random.randint(1, 3),
                "color": _random.choice([PINK, GREEN, BLUE, PURPLE]),
            })
        self._draw_particles()

    def _draw_particles(self):
        self._particle_canvas.delete("part")
        w = self._particle_canvas.winfo_width() or 1100
        h = self._particle_canvas.winfo_height() or 720
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < 0: p["x"] = w
            if p["x"] > w: p["x"] = 0
            if p["y"] < 0: p["y"] = h
            if p["y"] > h: p["y"] = 0
            self._particle_canvas.create_oval(
                p["x"] - p["r"], p["y"] - p["r"],
                p["x"] + p["r"], p["y"] + p["r"],
                fill=p["color"], outline="", tags="part", stipple="gray25")
        self.root.after(50, self._draw_particles)

    # ══════════════════════════════════
    #  START
    # ══════════════════════════════════

    def start(self):
        self._highlight()
        self.root.mainloop()


# ── HELPERS ──

def _find_strings(line):
    result = []
    i = 0
    while i < len(line):
        if line[i] == '"':
            start = i; i += 1
            while i < len(line) and line[i] != '"':
                i += 1
            result.append((start, i + 1 if i < len(line) else len(line)))
            i += 1
        else:
            i += 1
    return result


def _tokenize_line(line):
    result = []
    i = 0
    while i < len(line):
        if line[i].isalpha() or line[i] == "_":
            start = i
            while i < len(line) and (line[i].isalnum() or line[i] in "_ąćęłńóśźż"):
                i += 1
            result.append((line[start:i], start, i))
        elif line[i].isdigit():
            start = i
            while i < len(line) and (line[i].isdigit() or line[i] == "."):
                i += 1
            result.append((line[start:i], start, i))
        else:
            i += 1
    return result


def _is_number(s):
    try:
        float(s); return True
    except: return False


if __name__ == "__main__":
    VEXLangEditor().start()
