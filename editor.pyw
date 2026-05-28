#!/usr/bin/env python3
import sys, os, io, json, threading, zipfile, re, time, subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from urllib.request import urlopen, Request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vexlang import Lexer, Parser, Interpreter, SLOWA_KLUCZOWE, KOLORY_ANSI, KOLORY_HEX

VERSION = "2.2.0"
GITHUB_REPO = "wk12100lol-prog/vexlang"

try:
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class VEXLangEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VEXLang Editor")
        self.geometry("1100x720")
        self.minsize(800, 500)

        self._filepath = None
        self._modified = False
        self._find_results = []
        self._find_idx = -1

        self._build_ui()
        self._setup_binds()
        self._highlight_timer = None
        self._highlight()

        self.after(2000, self._check_update)

    # ── UI ──

    def _build_ui(self):
        # header toolbar
        hdr = ctk.CTkFrame(self, height=40, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="VEXLang", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#ff6b9d").pack(side="left", padx=10)

        self._python_cmd = ctk.StringVar(value="python")
        py_menu = ctk.CTkOptionMenu(hdr, values=["python", "py"], variable=self._python_cmd,
                                     width=50, height=22, font=ctk.CTkFont(size=9))
        py_menu.pack(side="left", padx=2)

        sep = lambda: ctk.CTkFrame(hdr, width=1, height=18, fg_color="#2a2d45").pack(side="left", padx=4)

        btns = [
            ("📄 Nowy", self._new), ("📂 Otwórz", self._open), ("💾 Zapisz", self._save),
        ]
        for t, cmd in btns:
            ctk.CTkButton(hdr, text=t, width=38, height=24, font=ctk.CTkFont(size=9),
                          corner_radius=4, command=cmd).pack(side="left", padx=1)
        sep()

        btns2 = [("▶ Uruchom", self._run), ("■ Zatrzymaj", self._stop)]
        for t, cmd in btns2:
            ctk.CTkButton(hdr, text=t, width=38, height=24, font=ctk.CTkFont(size=9),
                          corner_radius=4, fg_color="#1e3a2a" if "chomaj" not in t else "#3a1a1a",
                          command=cmd).pack(side="left", padx=1)
        sep()

        ctk.CTkButton(hdr, text="💻 REPL", width=34, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#1a2a3a", command=self._repl).pack(side="left", padx=1)
        ctk.CTkButton(hdr, text="🔍 Szukaj", width=36, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#2a1a3a", command=self._toggle_find).pack(side="left", padx=1)
        sep()
        ctk.CTkButton(hdr, text="📦 Biblioteki", width=34, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#1a2a2a", command=self._otworz_biblioteki).pack(side="left", padx=1)
        ctk.CTkButton(hdr, text="⬇ Aktualizacje", width=36, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#2a2a1a", command=self._check_update_now).pack(side="left", padx=1)

        self._upd_lbl = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9))
        self._upd_lbl.pack(side="right", padx=12)

        # find bar
        self._find_fr = ctk.CTkFrame(self, height=0, corner_radius=0)
        fi = ctk.CTkFrame(self._find_fr)
        fi.pack(fill="x", padx=8, pady=2)
        ctk.CTkLabel(fi, text="🔍", font=ctk.CTkFont(size=12)).pack(side="left", padx=4)
        self._find_en = ctk.CTkEntry(fi, placeholder_text="Szukaj...")
        self._find_en.pack(side="left", padx=4, fill="x", expand=True)
        self._find_en.bind("<Return>", lambda e: self._find())
        self._find_en.bind("<KeyRelease>", lambda e: self._find())
        ctk.CTkButton(fi, text="▲", width=28, command=lambda: self._find(False)).pack(side="left", padx=1)
        ctk.CTkButton(fi, text="▼", width=28, command=lambda: self._find(True)).pack(side="left", padx=1)
        self._find_cnt = ctk.CTkLabel(fi, text="", font=ctk.CTkFont(size=9), width=20)
        self._find_cnt.pack(side="left", padx=6)
        ctk.CTkButton(fi, text="✕", width=28, fg_color="transparent",
                      command=self._toggle_find).pack(side="left", padx=4)

        # editor area
        ef = ctk.CTkFrame(self, corner_radius=0)
        ef.pack(fill="both", expand=True)

        self._line_canvas = ctk.CTkCanvas(ef, width=48, highlightthickness=0)
        self._line_canvas.pack(side="left", fill="y")

        self._txt = ctk.CTkTextbox(ef, font=ctk.CTkFont(size=13), wrap="none",
                                   undo=True, activate_scrollbars=False)
        self._txt.pack(side="left", fill="both", expand=True)

        self._tb = self._txt._textbox

        sc = ctk.CTkScrollbar(ef, command=self._txt.yview)
        sc.pack(side="right", fill="y")
        self._txt.configure(yscrollcommand=sc.set)

        self._tb.tag_config("kw", foreground="#ff6b9d", font=("Consolas", 13, "bold"))
        self._tb.tag_config("str", foreground="#00ffa3")
        self._tb.tag_config("cm", foreground="#4a4d5e")
        self._tb.tag_config("num", foreground="#ffa640")
        self._tb.tag_config("blt", foreground="#40bfff")
        self._tb.tag_config("sel", foreground="#0a0c14", background="#ff6b9d")

        self._tb.configure(
            selectbackground="#3a1a40", selectforeground="#c8ccd4",
            insertbackground="#ff6b9d", padx=12, pady=8
        )
        self._line_canvas.configure(bg="#0f1220")

        # output
        of = ctk.CTkFrame(self, corner_radius=0)
        of.pack(fill="x")
        of.pack_propagate(False)
        of.configure(height=180)

        oh = ctk.CTkFrame(of, height=26, corner_radius=0)
        oh.pack(fill="x")
        oh.pack_propagate(False)

        self._out_lbls = {}
        for i, name in enumerate(["OUTPUT", "BŁĘDY", "REPL"]):
            lbl = ctk.CTkLabel(oh, text=name, font=ctk.CTkFont(size=9, weight="bold"),
                               text_color=("#ff6b9d" if i == 0 else None), padx=12,
                               cursor="hand2")
            lbl.pack(side="left", padx=1, pady=2)
            lbl.bind("<Button-1>", lambda e, n=name: self._switch_out(n))
            self._out_lbls[name] = lbl

        self._out = ctk.CTkTextbox(of, font=ctk.CTkFont(size=11), wrap="word",
                                   activate_scrollbars=False)
        self._out.pack(fill="both", expand=True)
        self._out.configure(state="disabled")
        self._out._textbox.tag_config("out_ok", foreground="#00ffa3")
        self._out._textbox.tag_config("out_err", foreground="#ef4444")
        self._out._textbox.tag_config("out_info", foreground="#40bfff")
        for k, v in [
            ("czerwony", "#ef4444"), ("zielony", "#00ffa3"), ("zolty", "#ffd700"),
            ("niebieski", "#40bfff"), ("fioletowy", "#a855f7"), ("cyjan", "#00ffff"),
            ("bialy", "#ffffff"), ("rozowy", "#ff6b9d"), ("pomaranczowy", "#ffa640"),
            ("szary", "#888888"),
        ]:
            self._out._textbox.tag_config(f"clr_{k}", foreground=v)

        # status
        st = ctk.CTkFrame(self, height=22, corner_radius=0)
        st.pack(fill="x")
        st.pack_propagate(False)
        self._st_line = ctk.CTkLabel(st, text="Ln 1, Col 1", font=ctk.CTkFont(size=9))
        self._st_line.pack(side="left", padx=10)
        self._st_file = ctk.CTkLabel(st, text="", font=ctk.CTkFont(size=9))
        self._st_file.pack(side="right", padx=10)

        self._active_out = "OUTPUT"

    # ── EVENTS ──

    def _setup_binds(self):
        self._tb.bind("<KeyRelease>", self._on_change)
        self._tb.bind("<ButtonRelease-1>", lambda e: self._update_status())
        self._tb.bind("<KeyPress>", lambda e: self.after(5, self._update_status))
        self._tb.bind("<Tab>", lambda e: self._tab(e))
        self._tb.bind("<Control-n>", lambda e: self._new())
        self._tb.bind("<Control-o>", lambda e: self._open())
        self._tb.bind("<Control-s>", lambda e: self._save())
        self._tb.bind("<Control-f>", lambda e: self._toggle_find())
        self._tb.bind("<F5>", lambda e: self._run())
        self._tb.bind("<F6>", lambda e: self._repl())
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.bind("<Control-q>", lambda e: self._quit())

    def _on_change(self, e=None):
        self._modified = True
        self._update_title()
        if self._highlight_timer:
            self.after_cancel(self._highlight_timer)
        self._highlight_timer = self.after(200, self._highlight)
        self._draw_lines()
        self._update_status()

    def _tab(self, e):
        self._txt.insert("insert", "    "); return "break"

    # ── STATUS ──

    def _update_status(self):
        try:
            ln, col = self._tb.index("insert").split(".")
            self._st_line.configure(text=f"Ln {ln}, Col {int(col)+1}")
            n = os.path.basename(self._filepath) if self._filepath else ""
            self._st_file.configure(text=n)
        except:
            pass

    def _update_title(self):
        n = os.path.basename(self._filepath) if self._filepath else "bez nazwy.vex"
        self.title(f"VEXLang Editor — {n}{' ●' if self._modified else ''}")

    # ── HIGHLIGHT ──

    def _highlight(self):
        tb = self._tb
        for t in ("kw", "str", "cm", "num", "blt", "sel"):
            tb.tag_remove(t, "1.0", "end")
        data = self._txt.get("1.0", "end")
        for i, line in enumerate(data.split("\n"), 1):
            if "#" in line:
                pos = line.index("#")
                tb.tag_add("cm", f"{i}.{pos}", f"{i}.end")
                line = line[:pos]
            for s, e in _find_strings(line):
                tb.tag_add("str", f"{i}.{s}", f"{i}.{e}")
            for tok, s, e in _tokenize(line):
                if tok in SLOWA_KLUCZOWE:
                    tb.tag_add("kw", f"{i}.{s}", f"{i}.{e}")
                elif tok in ("dlugosc","konwert","losuj","zaokraglij","min","max","abs",
                             "sqrt","sin","cos","flr","ceil","zawiera","zastep","dziel",
                             "laczenie","wielkie","male","przytnij","znajdz","dodaj","usun",
                             "odwroc","sortuj","suma","srednia","czysc","czekaj","zakoncz",
                             "data","czas","klucze","wartosci"):
                    tb.tag_add("blt", f"{i}.{s}", f"{i}.{e}")
                elif _is_num(tok):
                    tb.tag_add("num", f"{i}.{s}", f"{i}.{e}")
        self._draw_lines()

    def _draw_lines(self):
        self._line_canvas.delete("all")
        try:
            cnt = int(self._tb.index("end-1c").split(".")[0])
        except:
            cnt = 1
        try:
            cur = int(self._tb.index("insert").split(".")[0])
        except:
            cur = 1
        h = self._txt.winfo_height()
        self._line_canvas.configure(height=max(h, cnt * 22))
        for i in range(1, cnt + 1):
            y = (i - 1) * 22 + 4
            if i == cur:
                self._line_canvas.create_rectangle(
                    0, y - 2, 48, y + 18, fill="#1a1d40", outline=""
                )
            self._line_canvas.create_text(
                42, y, text=str(i), anchor="e", fill="#3a3d5e",
                font=("Consolas", 10)
            )

    # ── FIND ──

    def _toggle_find(self):
        if self._find_fr.winfo_ismapped():
            self._find_fr.pack_forget()
            self._find_fr.configure(height=0)
            self._tb.tag_remove("sel", "1.0", "end")
        else:
            self._find_fr.pack(fill="x")
            self._find_fr.configure(height=32)
            self._find_en.focus()
            try:
                self._find_en.delete(0, "end")
                self._find_en.insert(0, self._tb.selection_get())
            except:
                pass
            self._find()

    def _find(self, forward=True):
        q = self._find_en.get().strip()
        if not q:
            self._find_cnt.configure(text="")
            self._tb.tag_remove("sel", "1.0", "end")
            return
        self._tb.tag_remove("sel", "1.0", "end")
        self._find_results = []
        start = "1.0"
        while True:
            pos = self._tb.search(q, start, "end", nocase=True)
            if not pos:
                break
            self._find_results.append(pos)
            self._tb.tag_add("sel", pos, f"{pos}+{len(q)}c")
            start = f"{pos}+{len(q)}c"
        self._find_cnt.configure(text=f"{len(self._find_results)}")
        if self._find_results:
            self._find_idx = (
                (self._find_idx + 1) % len(self._find_results)
                if forward
                else (self._find_idx - 1) % len(self._find_results)
            )
            pos = self._find_results[self._find_idx]
            self._tb.mark_set("insert", pos)
            self._tb.see(pos)
            self._tb.focus_set()

    # ── FILE ──

    def _new(self):
        if self._modified and not messagebox.askokcancel("Nowy", "Odrzucić zmiany?"):
            return
        self._txt.delete("1.0", "end")
        self._filepath = None
        self._modified = False
        self._update_title()
        self._out_clear()
        self._highlight()

    def _open(self):
        fp = filedialog.askopenfilename(
            filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")]
        )
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                self._txt.delete("1.0", "end")
                self._txt.insert("1.0", f.read())
            self._filepath = fp
            self._modified = False
            self._update_title()
            self._highlight()
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def _save(self):
        if self._filepath:
            self._save_to(self._filepath)
        else:
            self._save_as()

    def _save_as(self):
        fp = filedialog.asksaveasfilename(
            defaultextension=".vex",
            filetypes=[("VEXLang", "*.vex"), ("Wszystkie", "*.*")]
        )
        if fp:
            self._filepath = fp
            self._save_to(fp)

    def _save_to(self, fp):
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self._txt.get("1.0", "end-1c"))
            self._modified = False
            self._update_title()
            self._out_write("✓ Zapisano\n", "ok")
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def _quit(self):
        if self._modified and not messagebox.askokcancel("Wyjście", "Odrzucić zmiany?"):
            return
        self.destroy()

    # ── RUN ──

    def _run(self):
        code = self._txt.get("1.0", "end-1c")
        if not code.strip():
            return
        tmp = os.path.join(os.environ.get("TEMP", os.getcwd()), f"vex_{int(time.time()*1000)}.vex")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
        py = self._python_cmd.get()
        try:
            self._proc = subprocess.Popen(
                ["cmd.exe", "/k", py, "vexlang.py", tmp],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def _stop(self):
        if hasattr(self, '_proc') and self._proc and self._proc.poll() is None:
            self._proc.kill()
            self._proc = None

    def _otworz_biblioteki(self):
        BibliotekiWindow(self)

    def _repl(self):
        py = self._python_cmd.get()
        try:
            subprocess.Popen(
                ["cmd.exe", "/k", py, "vexlang.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("Błąd", str(e))

    def _out_write(self, text, tag=None):
        self._out.configure(state="normal")
        if tag:
            self._out.insert("end", text, f"out_{tag}")
        else:
            text = re.sub('\x1b\\[\\d+m', '', text)
            self._out.insert("end", text)
        self._out.see("end")
        self._out.configure(state="disabled")

    def _out_clear(self):
        self._out.configure(state="normal")
        self._out.delete("1.0", "end")
        self._out.configure(state="disabled")

    def _switch_out(self, name):
        for n, lbl in self._out_lbls.items():
            lbl.configure(text_color=("#ff6b9d" if n == name else None))
        self._active_out = name

    # ── UPDATE ──

    def _check_update(self):
        threading.Thread(target=self._update_thread, daemon=True).start()

    def _check_update_now(self):
        self._upd_lbl.configure(text="Sprawdzanie...")
        self.after(100, self._check_update)

    def _update_thread(self):
        try:
            req = Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={"User-Agent": "VEXLang"},
            )
            data = json.loads(urlopen(req, timeout=8).read().decode())
            tag = data["tag_name"].lstrip("v")
            cur = VERSION.lstrip("v")
            if self._cmp(tag, cur) > 0:
                self.after(0, self._show_upd, tag, data.get("body", ""))
        except:
            pass

    def _cmp(self, a, b):
        pa = [int(x) for x in a.split(".")]
        pb = [int(x) for x in b.split(".")]
        for i in range(max(len(pa), len(pb))):
            va = pa[i] if i < len(pa) else 0
            vb = pb[i] if i < len(pb) else 0
            if va != vb:
                return va - vb
        return 0

    def _show_upd(self, tag, body):
        self._upd_lbl.configure(text=f"⬇ v{tag}!")
        if messagebox.askyesno(
            "Aktualizacja", f"Dostępna: v{tag}\n\n{body}\n\nPobrać?"
        ):
            threading.Thread(target=self._dl_upd, args=(tag,), daemon=True).start()

    def _dl_upd(self, tag):
        try:
            req = Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/v{tag}",
                headers={"User-Agent": "VEXLang"},
            )
            data = json.loads(urlopen(req, timeout=8).read().decode())
            zu = None
            for a in data.get("assets", []):
                if a["name"].endswith(".zip"):
                    zu = a["browser_download_url"]
                    break
            if not zu:
                zu = data.get("zipball_url")
            if not zu:
                raise Exception("Brak URL")
            resp = urlopen(Request(zu, headers={"User-Agent": "VEXLang"}), timeout=30)
            d = resp.read()
            base = os.path.dirname(os.path.abspath(__file__))

            for root, dirs, files in os.walk(base, topdown=True):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        os.remove(fp)
                    except:
                        pass
            for root, dirs, files in os.walk(base, topdown=False):
                dirs[:] = [d for d in dirs if d != ".git"]
                if root != base and not os.listdir(root):
                    try:
                        os.rmdir(root)
                    except:
                        pass

            with zipfile.ZipFile(io.BytesIO(d)) as z:
                names = z.namelist()
                roots = set()
                for n in names:
                    p = n.split("/")
                    if len(p) > 1 and p[0]:
                        roots.add(p[0])
                skip = len(roots) == 1
                for name in names:
                    parts = name.split("/")[1:] if skip else name.split("/")
                    if not parts:
                        continue
                    target = os.path.join(base, *parts)
                    if name.endswith("/"):
                        os.makedirs(target, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with open(target, "wb") as f:
                            f.write(z.read(name))
            messagebox.showinfo("OK", f"Zaktualizowano do v{tag}. Uruchom ponownie.")
            self.quit()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się: {e}")

    def start(self):
        self._highlight()
        self.mainloop()


# ── UTILS ──

def _find_strings(line):
    res = []
    i = 0
    while i < len(line):
        if line[i] == '"':
            s = i
            i += 1
            while i < len(line) and line[i] != '"':
                i += 1
            res.append((s, i + 1 if i < len(line) else len(line)))
        i += 1
    return res


def _tokenize(line):
    res = []
    i = 0
    while i < len(line):
        if line[i].isalpha() or line[i] == "_":
            s = i
            while i < len(line) and (
                line[i].isalnum() or line[i] in "_ąćęłńóśźż"
            ):
                i += 1
            res.append((line[s:i], s, i))
        elif line[i].isdigit():
            s = i
            while i < len(line) and (line[i].isdigit() or line[i] == "."):
                i += 1
            res.append((line[s:i], s, i))
        else:
            i += 1
    return res


def _is_num(s):
    try:
        float(s)
        return True
    except:
        return False


class BibliotekiWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Menadżer bibliotek Python")
        self.geometry("720x540")
        self.minsize(500, 400)
        self.after(100, self.lift)

        self._wyniki = []
        self._instalowane = []
        self._selected_pkg = None
        self._selected_inst = None

        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=8, pady=8)

        self._tabs = ctk.CTkTabview(main, corner_radius=6)
        self._tabs.pack(fill="both", expand=True)

        self._build_search_tab()
        self._build_installed_tab()

    def _build_search_tab(self):
        tab = self._tabs.add("Szukaj")

        top = ctk.CTkFrame(tab, height=36)
        top.pack(fill="x", padx=6, pady=6)
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="Szukaj:", font=ctk.CTkFont(size=10)).pack(side="left", padx=4)
        self._search_en = ctk.CTkEntry(top, placeholder_text="nazwa biblioteki...")
        self._search_en.pack(side="left", fill="x", expand=True, padx=4)
        self._search_en.bind("<Return>", lambda e: self._szukaj())
        ctk.CTkButton(top, text="🔍", width=32, command=self._szukaj).pack(side="left", padx=2)

        self._results_frame = ctk.CTkScrollableFrame(tab, corner_radius=4)
        self._results_frame.pack(fill="both", expand=True, padx=6, pady=2)

        bottom = ctk.CTkFrame(tab, height=36)
        bottom.pack(fill="x", padx=6, pady=6)
        bottom.pack_propagate(False)
        self._zainstaluj_btn = ctk.CTkButton(bottom, text="Zainstaluj", command=self._zainstaluj, state="disabled")
        self._zainstaluj_btn.pack(side="left", padx=4)

    def _build_installed_tab(self):
        tab = self._tabs.add("Zainstalowane")

        self._installed_frame = ctk.CTkScrollableFrame(tab, corner_radius=4)
        self._installed_frame.pack(fill="both", expand=True, padx=6, pady=2)

        bottom = ctk.CTkFrame(tab, height=36)
        bottom.pack(fill="x", padx=6, pady=6)
        bottom.pack_propagate(False)
        ctk.CTkButton(bottom, text="Odśwież", command=self._odswiez_instalowane).pack(side="left", padx=4)
        ctk.CTkButton(bottom, text="Odinstaluj", fg_color="#3a1a1a", command=self._odinstaluj).pack(side="left", padx=4)

        self._odswiez_instalowane()

    def _czysc_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=8)).pack()

    def _szukaj(self):
        q = self._search_en.get().strip()
        if not q:
            return
        self._czysc_frame(self._results_frame)
        self._selected_pkg = None
        self._zainstaluj_btn.configure(state="disabled")
        ctk.CTkLabel(self._results_frame, text="Szukanie...", font=ctk.CTkFont(size=11)).pack(pady=10)
        threading.Thread(target=self._szukaj_watek, args=(q,), daemon=True).start()

    def _szukaj_watek(self, q):
        try:
            from urllib.request import urlopen, Request
            # PyPI JSON search API
            url = f"https://pypi.org/simple/{q}/"
            req = Request(url, headers={"User-Agent": "VEXLang/2.1"})
            resp = urlopen(req, timeout=10)
            html = resp.read().decode()
            names = []
            for m in re.finditer(r'<a[^>]*href="[^"]*"[^>]*>([^<]+)</a>', html):
                name = m.group(1).strip()
                if q.lower() in name.lower():
                    names.append(name)
            self._wyniki = names[:60]
            self.after(0, self._pokaz_wyniki)
        except Exception as e:
            self.after(0, lambda: self._czysc_frame(self._results_frame))
            self.after(0, lambda: ctk.CTkLabel(
                self._results_frame, text=f"Błąd: {e}\nSprawdź połączenie.",
                font=ctk.CTkFont(size=11), text_color="#ef4444").pack(pady=10))

    def _pokaz_wyniki(self):
        self._czysc_frame(self._results_frame)
        if not self._wyniki:
            ctk.CTkLabel(self._results_frame, text="Brak wyników.",
                         font=ctk.CTkFont(size=11)).pack(pady=10)
            return
        for name in self._wyniki:
            btn = ctk.CTkButton(
                self._results_frame, text=name,
                font=ctk.CTkFont(size=11),
                fg_color="#141726", hover_color="#1e2240",
                anchor="w", height=26,
                command=lambda n=name: self._wybierz_pakiet(n)
            )
            btn.pack(fill="x", padx=4, pady=1)

    def _wybierz_pakiet(self, name):
        self._selected_pkg = name
        self._zainstaluj_btn.configure(state="normal", text=f"Zainstaluj {name}")

    def _zainstaluj(self):
        if not self._selected_pkg:
            return
        name = self._selected_pkg
        info = ctk.CTkLabel(self._results_frame, text=f"Instalowanie {name}...",
                            font=ctk.CTkFont(size=10), text_color="#ffa640")
        info.pack(pady=4)
        self._zainstaluj_btn.configure(state="disabled", text="Instalowanie...")
        threading.Thread(target=self._instaluj_watek, args=(name,), daemon=True).start()

    def _instaluj_watek(self, name):
        py = self.parent._python_cmd.get()
        try:
            r = subprocess.run([py, "-m", "pip", "install", name],
                               capture_output=True, text=True, timeout=120)
            out = r.stdout + r.stderr
            ok = "Successfully installed" in out or "already satisfied" in out
            self.after(0, lambda: ctk.CTkLabel(
                self._results_frame,
                text="✔ Gotowe!" if ok else f"❌ Błąd\n{out[:300]}",
                font=ctk.CTkFont(size=10),
                text_color="#00ffa3" if ok else "#ef4444"
            ).pack(pady=2))
            if ok:
                self.after(500, self._odswiez_instalowane)
        except Exception as e:
            self.after(0, lambda: ctk.CTkLabel(
                self._results_frame, text=f"Błąd: {e}",
                font=ctk.CTkFont(size=10), text_color="#ef4444"
            ).pack(pady=2))
        self.after(0, lambda: self._zainstaluj_btn.configure(state="disabled", text="Zainstaluj"))

    def _odswiez_instalowane(self):
        self._czysc_frame(self._installed_frame)
        self._selected_inst = None
        ctk.CTkLabel(self._installed_frame, text="Ładowanie...",
                     font=ctk.CTkFont(size=11)).pack(pady=10)
        threading.Thread(target=self._odswiez_watek, daemon=True).start()

    def _odswiez_watek(self):
        py = self.parent._python_cmd.get()
        try:
            r = subprocess.run([py, "-m", "pip", "list", "--format=columns"],
                               capture_output=True, text=True, timeout=30)
            lines = r.stdout.strip().split("\n")
            pkgs = []
            started = False
            for line in lines:
                if "-------" in line:
                    started = True
                    continue
                if started and line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        pkgs.append((parts[0], parts[1]))
            self._instalowane = pkgs
            self.after(0, self._pokaz_instalowane)
        except Exception as e:
            self.after(0, lambda: self._czysc_frame(self._installed_frame))
            self.after(0, lambda: ctk.CTkLabel(
                self._installed_frame, text=f"Błąd: {e}",
                font=ctk.CTkFont(size=11), text_color="#ef4444"
            ).pack(pady=10))

    def _pokaz_instalowane(self):
        self._czysc_frame(self._installed_frame)
        if not self._instalowane:
            ctk.CTkLabel(self._installed_frame, text="Brak pakietów.",
                         font=ctk.CTkFont(size=11)).pack(pady=10)
            return
        for name, ver in self._instalowane:
            f = ctk.CTkFrame(self._installed_frame, fg_color="transparent")
            f.pack(fill="x", padx=4, pady=1)
            btn = ctk.CTkButton(
                f, text=f"{name}  ({ver})",
                font=ctk.CTkFont(size=11),
                fg_color="#141726", hover_color="#1e2240",
                anchor="w", height=26,
                command=lambda n=name: self._wybierz_instalowany(n)
            )
            btn.pack(fill="x")

    def _wybierz_instalowany(self, name):
        self._selected_inst = name

    def _odinstaluj(self):
        if not self._selected_inst:
            return
        name = self._selected_inst
        from tkinter import messagebox as _mb
        if not _mb.askyesno("Odinstaluj", f"Usunąć {name}?"):
            return
        ctk.CTkLabel(self._installed_frame, text=f"Odinstalowywanie {name}...",
                     font=ctk.CTkFont(size=10), text_color="#ffa640").pack(pady=2)
        threading.Thread(target=self._odinstaluj_watek, args=(name,), daemon=True).start()

    def _odinstaluj_watek(self, name):
        py = self.parent._python_cmd.get()
        try:
            r = subprocess.run([py, "-m", "pip", "uninstall", name, "-y"],
                               capture_output=True, text=True, timeout=60)
            out = r.stdout + r.stderr
            ok = "Successfully uninstalled" in out
            self.after(0, lambda: ctk.CTkLabel(
                self._installed_frame,
                text="✔ Usunięto!" if ok else f"❌ {out[:200]}",
                font=ctk.CTkFont(size=10),
                text_color="#00ffa3" if ok else "#ef4444"
            ).pack(pady=2))
            if ok:
                self.after(500, self._odswiez_instalowane)
        except Exception as e:
            self.after(0, lambda: ctk.CTkLabel(
                self._installed_frame, text=f"Błąd: {e}",
                font=ctk.CTkFont(size=10), text_color="#ef4444"
            ).pack(pady=2))


if __name__ == "__main__":
    VEXLangEditor().start()
