#!/usr/bin/env python3
import sys, os, re, math, random as _random, time as _time

VERSION = "2.0.0"

# ── ANSI ──

KOLORY_ANSI = {
    "czerwony": 31, "zielony": 32, "zolty": 33, "niebieski": 34,
    "fioletowy": 35, "cyjan": 36, "bialy": 37, "rozowy": 95,
    "pomaranczowy": 93, "szary": 90, "jasny_czerwony": 91,
    "jasny_zielony": 92, "jasny_niebieski": 94,
}
KOLORY_HEX = {
    "czerwony": "#ef4444", "zielony": "#00ffa3", "zolty": "#ffd700",
    "niebieski": "#40bfff", "fioletowy": "#a855f7", "cyjan": "#00ffff",
    "bialy": "#ffffff", "rozowy": "#ff6b9d", "pomaranczowy": "#ffa640",
    "szary": "#888888", "jasny_czerwony": "#ff6b6b", "jasny_zielony": "#50ffb0",
    "jasny_niebieski": "#80dfff",
}

KANONICZNE = {
    "jesli": "jeśli", "falsz": "fałsz", "zwroc": "zwróć", "dopoki": "dopóki"
}

# ── LEXER ──

TOKENS = [
    ("KOMENTARZ_BLOK", r"/\*[\s\S]*?\*/"),
    ("KOMENTARZ", r"#.*"),
    ("SPACJA", r"[ \t]+"),
    ("LICZBA", r"\d+(\.\d+)?"),
    ("TEKST", r'"[^"]*"'),
    ("TEKST_POJ", r"'[^']*'"),
    ("IDENT", r"[a-ząćęłńóśźżA-Z_][a-ząćęłńóśźżA-Z0-9_]*"),
    ("DODAJ_PRZYP", r"\+="),
    ("ODEJMIJ_PRZYP", r"-="),
    ("MNOZ_PRZYP", r"\*="),
    ("DZIEL_PRZYP", r"/="),
    ("ROWNA_S", r"=="),
    ("NIE_ROWNE", r"!="),
    ("MNIEJSZE_R", r"<="),
    ("WIEKSZE_R", r">="),
    ("STRZALKA", r"=>"),
    ("PRZYPISANIE", r"="),
    ("WIĘKSZE", r">"),
    ("MNIEJSZE", r"<"),
    ("DODAJ", r"\+"),
    ("ODEJMIJ", r"-"),
    ("MNOZ", r"\*"),
    ("DZIEL", r"/"),
    ("POTEGA", r"\^"),
    ("MODULO", r"%"),
    ("PRZECINEK", r","),
    ("DWUKROPEK", r"::"),
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
    "licz", "tekst", "logiczna", "prawda", "fałsz", "falsz", "nic",
    "jeśli", "jesli", "to", "inaczej", "dopóki", "dopoki", "dla", "w", "az",
    "funkcja", "zwróć", "zwroc", "pisz", "pisz_kolorowo", "czytaj", "czysc",
    "lub", "nie", "i", "tablica", "slownik",
    "przerwij", "kontynuuj", "wybierz", "zakoncz", "czekaj",
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
                    if nazwa != "SPACJA" and nazwa != "KOMENTARZ" and nazwa != "KOMENTARZ_BLOK":
                        if nazwa == "IDENT" and tekst in SLOWA_KLUCZOWE:
                            kan = KANONICZNE.get(tekst, tekst)
                            self.tokeny.append(Token(kan.upper(), tekst, self.linia, self.kolumna))
                        elif nazwa == "TEKST":
                            self.tokeny.append(Token(nazwa, tekst[1:-1], self.linia, self.kolumna))
                        elif nazwa == "TEKST_POJ":
                            self.tokeny.append(Token("TEKST", tekst[1:-1], self.linia, self.kolumna))
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
    def __init__(self, start, koniec, krok=None):
        self.start = start
        self.koniec = koniec
        self.krok = krok

    def __repr__(self):
        return f"Zakres({self.start}..{self.koniec})"


class Przerwij(AST):
    def __repr__(self):
        return "Przerwij()"


class Kontynuuj(AST):
    def __repr__(self):
        return "Kontynuuj()"


class PiszKolorowo(AST):
    def __init__(self, wyrazenie, kolor):
        self.wyrazenie = wyrazenie
        self.kolor = kolor

    def __repr__(self):
        return f"PiszKolorowo({self.wyrazenie}, {self.kolor})"


class Czysc(AST):
    def __repr__(self):
        return "Czysc()"


class Czekaj(AST):
    def __init__(self, wyrazenie):
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"Czekaj({self.wyrazenie})"


class Zakoncz(AST):
    def __init__(self, wyrazenie=None):
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"Zakoncz({self.wyrazenie})"


class Wybierz(AST):
    def __init__(self, wyrazenie, przypadki, domyslnie=None):
        self.wyrazenie = wyrazenie
        self.przypadki = przypadki
        self.domyslnie = domyslnie

    def __repr__(self):
        return f"Wybierz({self.wyrazenie})"


class Przypadek(AST):
    def __init__(self, wartosci, cialo):
        self.wartosci = wartosci
        self.cialo = cialo

    def __repr__(self):
        return f"Przypadek({self.wartosci})"


class Az(AST):
    def __init__(self, cialo, warunek):
        self.cialo = cialo
        self.warunek = warunek

    def __repr__(self):
        return f"Az({self.cialo}, {self.warunek})"


class PrzypisanieZlozone(AST):
    def __init__(self, nazwa, operator, wyrazenie):
        self.nazwa = nazwa
        self.operator = operator
        self.wyrazenie = wyrazenie

    def __repr__(self):
        return f"PrzypisanieZlozone({self.nazwa} {self.operator}= {self.wyrazenie})"


class SlownikLiteral(AST):
    def __init__(self, pary):
        self.pary = pary

    def __repr__(self):
        return f"Slownik({self.pary})"


class Para(AST):
    def __init__(self, klucz, wartosc):
        self.klucz = klucz
        self.wartosc = wartosc

    def __repr__(self):
        return f"Para({self.klucz} => {self.wartosc})"


class InlineJesli(AST):
    def __init__(self, warunek, cialo, inaczej):
        self.warunek = warunek
        self.cialo = cialo
        self.inaczej = inaczej

    def __repr__(self):
        return f"InlineJesli({self.warunek})"


class Lambda(AST):
    def __init__(self, parametry, cialo):
        self.parametry = parametry
        self.cialo = cialo

    def __repr__(self):
        return f"Lambda({self.parametry})"


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
        self.pomija_nowe_linie()

        if self.biezacy().typ in ("LICZ", "TEKST", "LOGICZNA", "TABLICA", "SLOWNIK"):
            return self.deklaracja_zmiennej()
        if self.biezacy().typ == "IDENT" and self.nastepny().typ == "PRZYPISANIE":
            nazwa = self.spozywaj("IDENT").wartosc
            self.spozywaj("PRZYPISANIE")
            return Przypisanie(nazwa, self.wyrazenie())
        if self.biezacy().typ == "IDENT" and self.nastepny().typ == "LEWY_KWADRAT":
            idx_expr = self.wyrazenie()
            if self.sprawdz("PRZYPISANIE"):
                self.spozywaj()
                return Przypisanie(idx_expr, self.wyrazenie())
            return idx_expr
        if self.biezacy().typ == "IDENT" and self.nastepny().typ in ("DODAJ_PRZYP", "ODEJMIJ_PRZYP", "MNOZ_PRZYP", "DZIEL_PRZYP"):
            nazwa = self.spozywaj("IDENT").wartosc
            op = self.spozywaj().wartosc  # +=, -=, *=, /=
            return PrzypisanieZlozone(nazwa, op, self.wyrazenie())
        if self.biezacy().typ == "FUNKCJA":
            return self.deklaracja_funkcji()
        if self.biezacy().typ == "JEŚLI":
            return self.instrukcja_jesli()
        if self.biezacy().typ == "DOPÓKI":
            return self.instrukcja_dopoki()
        if self.biezacy().typ == "AZ":
            return self.instrukcja_az()
        if self.biezacy().typ == "DLA":
            return self.instrukcja_dla()
        if self.biezacy().typ == "WYBIERZ":
            return self.instrukcja_wybierz()
        if self.biezacy().typ == "PISZ":
            return self.instrukcja_pisz()
        if self.biezacy().typ == "PISZ_KOLOROWO":
            return self.instrukcja_pisz_kolorowo()
        if self.biezacy().typ == "ZWRÓĆ":
            return self.instrukcja_zwroc()
        if self.biezacy().typ == "CZYTAJ":
            return self.instrukcja_czytaj()
        if self.biezacy().typ == "CZYSC":
            self.spozywaj("CZYSC"); self.spozywaj("LEWY_NAWIAS"); self.spozywaj("PRAWY_NAWIAS")
            return Czysc()
        if self.biezacy().typ == "CZEKAJ":
            return self.instrukcja_czekaj()
        if self.biezacy().typ == "ZAKONCZ":
            return self.instrukcja_zakoncz()
        if self.biezacy().typ == "PRZERWIJ":
            self.spozywaj("PRZERWIJ"); return Przerwij()
        if self.biezacy().typ == "KONTYNUUJ":
            self.spozywaj("KONTYNUUJ"); return Kontynuuj()
        if self.biezacy().typ == "NOWA_LINIA":
            self.spozywaj("NOWA_LINIA"); return None
        if self.biezacy().typ == "EOF":
            return None
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
        if self.sprawdz("STRZALKA"):
            self.spozywaj()
            cialo = Blok()
            cialo.instrukcje = [Zwroc(self.wyrazenie())]
            return DeklaracjaFunkcji(nazwa, parametry, cialo)
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

    def instrukcja_pisz_kolorowo(self):
        self.spozywaj("PISZ_KOLOROWO")
        self.spozywaj("LEWY_NAWIAS")
        arg = self.wyrazenie()
        self.pomija_nowe_linie()
        self.spozywaj("PRZECINEK")
        self.pomija_nowe_linie()
        kolor = self.spozywaj()
        if kolor.typ == "IDENT":
            kolor_w = kolor.wartosc
        elif kolor.typ == "TEKST":
            kolor_w = kolor.wartosc
        else:
            self.blad("Oczekiwano nazwy koloru")
        self.spozywaj("PRAWY_NAWIAS")
        return PiszKolorowo(arg, kolor_w)

    def instrukcja_czekaj(self):
        self.spozywaj("CZEKAJ")
        self.spozywaj("LEWY_NAWIAS")
        arg = self.wyrazenie()
        self.spozywaj("PRAWY_NAWIAS")
        return Czekaj(arg)

    def instrukcja_zakoncz(self):
        self.spozywaj("ZAKONCZ")
        self.spozywaj("LEWY_NAWIAS")
        arg = None
        if not self.sprawdz("PRAWY_NAWIAS"):
            arg = self.wyrazenie()
        self.spozywaj("PRAWY_NAWIAS")
        return Zakoncz(arg)

    def instrukcja_az(self):
        self.spozywaj("AZ")
        self.pomija_nowe_linie()
        cialo = self.blok()
        self.pomija_nowe_linie()
        if self.sprawdz("DOPÓKI"):
            self.spozywaj("DOPÓKI")
        self.pomija_nowe_linie()
        warunek = self.wyrazenie()
        return Az(cialo, warunek)

    def instrukcja_wybierz(self):
        self.spozywaj("WYBIERZ")
        self.pomija_nowe_linie()
        expr = self.wyrazenie()
        self.pomija_nowe_linie()
        self.spozywaj("LEWY_KLAMRA")
        przypadki = []
        domyslnie = None
        while not self.sprawdz("PRAWY_KLAMRA") and not self.sprawdz("EOF"):
            self.pomija_nowe_linie()
            if self.sprawdz("PRAWY_KLAMRA"):
                break
            if self.sprawdz("INACZEJ"):
                self.spozywaj()
                self.pomija_nowe_linie()
                domyslnie = self.blok_po_klamrze() if self.sprawdz("LEWY_KLAMRA") else Blok()  # shouldn't reach
                # Actually collect statements until }
                continue
            # przypadki: lista wartości oddzielonych przecinkami, potem blok
            wartosci = [self.wyrazenie()]
            while self.sprawdz("PRZECINEK"):
                self.spozywaj()
                self.pomija_nowe_linie()
                wartosci.append(self.wyrazenie())
                self.pomija_nowe_linie()
            self.pomija_nowe_linie()
            cialo = self.blok()
            przypadki.append(Przypadek(wartosci, cialo))
        self.spozywaj("PRAWY_KLAMRA")
        return Wybierz(expr, przypadki, domyslnie)

    # ── wyrazenia ──

    def wyrazenie(self):
        return self.wyrazenie_logiczne()

    def wyrazenie_logiczne(self):
        lewy = self.wyrazenie_porownania()
        while self.sprawdz("I") or self.sprawdz("LUB") or (self.sprawdz("IDENT") and self.biezacy().wartosc == "i"):
            if self.sprawdz("IDENT"):
                self.spozywaj()
                op = "i"
            else:
                op = self.spozywaj().wartosc
            prawy = self.wyrazenie_porownania()
            lewy = OperatorBinarny(lewy, op, prawy)
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
        if tok.typ == "SLOWNIK":
            self.spozywaj()
            self.spozywaj("LEWY_NAWIAS")
            pary = []
            while not self.sprawdz("PRAWY_NAWIAS"):
                if pary:
                    self.spozywaj("PRZECINEK")
                klucz = self.wyrazenie()
                self.pomija_nowe_linie()
                if not self.sprawdz("STRZALKA"):
                    self.blad("Oczekiwano => w slowniku")
                self.spozywaj("STRZALKA")
                self.pomija_nowe_linie()
                wart = self.wyrazenie()
                pary.append(Para(klucz, wart))
            self.spozywaj("PRAWY_NAWIAS")
            return SlownikLiteral(pary)
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
            arg1 = self.wyrazenie()
            if self.sprawdz("PRZECINEK"):
                self.spozywaj()
                arg2 = self.wyrazenie()
                if self.sprawdz("PRZECINEK"):
                    self.spozywaj()
                    arg3 = self.wyrazenie()
                    self.spozywaj("PRAWY_NAWIAS")
                    return Zakres(arg1, arg2, arg3)
                self.spozywaj("PRAWY_NAWIAS")
                return Zakres(arg1, arg2)
            self.spozywaj("PRAWY_NAWIAS")
            return Zakres(None, arg1)
        if tok.typ == "FUNKCJA":
            return self.parse_lambda()
        if tok.typ == "JEŚLI":
            self.spozywaj()
            self.pomija_nowe_linie()
            warunek = self.wyrazenie()
            self.pomija_nowe_linie()
            if self.sprawdz("TO"):
                self.spozywaj("TO")
            self.pomija_nowe_linie()
            cialo = self.wyrazenie()
            self.pomija_nowe_linie()
            inaczej = None
            if self.sprawdz("INACZEJ"):
                self.spozywaj("INACZEJ")
                self.pomija_nowe_linie()
                inaczej = self.wyrazenie()
            return InlineJesli(warunek, cialo, inaczej if inaczej else Literal(None))
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

    def parse_lambda(self):
        self.spozywaj("FUNKCJA")
        self.spozywaj("LEWY_NAWIAS")
        parametry = []
        while not self.sprawdz("PRAWY_NAWIAS"):
            if parametry:
                self.spozywaj("PRZECINEK")
            parametry.append(self.spozywaj("IDENT").wartosc)
        self.spozywaj("PRAWY_NAWIAS")
        if self.sprawdz("STRZALKA"):
            self.spozywaj("STRZALKA")
            cialo = [Zwroc(self.wyrazenie())]
        else:
            self.pomija_nowe_linie()
            self.spozywaj("LEWY_KLAMRA")
            cialo = Blok()
            while not self.sprawdz("PRAWY_KLAMRA") and not self.sprawdz("EOF"):
                self.pomija_nowe_linie()
                if self.sprawdz("PRAWY_KLAMRA"):
                    break
                d = self.deklaracja()
                if d:
                    cialo.instrukcje.append(d)
            self.spozywaj("PRAWY_KLAMRA")
            return Lambda(parametry, cialo)
        b = Blok()
        b.instrukcje = cialo
        return Lambda(parametry, b)


# ── INTERPRETER ──

class BladWykonania(Exception):
    def __init__(self, msg, linia=None):
        self.msg = msg
        self.linia = linia
        super().__init__(f"Linia {linia}: {msg}" if linia else msg)


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

    def ustaw_lokalnie(self, nazwa, wartosc):
        # znajdź najbliższy kontekst z tą zmienną i zaktualizuj
        if nazwa in self.zmienne:
            self.zmienne[nazwa] = wartosc
            return True
        if self.rodzic:
            return self.rodzic.ustaw_lokalnie(nazwa, wartosc)
        self.ustaw(nazwa, wartosc)
        return True


class FunkcjaVEX:
    def __init__(self, nazwa, parametry, cialo, domkniecie, interpreter=None):
        self.nazwa = nazwa
        self.parametry = parametry
        self.cialo = cialo
        self.domkniecie = domkniecie
        self.interpreter = interpreter

    def __repr__(self):
        return f"<funkcja {self.nazwa}({', '.join(self.parametry)})>"

    def wywolaj(self, argumenty):
        lokalny = Kontekst(self.domkniecie)
        for p, a in zip(self.parametry, argumenty):
            lokalny.ustaw(p, a)
        for inst in self.cialo.instrukcje:
            if isinstance(inst, Zwroc):
                return self.interpreter.ewaluuj(inst.wyrazenie, lokalny)
            self.interpreter.wykonaj_instrukcje(inst, lokalny)
        return None

    def __call__(self, argumenty):
        return self.wywolaj(argumenty)


class Wbudowane:
    @staticmethod
    def dlugosc(args):
        if len(args) != 1:
            raise BladWykonania("dlugosc() wymaga 1 argumentu")
        v = args[0]
        if isinstance(v, (list, dict, str)):
            return len(v)
        raise BladWykonania(f"dlugosc() nie dziala dla {type(v).__name__}")

    @staticmethod
    def konwert(args):
        if len(args) != 2:
            raise BladWykonania("konwert(typ, wartosc) wymaga 2 argumentow")
        typ = args[0]
        wart = args[1]
        if typ == "licz":
            try: return int(wart)
            except: return float(wart)
        if typ == "tekst":
            return _reprezentacja(wart)
        if typ == "logiczna":
            return bool(wart)
        raise BladWykonania(f"Nieznany typ konwersji: {typ}")

    @staticmethod
    def losuj(args):
        if len(args) == 2:
            return _random.randint(int(args[0]), int(args[1]))
        if len(args) == 0:
            return _random.random()
        raise BladWykonania("losuj() - 0 lub 2 argumenty")

    @staticmethod
    def zaokraglij(args):
        if len(args) == 1:
            return round(args[0])
        if len(args) == 2:
            return round(args[0], int(args[1]))
        raise BladWykonania("zaokraglij() wymaga 1 lub 2 argumentow")

    @staticmethod
    def minf(args):
        if len(args) < 1:
            raise BladWykonania("min() wymaga co najmniej 1 argumentu")
        return min(args)

    @staticmethod
    def maxf(args):
        if len(args) < 1:
            raise BladWykonania("max() wymaga co najmniej 1 argumentu")
        return max(args)

    @staticmethod
    def absf(args):
        if len(args) != 1:
            raise BladWykonania("abs() wymaga 1 argumentu")
        return abs(args[0])

    @staticmethod
    def sqrt(args):
        if len(args) != 1:
            raise BladWykonania("sqrt() wymaga 1 argumentu")
        return math.sqrt(args[0])

    @staticmethod
    def sinf(args):
        if len(args) != 1:
            raise BladWykonania("sin() wymaga 1 argumentu")
        return math.sin(args[0])

    @staticmethod
    def cosf(args):
        if len(args) != 1:
            raise BladWykonania("cos() wymaga 1 argumentu")
        return math.cos(args[0])

    @staticmethod
    def flr(args):
        if len(args) != 1:
            raise BladWykonania("flr() wymaga 1 argumentu")
        return math.floor(args[0])

    @staticmethod
    def ceil(args):
        if len(args) != 1:
            raise BladWykonania("ceil() wymaga 1 argumentu")
        return math.ceil(args[0])

    @staticmethod
    def zawiera(args):
        if len(args) != 2:
            raise BladWykonania("zawiera() wymaga 2 argumentow")
        return args[1] in args[0] if isinstance(args[0], (str, list)) else False

    @staticmethod
    def zastep(args):
        if len(args) != 3:
            raise BladWykonania("zastep() wymaga 3 argumentow")
        return args[0].replace(args[1], args[2])

    @staticmethod
    def dziel(args):
        if len(args) != 2:
            raise BladWykonania("dziel() wymaga 2 argumentow")
        return args[0].split(args[1])

    @staticmethod
    def laczenie(args):
        if len(args) != 2:
            raise BladWykonania("laczenie() wymaga 2 argumentow")
        sep = args[1]
        return sep.join(str(x) for x in args[0])

    @staticmethod
    def wielkie(args):
        if len(args) != 1:
            raise BladWykonania("wielkie() wymaga 1 argumentu")
        return args[0].upper()

    @staticmethod
    def male(args):
        if len(args) != 1:
            raise BladWykonania("male() wymaga 1 argumentu")
        return args[0].lower()

    @staticmethod
    def przytnij(args):
        if len(args) != 1:
            raise BladWykonania("przytnij() wymaga 1 argumentu")
        return args[0].strip()

    @staticmethod
    def znajdz(args):
        if len(args) != 2:
            raise BladWykonania("znajdz() wymaga 2 argumentow")
        return args[0].find(args[1])

    @staticmethod
    def dodaj_do(args):
        if len(args) != 2:
            raise BladWykonania("dodaj() wymaga 2 argumentow")
        args[0].append(args[1])
        return args[0]

    @staticmethod
    def usun_z(args):
        if len(args) != 2:
            raise BladWykonania("usun() wymaga 2 argumentow")
        return args[0].pop(int(args[1]))

    @staticmethod
    def odwroc(args):
        if len(args) != 1:
            raise BladWykonania("odwroc() wymaga 1 argumentu")
        return list(reversed(args[0]))

    @staticmethod
    def sortujf(args):
        if len(args) != 1:
            raise BladWykonania("sortuj() wymaga 1 argumentu")
        return sorted(args[0])

    @staticmethod
    def suma(args):
        if len(args) != 1:
            raise BladWykonania("suma() wymaga 1 argumentu")
        return sum(args[0])

    @staticmethod
    def srednia(args):
        if len(args) != 1:
            raise BladWykonania("srednia() wymaga 1 argumentu")
        lst = args[0]
        return sum(lst) / len(lst) if lst else 0

    @staticmethod
    def czysc(args):
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")
        return None

    @staticmethod
    def czekajf(args):
        if len(args) != 1:
            raise BladWykonania("czekaj() wymaga 1 argumentu")
        _time.sleep(args[0] / 1000.0)
        return None

    @staticmethod
    def zakonczf(args):
        kod = args[0] if args else 0
        sys.exit(kod)

    @staticmethod
    def datag(args):
        import datetime
        return str(datetime.date.today())

    @staticmethod
    def czasf(args):
        import datetime
        return str(datetime.datetime.now().strftime("%H:%M:%S"))

    @staticmethod
    def klucze(args):
        if len(args) != 1 or not isinstance(args[0], dict):
            raise BladWykonania("klucze() wymaga slownika")
        return list(args[0].keys())

    @staticmethod
    def wartosci(args):
        if len(args) != 1 or not isinstance(args[0], dict):
            raise BladWykonania("wartosci() wymaga slownika")
        return list(args[0].values())

    # ── NOWE FUNKCJE v2.5 ──

    @staticmethod
    def czysc_konsola(args):
        """Czyści całą konsolę (jak cls/clear)."""
        if sys.stdout.isatty():
            os.system("cls" if os.name == "nt" else "clear")
        return None

    @staticmethod
    def typf(args):
        """Zwraca typ wartości jako tekst."""
        if len(args) != 1:
            raise BladWykonania("typ() wymaga 1 argumentu")
        v = args[0]
        if isinstance(v, int): return "liczba"
        if isinstance(v, float): return "liczba"
        if isinstance(v, str): return "tekst"
        if isinstance(v, list): return "lista"
        if isinstance(v, dict): return "slownik"
        if isinstance(v, bool): return "logiczna"
        if isinstance(v, type(None)): return "nic"
        return "nieznany"

    @staticmethod
    def zakresf(args):
        """Zwraca listę liczb: zakres(5) → [0,1,2,3,4]"""
        if len(args) == 1:
            return list(range(int(args[0])))
        if len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        if len(args) == 3:
            return list(range(int(args[0]), int(args[1]), int(args[2])))
        raise BladWykonania("zakres() wymaga 1-3 argumentow")

    @staticmethod
    def mapujf(args):
        """Stosuje funkcję do każdego elementu listy: mapuj(f, [1,2,3])"""
        if len(args) != 2:
            raise BladWykonania("mapuj(funkcja, lista) wymaga 2 argumentow")
        fn, lst = args[0], args[1]
        if not isinstance(lst, list):
            raise BladWykonania("mapuj() - drugi argument musi byc lista")
        if callable(fn):
            return [fn([x]) for x in lst]
        if isinstance(fn, FunkcjaVEX):
            return [fn.wywolaj([x]) for x in lst]
        raise BladWykonania("mapuj() - pierwszy argument musi byc funkcja")

    @staticmethod
    def filtrujf(args):
        """Filtruje listę: filtruj(f, [1,2,3]) → elementy gdzie f(x) == True"""
        if len(args) != 2:
            raise BladWykonania("filtruj(funkcja, lista) wymaga 2 argumentow")
        fn, lst = args[0], args[1]
        if not isinstance(lst, list):
            raise BladWykonania("filtruj() - drugi argument musi byc lista")
        if callable(fn):
            return [x for x in lst if fn([x])]
        if isinstance(fn, FunkcjaVEX):
            return [x for x in lst if fn.wywolaj([x])]
        raise BladWykonania("filtruj() - pierwszy argument musi byc funkcja")

    @staticmethod
    def wszystko(args):
        """Sprawdza czy wszystkie elementy są prawdziwe: wszystko([True, 1, 'a'])"""
        if len(args) != 1 or not isinstance(args[0], list):
            raise BladWykonania("wszystko() wymaga listy")
        return all(args[0])

    @staticmethod
    def jakiekolwiek(args):
        """Sprawdza czy jakikolwiek element jest prawdziwy: jakiekolwiek([False, 0, 'a'])"""
        if len(args) != 1 or not isinstance(args[0], list):
            raise BladWykonania("jakiekolwiek() wymaga listy")
        return any(args[0])

    @staticmethod
    def potegaf(args):
        """Potęgowanie: potega(2, 3) → 8"""
        if len(args) != 2:
            raise BladWykonania("potega() wymaga 2 argumentow")
        return args[0] ** args[1]

    @staticmethod
    def logf(args):
        """Logarytm: log(100) lub log(100, 10)"""
        if len(args) == 1:
            return math.log(args[0])
        if len(args) == 2:
            return math.log(args[0], args[1])
        raise BladWykonania("log() wymaga 1 lub 2 argumentow")

    @staticmethod
    def znakf(args):
        """Znak z kodu ASCII: znak(65) → 'A'"""
        if len(args) != 1:
            raise BladWykonania("znak() wymaga 1 argumentu")
        return chr(int(args[0]))

    @staticmethod
    def kod_znaku(args):
        """Kod ASCII znaku: kod_znaku('A') → 65"""
        if len(args) != 1 or not isinstance(args[0], str) or len(args[0]) == 0:
            raise BladWykonania("kod_znaku() wymaga 1 znaku")
        return ord(args[0][0])

    @staticmethod
    def zaczyna_sie(args):
        """Sprawdza czy tekst zaczyna się od prefixu"""
        if len(args) != 2:
            raise BladWykonania("zaczyna_sie() wymaga 2 argumentow")
        return args[0].startswith(args[1])

    @staticmethod
    def konczy_sie(args):
        """Sprawdza czy tekst kończy się na sufiks"""
        if len(args) != 2:
            raise BladWykonania("konczy_sie() wymaga 2 argumentow")
        return args[0].endswith(args[1])

    @staticmethod
    def liczf(args):
        """Liczy wystąpienia fragmentu w tekście"""
        if len(args) != 2:
            raise BladWykonania("licz() wymaga 2 argumentow")
        return args[0].count(args[1])

    @staticmethod
    def wyliczf(args):
        """Zwraca listę par (indeks, wartość)"""
        if len(args) != 1 or not isinstance(args[0], list):
            raise BladWykonania("wylicz() wymaga listy")
        return [[i, args[0][i]] for i in range(len(args[0]))]


WBUDOWANE = {
    "dlugosc": Wbudowane.dlugosc,
    "konwert": Wbudowane.konwert,
    "losuj": Wbudowane.losuj,
    "zaokraglij": Wbudowane.zaokraglij,
    "min": Wbudowane.minf,
    "max": Wbudowane.maxf,
    "abs": Wbudowane.absf,
    "sqrt": Wbudowane.sqrt,
    "sin": Wbudowane.sinf,
    "cos": Wbudowane.cosf,
    "flr": Wbudowane.flr,
    "ceil": Wbudowane.ceil,
    "zawiera": Wbudowane.zawiera,
    "zastep": Wbudowane.zastep,
    "dziel": Wbudowane.dziel,
    "laczenie": Wbudowane.laczenie,
    "wielkie": Wbudowane.wielkie,
    "male": Wbudowane.male,
    "przytnij": Wbudowane.przytnij,
    "znajdz": Wbudowane.znajdz,
    "dodaj": Wbudowane.dodaj_do,
    "usun": Wbudowane.usun_z,
    "odwroc": Wbudowane.odwroc,
    "sortuj": Wbudowane.sortujf,
    "suma": Wbudowane.suma,
    "srednia": Wbudowane.srednia,
    "czysc": Wbudowane.czysc,
    "czekaj": Wbudowane.czekajf,
    "zakoncz": Wbudowane.zakonczf,
    "data": Wbudowane.datag,
    "czas": Wbudowane.czasf,
    "klucze": Wbudowane.klucze,
    "wartosci": Wbudowane.wartosci,
    "pisz": lambda args: (print(*[_reprezentacja(a) for a in args]), None)[1],
    # nowe v2.5
    "czysc_konsola": Wbudowane.czysc_konsola,
    "typ": Wbudowane.typf,
    "zakres": Wbudowane.zakresf,
    "mapuj": Wbudowane.mapujf,
    "filtruj": Wbudowane.filtrujf,
    "wszystko": Wbudowane.wszystko,
    "jakiekolwiek": Wbudowane.jakiekolwiek,
    "potega": Wbudowane.potegaf,
    "log": Wbudowane.logf,
    "znak": Wbudowane.znakf,
    "kod_znaku": Wbudowane.kod_znaku,
    "zaczyna_sie": Wbudowane.zaczyna_sie,
    "konczy_sie": Wbudowane.konczy_sie,
    "policz": Wbudowane.liczf,
    "wylicz": Wbudowane.wyliczf,
    "podziel": Wbudowane.dziel,
    "lacz": Wbudowane.laczenie,
    "pierwiastek": Wbudowane.sqrt,
    "zamien": Wbudowane.zastep,
}


class Interpreter:
    def __init__(self, kolor_output=False):
        self.globalny = Kontekst()
        self.funkcje = {}
        self.przerwano = False
        self.kolor_output = kolor_output

    def wykonaj(self, program):
        for d in program.deklaracje:
            if isinstance(d, DeklaracjaFunkcji):
                fn = FunkcjaVEX(d.nazwa, d.parametry, d.cialo, self.globalny, self)
                self.funkcje[d.nazwa] = fn
        wynik = None
        for d in program.deklaracje:
            if isinstance(d, DeklaracjaFunkcji):
                continue
            try:
                wynik = self.wykonaj_instrukcje(d)
            except BladWykonania as e:
                if e.linia is None:
                    raise
                raise
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
                kontekst.ustaw_lokalnie(inst.nazwa, wart)
            elif isinstance(inst.nazwa, Indeksowanie):
                obiekt = self.ewaluuj(inst.nazwa.obiekt, kontekst)
                indeks = self.ewaluuj(inst.nazwa.indeks, kontekst)
                if isinstance(obiekt, dict):
                    obiekt[_reprezentacja(indeks) if not isinstance(indeks, str) else indeks] = wart
                else:
                    obiekt[int(indeks)] = wart
            else:
                raise BladWykonania(f"Nieprawidlowy cel przypisania: {type(inst.nazwa).__name__}")

        elif isinstance(inst, PrzypisanieZlozone):
            stara = kontekst.pobierz(inst.nazwa)
            tmp_ast = OperatorBinarny(Literal(stara), inst.operator[0], inst.wyrazenie)
            nowa = self.ewaluuj(tmp_ast, kontekst)
            kontekst.ustaw_lokalnie(inst.nazwa, nowa)

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

        elif isinstance(inst, Az):
            max_iter = 100000
            count = 0
            while True:
                self.wykonaj_blok(inst.cialo, kontekst)
                count += 1
                if count > max_iter:
                    raise BladWykonania("Przekroczono limit iteracji (100000)")
                if self.przerwano:
                    self.przerwano = False
                    break
                if not self.ewaluuj(inst.warunek, kontekst):
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

        elif isinstance(inst, Wybierz):
            wart = self.ewaluuj(inst.wyrazenie, kontekst)
            dopasowano = False
            for p in inst.przypadki:
                for w in p.wartosci:
                    if self.ewaluuj(w, kontekst) == wart:
                        self.wykonaj_blok(p.cialo, kontekst)
                        dopasowano = True
                        break
                if dopasowano:
                    break
            if not dopasowano and inst.domyslnie:
                self.wykonaj_blok(inst.domyslnie, kontekst)

        elif isinstance(inst, Pisz):
            wart = self.ewaluuj(inst.wyrazenie, kontekst)
            print(_reprezentacja(wart))

        elif isinstance(inst, PiszKolorowo):
            wart = self.ewaluuj(inst.wyrazenie, kontekst)
            txt = _reprezentacja(wart)
            kolor = inst.kolor
            if self.kolor_output and kolor in KOLORY_ANSI:
                print(f"\033[{KOLORY_ANSI[kolor]}m{txt}\033[0m")
            else:
                print(f"[{kolor}] {txt}")

        elif isinstance(inst, Zwroc):
            return ("zwroc", self.ewaluuj(inst.wyrazenie, kontekst))

        elif isinstance(inst, Czytaj):
            return input()

        elif isinstance(inst, Czysc):
            os.system("cls" if os.name == "nt" else "clear")

        elif isinstance(inst, Czekaj):
            ms = self.ewaluuj(inst.wyrazenie, kontekst)
            _time.sleep(ms / 1000.0)

        elif isinstance(inst, Zakoncz):
            kod = self.ewaluuj(inst.wyrazenie, kontekst) if inst.wyrazenie else 0
            sys.exit(kod)

        elif isinstance(inst, Przerwij):
            self.przerwano = True

        elif isinstance(inst, Kontynuuj):
            self.przerwano = True

        elif isinstance(inst, WywolanieFunkcji):
            return self.wywolaj(inst.nazwa, [self.ewaluuj(a, kontekst) for a in inst.argumenty], kontekst)

        elif isinstance(inst, (Literal, OperatorBinarny, OperatorUnarny, Zmienna, TablicaLiteral,
                                Indeksowanie, Zakres, SlownikLiteral, InlineJesli, Lambda)):
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

        if isinstance(wyrazenie, SlownikLiteral):
            d = {}
            for para in wyrazenie.pary:
                klucz = self.ewaluuj(para.klucz, kontekst)
                wart = self.ewaluuj(para.wartosc, kontekst)
                d[_reprezentacja(klucz) if not isinstance(klucz, str) else klucz] = wart
            return d

        if isinstance(wyrazenie, Indeksowanie):
            obiekt = self.ewaluuj(wyrazenie.obiekt, kontekst)
            indeks = self.ewaluuj(wyrazenie.indeks, kontekst)
            if isinstance(obiekt, dict):
                return obiekt.get(_reprezentacja(indeks) if not isinstance(indeks, str) else indeks, None)
            return obiekt[int(indeks)]

        if isinstance(wyrazenie, Zakres):
            start = self.ewaluuj(wyrazenie.start, kontekst) if wyrazenie.start is not None else 0
            koniec = self.ewaluuj(wyrazenie.koniec, kontekst)
            krok = self.ewaluuj(wyrazenie.krok, kontekst) if wyrazenie.krok is not None else 1
            return list(range(int(start), int(koniec), int(krok)))

        if isinstance(wyrazenie, WywolanieFunkcji):
            argi = [self.ewaluuj(a, kontekst) for a in wyrazenie.argumenty]
            return self.wywolaj(wyrazenie.nazwa, argi, kontekst)

        if isinstance(wyrazenie, InlineJesli):
            if self.ewaluuj(wyrazenie.warunek, kontekst):
                return self.ewaluuj(wyrazenie.cialo, kontekst)
            return self.ewaluuj(wyrazenie.inaczej, kontekst)

        if isinstance(wyrazenie, Lambda):
            fn = FunkcjaVEX("<lambda>", wyrazenie.parametry, wyrazenie.cialo, kontekst, self)
            return fn

        if isinstance(wyrazenie, Czytaj):
            return input()

        if isinstance(wyrazenie, Pisz):
            wart = self.ewaluuj(wyrazenie.wyrazenie, kontekst)
            print(_reprezentacja(wart))
            return None

        raise BladWykonania(f"Nieznane wyrazenie: {type(wyrazenie).__name__}")

    def wywolaj(self, nazwa, argumenty, kontekst):
        if nazwa in WBUDOWANE:
            return WBUDOWANE[nazwa](argumenty)
        if nazwa in self.funkcje:
            fn = self.funkcje[nazwa]
            if not fn.interpreter:
                fn.interpreter = self
            lokalny = Kontekst(fn.domkniecie if hasattr(fn, 'domkniecie') else self.globalny)
            for p, a in zip(fn.parametry, argumenty):
                lokalny.ustaw(p, a)
            wynik = self.wykonaj_blok(fn.cialo, lokalny)
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
    if isinstance(w, dict):
        items = ", ".join(f"{_reprezentacja(k)} => {_reprezentacja(v)}" for k, v in w.items())
        return "{" + items + "}"
    if isinstance(w, FunkcjaVEX):
        return f"<funkcja {w.nazwa}>"
    return str(w)


# ── CLI ──

def uruchom_plik(sciezka, kolor=False):
    with open(sciezka, "r", encoding="utf-8") as f:
        kod = f.read()
    interp = Interpreter(kolor_output=kolor)
    try:
        interp.uruchom(kod)
    except (SyntaxError, BladWykonania) as e:
        print(f"Blad: {e}", file=sys.stderr)
        return 1
    return 0


def repl():
    print(f"VEXLang v{VERSION} - wpisz 'exit' lub Ctrl+C aby wyjsc")
    interp = Interpreter(kolor_output=sys.stdout.isatty())
    while True:
        try:
            kod = input(">>> ")
            if kod.strip().lower() == "exit":
                break
            if not kod.strip():
                continue
            while kod.count("{") != kod.count("}") or (kod.count("(") != kod.count(")")):
                kod += "\n" + input("... ")
            interp.uruchom(kod)
        except KeyboardInterrupt:
            print()
            break
        except (SyntaxError, BladWykonania) as e:
            print(f"Blad: {e}")


if __name__ == "__main__":
    kolor = "--kolor" in sys.argv or sys.stdout.isatty()
    if len(sys.argv) > 1 and sys.argv[1] != "--kolor":
        sys.exit(uruchom_plik(sys.argv[1], kolor))
    else:
        repl()
