# Start projektu — Planet X and SPHEREx

**Aktualny start po naprawach:** przeczytaj [AUDYT_NAPRAWY.md](AUDYT_NAPRAWY.md), [WYNIKI_5_OBIEKTOW.md](WYNIKI_5_OBIEKTOW.md) i [PLAN_24H.md](PLAN_24H.md). Angielskie materiały: [PAKIET_ZGLOSZENIA_EN.md](PAKIET_ZGLOSZENIA_EN.md). Wdrożenie: [DEPLOYMENT.md](DEPLOYMENT.md). Dane katalogowe i bieżące presety poprawiono; wcześniejsze raporty nie identyfikowały wszystkich obiektów. Projekt działa lokalnie; brak publicznego hosta.

Projekt **nie ma nazwy**. Budujemy aplikację łączącą **dobór pasm zwiększający widoczność źródeł z porównaniem ruchu i jasności w czasie**. Dodajemy do planu panel **„Gdzie patrzę?”**: mapę wybranego pola i jego kierunek względem Ziemi oraz lokalnego horyzontu. Istniejąca lupa czasu i ręczna hipoteza ruchu pozostają częścią narzędzia.

## Aktualny stan implementacji

Pierwszy lokalny prototyp został zaimplementowany. Uruchomienie: [README.md](README.md). Stan i ograniczenia: [STATUS_IMPLEMENTACJI.md](STATUS_IMPLEMENTACJI.md). Rzeczywisty audyt pięciu pól: [RAPORT_DANYCH.md](RAPORT_DANYCH.md).

Część planu 4.0 wdrożono lokalnie: orientację, eksploracyjne pomiary i widmo, ręczne pasma, jakościowe operacje oraz adapter Gaia/AllWISE. Szczegóły i ograniczenia w STATUS_IMPLEMENTACJI.md; nie wszystkie warunki odbioru są zakończone. Obowiązuje wersja 4.0 koncepcji, szczególnie sekcja 21: najpierw rdzeń czasowy i orientacja nieba, następnie pomiary z niepewnościami, ręczne pasma i asystent, później widmo i Gaia/WISE. Nie restartujemy istniejącej implementacji.

## Dokumenty

- [KONCEPCJA_I_PLAN_PROJEKTU.md](KONCEPCJA_I_PLAN_PROJEKTU.md) — pełny, samodzielny plan, stack, architektura, dane, etapy i warunki odbioru.
- [OCENA_ZGODNOSCI_Z_WYZWANIEM.md](OCENA_ZGODNOSCI_Z_WYZWANIEM.md) — wymagania zadania i dowody dla jurorów.
- Ten plik — skrót i polecenie do rozpoczęcia w nowym repozytorium.

Dokumenty zastępują wcześniejszy pomysł symulacji wysokości orbity. Kod aplikacji znajduje się w `backend/` oraz `frontend/`. Publiczne wdrożenie nie zostało jeszcze wykonane.

## Najważniejsze ustalenia

- Wyzwanie: [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/).
- Główny przebieg: RA/Dec → mapa kontekstu → obserwacje → źródło / hipoteza ruchu → dobór pasm → animacja zgodnych epok → udostępnienie analizy.
- Rozszerzenia: ręczny i automatyczny dobór pasm, składanie zgodnych obserwacji, różnice epok, widmo na żądanie i Gaia/WISE. Asystent wymaga najpierw wiarygodnych pomiarów z błędami; nie wystarczy operacja na PNG.
- „Gdzie patrzę?”: ramka pola na mapie nieba oraz schemat Ziemi i lokalnego horyzontu. Kierunek zależy od jawnego miejsca i czasu. To widok wybranego pola, nie śledzenie aktualnego ustawienia SPHEREx. Geolokalizacja jest opcjonalna.
- W animacji utrzymujemy te same efektywne pasma, wagi i skalę; brak zgodnych danych jest widoczny. Wynik asystenta oceniamy na niezależnych obserwacjach.
- Pierwsze testy: zgodność długości fal, flagi jakości, zależność od jednej ekspozycji. Potem geometria, tło, PSF i katalogi.
- Dane SPHEREx stanowią rdzeń. Gaia DR3 i WISE dostarczają kontekstu; NEOSSat/CADC są rozszerzeniem, jeśli mają rzeczywiste zastosowanie.
- Testujemy Barnard’s Star, Epsilon Indi B, WISE 0855, RW Aurigae i R Draconis. Nie zakładamy wykrywalnego efektu na każdym obiekcie.
- Stack aktualnej wersji: React, TypeScript, Vite, CSS, Canvas; Python, FastAPI, Pydantic, NumPy, Astropy, Astroquery, Reproject, Pillow; SQLite, cache plikowy i osobny proces obliczeniowy. Definicje Docker przygotowano, lecz kontenera jeszcze nie uruchomiono. Aladin Lite jest ładowany na żądanie z lokalnego buildu; wykresy są w SVG, pomiary apertury w NumPy/Astropy. Plotly i Photutils nie zostały dodane.
- Pomiary wykonujemy na danych naukowych. PNG/WebP służą do wyświetlania.
- Każda analiza ma manifest obserwacji i przetwarzania. Link do wyszukiwania i link do konkretnej analizy mają inne znaczenie.
- Syntetyczne sygnały są osobnym, wyraźnie oznaczonym trybem testowym.
- Projekt oceniamy przez wymagania wyzwania i dowody dla jury. Nie tworzymy strategii klientów ani sprzedaży.
- Robimy możliwie dużo, ale rozwijamy działające, sprawdzone etapy. Pierwszy przebieg nie jest z góry ustalonym końcem.

## Polecenie do wklejenia w nowym projekcie

> Przeczytaj KONCEPCJA_I_PLAN_PROJEKTU.md oraz OCENA_ZGODNOSCI_Z_WYZWANIEM.md i rozpocznij implementację publicznej aplikacji webowej dla Planet X and SPHEREx. Najpierw sprawdź instrukcje repozytorium, istniejący kod i środowisko. Nie nadawaj projektowi nazwy. Zacznij od etapu A: uruchom rzeczywiste zapytanie do archiwum SPHEREx, odczytaj dane, sprawdź dostępność pięciu obiektów wskazanych w zadaniu i zapisz raport. Następnie zbuduj pełny przebieg RA/Dec → obserwacje → wyrównana animacja → diagnostyka → udostępnienie. Użyj stacku z sekcji 8 i etapów z sekcji 12. Kontynuuj po pierwszym działającym przekroju, zachowując czas na integrację i walidację. Prowadź STATUS_IMPLEMENTACJI.md. Nie przedstawiaj planowanych funkcji ani niewykonanych testów jako gotowych. Nie fabrykuj obserwacji, wyników ani odkryć. Nie wracaj do poprzedniej koncepcji wysokości orbity.

## Pierwszy rezultat

Rzeczywiste zapytanie SPHEREx, odczyt FITS, raport dostępności danych pięciu obiektów i sprawdzone zależności. Dalej działająca publiczna ścieżka webowa, a następnie diagnostyka i pomiary. Jeśli dane nie pozwalają na ilościową analizę, zapisujemy ograniczenie i rozwijamy poprawny zakres, zamiast udawać detekcję.
