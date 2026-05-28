#!/usr/bin/env python3
import sys, os, io, json, threading, zipfile, re, time, subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from urllib.request import urlopen, Request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vexlang import Lexer, Parser, Interpreter, SLOWA_KLUCZOWE

VERSION = "1.2.1"
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
        self._exec_thread = None
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
                     text_color="#ff6b9d").pack(side="left", padx=14)

        sep = lambda: ctk.CTkFrame(hdr, width=1, height=18, fg_color="#2a2d45").pack(side="left", padx=4)

        btns = [
            ("📄 Nowy", self._new), ("📂 Otwórz", self._open), ("💾 Zapisz", self._save),
        ]
        for t, cmd in btns:
            ctk.CTkButton(hdr, text=t, width=42, height=24, font=ctk.CTkFont(size=9),
                          corner_radius=4, command=cmd).pack(side="left", padx=2)
        sep()

        btns2 = [("▶ Uruchom", self._run), ("■ Zatrzymaj", self._stop)]
        for t, cmd in btns2:
            ctk.CTkButton(hdr, text=t, width=40, height=24, font=ctk.CTkFont(size=9),
                          corner_radius=4, fg_color="#1e3a2a" if "chomaj" not in t else "#3a1a1a",
                          command=cmd).pack(side="left", padx=2)
        sep()

        ctk.CTkButton(hdr, text="💻 REPL", width=36, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#1a2a3a", command=self._repl).pack(side="left", padx=2)
        ctk.CTkButton(hdr, text="🔍 Szukaj", width=40, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#2a1a3a", command=self._toggle_find).pack(side="left", padx=2)
        sep()
        ctk.CTkButton(hdr, text="⬇ Aktualizacje", width=38, height=24, font=ctk.CTkFont(size=9),
                      corner_radius=4, fg_color="#2a2a1a", command=self._check_update_now).pack(side="left", padx=2)

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
                elif tok in ("dlugosc","konwert","losuj","zaokraglij"):
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
        if self._exec_thread and self._exec_thread.is_alive():
            return
        code = self._txt.get("1.0", "end-1c")
        if not code.strip():
            return
        self._switch_out("OUTPUT")
        self._out_clear()
        self._out_write("═══════════════════════\n", "info")
        self._out_write("  ▶ Uruchamianie...\n", "info")
        self._out_write("═══════════════════════\n", "info")
        self._exec_thread = threading.Thread(
            target=self._exec, args=(code,), daemon=True
        )
        self._exec_thread.start()

    def _stop(self):
        if self._exec_thread and self._exec_thread.is_alive():
            self._exec_thread = None
            self._out_write("■ Przerwano\n", "err")

    def _exec(self, code):
        old_out, old_in = sys.stdout, sys.stdin
        buf = io.StringIO()
        err = io.StringIO()
        try:
            sys.stdout = buf
            sys.stdin = io.StringIO()
            interp = Interpreter()
            interp.uruchom(code)
        except SyntaxError as e:
            err.write(f"Składnia: {e}\n")
        except Exception as e:
            err.write(f"Błąd: {e}\n")
        finally:
            sys.stdout = old_out
            sys.stdin = old_in
        out = buf.getvalue()
        e = err.getvalue()
        self.after(0, lambda: self._show_res(out, e))

    def _show_res(self, out, err):
        if out:
            self._switch_out("OUTPUT")
            self._out_write(out)
        if err:
            self._switch_out("BŁĘDY")
            self._out_write(err, "err")
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
                self._out_write("Bye!\n", "info")
                break
            try:
                self._repl_interp.uruchom(inp)
            except Exception as e:
                self.after(0, self._out_write, f"Błąd: {e}\n", "err")

    def _repl_input(self, prompt):
        res = []
        ev = threading.Event()
        self.after(0, self._show_repl_inp, prompt, res, ev)
        ev.wait()
        return res[0] if res else None

    def _show_repl_inp(self, prompt, res, ev):
        dlg = ctk.CTkToplevel(self)
        dlg.title("VEXLang Input")
        dlg.geometry("360x110")
        dlg.transient(self)
        dlg.grab_set()
        f = ctk.CTkFrame(dlg)
        f.pack(fill="both", expand=True, padx=16, pady=12)
        ctk.CTkLabel(f, text=prompt, font=ctk.CTkFont(size=12)).pack(anchor="w")
        ent = ctk.CTkEntry(f)
        ent.pack(fill="x", pady=8)
        ent.focus()

        def ok():
            res.append(ent.get())
            ev.set()
            dlg.destroy()

        ent.bind("<Return>", lambda e: ok())
        ctk.CTkButton(f, text="OK", command=ok).pack()

    def _out_write(self, text, tag=None):
        self._out.configure(state="normal")
        if tag:
            # tags defined on underlying text widget
            self._out.insert("end", text, tag)
        else:
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


if __name__ == "__main__":
    VEXLangEditor().start()
