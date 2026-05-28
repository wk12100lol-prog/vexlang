#!/usr/bin/env python3
# VEXLang Editor — launcher (uruchamia editor.pyw bez konsoli)
import sys, os, subprocess

script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor.pyw")
if os.path.isfile(script):
    subprocess.Popen([sys.executable, script], shell=True)
else:
    print("Blad: nie znaleziono editor.pyw")
