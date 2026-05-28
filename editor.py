#!/usr/bin/env python3
# VEXLang Editor – edytor kodu z syntax highlighting i uruchamianiem

import sys, os, io, json, threading, zipfile, subprocess, tempfile, shutil
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext
from tkinter.font import Font

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vexlang import Lexer, Parser, Interpreter, SLOWA_KLUCZOWE

VERSION = "1.0.0"
GITHUB_REPO = "wk12100lol-prog/vexlang"

# ── KOLORY (VEXHACK neon theme) ──
BG = "#0d0f1a"
BG_CARD = "#141726"
TEXT = "#c8ccd4"
PINK = "#ff6b9d"
GREEN = "#00ffa3"
ORANGE = "#ffa640"
BLUE = "#40bfff"
GRAY = "#6a6f85"
COMMENT_COLOR = "#4a4d5e"
STRING_COLOR = "#00ffa3"
KEYWORD_COLOR = "#ff6b9d"
NUMBER_COLOR = "#ffa640"
BUILTIN_COLOR = "#40bfff"

KEYWORD_LIST = sorted(SLOWA_KLUCZOWE)
KEYWORD_SET = SLOWA_KLUCZOWE
BUILTIN_SET = {"dlugosc", "konwert", "losuj", "zaokraglij", "pisz"}

THEME_CS = f"background: {BG}; color: {TEXT};"


class VEXLangEditor:
    def __init__(self):
        self.root = Tk()
        self.root.title(f"VEXLang Editor v{VERSION}")
        self.root.geometry("900x650")
        self.root.configure(bg=BG)
        self._ustaw_ikone()

        self._plik = None
        self._zmieniony = False

        # czcionka
        self._font = Font(family="Consolas", size=12)
        self._font_bold = Font(family="Consolas", size=12, weight="bold")

        self._build_menu()
        self._build_ui()
        self._bind_events()
        self._highlight_timer = None

        # ── auto-update ──
        self._update_sterowanie()
        self.root.after(2000, self._sprawdz_aktualizacje)

    def _ustaw_ikone(self):
        try:
            self.root.iconbitmap(default="")
        except:
            pass

    # ── MENU ──

    def _build_menu(self):
        mb = Menu(self.root, bg=BG_CARD, fg=TEXT, activebackground=PINK, activeforeground=BG)
        self.root.config(menu=mb)

        fm = Menu(mb, tearoff=0, bg=BG_CARD, fg=TEXT, activebackground=PINK, activeforeground=BG)
        fm.add_command(label="Nowy", command=self._nowy, accelerator="Ctrl+N")
        fm.add_command(label="Otwórz", command=self._otworz, accelerator="Ctrl+O")
        fm.add_command(label="Zapisz", command=self._zapisz, accelerator="Ctrl+S")
        fm.add_command(label="Zapisz jako", command=self._zapisz_jako)
        fm.add_separator()
        fm.add_command(label="Wyjście", command=self.root.quit)
        mb.add_cascade(label="Plik", menu=fm)

        rm = Menu(mb, tearoff=0, bg=BG_CARD, fg=TEXT, activebackground=PINK, activeforeground=BG)
        rm.add_command(label="Uruchom", command=self._uruchom, accelerator="F5")
        rm.add_command(label="REPL", command=self._uruchom_repl, accelerator="F6")
        mb.add_cascade(label="Uruchom", menu=rm)

        # aktualizacje w menu Pomoc
        hm = Menu(mb, tearoff=0, bg=BG_CARD, fg=TEXT, activebackground=PINK, activeforeground=BG)
        hm.add_command(label="Sprawdź aktualizacje", command=self._reczna_aktualizacja)
        hm.add_command(label="O programie", command=self._o_programie)
        mb.add_cascade(label="Pomoc", menu=hm)

    # ── UI ──

    def _build_ui(self):
        # główny frame
        main = Frame(self.root, bg=BG)
        main.pack(fill=BOTH, expand=True)

        # pasek narzędzi
        toolbar = Frame(main, bg=BG_CARD, height=36)
        toolbar.pack(fill=X)
        toolbar.pack_propagate(False)

        self._run_btn = self._btn(toolbar, "▶ Uruchom", self._uruchom, PINK)
        self._run_btn.pack(side=LEFT, padx=4, pady=4)

        self._repl_btn = self._btn(toolbar, "💻 REPL", self._uruchom_repl, GREEN)
        self._repl_btn.pack(side=LEFT, padx=4, pady=4)

        self._update_lbl = Label(toolbar, text="", bg=BG_CARD, fg=GRAY, font=("Segoe UI", 9))
        self._update_lbl.pack(side=RIGHT, padx=8)

        # obszar edytora + numery linii
        editor_frame = Frame(main, bg=BG)
        editor_frame.pack(fill=BOTH, expand=True)

        # numery linii
        self._linie = Text(editor_frame, width=4, padx=6, pady=6,
                           bg=BG_CARD, fg=GRAY, font=self._font,
                           state=DISABLED, wrap=NONE, border=0)
        self._linie.pack(side=LEFT, fill=Y)

        # edytor
        self._text = Text(editor_frame, bg=BG, fg=TEXT, font=self._font,
                         insertbackground=PINK, wrap=NONE, border=0,
                         padx=8, pady=6, undo=True)
        self._text.pack(side=LEFT, fill=BOTH, expand=True)

        # scrollbar
        sc = Scrollbar(editor_frame, command=self._text.yview, bg=BG_CARD)
        sc.pack(side=RIGHT, fill=Y)
        self._text.config(yscrollcommand=sc.set)

        # output
        out_frame = Frame(main, bg=BG_CARD, height=160)
        out_frame.pack(fill=X)
        out_frame.pack_propagate(False)

        out_header = Frame(out_frame, bg=BG_CARD)
        out_header.pack(fill=X)
        Label(out_header, text="OUTPUT", bg=BG_CARD, fg=GRAY,
              font=("Segoe UI", 8, "bold")).pack(side=LEFT, padx=8)
        self._clear_out_btn = Button(out_header, text="✕", bg=BG_CARD, fg=GRAY,
                                     font=("Segoe UI", 8), border=0, cursor="hand2",
                                     command=self._czysc_output)
        self._clear_out_btn.pack(side=RIGHT, padx=4)
        self._clear_out_btn.bind("<Enter>", lambda e: self._clear_out_btn.config(fg=TEXT))
        self._clear_out_btn.bind("<Leave>", lambda e: self._clear_out_btn.config(fg=GRAY))

        self._output = Text(out_frame, bg=BG, fg=TEXT, font=self._font,
                           wrap=WORD, border=0, padx=8, pady=4,
                           state=DISABLED, height=6)
        self._output.pack(fill=BOTH, expand=True)

    def _btn(self, parent, text, cmd, color=PINK):
        b = Button(parent, text=text, bg=color, fg=BG, font=("Segoe UI", 9, "bold"),
                   border=0, padx=10, pady=2, cursor="hand2", command=cmd)
        b.bind("<Enter>", lambda e: b.config(bg=TEXT))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    # ── ZDARZENIA ──

    def _bind_events(self):
        self._text.bind("<KeyRelease>", self._on_zmiana)
        self._text.bind("<<Modified>>", self._on_modified)
        self._text.bind("<Control-n>", lambda e: self._nowy())
        self._text.bind("<Control-N>", lambda e: self._nowy())
        self._text.bind("<Control-o>", lambda e: self._otworz())
        self._text.bind("<Control-O>", lambda e: self._otworz())
        self._text.bind("<Control-s>", lambda e: self._zapisz())
        self._text.bind("<Control-S>", lambda e: self._zapisz())
        self._text.bind("<F5>", lambda e: self._uruchom())
        self._text.bind("<F6>", lambda e: self._uruchom_repl())
        self._text.bind("<Tab>", self._wciecie)
        self._text.bind("<MouseWheel>", self._scroll)
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.protocol("WM_DELETE_WINDOW", self._zamknij)

    def _on_zmiana(self, e=None):
        self._zmieniony = True
        self._aktualizuj_tytul()
        if self._highlight_timer:
            self.root.after_cancel(self._highlight_timer)
        self._highlight_timer = self.root.after(300, self._highlight)

    def _on_modified(self, e=None):
        self._text.edit_modified(False)

    def _wciecie(self, e):
        self._text.insert(INSERT, "    ")
        return "break"

    def _scroll(self, e):
        self._text.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self._linie.yview_moveto(self._text.yview()[0])

    def _aktualizuj_tytul(self):
        nazwa = os.path.basename(self._plik) if self._plik else "bez nazwy"
        znak = " *" if self._zmieniony else ""
        self.root.title(f"VEXLang Editor v{VERSION} — {nazwa}{znak}")

    # ── SYNTAX HIGHLIGHTING ──

    def _highlight(self):
        self._text.mark_set("range_start", "1.0")
        data = self._text.get("1.0", END)
        # wyczyść tagi
        for t in ("keyword", "string", "comment", "number", "builtin"):
            self._text.tag_remove(t, "1.0", END)

        # ustaw tagi
        self._text.tag_config("keyword", foreground=KEYWORD_COLOR, font=self._font_bold)
        self._text.tag_config("string", foreground=STRING_COLOR)
        self._text.tag_config("comment", foreground=COMMENT_COLOR)
        self._text.tag_config("number", foreground=NUMBER_COLOR)
        self._text.tag_config("builtin", foreground=BUILTIN_COLOR)

        # proste podświetlanie linia po linii
        for i, linia in enumerate(data.split("\n"), 1):
            idx = f"{i}.0"
            # komentarz
            if "#" in linia:
                pos = linia.index("#")
                self._text.tag_add("comment", f"{i}.{pos}", f"{i}.end")
                linia = linia[:pos]
            # stringi (uproszczone)
            for m in _znajdz_stringi(linia):
                self._text.tag_add("string", f"{i}.{m[0]}", f"{i}.{m[1]}")
            # tokeny
            for tok, start, end in _tokenizuj_linie(linia):
                if tok in KEYWORD_SET:
                    self._text.tag_add("keyword", f"{i}.{start}", f"{i}.{end}")
                elif tok in BUILTIN_SET:
                    self._text.tag_add("builtin", f"{i}.{start}", f"{i}.{end}")
                elif _czy_liczba(tok):
                    self._text.tag_add("number", f"{i}.{start}", f"{i}.{end}")

        self._aktualizuj_linie()

    def _aktualizuj_linie(self):
        self._linie.config(state=NORMAL)
        self._linie.delete("1.0", END)
        ilosc = int(self._text.index("end-1c").split(".")[0])
        numery = "\n".join(str(i) for i in range(1, ilosc + 1))
        self._linie.insert("1.0", numery)
        self._linie.config(state=DISABLED)

    # ── OPERACJE NA PLIKACH ──

    def _nowy(self):
        if self._zmieniony:
            if not messagebox.askokcancel("Nowy", "Odrzucić zmiany?"):
                return
        self._text.delete("1.0", END)
        self._plik = None
        self._zmieniony = False
        self._aktualizuj_tytul()
        self._czysc_output()
        self._highlight()

    def _otworz(self):
        fp = filedialog.askopenfilename(filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")])
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                kod = f.read()
            self._text.delete("1.0", END)
            self._text.insert("1.0", kod)
            self._plik = fp
            self._zmieniony = False
            self._aktualizuj_tytul()
            self._highlight()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można otworzyć:\n{e}")

    def _zapisz(self, e=None):
        if self._plik:
            self._zapisz_do(self._plik)
        else:
            self._zapisz_jako()

    def _zapisz_jako(self):
        fp = filedialog.asksaveasfilename(defaultextension=".vex",
                                           filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")])
        if not fp:
            return
        self._plik = fp
        self._zapisz_do(fp)

    def _zapisz_do(self, fp):
        try:
            kod = self._text.get("1.0", "end-1c")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(kod)
            self._zmieniony = False
            self._aktualizuj_tytul()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać:\n{e}")

    def _zamknij(self):
        if self._zmieniony:
            if not messagebox.askokcancel("Wyjście", "Odrzucić zmiany?"):
                return
        self.root.destroy()

    # ── URUCHAMIANIE ──

    def _uruchom(self, e=None):
        kod = self._text.get("1.0", "end-1c")
        if not kod.strip():
            return
        self._czysc_output()
        self._dodaj_output("→ Uruchamianie...\n", GRAY)
        threading.Thread(target=self._wykonaj_kod, args=(kod,), daemon=True).start()

    def _wykonaj_kod(self, kod):
        try:
            # przechwyć stdout
            old_stdout = sys.stdout
            old_stdin = sys.stdin
            sys.stdout = buf = io.StringIO()
            sys.stdin = io.StringIO()  # puste stdin

            interp = Interpreter()
            try:
                interp.uruchom(kod)
            except (SyntaxError, Exception) as e:
                print(f"Błąd: {e}")

            sys.stdout = old_stdout
            sys.stdin = old_stdin
            wynik = buf.getvalue()
            self.root.after(0, self._wyswietl_wynik, wynik)
        except Exception as e:
            sys.stdout = old_stdout
            sys.stdin = old_stdin
            self.root.after(0, self._wyswietl_wynik, f"Błąd wykonania: {e}")

    def _wyswietl_wynik(self, tekst):
        if tekst:
            self._dodaj_output(tekst, TEXT)
        else:
            self._dodaj_output("(brak outputu)\n", GRAY)
        self._dodaj_output("✓ Gotowe\n", GREEN)

    def _uruchom_repl(self):
        self._czysc_output()
        self._dodaj_output("VEXLang REPL — wpisz 'exit' aby wyjść\n", GREEN)
        threading.Thread(target=self._petla_repl, daemon=True).start()

    def _petla_repl(self):
        interp = Interpreter()
        while True:
            def wejscie():
                return self._czekaj_input(">>> ")
            sys.stdin = _StdinReader(wejscie)
            sys.stdout = buf = _StdoutRedirect(self._repl_dodaj)

            try:
                kod = input()
                if kod.strip().lower() == "exit":
                    self._repl_dodaj("Bye!\n")
                    break
                interp.uruchom(kod)
            except EOFError:
                break
            except Exception as e:
                self._repl_dodaj(f"Błąd: {e}\n")

    def _czekaj_input(self, prompt):
        import threading as _t
        wynik = []
        ev = _t.Event()

        def get():
            self.root.after(0, self._repl_prompt, prompt, wynik, ev)
        get()
        ev.wait()
        return wynik[0] if wynik else ""

    def _repl_prompt(self, prompt, wynik, ev):
        # input dialog
        dlg = Toplevel(self.root)
        dlg.title("VEXLang Input")
        dlg.geometry("300x100")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        Label(dlg, text=prompt, bg=BG, fg=TEXT, font=self._font).pack(pady=8)
        ent = Entry(dlg, bg=BG_CARD, fg=TEXT, font=self._font, insertbackground=PINK, border=0)
        ent.pack(padx=16, fill=X)
        ent.focus()
        def ok():
            wynik.append(ent.get())
            ev.set()
            dlg.destroy()
        ent.bind("<Return>", lambda e: ok())
        Button(dlg, text="OK", bg=PINK, fg=BG, font=("Segoe UI", 9, "bold"),
               border=0, padx=16, pady=4, command=ok, cursor="hand2").pack(pady=8)

    def _repl_dodaj(self, tekst):
        self.root.after(0, self._dodaj_output, tekst, TEXT)

    def _dodaj_output(self, tekst, kolor=TEXT):
        self._output.config(state=NORMAL)
        self._output.insert(END, tekst)
        self._output.see(END)
        self._output.tag_add("out", "end-2l", "end-1l")
        self._output.tag_config("out", foreground=kolor)
        self._output.config(state=DISABLED)

    def _czysc_output(self):
        self._output.config(state=NORMAL)
        self._output.delete("1.0", END)
        self._output.config(state=DISABLED)

    # ── AUTO-UPDATE ──

    def _update_sterowanie(self):
        self._update_worker = None
        self._update_lbl.config(text="")

    def _sprawdz_aktualizacje(self):
        threading.Thread(target=self._szukaj_aktualizacji, daemon=True).start()

    def _reczna_aktualizacja(self):
        self._update_lbl.config(text="Sprawdzanie...")
        threading.Thread(target=self._szukaj_aktualizacji, daemon=True).start()

    def _szukaj_aktualizacji(self):
        from urllib.request import urlopen, Request
        import json as _json
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = Request(url, headers={"User-Agent": "VEXLang"})
            resp = urlopen(req, timeout=8)
            data = _json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            current = VERSION.lstrip("v")
            body = data.get("body", "")[:200]

            def _cmp(a, b):
                pa = [int(x) for x in a.split(".")]
                pb = [int(x) for x in b.split(".")]
                for i in range(max(len(pa), len(pb))):
                    va = pa[i] if i < len(pa) else 0
                    vb = pb[i] if i < len(pb) else 0
                    if va != vb: return va - vb
                return 0

            if _cmp(tag, current) > 0:
                self.root.after(0, self._pokaz_aktualizacje, tag, data.get("body", ""))
            else:
                self.root.after(0, lambda: self._update_lbl.config(text="✔ Aktualny"))
                self.root.after(5000, lambda: self._update_lbl.config(text=""))
        except Exception as e:
            self.root.after(0, lambda: self._update_lbl.config(text=""))

    def _pokaz_aktualizacje(self, tag, body):
        self._update_lbl.config(text=f"⬇ v{tag}!")
        ok = messagebox.askyesno("Aktualizacja",
            f"Dostępna wersja: v{tag}\n\n{body}\n\nPobrać i zainstalować?")
        if ok:
            self._pobierz_aktualizacje(tag)

    def _pobierz_aktualizacje(self, tag):
        from urllib.request import urlopen, Request
        import json as _json
        self._update_lbl.config(text="Pobieranie...")
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/v{tag}"
            req = Request(url, headers={"User-Agent": "VEXLang"})
            resp = urlopen(req, timeout=8)
            data = _json.loads(resp.read().decode())
            zip_url = None
            for a in data.get("assets", []):
                if a["name"].endswith(".zip"):
                    zip_url = a["browser_download_url"]
                    break
            if not zip_url:
                zip_url = data.get("zipball_url")
            if not zip_url:
                raise Exception("Brak URL do pobrania")

            req2 = Request(zip_url, headers={"User-Agent": "VEXLang"})
            resp2 = urlopen(req2, timeout=30)
            data_zip = resp2.read()

            base = os.path.dirname(os.path.abspath(__file__))
            z = zipfile.ZipFile(io.BytesIO(data_zip))
            names = z.namelist()
            # skip root dir
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
            messagebox.showerror("Błąd", f"Nie udało się zaktualizować:\n{e}")
            self._update_lbl.config(text="")

    # ── O PROGRAMIE ──

    def _o_programie(self):
        text = f"""VEXLang Editor v{VERSION}

Edytor języka VEXLang z polskimi słowami kluczowymi.

• Składnia: jeśli, dopóki, funkcja, pisz, ...
• Wbudowane funkcje: dlugosc(), konwert(), losuj(), zaokraglij()
• Szyfrowanie AES-256 w archiwach VEXARCHIVE

Autor: v0idvex
Licencja: MIT"""
        messagebox.showinfo("O programie", text)

    def start(self):
        self._highlight()
        self.root.mainloop()


# ── POMOCNICZE ──

def _znajdz_stringi(linia):
    """Znajduje pary (start, end) dla stringów w linii"""
    wynik = []
    i = 0
    while i < len(linia):
        if linia[i] == '"':
            start = i
            i += 1
            while i < len(linia) and linia[i] != '"':
                i += 1
            if i < len(linia):
                wynik.append((start, i + 1))
                i += 1
            else:
                wynik.append((start, len(linia)))
        else:
            i += 1
    return wynik


def _tokenizuj_linie(linia):
    """Zwraca listę (token, start, end) dla linii"""
    wynik = []
    i = 0
    while i < len(linia):
        if linia[i].isalpha() or linia[i] == "_":
            start = i
            while i < len(linia) and (linia[i].isalnum() or linia[i] in "_ąćęłńóśźż"):
                i += 1
            wynik.append((linia[start:i], start, i))
        elif linia[i].isdigit():
            start = i
            while i < len(linia) and (linia[i].isdigit() or linia[i] == "."):
                i += 1
            wynik.append((linia[start:i], start, i))
        else:
            i += 1
    return wynik


def _czy_liczba(s):
    try:
        float(s)
        return True
    except:
        return False


class _StdinReader:
    def __init__(self, input_fn):
        self.input_fn = input_fn
    def readline(self):
        return self.input_fn() + "\n"


class _StdoutRedirect:
    def __init__(self, write_fn):
        self.write_fn = write_fn
    def write(self, s):
        self.write_fn(s)
    def flush(self):
        pass


if __name__ == "__main__":
    VEXLangEditor().start()
