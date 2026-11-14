# Rzeczywisty audyt danych — 14 listopada 2026

**Raport historyczny, skorygowany w finalizacji:** centra Epsilon Indi B i R Draconis były niepoprawne, a pozycje nie uwzględniały ruchu własnego. Poniższych liczb nie traktować jako potwierdzonych testów właściwych celów. Aktualne próby i źródła: [WYNIKI_5_OBIEKTOW.md](WYNIKI_5_OBIEKTOW.md).

Wykonano zapytania SIA do IRSA, kolekcja `spherex_dr1`, promień wyszukiwania 2 minuty łuku wokół pozycji startowych. Surowe odpowiedzi: `data/audit/*.ecsv`; podsumowanie: `data/audit/coverage.json`. Te pliki są lokalnym cache i nie trafiają do repozytorium.

| Pole wokół obiektu | Rekordy SIA | Pierwsza obserwacja UTC | Ostatnia obserwacja UTC |
|---|---:|---|---|
| Barnard's Star | 252 | 2025-08-15 | 2026-05-05 |
| Epsilon Indi B | 390 | 2025-04-24 | 2026-05-04 |
| WISE 0855 | 270 | 2025-05-05 | 2026-05-14 |
| RW Aurigae | 227 | 2025-09-01 | 2026-03-12 |
| R Draconis | 449 | 2025-05-16 | 2026-05-13 |

## Co potwierdzono

- Archiwum odpowiada i ma obrazy przecinające wszystkie pięć pól.
- Odczytano rzeczywiste FITS IMAGE, FLAGS i WCS-WAVE. Wykonano reprojekcję i utworzono podglądy oraz manifesty.
- OBSID może być wspólny dla różnych detektorów; produkty deduplikujemy po URL, nie po samym OBSID.
- Archiwum okresowo zwraca HTTP 503 (Server busy). Pobieranie ma trzy próby, a pominięte produkty są jawnie zapisane.

## Czego ten audyt nie potwierdza

Liczby oznaczają rekordy obrazów pola, nie liczbę detekcji obiektu ani niezależnych epok. Różne detektory mogą obserwować równocześnie. Nie wykonano propagacji pozycji katalogowych ani niezależnej identyfikacji źródeł. Pokrycie pola nie dowodzi wykrywalnego ruchu lub zmienności. Końcowy raport pięciu obiektów wymaga jeszcze porównania zgodnych pasm, kontroli lokalnego pokrycia, identyfikacji źródeł i oceny wyniku.

## Lokalny przykład obrazowy

Analiza `38563b10fdeb4cacbd8c19872377c702`: 10 udanych klatek, 2 nieudanych pobrań. Link: `http://127.0.0.1:8000/?analysis=38563b10fdeb4cacbd8c19872377c702`.

Jest to przykład działania pipeline i interfejsu. Nie stanowi potwierdzenia wykrycia ruchu Barnard’s Star. Zgodność pasm należy odczytać w miejscu źródła.
