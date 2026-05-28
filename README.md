# VEXLang

Język programowania z polskimi słowami kluczowymi i własnym edytorem.

```bash
# Uruchomienie pliku
python vexlang.py przyklady/fibonacci.vex

# Edytor
python editor.py

# REPL (tryb interaktywny)
python vexlang.py
```

## Składnia

| Przykład | Opis |
|---------|------|
| `licz x = 5` | Zmienna liczbowa |
| `tekst s = "hello"` | Zmienna tekstowa |
| `logiczna b = prawda` | Zmienna logiczna |
| `tablica t = [1, 2, 3]` | Lista |
| `jeśli x > 5 to { pisz "ok" }` | Warunek |
| `dopóki x > 0 to { ... }` | Pętla while |
| `dla i w zakres(1, 10) { ... }` | Pętla for |
| `funkcja foo(x) { zwróć x * 2 }` | Funkcja |
| `pisz "hello"` | Wypisz |
| `x = czytaj()` | Wczytaj |

## Wbudowane funkcje

- `dlugosc(lista)` – długość listy/tekstu
- `konwert("licz", "123")` – konwersja typu
- `losuj(1, 100)` – losowa liczba
- `zaokraglij(3.1415, 2)` – zaokrąglenie

## Instalacja

```bash
git clone https://github.com/wk12100lol-prog/vexlang.git
cd vexlang
python editor.py
```

## Licencja

MIT — v0idvex
