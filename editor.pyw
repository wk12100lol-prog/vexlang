#!/usr/bin/env python3
# VEXLang Editor Pro

import sys, os, io, json, threading, zipfile, re, time, random, subprocess
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.font import Font
from urllib.request import urlopen, Request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vexlang import Lexer, Parser, Interpreter, SLOWA_KLUCZOWE

VERSION = "1.1.1"
GITHUB_REPO = "wk12100lol-prog/vexlang"

try:
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

BG = "#0a0c14"; BG2 = "#0f1220"; BG3 = "#151830"
CARD = "#141726"; CARD2 = "#1a1d35"
TEXT = "#c8ccd4"; TEXT_DIM = "#6a6f85"
PINK = "#ff6b9d"; GREEN = "#00ffa3"; ORANGE = "#ffa640"
BLUE = "#40bfff"; PURPLE = "#a855f7"; RED = "#ef4444"
BORDER = "#1e2240"

FONT_NAME = "JetBrains Mono"
FN = lambda s=13, b=False: Font(family=FONT_NAME, size=s, weight="bold" if b else "normal")


def btn(parent, text, cmd, bg=PINK, w=None):
    b = Button(parent, text=text, bg=bg, fg=BG, font=FN(10, True),
               border=0, padx=14, pady=4, cursor="hand2", command=cmd)
    if w: b.config(width=w)
    for ev, cb in [("<Enter>", lambda e, b=b, bg=bg: b.config(bg=TEXT)),
                   ("<Leave>", lambda e, b=b, bg=bg: b.config(bg=bg))]:
        b.bind(ev, cb)
    return b


class VEXLangEditor:
    def __init__(self):
        self.root = Tk()
        self.root.title("VEXLang Editor")
        self.root.geometry("1100x720")
        self.root.configure(bg=BG)
        self.root.minsize(800, 500)

        self._filepath = None
        self._modified = False
        self._exec_thread = None
        self._find_results = []
        self._find_idx = -1

        self._build_ui()
        self._bind()
        self._highlight_timer = None
        self._highlight()

        self.root.after(2000, self._check_update)

    # ── UI ──

    def _build_ui(self):
        # header
        hdr = Frame(self.root, bg=BG, height=44)
        hdr.pack(fill=X)
        Label(hdr, text="VEXLang", bg=BG, fg=PINK, font=FN(16, True)).pack(side=LEFT, padx=16)

        tb = Frame(hdr, bg=BG); tb.pack(side=LEFT, padx=8)
        for t, c, cmd in [("▶", PINK, self._run), ("■", RED, self._stop), ("💻", GREEN, self._repl),
                          ("🔍", BLUE, self._toggle_find), ("💾", ORANGE, self._save)]:
            btn(tb, t, cmd, c, w=3).pack(side=LEFT, padx=1)

        self._upd_lbl = Label(hdr, text="", bg=BG, fg=TEXT_DIM, font=FN(9))
        self._upd_lbl.pack(side=RIGHT, padx=12)

        Frame(self.root, height=1, bg=BORDER).pack(fill=X)

        # find bar
        self._find_fr = Frame(self.root, bg=BG, height=0)
        fi = Frame(self._find_fr, bg=CARD, padx=8, pady=4)
        fi.pack(fill=X, padx=8, pady=2)
        Label(fi, text="🔍", bg=CARD, fg=TEXT_DIM, font=FN(12)).pack(side=LEFT)
        self._find_en = Entry(fi, bg=BG2, fg=TEXT, font=FN(11), insertbackground=PINK,
                              border=0, relief=FLAT, width=30)
        self._find_en.pack(side=LEFT, padx=4, fill=X, expand=True)
        self._find_en.bind("<Return>", lambda e: self._find())
        self._find_en.bind("<KeyRelease>", lambda e: self._find())
        btn(fi, "▲", lambda: self._find(False), BG3).pack(side=LEFT, padx=1)
        btn(fi, "▼", lambda: self._find(True), BG3).pack(side=LEFT, padx=1)
        self._find_cnt = Label(fi, text="", bg=CARD, fg=TEXT_DIM, font=FN(9))
        self._find_cnt.pack(side=LEFT, padx=6)
        btn(fi, "✕", self._toggle_find, RED).pack(side=LEFT, padx=4)

        # editor
        ef = Frame(self.root, bg=BG); ef.pack(fill=BOTH, expand=True)

        self._line_canvas = Canvas(ef, width=48, bg=BG2, highlightthickness=0)
        self._line_canvas.pack(side=LEFT, fill=Y)

        self._txt = Text(ef, bg=BG, fg=TEXT, font=FN(13), insertbackground=PINK,
                         selectbackground="#3a1a40", selectforeground=TEXT,
                         wrap=NONE, border=0, padx=12, pady=8, undo=True)
        self._txt.pack(side=LEFT, fill=BOTH, expand=True)

        sc = Scrollbar(ef, command=self._txt.yview, bg=BG2, troughcolor=BG,
                       activebackground=PINK, border=0, width=10)
        sc.pack(side=RIGHT, fill=Y)
        self._txt.config(yscrollcommand=sc.set)

        # tags
        self._txt.tag_config("kw", foreground=PINK, font=FN(13, True))
        self._txt.tag_config("str", foreground=GREEN)
        self._txt.tag_config("cm", foreground="#4a4d5e")
        self._txt.tag_config("num", foreground=ORANGE)
        self._txt.tag_config("blt", foreground=BLUE)
        self._txt.tag_config("sel", foreground=BG, background=PINK)

        Frame(self.root, height=1, bg=BORDER).pack(fill=X)

        # output
        of = Frame(self.root, bg=BG, height=180); of.pack(fill=X)

        oh = Frame(of, bg=BG2, height=26); oh.pack(fill=X)
        self._out_lbls = {}
        for i, (name, clr) in enumerate([("OUTPUT", GREEN), ("BŁĘDY", RED), ("REPL", BLUE)]):
            lbl = Label(oh, text=name, bg=BG2, fg=PINK if i == 0 else TEXT_DIM,
                        font=FN(9, True), padx=12, cursor="hand2")
            lbl.pack(side=LEFT, padx=1, pady=2)
            lbl.bind("<Button-1>", lambda e, n=name: self._switch_out(n))
            self._out_lbls[name] = lbl

        Label(oh, text="✕", bg=BG2, fg=TEXT_DIM, font=FN(9), cursor="hand2",
              padx=8).pack(side=RIGHT)
        self._out = Text(of, bg=BG, fg=TEXT, font=FN(11), wrap=WORD,
                         border=0, padx=8, pady=4, state=DISABLED)
        self._out.pack(fill=BOTH, expand=True)
        self._out.tag_config("ok", foreground=GREEN)
        self._out.tag_config("err", foreground=RED)
        self._out.tag_config("info", foreground=BLUE)

        # status
        st = Frame(self.root, bg=BG2, height=22); st.pack(fill=X)
        self._st_line = Label(st, text="Ln 1, Col 1", bg=BG2, fg=TEXT_DIM, font=FN(9))
        self._st_line.pack(side=LEFT, padx=10)
        self._st_file = Label(st, text="", bg=BG2, fg=TEXT_DIM, font=FN(9))
        self._st_file.pack(side=RIGHT, padx=10)

        self._active_out = "OUTPUT"

    # ── EVENTS ──

    def _bind(self):
        self._txt.bind("<KeyRelease>", self._on_change)
        self._txt.bind("<ButtonRelease-1>", lambda e: self._update_status())
        self._txt.bind("<KeyPress>", lambda e: self.root.after(5, self._update_status))
        self._txt.bind("<Tab>", lambda e: self._tab(e))
        self._txt.bind("<Control-n>", lambda e: self._new())
        self._txt.bind("<Control-o>", lambda e: self._open())
        self._txt.bind("<Control-s>", lambda e: self._save())
        self._txt.bind("<Control-f>", lambda e: self._toggle_find())
        self._txt.bind("<F5>", lambda e: self._run())
        self._txt.bind("<F6>", lambda e: self._repl())
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.bind("<Control-q>", lambda e: self._quit())

    def _on_change(self, e=None):
        self._modified = True
        self._update_title()
        if self._highlight_timer: self.root.after_cancel(self._highlight_timer)
        self._highlight_timer = self.root.after(200, self._highlight)
        self._draw_lines()

    def _tab(self, e):
        self._txt.insert(INSERT, "    "); return "break"

    # ── STATUS ──

    def _update_status(self):
        try:
            ln, col = self._txt.index(INSERT).split(".")
            self._st_line.config(text=f"Ln {ln}, Col {int(col)+1}")
            n = os.path.basename(self._filepath) if self._filepath else ""
            self._st_file.config(text=n)
        except: pass

    def _update_title(self):
        n = os.path.basename(self._filepath) if self._filepath else "bez nazwy.vex"
        self.root.title(f"VEXLang Editor — {n}{' ●' if self._modified else ''}")

    # ── HIGHLIGHT ──

    def _highlight(self):
        self._txt.mark_set("range_start", "1.0")
        for t in ("kw", "str", "cm", "num", "blt", "sel"): self._txt.tag_remove(t, "1.0", END)
        data = self._txt.get("1.0", END)
        for i, line in enumerate(data.split("\n"), 1):
            if "#" in line:
                pos = line.index("#")
                self._txt.tag_add("cm", f"{i}.{pos}", f"{i}.end")
                line = line[:pos]
            for s, e in _find_strings(line):
                self._txt.tag_add("str", f"{i}.{s}", f"{i}.{e}")
            for tok, s, e in _tokenize(line):
                if tok in SLOWA_KLUCZOWE: self._txt.tag_add("kw", f"{i}.{s}", f"{i}.{e}")
                elif tok in ("dlugosc","konwert","losuj","zaokraglij"): self._txt.tag_add("blt", f"{i}.{s}", f"{i}.{e}")
                elif _is_num(tok): self._txt.tag_add("num", f"{i}.{s}", f"{i}.{e}")
        self._draw_lines()

    def _draw_lines(self):
        self._line_canvas.delete("all")
        try: cnt = int(self._txt.index("end-1c").split(".")[0])
        except: cnt = 1
        try: cur = int(self._txt.index(INSERT).split(".")[0])
        except: cur = 1
        h = self._txt.winfo_height()
        self._line_canvas.config(height=max(h, cnt * 22))
        for i in range(1, cnt + 1):
            y = (i - 1) * 22 + 4
            if i == cur:
                self._line_canvas.create_rectangle(0, y - 2, 48, y + 18, fill="#1a1d40", outline="")
            self._line_canvas.create_text(42, y, text=str(i), anchor="e", fill="#3a3d5e", font=FN(10))

    # ── FIND ──

    def _toggle_find(self):
        if self._find_fr.winfo_ismapped():
            self._find_fr.pack_forget(); self._find_fr.config(height=0)
            self._txt.tag_remove("sel", "1.0", END)
        else:
            self._find_fr.pack(fill=X); self._find_fr.config(height=32)
            self._find_en.focus()
            try: self._find_en.delete(0, END); self._find_en.insert(0, self._txt.selection_get())
            except: pass
            self._find()

    def _find(self, forward=True):
        q = self._find_en.get().strip()
        if not q: self._find_cnt.config(text=""); self._txt.tag_remove("sel", "1.0", END); return
        self._txt.tag_remove("sel", "1.0", END)
        self._find_results = []
        start = "1.0"
        while True:
            pos = self._txt.search(q, start, END, nocase=True)
            if not pos: break
            self._find_results.append(pos)
            self._txt.tag_add("sel", pos, f"{pos}+{len(q)}c")
            start = f"{pos}+{len(q)}c"
        self._find_cnt.config(text=f"{len(self._find_results)}")
        if self._find_results:
            self._find_idx = (self._find_idx + 1) % len(self._find_results) if forward else (
                (self._find_idx - 1) % len(self._find_results))
            pos = self._find_results[self._find_idx]
            self._txt.mark_set(INSERT, pos); self._txt.see(pos); self._txt.focus()

    def _find_prev(self):
        self._find(False)

    # ── FILE ──

    def _new(self):
        if self._modified and not messagebox.askokcancel("Nowy", "Odrzucić zmiany?"): return
        self._txt.delete("1.0", END); self._filepath = None; self._modified = False
        self._update_title(); self._out_clear(); self._highlight()

    def _open(self):
        fp = filedialog.askopenfilename(filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")])
        if not fp: return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                self._txt.delete("1.0", END); self._txt.insert("1.0", f.read())
            self._filepath = fp; self._modified = False; self._update_title(); self._highlight()
        except Exception as e: messagebox.showerror("Błąd", str(e))

    def _save(self):
        if self._filepath: self._save_to(self._filepath)
        else: self._save_as()

    def _save_as(self):
        fp = filedialog.asksaveasfilename(defaultextension=".vex", filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")])
        if fp: self._filepath = fp; self._save_to(fp)

    def _save_to(self, fp):
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self._txt.get("1.0", "end-1c"))
            self._modified = False; self._update_title()
            self._out_write(f"✓ Zapisano\n", "ok")
        except Exception as e: messagebox.showerror("Błąd", str(e))

    def _quit(self):
        if self._modified and not messagebox.askokcancel("Wyjście", "Odrzucić zmiany?"): return
        self.root.destroy()

    # ── RUN ──

    def _run(self):
        if self._exec_thread and self._exec_thread.is_alive(): return
        code = self._txt.get("1.0", "end-1c")
        if not code.strip(): return
        self._switch_out("OUTPUT"); self._out_clear()
        self._out_write("═══════════════════════\n", "info")
        self._out_write("  ▶ Uruchamianie...\n", "info")
        self._out_write("═══════════════════════\n", "info")
        self._exec_thread = threading.Thread(target=self._exec, args=(code,), daemon=True)
        self._exec_thread.start()

    def _stop(self):
        if self._exec_thread and self._exec_thread.is_alive():
            self._exec_thread = None; self._out_write("■ Przerwano\n", "err")

    def _exec(self, code):
        old_out, old_in = sys.stdout, sys.stdin
        buf = io.StringIO(); err = io.StringIO()
        try:
            sys.stdout = buf; sys.stdin = io.StringIO()
            interp = Interpreter()
            interp.uruchom(code)
        except SyntaxError as e: err.write(f"Składnia: {e}\n")
        except Exception as e: err.write(f"Błąd: {e}\n")
        finally: sys.stdout = old_out; sys.stdin = old_in
        out = buf.getvalue(); e = err.getvalue()
        self.root.after(0, lambda: self._show_res(out, e))

    def _show_res(self, out, err):
        if out: self._switch_out("OUTPUT"); self._out_write(out)
        if err: self._switch_out("BŁĘDY"); self._out_write(err, "err")
        if out and not err:
            self._out_write("✔ Zakończono\n", "ok")

    def _repl(self):
        self._switch_out("REPL")
        self._out_write("VEXLang REPL — exit aby wyjść\n\n", "info")
        self._repl_interp = Interpreter()
        threading.Thread(target=self._repl_loop, daemon=True).start()

    def _repl_loop(self):
        while True:
            inp = self._repl_input(">>> ")
            if inp is None or inp.strip().lower() == "exit":
                self._out_write("Bye!\n", "info"); break
            try: self._repl_interp.uruchom(inp)
            except Exception as e: self.root.after(0, self._out_write, f"Błąd: {e}\n", "err")

    def _repl_input(self, prompt):
        import threading as _t
        res = []; ev = _t.Event()
        self.root.after(0, self._show_repl_inp, prompt, res, ev)
        ev.wait()
        return res[0] if res else None

    def _show_repl_inp(self, prompt, res, ev):
        dlg = Toplevel(self.root)
        dlg.title("VEXLang Input"); dlg.geometry("360x110"); dlg.configure(bg=BG)
        dlg.transient(self.root); dlg.grab_set()
        f = Frame(dlg, bg=BG, padx=16, pady=12); f.pack(fill=BOTH, expand=True)
        Label(f, text=prompt, bg=BG, fg=TEXT, font=FN(12)).pack(anchor="w")
        ent = Entry(f, bg=BG2, fg=TEXT, font=FN(12), insertbackground=PINK, border=0)
        ent.pack(fill=X, pady=8); ent.focus()
        def ok(): res.append(ent.get()); ev.set(); dlg.destroy()
        ent.bind("<Return>", lambda e: ok())
        Button(f, text="OK", bg=PINK, fg=BG, font=FN(10, True), border=0, padx=20, pady=4, command=ok, cursor="hand2").pack()

    def _out_write(self, text, tag=None):
        self._out.config(state=NORMAL)
        self._out.insert(END, text, tag) if tag else self._out.insert(END, text)
        self._out.see(END); self._out.config(state=DISABLED)

    def _out_clear(self):
        self._out.config(state=NORMAL); self._out.delete("1.0", END); self._out.config(state=DISABLED)

    def _switch_out(self, name):
        for n, lbl in self._out_lbls.items():
            lbl.config(fg=PINK if n == name else TEXT_DIM)
        self._active_out = name

    # ── UPDATE ──

    def _check_update(self):
        threading.Thread(target=self._update_thread, daemon=True).start()

    def _update_thread(self):
        try:
            req = Request(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                          headers={"User-Agent": "VEXLang"})
            data = json.loads(urlopen(req, timeout=8).read().decode())
            tag = data["tag_name"].lstrip("v")
            cur = VERSION.lstrip("v")
            if self._cmp(tag, cur) > 0:
                self.root.after(0, self._show_upd, tag, data.get("body",""))
        except: pass

    def _cmp(self, a, b):
        pa = [int(x) for x in a.split(".")]; pb = [int(x) for x in b.split(".")]
        for i in range(max(len(pa), len(pb))):
            va = pa[i] if i < len(pa) else 0; vb = pb[i] if i < len(pb) else 0
            if va != vb: return va - vb
        return 0

    def _show_upd(self, tag, body):
        self._upd_lbl.config(text=f"⬇ v{tag}!")
        if messagebox.askyesno("Aktualizacja", f"Dostępna: v{tag}\n\n{body}\n\nPobrać?"):
            threading.Thread(target=self._dl_upd, args=(tag,), daemon=True).start()

    def _dl_upd(self, tag):
        try:
            req = Request(f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/v{tag}",
                          headers={"User-Agent": "VEXLang"})
            data = json.loads(urlopen(req, timeout=8).read().decode())
            zu = None
            for a in data.get("assets", []):
                if a["name"].endswith(".zip"): zu = a["browser_download_url"]; break
            if not zu: zu = data.get("zipball_url")
            if not zu: raise Exception("Brak URL")
            resp = urlopen(Request(zu, headers={"User-Agent":"VEXLang"}), timeout=30)
            d = resp.read()
            base = os.path.dirname(os.path.abspath(__file__))
            with zipfile.ZipFile(io.BytesIO(d)) as z:
                names = z.namelist()
                roots = set()
                for n in names:
                    p = n.split("/")
                    if len(p) > 1 and p[0]: roots.add(p[0])
                skip = len(roots) == 1
                for name in names:
                    parts = name.split("/")[1:] if skip else name.split("/")
                    if not parts: continue
                    target = os.path.join(base, *parts)
                    if name.endswith("/"): os.makedirs(target, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with open(target, "wb") as f: f.write(z.read(name))
            messagebox.showinfo("OK", f"Zaktualizowano do v{tag}. Uruchom ponownie.")
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się: {e}")

    def start(self):
        self._highlight(); self.root.mainloop()


# ── UTILS ──

def _find_strings(line):
    res = []; i = 0
    while i < len(line):
        if line[i] == '"':
            s = i; i += 1
            while i < len(line) and line[i] != '"': i += 1
            res.append((s, i+1 if i < len(line) else len(line)))
        i += 1
    return res

def _tokenize(line):
    res = []; i = 0
    while i < len(line):
        if line[i].isalpha() or line[i] == "_":
            s = i
            while i < len(line) and (line[i].isalnum() or line[i] in "_ąćęłńóśźż"): i += 1
            res.append((line[s:i], s, i))
        elif line[i].isdigit():
            s = i
            while i < len(line) and (line[i].isdigit() or line[i] == "."): i += 1
            res.append((line[s:i], s, i))
        else: i += 1
    return res

def _is_num(s):
    try: float(s); return True
    except: return False


if __name__ == "__main__":
    VEXLangEditor().start()
