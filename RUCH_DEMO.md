# Rzeczywisty przykład ruchu — 3I/ATLAS

Pokaz: [otwórz lokalnie](http://127.0.0.1:8000/?motion=1). Na stronie głównej jest przycisk „Zobacz przykład ruchu”. Pełny warsztat pozostaje dostępny. Pokaz korzysta z przenośnych plików w `frontend/public/motion-demo/`, więc odtwarzanie nie wymaga ponownego połączenia z IRSA.

## Dane i kontrola

Źródło: [oficjalne obserwacje SPHEREx 3I/ATLAS](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/comet3iatlas/) i [IRSA MOST](https://irsa.ipac.caltech.edu/applications/MOST/). Pobrano produkty DR1 wskazane przez MOST, detektor D6:

| Obserwacja | Początek UTC 14.12.2025 | Pasmo w centrum pola |
| --- | --- | --- |
| `2025W50_2A_0741_2` | 11:00:48.129 | 4,482 µm |
| `2025W50_2A_0755_2` | 12:38:45.224 | 4,614 µm |

- Odstęp między środkami ekspozycji: 97,952 minuty.
- Przesunięcie według efemeryd MOST: 4,771 minuty łuku.
- Rozdzielenie lokalnych maksimów obrazu przy przewidywanych pozycjach: 46,819 piksela wspólnej siatki. Maksima są w odległości odpowiednio 1,015 i 1,092 piksela od pozycji przewidywanych.
- Pięć kontrolnych maksimów poza otoczeniem komety zmienia położenie o 0–2,236 piksela. To kontrola przeglądowa, bez dopasowania PSF lub precyzyjnego rozwiązania astrometrycznego.
- Wzrokowo sprawdzono jasne źródło w obu pozycjach. Pierwsza sprawdzona para z sierpnia miała zbyt słaby sygnał i nie jest używana w pokazie.

Oba obrazy mają identyczny WCS i pole 12′, 117 × 117 pikseli. Nie przesuwamy komety ani tła między klatkami. Dla czytelności odjęto osobną stałą medianę tła w każdej klatce, potem zastosowano jeden wspólny kontrast asinh. Można włączyć obrazy bez odejmowania tego poziomu. Znaczniki A/B są nieruchomymi pozycjami z efemeryd, które można ukryć.

To demonstracja ruchu znanej komety, a nie nowe odkrycie, automatyczna detekcja ani precyzyjny pomiar ruchu. Pasma i PSF różnią się; z tych klatek nie wyciągamy wniosku o zmienności jasności. Pliki FITS, adresy produktów, sumy SHA-256 i ograniczenia znajdują się w `frontend/public/motion-demo/evidence.json`.

## Odtworzenie i testy

`scripts/prepare_motion_demo.py --december` przygotowuje parę z zapisanej odpowiedzi MOST w `data/audit/3iatlas-december-most.json`. `scripts/export_motion_demo.py` eksportuje obrazy, wyrównane FITS i raport. Oryginalne pobrania FITS pozostają w `data/fits/`; pełny warsztat otwiera analizę `motion3iatlas20251214d6`. Skrypt pakowania dodaje ją do przenośnego pakietu danych.

Test: `.venv\Scripts\python.exe -m pytest backend/tests/test_motion_demo.py -q`. Sprawdza wspólną geometrię i pochodzenie plików, położenie jasnego źródła, przewagę jego przesunięcia nad zmianami punktów kontrolnych oraz zgodność wartości kątowej z efemerydami. Test nie oblicza prawdopodobieństwa detekcji.
