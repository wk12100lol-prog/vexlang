#!/usr/bin/env python3
import sys, os, re, math, random as _random

VERSION = "1.0.0"

# ── LEXER ──

TOKENS = [
    ("KOMENTARZ", r"#.*"),
    ("SPACJA", r"[ \t]+"),
    ("LICZBA", r"\d+(\.\d+)?"),
    ("TEKST", r'"[^"]*"'),
    ("IDENT", r"[a-ząćęłńóśźżA-Z_][a-ząćęłńóśźżA-Z0-9_]*"),
    ("DWUKROPEK", r"::"),
    ("ROWNA_S", r"=="),
    ("NIE_ROWNE", r"!="),
    ("MNIEJSZE_R", r"<="),
    ("WIEKSZE_R", r">="),
    ("PRZYPISANIE", r"="),
    ("STRZALKA", r"=>"),
    ("WIĘKSZE", r">"),
    ("MNIEJSZE", r"<"),
    ("DODAJ", r"\+"),
    ("ODEJMIJ", r"-"),
    ("MNOZ", r"\*"),
    ("DZIEL", r"/"),
    ("POTEGA", r"\^"),
    ("MODULO", r"%"),
    ("PRZECINEK", r","),
    ("KROPKA", r"\."),
    ("LEWY_NAWIAS", r"\("),
    ("PRAWY_NAWIAS", r"\)"),
    ("LEWY_KWADRAT", r"\["),
    ("PRAWY_KWADRAT", r"\]"),
    ("LEWY_KLAMRA", r"\{"),
    ("PRAWY_KLAMRA", r"\}"),
    ("NOWA_LINIA", r"\n"),
    ("SREDNIK", r";"),
]

SLOWA_KLUCZOWE = {
    "licz", "tekst", "logiczna", "prawda", "fałsz", "nic",
    "jeśli", "to", "inaczej", "dopóki", "dla", "w",
    "funkcja", "zwróć", "pisz", "czytaj",
    "lub", "nie", "tablica", "przerwij", "kontynuuj", "zakres",
}


class Token:
    def __init__(self, typ, wartosc, linia, kolumna):
        self.typ = typ
        self.wartosc = wartosc
        self.linia = linia
        self.kolumna = kolumna

    def __repr__(self):
        return f"Token({self.typ}, {self.wartosc!r}, L:{self.linia})"


class Lexer:
    def __init__(self, kod):
        self.kod = kod
        self.pozycja = 0
        self.linia = 1
        self.kolumna = 1
        self.tokeny = []

    def blad(self, msg):
        raise SyntaxError(f"Linia {self.linia}:{self.kolumna} - {msg}")

    def tokenizuj(self):
        while self.pozycja < len(self.kod):
            dopasowano = False
            for nazwa, wzor in TOKENS:
                m = re.compile(wzor).match(self.kod, self.pozycja)
                if m:
                    tekst = m.group(0)
                    if nazwa != "SPACJA" and nazwa != "KOMENTARZ":
                        if nazwa == "IDENT" and tekst in SLOWA_KLUCZOWE:
                            self.tokeny.append(Token(tekst.upper(), tekst, self.linia, self.kolumna))
                        elif nazwa == "TEKST":
                            self.tokeny.append(Token(nazwa, tekst[1:-1], self.linia, self.kolumna))
                        elif nazwa == "LICZBA":
                            self.tokeny.append(Token(nazwa, float(tekst) if "." in tekst else int(tekst), self.linia, self.kolumna))
                        else:
                            self.tokeny.append(Token(nazwa, tekst, self.linia, self.kolumna))
                    if nazwa == "NOWA_LINIA":
                        self.linia += 1
                        self.kolumna = 1
                    else:
                        self.kolumna += len(tekst)
                    self.pozycja = m.end()
                    dopasowano = True
                    break
            if not dopasowano:
                self.blad(f"Nieznany znak: {self.kod[self.pozycja]!r}")
        self.tokeny.append(Token("EOF", "", self.linia, self.kolumna))
        return self.tokeny


# ── PARSER ──

class AST:
    pass


class Program(AST):
    def __init__(self):
        self.deklaracje = []

    def __repr__(self):
        return f"Program({self.deklaracje})"


class Przypisanie(AST):
    def __init__(self, nazwa, wyrazenie):
        self.nazwa = nazwa
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"Przypisanie({self.nazwa} = {self.wyrazenie})"


class DeklaracjaZmiennej(AST):
    def __init__(self, typ, nazwa, wyrazenie=None):
        self.typ = typ
        self.nazwa = nazwa
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"DeklaracjaZmiennej({self.typ} {self.nazwa} = {self.wyrazenie})"


class DeklaracjaFunkcji(AST):
    def __init__(self, nazwa, parametry, cialo):
        self.nazwa = nazwa
        self.parametry = parametry
        self.cialo = cialo

    def __repr__(self):
        return f"DeklaracjaFunkcji({self.nazwa}({self.parametry}))"


class Jesli(AST):
    def __init__(self, warunek, cialo, inaczej=None):
        self.warunek = warunek
        self.cialo = cialo
        self.inaczej = inaczej

    def __repr__(self):
        return f"Jesli({self.warunek})"


class Dopoki(AST):
    def __init__(self, warunek, cialo):
        self.warunek = warunek
        self.cialo = cialo

    def __repr__(self):
        return f"Dopoki({self.warunek})"


class Dla(AST):
    def __init__(self, zmienna, iterowalne, cialo):
        self.zmienna = zmienna
        self.iterowalne = iterowalne
        self.cialo = cialo

    def __repr__(self):
        return f"Dla({self.zmienna} w {self.iterowalne})"


class Zwroc(AST):
    def __init__(self, wyrazenie):
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"Zwroc({self.wyrazenie})"


class Pisz(AST):
    def __init__(self, wyrazenie):
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"Pisz({self.wyrazenie})"


class Czytaj(AST):
    def __init__(self):
        pass

    def __repr__(self):
        return "Czytaj()"


class Blok(AST):
    def __init__(self):
        self.instrukcje = []

    def __repr__(self):
        return f"Blok({self.instrukcje})"


class WywolanieFunkcji(AST):
    def __init__(self, nazwa, argumenty):
        self.nazwa = nazwa
        self.argumenty = argumenty

    def __repr__(self):
        return f"Wywolanie({self.nazwa}({self.argumenty}))"


class OperatorBinarny(AST):
    def __init__(self, lewy, operator, prawy):
        self.lewy = lewy
        self.operator = operator
        self.prawy = prawy

    def __repr__(self):
        return f"({self.lewy} {self.operator} {self.prawy})"


class OperatorUnarny(AST):
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand = operand

    def __repr__(self):
        return f"({self.operator}{self.operand})"


class Zmienna(AST):
    def __init__(self, nazwa):
        self.nazwa = nazwa

    def __repr__(self):
        return f"Zmienna({self.nazwa})"


class Literal(AST):
    def __init__(self, wartosc):
        self.wartosc = wartosc

    def __repr__(self):
        return f"Literal({self.wartosc})"


class TablicaLiteral(AST):
    def __init__(self, elementy):
        self.elementy = elementy

    def __repr__(self):
        return f"Tablica({self.elementy})"


class Indeksowanie(AST):
    def __init__(self, obiekt, indeks):
        self.obiekt = obiekt
        self.indeks = indeks

    def __repr__(self):
        return f"Indeks({self.obiekt}[{self.indeks}])"


class Zakres(AST):
    def __init__(self, start, koniec):
        self.start = start
        self.koniec = koniec

    def __repr__(self):
        return f"Zakres({self.start}..{self.koniec})"


class Przerwij(AST):
    def __repr__(self):
        return "Przerwij()"


class Kontynuuj(AST):
    def __repr__(self):
        return "Kontynuuj()"


class Parser:
    def __init__(self, tokeny):
        self.tokeny = tokeny
        self.indeks = 0

    def biezacy(self):
        return self.tokeny[self.indeks]

    def poprzedni(self):
        return self.tokeny[self.indeks - 1]

    def spozywaj(self, typ=None):
        tok = self.biezacy()
        if typ and tok.typ != typ:
            self.blad(f"Oczekiwano {typ}, otrzymano {tok.typ}({tok.wartosc})")
        self.indeks += 1
        return tok

    # sprawdz typ bez spożywania
    def sprawdz(self, typ):
        return self.biezacy().typ == typ

    def pomija_nowe_linie(self):
        while self.sprawdz("NOWA_LINIA") or self.sprawdz("SREDNIK"):
            self.spozywaj()

    def blad(self, msg):
        tok = self.biezacy()
        raise SyntaxError(f"Linia {tok.linia}:{tok.kolumna} - {msg}")

    def parsuj(self):
        prog = Program()
        while self.biezacy().typ != "EOF":
            d = self.deklaracja()
            if d:
                prog.deklaracje.append(d)
        return prog

    def deklaracja(self):
        # pomiń nowe linie i średniki
        self.pomija_nowe_linie()

        if self.biezacy().typ in ("LICZ", "TEKST", "LOGICZNA", "TABLICA"):
            return self.deklaracja_zmiennej()
        if self.biezacy().typ == "IDENT" and self.nastepny().typ == "PRZYPISANIE":
            nazwa = self.spozywaj("IDENT").wartosc
            self.spozywaj("PRZYPISANIE")
            return Przypisanie(nazwa, self.wyrazenie())
        if self.biezacy().typ == "IDENT" and self.nastepny().typ == "LEWY_KWADRAT":
            # może być przypisanie indeksowane: tab[j] = ...
            idx_expr = self.wyrazenie()  # parse tab[j] as Indeksowanie
            if self.sprawdz("PRZYPISANIE"):
                self.spozywaj()
                return Przypisanie(idx_expr, self.wyrazenie())
            return idx_expr
        if self.biezacy().typ == "FUNKCJA":
            return self.deklaracja_funkcji()
        if self.biezacy().typ == "JEŚLI":
            return self.instrukcja_jesli()
        if self.biezacy().typ == "DOPÓKI":
            return self.instrukcja_dopoki()
        if self.biezacy().typ == "DLA":
            return self.instrukcja_dla()
        if self.biezacy().typ == "PISZ":
            return self.instrukcja_pisz()
        if self.biezacy().typ == "ZWRÓĆ":
            return self.instrukcja_zwroc()
        if self.biezacy().typ == "CZYTAJ":
            return self.instrukcja_czytaj()
        if self.biezacy().typ == "PRZERWIJ":
            self.spozywaj("PRZERWIJ"); return Przerwij()
        if self.biezacy().typ == "KONTYNUUJ":
            self.spozywaj("KONTYNUUJ"); return Kontynuuj()
        if self.biezacy().typ == "NOWA_LINIA":
            self.spozywaj("NOWA_LINIA"); return None
        if self.biezacy().typ == "EOF":
            return None
        # może być wywołanie funkcji jako instrukcja
        if self.biezacy().typ == "IDENT" and self.nastepny().typ == "LEWY_NAWIAS":
            return self.wyrazenie()
        if self.biezacy().typ == "IDENT" and self.nastepny().typ == "LEWY_KWADRAT":
            return self.wyrazenie()
        self.blad(f"Nieoczekiwany token: {self.biezacy()}")

    def nastepny(self):
        if self.indeks + 1 < len(self.tokeny):
            return self.tokeny[self.indeks + 1]
        return self.tokeny[-1]

    def deklaracja_zmiennej(self):
        typ = self.spozywaj().wartosc
        nazwa = self.spozywaj("IDENT").wartosc
        if self.sprawdz("PRZYPISANIE"):
            self.spozywaj("PRZYPISANIE")
            return DeklaracjaZmiennej(typ, nazwa, self.wyrazenie())
        return DeklaracjaZmiennej(typ, nazwa)

    def deklaracja_funkcji(self):
        self.spozywaj("FUNKCJA")
        self.pomija_nowe_linie()
        nazwa = self.spozywaj("IDENT").wartosc
        self.pomija_nowe_linie()
        self.spozywaj("LEWY_NAWIAS")
        parametry = []
        while not self.sprawdz("PRAWY_NAWIAS"):
            self.pomija_nowe_linie()
            if self.sprawdz("PRAWY_NAWIAS"):
                break
            if parametry:
                self.spozywaj("PRZECINEK")
            self.pomija_nowe_linie()
            parametry.append(self.spozywaj("IDENT").wartosc)
        self.pomija_nowe_linie()
        self.spozywaj("PRAWY_NAWIAS")
        self.pomija_nowe_linie()
        self.spozywaj("LEWY_KLAMRA")
        cialo = self.blok_po_klamrze()
        return DeklaracjaFunkcji(nazwa, parametry, cialo)

    def blok(self):
        self.pomija_nowe_linie()
        self.spozywaj("LEWY_KLAMRA")
        return self.blok_po_klamrze()

    def blok_po_klamrze(self):
        b = Blok()
        while not self.sprawdz("PRAWY_KLAMRA") and not self.sprawdz("EOF"):
            self.pomija_nowe_linie()
            if self.sprawdz("PRAWY_KLAMRA"):
                break
            d = self.deklaracja()
            if d:
                b.instrukcje.append(d)
        self.spozywaj("PRAWY_KLAMRA")
        return b

    def instrukcja_jesli(self):
        self.spozywaj("JEŚLI")
        self.pomija_nowe_linie()
        warunek = self.wyrazenie()
        self.pomija_nowe_linie()
        if self.sprawdz("TO"):
            self.spozywaj("TO")
        self.pomija_nowe_linie()
        cialo = self.blok()
        self.pomija_nowe_linie()
        inaczej = None
        if self.sprawdz("INACZEJ"):
            self.spozywaj("INACZEJ")
            self.pomija_nowe_linie()
            # else if
            if self.sprawdz("JEŚLI"):
                inaczej = self.instrukcja_jesli()
            else:
                inaczej = self.blok()
        return Jesli(warunek, cialo, inaczej)

    def instrukcja_dopoki(self):
        self.spozywaj("DOPÓKI")
        self.pomija_nowe_linie()
        warunek = self.wyrazenie()
        self.pomija_nowe_linie()
        if self.sprawdz("TO"):
            self.spozywaj("TO")
        self.pomija_nowe_linie()
        cialo = self.blok()
        return Dopoki(warunek, cialo)

    def instrukcja_dla(self):
        self.spozywaj("DLA")
        self.pomija_nowe_linie()
        zmienna = self.spozywaj("IDENT").wartosc
        self.pomija_nowe_linie()
        self.spozywaj("W")
        self.pomija_nowe_linie()
        iterowalne = self.wyrazenie()
        self.pomija_nowe_linie()
        cialo = self.blok()
        return Dla(zmienna, iterowalne, cialo)

    def instrukcja_pisz(self):
        self.spozywaj("PISZ")
        return Pisz(self.wyrazenie())

    def instrukcja_zwroc(self):
        self.spozywaj("ZWRÓĆ")
        return Zwroc(self.wyrazenie())

    def instrukcja_czytaj(self):
        self.spozywaj("CZYTAJ")
        self.spozywaj("LEWY_NAWIAS")
        self.spozywaj("PRAWY_NAWIAS")
        return Czytaj()

    # ── wyrazenia ──

    def wyrazenie(self):
        return self.wyrazenie_logiczne()

    def wyrazenie_logiczne(self):
        lewy = self.wyrazenie_porownania()
        while (self.sprawdz("I") or self.sprawdz("LUB") or
               (self.sprawdz("IDENT") and self.biezacy().wartosc == "i")):
            if self.sprawdz("IDENT"):
                self.spozywaj()
                op = "i"
            else:
                op = self.spozywaj().wartosc
            lewy = OperatorBinarny(lewy, op, self.wyrazenie_porownania())
        return lewy

    def wyrazenie_porownania(self):
        lewy = self.wyrazenie_dodawania()
        while self.sprawdz("ROWNA_S") or self.sprawdz("NIE_ROWNE") or \
              self.sprawdz("MNIEJSZE") or self.sprawdz("WIĘKSZE") or \
              self.sprawdz("MNIEJSZE_R") or self.sprawdz("WIEKSZE_R"):
            op = self.spozywaj().wartosc
            lewy = OperatorBinarny(lewy, op, self.wyrazenie_dodawania())
        return lewy

    def wyrazenie_dodawania(self):
        lewy = self.wyrazenie_mnozenia()
        while self.sprawdz("DODAJ") or self.sprawdz("ODEJMIJ"):
            op = self.spozywaj().wartosc
            lewy = OperatorBinarny(lewy, op, self.wyrazenie_mnozenia())
        return lewy

    def wyrazenie_mnozenia(self):
        lewy = self.wyrazenie_potegi()
        while self.sprawdz("MNOZ") or self.sprawdz("DZIEL") or self.sprawdz("MODULO"):
            op = self.spozywaj().wartosc
            lewy = OperatorBinarny(lewy, op, self.wyrazenie_potegi())
        return lewy

    def wyrazenie_potegi(self):
        lewy = self.wyrazenie_uname()
        while self.sprawdz("POTEGA"):
            op = self.spozywaj().wartosc
            lewy = OperatorBinarny(lewy, op, self.wyrazenie_uname())
        return lewy

    def wyrazenie_uname(self):
        if self.sprawdz("ODEJMIJ") or self.sprawdz("NIE"):
            op = self.spozywaj().wartosc
            return OperatorUnarny(op, self.wyrazenie_uname())
        return self.wyrazenie_pierwotne()

    def wyrazenie_pierwotne(self):
        tok = self.biezacy()

        if tok.typ == "LICZBA":
            self.spozywaj()
            return Literal(tok.wartosc)
        if tok.typ == "TEKST":
            self.spozywaj()
            return Literal(tok.wartosc)
        if tok.typ == "PRAWDA":
            self.spozywaj(); return Literal(True)
        if tok.typ == "FAŁSZ":
            self.spozywaj(); return Literal(False)
        if tok.typ == "NIC":
            self.spozywaj(); return Literal(None)
        if tok.typ == "TABLICA":
            self.spozywaj()
            self.spozywaj("LEWY_NAWIAS")
            el = []
            while not self.sprawdz("PRAWY_NAWIAS"):
                if el:
                    self.spozywaj("PRZECINEK")
                el.append(self.wyrazenie())
            self.spozywaj("PRAWY_NAWIAS")
            return TablicaLiteral(el)
        if tok.typ == "LEWY_KWADRAT":
            self.spozywaj()
            el = []
            while not self.sprawdz("PRAWY_KWADRAT"):
                if el:
                    self.spozywaj("PRZECINEK")
                el.append(self.wyrazenie())
            self.spozywaj("PRAWY_KWADRAT")
            return TablicaLiteral(el)
        if tok.typ == "LEWY_NAWIAS":
            self.spozywaj()
            w = self.wyrazenie()
            self.spozywaj("PRAWY_NAWIAS")
            return w
        if tok.typ == "ZAKRES":
            self.spozywaj()
            self.spozywaj("LEWY_NAWIAS")
            start = self.wyrazenie()
            self.spozywaj("PRZECINEK")
            koniec = self.wyrazenie()
            self.spozywaj("PRAWY_NAWIAS")
            return Zakres(start, koniec)
        if tok.typ == "IDENT":
            nazwa = self.spozywaj().wartosc
            if self.sprawdz("LEWY_NAWIAS"):
                self.spozywaj()
                argi = []
                while not self.sprawdz("PRAWY_NAWIAS"):
                    if argi:
                        self.spozywaj("PRZECINEK")
                    argi.append(self.wyrazenie())
                self.spozywaj("PRAWY_NAWIAS")
                return WywolanieFunkcji(nazwa, argi)
            if self.sprawdz("LEWY_KWADRAT"):
                self.spozywaj()
                indeks = self.wyrazenie()
                self.spozywaj("PRAWY_KWADRAT")
                return Indeksowanie(Zmienna(nazwa), indeks)
            return Zmienna(nazwa)
        if tok.typ == "CZYTAJ":
            self.spozywaj()
            self.spozywaj("LEWY_NAWIAS")
            self.spozywaj("PRAWY_NAWIAS")
            return Czytaj()

        self.blad(f"Nieoczekiwany token w wyrazeniu: {tok}")


# ── INTERPRETER ──

class BladWykonania(Exception):
    pass


class Kontekst:
    def __init__(self, rodzic=None):
        self.zmienne = {}
        self.rodzic = rodzic

    def ustaw(self, nazwa, wartosc):
        self.zmienne[nazwa] = wartosc

    def pobierz(self, nazwa):
        if nazwa in self.zmienne:
            return self.zmienne[nazwa]
        if self.rodzic:
            return self.rodzic.pobierz(nazwa)
        raise BladWykonania(f"Nieznana zmienna: {nazwa}")

    def czy_istnieje(self, nazwa):
        return nazwa in self.zmienne


class Wbudowane:
    @staticmethod
    def dlugosc(args):
        if len(args) != 1:
            raise BladWykonania("dlugosc() wymaga 1 argumentu")
        v = args[0]
        if isinstance(v, list):
            return len(v)
        if isinstance(v, str):
            return len(v)
        raise BladWykonania(f"dlugosc() nie działa dla {type(v)}")

    @staticmethod
    def konwert(args):
        if len(args) != 2:
            raise BladWykonania("konwert(typ, wartosc) wymaga 2 argumentow")
        typ = args[0]
        wart = args[1]
        if typ == "licz":
            return int(wart) if isinstance(wart, float) and wart == int(wart) else float(wart)
        if typ == "tekst":
            return str(wart)
        raise BladWykonania(f"Nieznany typ konwersji: {typ}")

    @staticmethod
    def losuj(args):
        if len(args) == 2:
            return _random.randint(int(args[0]), int(args[1]))
        return _random.random()

    @staticmethod
    def zaokraglij(args):
        if len(args) == 1:
            return round(args[0])
        return round(args[0], int(args[1]))


WBUDOWANE = {
    "dlugosc": Wbudowane.dlugosc,
    "konwert": Wbudowane.konwert,
    "losuj": Wbudowane.losuj,
    "zaokraglij": Wbudowane.zaokraglij,
    "pisz": lambda args: (print(*[str(a) for a in args]), None)[1],
}


class Interpreter:
    def __init__(self):
        self.globalny = Kontekst()
        self.funkcje = {}
        self.przerwano = False

    def wykonaj(self, program):
        for d in program.deklaracje:
            if isinstance(d, DeklaracjaFunkcji):
                self.funkcje[d.nazwa] = d
        wynik = None
        for d in program.deklaracje:
            wynik = self.wykonaj_instrukcje(d)
            if self.przerwano:
                break
        return wynik

    def wykonaj_instrukcje(self, inst, kontekst=None):
        if kontekst is None:
            kontekst = self.globalny

        if isinstance(inst, DeklaracjaZmiennej):
            wart = None
            if inst.wyrazenie:
                wart = self.ewaluuj(inst.wyrazenie, kontekst)
            kontekst.ustaw(inst.nazwa, wart)

        elif isinstance(inst, Przypisanie):
            wart = self.ewaluuj(inst.wyrazenie, kontekst)
            if isinstance(inst.nazwa, str):
                kontekst.ustaw(inst.nazwa, wart)
            elif isinstance(inst.nazwa, Indeksowanie):
                obiekt = self.ewaluuj(inst.nazwa.obiekt, kontekst)
                indeks = int(self.ewaluuj(inst.nazwa.indeks, kontekst))
                obiekt[indeks] = wart
            else:
                raise BladWykonania(f"Nieprawidlowy cel przypisania: {type(inst.nazwa)}")

        elif isinstance(inst, Jesli):
            if self.ewaluuj(inst.warunek, kontekst):
                return self.wykonaj_blok(inst.cialo, kontekst)
            elif inst.inaczej:
                if isinstance(inst.inaczej, Jesli):
                    return self.wykonaj_instrukcje(inst.inaczej, kontekst)
                return self.wykonaj_blok(inst.inaczej, kontekst)

        elif isinstance(inst, Dopoki):
            max_iter = 100000
            count = 0
            while self.ewaluuj(inst.warunek, kontekst):
                self.wykonaj_blok(inst.cialo, kontekst)
                count += 1
                if count > max_iter:
                    raise BladWykonania("Przekroczono limit iteracji (100000)")
                if self.przerwano:
                    self.przerwano = False
                    break

        elif isinstance(inst, Dla):
            iter = self.ewaluuj(inst.iterowalne, kontekst)
            for wart in iter:
                lokalny = Kontekst(kontekst)
                lokalny.ustaw(inst.zmienna, wart)
                self.wykonaj_blok(inst.cialo, lokalny)
                if self.przerwano:
                    self.przerwano = False
                    break

        elif isinstance(inst, Pisz):
            wart = self.ewaluuj(inst.wyrazenie, kontekst)
            print(_reprezentacja(wart))

        elif isinstance(inst, Zwroc):
            return ("zwroc", self.ewaluuj(inst.wyrazenie, kontekst))

        elif isinstance(inst, Czytaj):
            return input()

        elif isinstance(inst, Przerwij):
            self.przerwano = True

        elif isinstance(inst, Kontynuuj):
            self.przerwano = True
            # handled by loop

        elif isinstance(inst, WywolanieFunkcji):
            return self.wywolaj(inst.nazwa, [self.ewaluuj(a, kontekst) for a in inst.argumenty], kontekst)

        elif isinstance(inst, (Literal, OperatorBinarny, OperatorUnarny, Zmienna, TablicaLiteral, Indeksowanie, Zakres)):
            return self.ewaluuj(inst, kontekst)

        return None

    def wykonaj_blok(self, blok, kontekst):
        for i in blok.instrukcje:
            wynik = self.wykonaj_instrukcje(i, kontekst)
            if wynik is not None and isinstance(wynik, tuple) and wynik[0] == "zwroc":
                return wynik
            if self.przerwano:
                return None
        return None

    def ewaluuj(self, wyrazenie, kontekst):
        if isinstance(wyrazenie, Literal):
            return wyrazenie.wartosc

        if isinstance(wyrazenie, Zmienna):
            return kontekst.pobierz(wyrazenie.nazwa)

        if isinstance(wyrazenie, OperatorBinarny):
            lewy = self.ewaluuj(wyrazenie.lewy, kontekst)
            prawy = self.ewaluuj(wyrazenie.prawy, kontekst)
            op = wyrazenie.operator
            if op == "+":
                if isinstance(lewy, str) or isinstance(prawy, str):
                    return _reprezentacja(lewy) + _reprezentacja(prawy)
                return lewy + prawy
            if op == "-": return lewy - prawy
            if op == "*": return lewy * prawy
            if op == "/":
                if prawy == 0: raise BladWykonania("Dzielenie przez zero")
                return lewy / prawy
            if op == "^": return lewy ** prawy
            if op == "%": return lewy % prawy
            if op == "==": return lewy == prawy
            if op == "!=": return lewy != prawy
            if op == "<": return lewy < prawy
            if op == ">": return lewy > prawy
            if op == "<=": return lewy <= prawy
            if op == ">=": return lewy >= prawy
            if op == "i": return bool(lewy) and bool(prawy)
            if op == "lub": return bool(lewy) or bool(prawy)

        if isinstance(wyrazenie, OperatorUnarny):
            op = wyrazenie.operator
            operand = self.ewaluuj(wyrazenie.operand, kontekst)
            if op == "-": return -operand
            if op == "nie": return not operand

        if isinstance(wyrazenie, TablicaLiteral):
            return [self.ewaluuj(e, kontekst) for e in wyrazenie.elementy]

        if isinstance(wyrazenie, Indeksowanie):
            obiekt = self.ewaluuj(wyrazenie.obiekt, kontekst)
            indeks = int(self.ewaluuj(wyrazenie.indeks, kontekst))
            return obiekt[indeks]

        if isinstance(wyrazenie, Zakres):
            start = int(self.ewaluuj(wyrazenie.start, kontekst))
            koniec = int(self.ewaluuj(wyrazenie.koniec, kontekst))
            return list(range(start, koniec + 1))

        if isinstance(wyrazenie, WywolanieFunkcji):
            argi = [self.ewaluuj(a, kontekst) for a in wyrazenie.argumenty]
            return self.wywolaj(wyrazenie.nazwa, argi, kontekst)

        if isinstance(wyrazenie, Czytaj):
            return input()

        if isinstance(wyrazenie, Pisz):
            wart = self.ewaluuj(wyrazenie.wyrazenie, kontekst)
            print(_reprezentacja(wart))
            return None

        raise BladWykonania(f"Nieznane wyrazenie: {type(wyrazenie)}")

    def wywolaj(self, nazwa, argumenty, kontekst):
        if nazwa in WBUDOWANE:
            return WBUDOWANE[nazwa](argumenty)
        if nazwa in self.funkcje:
            func = self.funkcje[nazwa]
            lokalny = Kontekst(self.globalny)
            for p, a in zip(func.parametry, argumenty):
                lokalny.ustaw(p, a)
            wynik = self.wykonaj_blok(func.cialo, lokalny)
            if wynik and isinstance(wynik, tuple) and wynik[0] == "zwroc":
                return wynik[1]
            return None
        raise BladWykonania(f"Nieznana funkcja: {nazwa}")

    def uruchom(self, kod):
        lexer = Lexer(kod)
        tokeny = lexer.tokenizuj()
        parser = Parser(tokeny)
        program = parser.parsuj()
        return self.wykonaj(program)


def _reprezentacja(w):
    if w is None:
        return "nic"
    if isinstance(w, bool):
        return "prawda" if w else "fałsz"
    if isinstance(w, float) and w == int(w):
        return str(int(w))
    if isinstance(w, list):
        return "[" + ", ".join(_reprezentacja(x) for x in w) + "]"
    return str(w)


# ── CLI ──

def uruchom_plik(sciezka):
    with open(sciezka, "r", encoding="utf-8") as f:
        kod = f.read()
    interp = Interpreter()
    try:
        interp.uruchom(kod)
    except (SyntaxError, BladWykonania) as e:
        print(f"Blad: {e}", file=sys.stderr)
        return 1
    return 0


def repl():
    print("VEXLang v1.0 - wpisz 'exit' lub Ctrl+C aby wyjsc")
    interp = Interpreter()
    while True:
        try:
            kod = input(">>> ")
            if kod.strip().lower() == "exit":
                break
            if not kod.strip():
                continue
            # zbieraj linie a nie jest kompletne
            while kod.count("{") != kod.count("}") or (kod.count("(") != kod.count(")")):
                kod += "\n" + input("... ")
            interp.uruchom(kod)
        except KeyboardInterrupt:
            print()
            break
        except (SyntaxError, BladWykonania) as e:
            print(f"Blad: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(uruchom_plik(sys.argv[1]))
    else:
        repl()
