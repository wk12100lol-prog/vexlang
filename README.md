# VEXLang v2.0.0

Język programowania z polskimi słowami kluczowymi.

## Spis treści
1. [Uruchamianie](#uruchamianie)
2. [Składnia](#składnia)
3. [Typy danych](#typy-danych)
4. [Zmienne](#zmienne)
5. [Operatory](#operatory)
6. [Instrukcje warunkowe](#instrukcje-warunkowe)
7. [Pętle](#pętle)
8. [Funkcje](#funkcje)
9. [Funkcje wbudowane](#funkcje-wbudowane)
10. [Przykłady](#przykłady)

---

## Uruchamianie

### REPL
```
python vexlang.py
```
lub dwukrotne kliknięcie `VEXLang.bat`.

### Uruchom plik
```
python vexlang.py program.vex
```

### Edytor (GUI)
```
python editor.pyw
```
Edytor z syntax highlighting, REPL, zakładkami outputu i auto-update.

---

## Składnia

### Komentarze
```
# komentarz liniowy
/* komentarz blokowy */
```

### Zmienne
```
licz x = 10
tekst nazwa = "Jan"
logiczna flag = prawda
tablica lista = [1, 2, 3]
slownik d = slownik("a" => 1, "b" => 2)
```

### Instrukcje warunkowe
```
jesli x > 5 to {
    pisz "duże"
} inaczej {
    pisz "małe"
}
```

### Wyrażenie warunkowe inline
```
x = jesli wiek >= 18 to "dorosły" inaczej "dziecko"
```

### Switch (wybierz)
```
wybierz x {
    1 { pisz "jeden" }
    2 { pisz "dwa" }
    3, 4 { pisz "trzy lub cztery" }
}
```

### Pętle
```
# dopóki
dopoki x < 10 {
    pisz x
    x += 1
}

# dla
dla i w zakres(1, 5) {
    pisz i
}

dla el w tablica {
    pisz el
}

# az (do-while)
az {
    pisz x
    x += 1
} dopoki x < 3
```

### Funkcje
```
# standardowa
funkcja kwadrat(x) {
    zwroc x * x
}

# lambda (jednolinijkowa)
funkcja podwoj(x) => x * 2

# rekurencja
funkcja silnia(n) {
    jesli n <= 1 to {
        zwroc 1
    }
    zwroc n * silnia(n - 1)
}
```

### Operatory złożone
```
x += 5
x -= 3
x *= 2
x /= 4
```

### Kolory w output
```
pisz_kolorowo("czerwony tekst", czerwony)
pisz_kolorowo("zielony tekst", zielony)
pisz_kolorowo("niebieski tekst", niebieski)
```

Dostępne kolory: `czerwony`, `zielony`, `zolty`, `niebieski`, `fioletowy`, `cyjan`, `bialy`, `rozowy`, `pomaranczowy`, `szary`.

---

## Typy danych

| Typ | Opis | Przykład |
|-----|------|----------|
| `licz` | Liczba całkowita/zmiennoprzecinkowa | `10`, `3.14` |
| `tekst` | Ciąg znaków | `"hello"`, `'world'` |
| `logiczna` | Wartość logiczna | `prawda`, `fałsz` |
| `tablica` | Lista elementów | `[1, 2, 3]` |
| `slownik` | Mapa klucz → wartość | `slownik("a" => 1)` |
| `nic` | Brak wartości | `nic` |

---

## Operatory

| Operator | Opis |
|----------|------|
| `+` | Dodawanie / konkatenacja |
| `-` | Odejmowanie |
| `*` | Mnożenie |
| `/` | Dzielenie |
| `^` | Potęgowanie |
| `%` | Modulo (reszta z dzielenia) |
| `==` | Równe |
| `!=` | Nie równe |
| `<` `>` `<=` `>=` | Porównanie |
| `i` | Logiczne AND |
| `lub` | Logiczne OR |
| `nie` | Logiczne NOT |
| `+=` `-=` `*=` `/=` | Operatory złożone |

---

## Funkcje wbudowane

### Matematyczne
| Funkcja | Opis |
|---------|------|
| `min(a, b, ...)` | Minimum |
| `max(a, b, ...)` | Maximum |
| `abs(x)` | Wartość bezwzględna |
| `sqrt(x)` | Pierwiastek kwadratowy |
| `sin(x)` | Sinus |
| `cos(x)` | Cosinus |
| `flr(x)` | Podłoga (zaokrąglenie w dół) |
| `ceil(x)` | Sufit (zaokrąglenie w górę) |
| `losuj()` | Losowa liczba 0-1 |
| `losuj(min, max)` | Losowa liczba całkowita z zakresu |
| `zaokraglij(x)` | Zaokrąglenie |
| `zaokraglij(x, n)` | Zaokrąglenie do n miejsc |

### Stringi
| Funkcja | Opis |
|---------|------|
| `dlugosc(s)` | Długość stringu/tablicy/słownika |
| `zawiera(s, pod)` | Czy zawiera podciąg |
| `zastep(s, stary, nowy)` | Zamień wszystkie wystąpienia |
| `dziel(s, sep)` | Podziel na tablicę |
| `laczenie(tab, sep)` | Połącz tablicę w string |
| `wielkie(s)` | Na wielkie litery |
| `male(s)` | Na małe litery |
| `przytnij(s)` | Usuń białe znaki z końców |
| `znajdz(s, pod)` | Znajdź pozycję podciągu |
| `konwert(typ, val)` | Konwersja typu |

### Tablice
| Funkcja | Opis |
|---------|------|
| `dodaj(tab, el)` | Dodaj element na koniec |
| `usun(tab, idx)` | Usuń element pod indeksem |
| `odwroc(tab)` | Odwróć kolejność |
| `sortuj(tab)` | Sortuj rosnąco |
| `suma(tab)` | Suma elementów |
| `srednia(tab)` | Średnia arytmetyczna |

### Systemowe
| Funkcja | Opis |
|---------|------|
| `czysc()` | Wyczyść konsolę |
| `czekaj(ms)` | Czekaj milisekundy |
| `zakoncz(kod)` | Zakończ program |
| `data()` | Aktualna data |
| `czas()` | Aktualny czas |

### Słowniki
| Funkcja | Opis |
|---------|------|
| `klucze(d)` | Lista kluczy słownika |
| `wartosci(d)` | Lista wartości słownika |

### Wejście/Wyjście
| Funkcja | Opis |
|---------|------|
| `pisz(x)` | Wypisz wartość |
| `pisz_kolorowo(x, kolor)` | Wypisz kolorowo |
| `czytaj()` | Wczytaj linię z klawiatury |

---

## Przykłady

### FizzBuzz
```
dla i w zakres(1, 100) {
    jesli i % 15 == 0 to {
        pisz "FizzBuzz"
    } inaczej jesli i % 3 == 0 to {
        pisz "Fizz"
    } inaczej jesli i % 5 == 0 to {
        pisz "Buzz"
    } inaczej {
        pisz i
    }
}
```

### Silnia rekurencyjna
```
funkcja silnia(n) {
    jesli n <= 1 to {
        zwroc 1
    }
    zwroc n * silnia(n - 1)
}

pisz silnia(10)
```

### Sortowanie bąbelkowe
```
funkcja sortuj_babelkowo(tab) {
    licz n = dlugosc(tab)
    dla i w zakres(0, n - 2) {
        dla j w zakres(0, n - i - 2) {
            jesli tab[j] > tab[j + 1] to {
                licz temp = tab[j]
                tab[j] = tab[j + 1]
                tab[j + 1] = temp
            }
        }
    }
    zwroc tab
}

tablica liczby = [5, 2, 8, 1, 9, 3]
pisz sortuj_babelkowo(liczby)
```

### Gra w zgadywanie
```
losuj(1, 100)
licz szukana = losuj(1, 100)
licz prob = 0

pisz "Zgadnij liczbe od 1 do 100!"

dopoki prawda {
    prob += 1
    pisz "Twoj typ:"
    licz typ = konwert("licz", czytaj())
    
    jesli typ == szukana to {
        pisz "Brawo! Zgadles za " + prob + " razem!"
        przerwij
    } inaczej jesli typ < szukana to {
        pisz "Za malo!"
    } inaczej {
        pisz "Za duzo!"
    }
}
```

### Słownik
```
slownik osoba = slownik(
    "imie" => "Jan",
    "wiek" => 25,
    "miasto" => "Warszawa"
)

pisz osoba["imie"]
pisz "Klucze:"
pisz klucze(osoba)
pisz "Wartosci:"
pisz wartosci(osoba)
```

### Kolorowy output
```
pisz_kolorowo("To jest czerwony tekst!", czerwony)
pisz_kolorowo("A to zielony!", zielony)
pisz_kolorowo("Niebieski tez moze byc", niebieski)
```
