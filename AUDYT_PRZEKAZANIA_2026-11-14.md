# Audyt przekazania — 14 listopada 2026

## Cel i granice tej kontroli

Przegląd aktualnego repozytorium, wykonanie testów i buildu, porównanie działającego API z kodem oraz bezpośredni odczyt oficjalnych materiałów NASA Space Apps 2026. Użytkownik zadeklarował, że ma jeszcze około jeden dzień; nie podał lokalnego eventu ani godziny pitchingu. Nie wykonano w tym audycie napraw, restartu serwera użytkownika ani nowej pełnej walidacji astronomicznej. Repozytorium zmieniało się podczas odczytu; nowy agent musi ponownie sprawdzić stan.

## Aktualny stan

| Obszar | Dowód / status |
|---|---|
| Backend | Python 3.12, FastAPI, Astropy, Astroquery, Reproject, NumPy, SQLite/cache, proces roboczy; obecnie dodana zależność SEP. |
| Interfejs | React/TypeScript/Vite/Canvas; porównanie A/B, lupa, miganie, seria dat, ręczna trasa, karta podejrzenia. |
| Dane | Rzeczywiste zapytania IRSA, FITS, manifesty, reprojekcja i podglądy; obsługa braków i częściowych niepowodzeń. |
| Pasma | `SpectralExplorer.tsx`, suwak i odtwarzanie rzeczywistych obserwacji, lokalne długości fal, umowne kolory, pokrycie spektralne, przejście do czasu i pomiarów. |
| Pomiary | Eksploracyjna fotometria aperturowa, błędy losowe, punkty widmowe z datami, diagnostyka różnic; nie stanowią samodzielnie potwierdzenia zmienności. |
| Kontekst | Aladin, mapa pola, lokalny horyzont, Gaia/AllWISE. |
| Nowy kod IRSA | HiPS DR1, mapy CWAVE/CBAND i powierzchni piksela, lokalne dopasowanie ePSF, SEP, MOST, import referencyjnego widma. `IrsaWorkbench` jest obecnie importowany i renderowany w zakładce pomiarów. |
| Publiczne wdrożenie | W dotychczasowej dokumentacji nie potwierdzono publicznego backendu z trwałymi danymi. `localhost` nie realizuje publicznego dostępu dla jury. |

Nowe moduły: `backend/calibrated.py`, `irsa_resources.py`, `irsa_jobs.py`, `source_discovery.py`, `moving_objects.py`, `reference_spectra.py` oraz `frontend/src/IrsaWorkbench.tsx`. Ich importy w bieżącym środowisku przeszły. To dowód importowalności, nie poprawności naukowej ani działania zewnętrznych usług.

## Sprawdzone w tym audycie

- Frontend: `npm.cmd test` — 22 testy przeszły.
- Frontend: `npm.cmd run build` — TypeScript/Vite zakończyły się poprawnie. Pozostaje ostrzeżenie o dużym chunku Aladin.
- Backend: 54 testy pytest przeszły. Uruchomiono je poza ograniczeniami sandboxu Windows, z TEMP/TMP w lokalnym `.cache` i osobnym katalogiem testowym.
- W odczytanych testach nie znaleziono bezpośrednich testów nowych modułów kalibracji, ePSF, HiPS, MOST, SEP i referencji. Powyższy zielony zestaw nie dowodzi ich poprawności.
- Działający serwer `http://127.0.0.1:8000/openapi.json` NIE zawierał poniższych tras obecnych w aktualnym `backend/main.py`:
  - `/api/irsa/hips`
  - `/api/analyses/{id}/calibrated`
  - `/api/analyses/{id}/discovery`
  - `/api/irsa/most`
  - `/api/analyses/{id}/reference`

To potwierdzona rozbieżność działającego API i kodu. Prawdopodobnym wyjaśnieniem jest uruchomiony starszy proces, lecz przed naprawą należy ustalić proces, katalog roboczy i sposób startu. Nie zmieniano ani nie zatrzymywano serwera użytkownika w tym audycie.

## Dane demonstracyjne i ograniczenia

Przykład lokalny: `http://127.0.0.1:8000/?analysis=7e67f96510f848eebe9407d07022d484&view=spectrum`.

Przygotowano 10 z 12 obserwacji, sześć detektorów, około 0,744–4,876 µm w centrum, około 0,27 dnia. Dwa pobrania zwróciły HTTP 503 i 422. Metadane: `data/spectral_demo.json`. Zrzut poprzedniej weryfikacji: `data/spectral-preview.jpg`.

Raporty `RAPORT_DANYCH.md` i `WALIDACJA_PLANU_V4.md` dokumentują dostępność pięciu pól i ograniczenia próbkowanych par. Nie potwierdzają identyfikacji wszystkich pięciu źródeł ani wykrycia ich ruchu/zmienności. Nie można ekstrapolować wyników pojedynczych par na całe archiwum.

Starsze twierdzenia o braku mapy kanałów lub całkowitym braku kalibracji trzeba zestawić z nowym kodem. Obecność nowej implementacji nie oznacza zakończonej walidacji. `START_TUTAJ.md` i `OCENA_ZGODNOSCI_Z_WYZWANIEM.md` zawierają starsze opisy zakresu.

## Zweryfikowane wymagania wyzwania

Źródło: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/ — bezpośredni odczyt zakładki Details w przeglądarce 14 listopada 2026. Narzędzie wyszukiwania zwracało 502; odczyt przeglądarkowy powiódł się.

Wymagany rdzeń to publiczna aplikacja WWW: RA/Dec → rzeczywiste obrazy SPHEREx wybranego pola → seria w czasie ułatwiająca zauważenie ruchu. Należy przetestować Barnard’s Star, Epsilon Indi B, WISE 0855, RW Aurigae i R Draconis.

Zastosowanie pasm, składanie/różnice, wybór FOV, Gaia/WISE, współrzędne w URL, flagi i narzędzia astronomiczne są propozycjami rozszerzeń. Pełna mapa wszystkich kanałów nie jest warunkiem podstawowym. Rozszerzenia mają wspierać rdzeń.

## Oficjalne ocenianie i zgłoszenie 2026

Źródła, oba datowane 13 listopada 2026:

- https://www.spaceappschallenge.org/resources/judging-awards-guide/
- https://www.spaceappschallenge.org/resources/project-submission-guide/

Przewodnik potwierdza pięć kryteriów, każde w skali 1–5: Impact, Creativity, Validity, Relevance, Presentation. Dotyczą wpływu, oryginalności, poprawności i wykonalności wraz z użytecznością, zgodności z wyzwaniem i istotnego wykorzystania danych NASA oraz jasnego przekazu. Nie ustalono dodatkowych wag ani lokalnej punktacji.

Zgłoszenie: publiczne linki, angielskie materiały, demo do 30 sekund lub do 7 slajdów, źródło NASA, referencje i ujawnienie AI. Film obcojęzyczny wymaga angielskich napisów. Trzeba użyć „Submit for Judging”. Termin: 15 listopada 2026, 23:59 w strefie eventu; lokalny pitching może być wcześniej.

SI/AI może wspierać realizację, lecz według przewodnika nie powinno zastępować zespołu w wymyślaniu pierwotnej idei. Trzeba rzetelnie oznaczać jego wkład w kod, dane i media; wygenerowane obrazy/filmy wymagają widocznego oznaczenia.

Kategorie warte analizy dla istniejącego projektu: Best Use of Data oraz Best Use of Science. To rekomendacja strategiczna, nie obietnica nominacji. Nie należy zmieniać projektu wyłącznie dla listy nagród.

## Materiał dowodowy

Snapshoty oficjalnych stron zapisano lokalnie, do ponownego odczytu przez agenta:

- `data/audit/nasa-2026-judging-snapshot.txt`
- `data/audit/nasa-2026-submission-snapshot.txt`
- `data/audit/nasa-2026-challenge-snapshot.txt`

Nie wysyłano zgłoszenia ani wiadomości do organizatorów. Audyt nie gwarantuje punktacji. Wniosek: największa wartość następnej doby to zsynchronizowanie działającej aplikacji z kodem, domknięcie pięciu testów obiektów i publicznego przebiegu, wykazanie jednego użytecznego wyróżnika i przygotowanie mocnego zgłoszenia.
