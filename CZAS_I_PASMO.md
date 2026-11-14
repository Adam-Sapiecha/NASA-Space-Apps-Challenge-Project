# Wspólny podgląd czasu i pasma

Panel „Czas i pasmo” zastępuje osobne podglądy ruchu oraz kanałów. Wybrana para A/B działa w widoku obok siebie, miganiu, lupie i szkicu ruchu. Animację można prowadzić według dat albo długości fali.

## Wybór obserwacji

- **Automatycznie** otwiera rekomendowaną parę po lokalnej kontroli. W tej samej klasie poprawności apertury dobór preferuje największy odstęp czasu w sprawdzonej próbce.
- **Ruch w czasie** dobiera zgodne lokalne pasmo aktualnego obrazu B, preferując znaną poprawność apertury i długą bazę czasową. Gdy drugiej znanej epoki nie ma, panel to zgłasza.
- **Różne pasma** proponuje obserwacje różnych detektorów możliwie blisko daty B. Rzeczywiste długości fal są sprawdzane po pobraniu FITS.
- **Dowolne A/B** udostępnia wszystkie obserwacje z wyników wyszukiwania danego pola. Każde A można zestawić z każdym B, także A z samym sobą w różnych ustawieniach wyświetlania.

„Pasmo dla obu zdjęć” zmienia oba obrazy, zachowując wskazane daty, jeśli istnieją w danym paśmie, albo proponując najbliższe dostępne obserwacje. Przed pobraniem widać ich rzeczywiste daty. Nie tworzymy brakujących kombinacji daty i pasma. Gwiazdka przy zakresie oznacza zakres detektora; dokładna lokalna długość fali może być jeszcze nieznana.

Gotowe zdjęcia otwierają się od razu. Inne wymagają przycisku „Przygotuj i otwórz zestaw”. Pobieramy brakujące dane, wykorzystując już przygotowane obrazy. Dodanie pasma zachowuje powiększenie oraz wskazany punkt nieba; punkt jest ponownie próbkowany dla rozszerzonego zestawu. Błąd pobrania zachowuje poprzednią parę i pokazuje przyczynę.

## Wyświetlanie i domyślne ustawienia

Ustawienia przy obrazie obejmują standardową jasność, uwydatnianie słabych źródeł lub pełny zakres, wszystkie dostępne piksele albo piksele po kontroli jakości, maskę flag oraz umowny kolor długości fali. Domyślnie skala jasności jest wspólna, kolor i maska wyłączone, a całe pole widoczne. Wspólna skala obejmuje aktualną parę lub odtwarzaną serię; inne przygotowane pasma nie zmieniają jej kontrastu.

Opcja „Osobne ustawienia obrazu A i B” pozwala zmieniać każdy obraz niezależnie. Niezależne skale mogą zmienić wizualne wrażenie różnicy. Pomiary nadal korzystają z danych naukowych i ich masek. Umowne kolory nie przedstawiają naturalnego koloru nieba.

„Najlepszy zestaw i ustawienia” przywraca rekomendowaną parę, wspólną standardową skalę, całe pole, widok obok siebie i odtwarzanie według czasu. „Kopiuj link” zapisuje identyfikatory A/B, oś odtwarzania, ustawienia wspólne i osobne, powiększenie oraz wskazany punkt. Lokalny link wymaga dostępu do tej instancji aplikacji i zachowanego katalogu `data/`.

## Dane i kontrola

Endpoint `POST /api/analyses/{id}/comparison` przygotowuje nową, niezmienną wersję zestawu. Przyjmuje tylko identyfikatory obserwacji z tego samego wyszukiwania. Oryginalna analiza i jej raport doboru pozostają zachowane. Ręczna para ma własne oznaczenie: kontrola rekomendowanego zestawu nie jest dowodem poprawności nowej pary.

Pula gotowych obrazów mieści do 48 klatek, zachowując rekomendowane, bieżące i nowo wybrane. To ograniczenie pamięci podglądu; każdą obserwację z katalogu nadal można wybrać i przygotować. Nie pobieramy wszystkich par ani całego archiwum z góry. Różne pasma i różne daty nie stanowią jednoczesnego widma; samo zestawienie obrazów nie potwierdza ruchu ani zmienności źródła.

Weryfikacja tej zmiany:

- 136 testów backendu oraz 43 testy frontendu; produkcyjny build frontendu.
- Rzeczywiste API dla pola Epsilon Indi B: katalog 368 obserwacji, dodanie trzeciego obrazu z innego detektora, zachowanie geometrii i oryginalnej analizy, osobne podglądy A/B oraz odrzucenie obcego identyfikatora.
- Przeglądarka: dodanie pasma z zachowaniem powiększenia i punktu, niezależne style, odtworzenie linku, porównanie tej samej klatki w dwóch stylach i powrót do ustawień domyślnych.

Powtórzenie kontroli na lokalnych zapisanych danych:

```powershell
.\.venv\Scripts\python.exe scripts/smoke_comparison_workspace.py
cd frontend
npm.cmd test
npm.cmd run build
```

Skrypt zapisuje wynik w `data/audit/combined-workspace.json`. Nowa obserwacja może wymagać dostępu do IRSA.
