# Audyt i naprawy — finalizacja 14 listopada 2026

## Wynik i granice

Pracowano na istniejącym kodzie React/FastAPI, z zachowaniem staged, unstaged, untracked i całego cache użytkownika. Nie wykonano resetu ani restartu koncepcji. Zespół nie nadał nazwy projektowi. Zrealizowano naprawy, nowe próby rzeczywistych danych, przenośny eksport dowodów i angielskie demo. **Brak publicznego backendu wyszukującego nowe RA/Dec.** Sam replay nie spełnia tego wymagania.

Aktualne materiały: [wyniki pięciu obiektów](WYNIKI_5_OBIEKTOW.md), [plan doby i wybór wyróżnika](PLAN_24H.md), [pakiet EN](PAKIET_ZGLOSZENIA_EN.md), [wdrożenie i seed](DEPLOYMENT.md). Użytkownik wybrał pozostawienie pakietu lokalnie. **Nie opublikowano dema.** Przed próbą wysłania zarejestrowano prywatny projekt Sites, bez wdrożenia; nie jest to publiczny dostęp.

## Wymagania i oficjalne źródła

Przeczytano audyt przekazania, instrukcję finalizacji, README, START_TUTAJ, STATUS_IMPLEMENTACJI, koncepcję z sekcją 21, ocenę zgodności, raporty danych, design i źródła zasobów. Rzeczywisty kod, testy i konfigurację zestawiono z tymi opisami. Nie uznano dokumentacji za dowód wykonania.

Ponowny odczyt web stron wyzwania, judging, submission i FAQ zwracał 502/timeout. Wykorzystano datowane snapshoty `data/audit/nasa-2026-*-snapshot.txt` z bezpośredniego odczytu 14 listopada 2026. FAQ dodatkowo odczytano w przeglądarce: strona z 13 listopada potwierdza event 14–15 listopada 2026 i ujawnianie użycia SI. Dokumentację IRSA odczytano bezpośrednio; DR1 jest rzeczywistym wydaniem z listopada 2026.

Oficjalny rdzeń: publiczny web, RA/Dec, prawdziwe obrazy SPHEREx i seria dat wspierająca zauważenie ruchu; testy Barnard’s Star, Epsilon Indi B, WISE 0855, RW Aurigae i R Draconis. 102 pasma, widma, różnice, składanie, FOV i kontekst katalogowy są opcjonalnymi rozszerzeniami. Potwierdzono pięć kryteriów, każde 1–5: **Impact, Creativity, Validity, Relevance, Presentation**. Nie dodano wag ani gwarancji punktacji.

Przewodnik zgłoszeń wymaga publicznych linków, materiałów angielskich, źródeł i ujawnienia SI/AI oraz filmu ≤30 s albo prezentacji ≤7 slajdów. Termin podany w przewodniku to 15 listopada 2026, 23:59 w strefie eventu; lokalne prezentacje mogą być wcześniej. Nie wysłano zgłoszenia ani wiadomości i nie zaakceptowano warunków za zespół.

## Regresje, przyczyny i poprawki

| Problem / odtworzenie | Przyczyna i poprawka | Dowód ponownej próby |
|---|---|---|
| Wybrać Epsilon Indi B lub R Draconis w dawnym presecie | Wpisane centra nie odpowiadały identyfikatorom SIMBAD: 330,841667° zamiast ok. 331,044147° i 249,2117° zamiast ok. 248,167611° w epoce odniesienia. Dodano wspólny katalog `backend/targets.json`, źródła, epoki i przewidywania J2026.0 dla UI i skryptów | Zapytanie SIMBAD Harvard i tabela Kirkpatrick/VizieR IDIA; test regresji tożsamości; nowe pięć zapytań i 22 obrazy poprawionych pól |
| Pomiary przy starym centrum szybko poruszającego się obiektu | Stały punkt startowy nie śledził obiektu; stara pozycja Barnard’s Star jest ponad 4′ od przewidywania 2026. Nowy audyt mierzy przy osobnej pozycji dla każdego MJD | Każda próbka przechowuje przewidywane RA/Dec i współrzędne obrazu. Nie przedstawia się tego jako pełnej astrometrii |
| Jasny sąsiad lub artefakt wpływa na aperturę i tło | Rozszerzono maskę pomiarową o udokumentowane flagi artefaktów. SOURCE jest dozwolone w aperturze celu, ale wykluczane z tła; za mało czystego tła daje odmowę. Klucz nowej metody `native-aperture-2` nie nadpisuje starych pomiarów | Kontrolowany test źródła w pierścieniu i prawdziwe flagi: Barnard/RW Aur/R Dra mają m.in. OVERFLOW/SUR_ERROR/BLOOM, Epsilon Indi B ma silnie zamaskowany pierścień. Ważne apertury D6 nadal działają |
| Utrata procesu zostawia zadanie w stanie running | Future procesu nie miał obsługi błędu wykonawcy. Dodano callback ustawiający failed; niedostępny wykonawca daje HTTP 503 i instrukcję restartu | Test przerwania Future i błędu submit. Rzeczywista awaria kolejki Windows także dała jawne failed |
| API procesu może różnić się od plików na dysku | Health zawiera SHA-256 załadowanych modułów i `code_changed`; fingerprint jest porównywany przez smoke. Ustalono proces, port i polecenie; restartowano tylko zidentyfikowaną instancję po zakończeniu prac | Początkowy serwer miał już pięć tras IRSA brakujących w starszym audycie. Weryfikacja OpenAPI i fingerprintu jest zapisywana w `data/audit/` |
| Proxy zwraca HTML 503 lub połączenie zanika | `response.json()` pokazywało błąd parsera. Dodano komunikaty z HTTP i możliwością ponowienia; zachowano szczegóły 422 | Dwa testy transportu frontendu, w tym HTML 503 i rzeczywisty typ błędu fetch |
| Stary pomiar może powrócić po zmianie punktu | Przywracanie pomiaru z URL nie weryfikowało punktu i mogło wygrać wyścig żądań. Dodano kontrolę analizy, punktu, promienia i generacji; reset wyników IRSA przy zmianie kontekstu | Przegląd ścieżki i kontrola UI na rzeczywistym punkcie; nie wykonano testu wszystkich możliwych opóźnień sieci |
| Strona mapy rozszerza się przy 390 px | Podpowiedź Aladin miała ok. 422 px. Ograniczono szerokość i zawijanie | Przed poprawką scrollWidth 441 px przy viewport 390; po załadowaniu poprawionej mapy 375 px, bez poziomego przepełnienia dokumentu |
| Widok ręcznej trasy rozszerza stronę telefonu | Późniejsza reguła CSS przywracała wiersz timeline, a podpis miał nowrap. Przywrócono układ kolumny i zawijanie na małym ekranie | Przed poprawką scrollWidth 411 przy 390; po buildzie i odtworzeniu dwóch kotwic z linku: 375 przy 390 |

W jednej instancji uruchomionej przez pomocniczy `Start-Process` kolejka Windows zgłosiła `WinError 6` po pierwszym zadaniu. Zarejestrowano błędy i uruchomiono serwer w utrzymywanej sesji. Następnie trzy różne zadania i kolejne zadania z UI zakończyły się poprawnie. To potwierdza odzyskanie działania w tej próbie, nie dowodzi usunięcia każdej możliwej przyczyny awarii Windows. Nie zatrzymywano niepowiązanego serwera na porcie 8001.

## Stan: wymaganie → kod → API → UI → test → rzeczywiste dane

| Zakres | Implementacja i endpoint | UI / wykonanie | Test i dane | Granica |
|---|---|---|---|---|
| Współrzędne i archiwum | `archive.py`, `/api/search`, `/api/field` | Formularz i wybór obiektu | Pięć świeżych zapytań liczbowych oraz prawdziwe zapytanie godzinowe WISE: 280 rekordów; 422 i niedostępność w testach | Pokrycie pola nie jest detekcją; brak żywego przykładu pustej odpowiedzi w pełnym DR1 |
| Wspólne obrazy i czas | `science.py`, analizy/klatki/sample, `Viewer.tsx` | Obejrzano prawdziwe rastry, klawiaturowy punkt, serię play/pause, A/B i ręczną trasę | Testy reprojekcji, maskowania, jednostek, częściowego sukcesu i ponowienia; zapisane FITS | Obraz porównawczy jest jakościowy; PSF między epokami nie dopasowano |
| Pasma | `spectral.ts`, `SpectralExplorer.tsx` | Odtwarzanie i zatrzymanie pasm; osobna informacja, że to nie czas | Testy luk bez fallbacku do centrum i pary zakotwiczonej w paśmie; dziesięć prawdziwych klatek z sześciu detektorów | Nie jest to jednoczesne ani pełne widmo 102 kanałów |
| Punkt i różnica jasności | `measurements.py`, `change_diagnostics.py` | Wybrano punkt klawiaturą, uruchomiono diagnostykę i zapisano kartę | Rzeczywista stała pozycja: A−B = −0,19313 ± 0,24261 mJy (błąd losowy), 161,901 dni, lokalne pasma ok. 4,41782/4,42378 µm | Brak potwierdzenia zmienności; stała pozycja nie podąża za ruchem |
| Karta i odtworzenie | `ObservationCard.tsx`, `/api/notes`, `evidence.py` | Zapis, link, odświeżenie i przywrócenie tekstu/punktu; eksport HTML/JSON | Test braku podmiany brakującej λ, pochodzenia, zewnętrznych zasobów i bezpiecznego tekstu HTML; rzeczywista karta `a6971713a10c44bf8ca7045c5c748759` | Interpretacja pochodzi od użytkownika; karta nie orzeka o odkryciu |
| Kalibracje i ePSF | `calibrated.py`, `/calibrated` i raporty kolejki | Kliknięto pomiar; obejrzano cztery wyniki i jedno odrzucenie w tabeli | DR1 D6, pipeline źródłowy 7.0.5, CWAVE/CBAND `cal-swcs-v5-2026-191`, powierzchnia `cal-sapm-v3-2026-191`; SHA w raporcie. χ²/dof ok. 1,05–1,31 | Brak porównania z rzeczywistym eksportem Tractor; liczba χ² nie jest pełną walidacją modelu |
| SEP | `source_discovery.py`, `/discovery` | Kliknięto ekstrakcję, wyświetlono rzeczywisty wynik | Smoke: 4 kandydatów w pierwszym obrazie; UI: 3 w wybranej listopadowej ekspozycji; test artefaktu | Kandydaci nie są identyfikacją celu ani wykrytym ruchem |
| MOST | `moving_objects.py`, `/api/irsa/most` | Formularz jest podłączony; test żywego API | 160 przecięć dla 3I, 1–20.08.2025; test pustego wyniku i limitu dat | Nie sprawdzono w UI całego przebiegu MOST w tej sesji; nie szuka nieznanej Planet Nine |
| Import referencji | `reference_spectra.py`, `/reference` | Podłączony import pliku i instrukcja IRSA | Kontrolowane CSV/VOTable, jednostki, odrzucenie niezgodnych ekspozycji i XML zewnętrznego | **Brak prawdziwego dopasowanego eksportu IRSA. Integracja nie jest naukowo zakończona** |
| Mapa HiPS i kontekst | `SkyContext.tsx`, proxy HiPS | Obejrzano mapę WebGL i zmianę AllWISE/SPHEREx, kanał D6 | 102 metadane kanałów, puste 50/51 odrzucone, prawdziwe PNG kafelka i Allsky | Mapa wielodatowa, nie czas; pojedynczy błąd logowania Aladin w konsoli nie blokował widocznej mapy |
| Gaia / horyzont | Istniejące `catalogs.py`, `orientation.py` | Kontrolki i kod są podłączone | Istniejące testy propagacji, luster i niezależnego wzoru horyzontu przeszły | W tej finalizacji nie wykonano pełnego nowego scenariusza Gaia/geolokalizacji w UI |
| Publiczny dostęp | Docker + Caddy + seed i smoke | Lokalna aplikacja oraz replay EN | Pakiet danych i kontrola odtworzenia; stan Sites oddzielnie | **Brak publicznego backendu i próby na drugim fizycznym urządzeniu** |

## Rzeczywiste dane i niezależna kontrola

Nowy audyt przygotował **22/25 produktów**: Barnard 4/4, Epsilon Indi B 6/6, WISE 0855 5/7, RW Aur 4/4 i R Dra 3/4. Błędy trzech pobrań HTTP 503 zachowano. Cztery apertury WISE spełniły warunki, jedna para przeszła heurystykę pasm. Pozostałe odmowy wynikają z rzeczywistych ograniczeń produktu i metody; nie wymuszono dodatnich wyników. Pełny wynik i przewidywania dla każdej ekspozycji: WYNIKI_5_OBIEKTOW.md.

Photutils 3.1.1 zainstalowano wyłącznie w `.cache/validation-libs`, bez zmiany produkcyjnego stosu. Niezależnie obliczono 30 apertur na natywnych obrazach, również w pozycjach kontrolnych poza przewidywanym celem. Mediana |różnicy| = **0,01580 mJy**, maksimum **0,10756 mJy**, najwyżej **0,4647** lokalnego formalnego błędu losowego w tej próbce. Maski lokalnego przybliżenia koła Photutils różniły się czasem o piksel od koła sferycznego; wynik nie jest identycznością algorytmów ani potwierdzeniem kalibracji źródła.

Nie sklasyfikowano niezależnie kontrolnych źródeł jako stałych ani pól jako astrofizycznie pustych. Nie uzyskano porównywalnej trzeciej epoki do niezależnego potwierdzenia ruchu. Nie wykazano poprawy wykrywalności. Dla pojedynczej pary usunięcie ekspozycji pozostawia jeden termin, co jawnie uniemożliwia taki test. Brakuje pełnych krzywych odpowiedzi spektralnej i propagacji systematyki. Zachowane są ograniczenia tła, PSF, centrowania i sąsiadów.

## Weryfikacja techniczna

- Początkowy aktualny zestaw: **67 testów backendu, 22 frontendu i build** przeszły. Stan był nowszy niż podany w audycie przekazania.
- Po naprawach: **71 testów backendu, 24 frontendu i produkcyjny build**. Końcowe polecenia: pytest z lokalnym TEMP/TMP i osobnym `--basetemp`, `npm.cmd test`, `npm.cmd run build`. Backend uruchamiano poza ograniczeniami sandboxu Windows; w sandboxie test TestClient wisiał i import DLL Photutils był blokowany. To ograniczenia środowiska, nie zaliczony test aplikacji.
- Ostrzeżenia: deprecjacja adaptera TestClient/httpx oraz duży opcjonalny chunk Aladin ok. 2,6 MB. Nie ukryto ich przez podniesienie progów.
- Live smoke IRSA zakończył trzy zadania na aktualnym serwerze: raport `data/smoke_irsa_api.json`.
- Kontrole wizualne wykonano przez CUA w Edge i przeglądarce aplikacji. Edge utracił podłączenie podczas pracy; dokończono w przeglądarce aplikacji. Nie zadeklarowano pełnego badania WCAG ani testu fizycznego telefonu.
- Angielski replay i karta są rzeczywistymi artefaktami, bez generowania obrazów AI. Demo pokazuje dwa przygotowane terminy i dziesięć obserwacji spektralnych; zawiera źródłowe daty, adresy i sumy kontrolne.
- Replay EN obejrzano przy 1440 px; play zmienia się w pause, a przejście do pasm zatrzymuje animację i pokazuje 1/10 obserwacji oraz jednoznaczny opis. Karta EN przy 390 px: obydwa osadzone obrazy załadowane, scrollWidth 375. Dwie kotwice ręcznej trasy i wycinki odtworzono z linku po przeładowaniu.
- Odtworzono seed w **osobnym** katalogu, sprawdzono **32 natywne FITS i ich SHA-256, sześć analiz oraz jedną demonstracyjną notatkę**. Następnie serwer na porcie 8002 przeszedł smoke odtworzenia; zatrzymano tylko tę instancję testową. Oryginalny cache i baza nie zostały zastąpione.
- Końcowy serwer na 8000 przeszedł `smoke_submission.py` po restarcie: zgodny fingerprint, notatka, ten sam punkt pomiaru, PNG, karta i demo EN. `public_url_verified: false`. Aktualny raport: `data/audit/submission-smoke.json`.

Końcowe odczyty po restarcie i odtworzeniu seed są zapisywane przez `scripts/smoke_submission.py`. Nie zaliczać samego przygotowania kontenera jako uruchomienia Dockera: Docker nie jest zainstalowany w tym środowisku.

## Macierz pięciu kryteriów — dowód, luka, działanie, wykazanie

To diagnoza projektu, bez przewidywania punktów jury.

| Kryterium oficjalne (1–5) | Obecny konkretny dowód | Największa luka | Działanie i sposób wykazania |
|---|---|---|---|
| **Impact** | Użytkownik przechodzi od RA/Dec do obrazów i zapisanej, odtwarzalnej oceny; obsługa klawiaturą i poprawki telefonu | Brak badania, czy początkujący pracują szybciej lub trafniej | Krótka obserwacja kilku realnych osób: czas do rozróżnienia pasma/czasu i zapisania poprawnie opisanej karty. Raportować fakty i liczebność, bez ekstrapolacji |
| **Creativity** | Istniejąca koncepcja łączy pasmo, czas, alternatywne wyjaśnienia i ręczną hipotezę w karcie z pochodzeniem | Standardowe blink/photometry już istnieją; brak dowodu absolutnej nowości | Pokazać pełną ścieżkę „podejrzenie → kontrola → nierozstrzygnięty wynik → dowody”, odróżnić ją od funkcji WiseView/IRSA bez przypisywania im nieprzeczytanych ograniczeń |
| **Validity** | Poprawione identyfikatory, jawne odmowy, niezależny Photutils, rzeczywiste flagi/kalibracje, regresje i fingerprint | Brak niezależnej astrometrii, kalibracji ePSF/Tractor i systematyki | Zachować status eksploracyjny, porównać rzeczywisty eksport IRSA przed wnioskami; udostępnić parametry i natywne hashe do kontroli |
| **Relevance** | RA/Dec, prawdziwe SPHEREx, czas, pięć poprawionych pól; NASA data stanowią rdzeń | Publiczny backend nie jest wdrożony; replay ma stały zestaw | Uruchomić przygotowany backend z trwałym seed, wykonać świeże wyszukiwanie i odtworzenie linku na drugim urządzeniu; zachować raport publicznego smoke |
| **Presentation** | EN replay, karta offline, krótki scenariusz i plan siedmiu slajdów, jawny wkład AI | Brak finalnego nagrania/decku z nazwą zespołu i publicznych linków; pełne UI jest polskie | Zespół wybiera nazwę i tożsamości, przygotowuje finalne ≤30 s/≤7 slajdów, publikuje EN materiały, sprawdza ich dostęp bez logowania |

Wdrożono najwyżej dwa ograniczone dodatki: przenośną kartę dowodową oraz EN replay odporny na awarię archiwum. Pozostałe zmiany to naprawy i walidacja istniejącego rdzenia. Nie dodano czatu AI, efektów 3D, nowego systemu ani niezwalidowanego rankingu odkryć. Porównanie z narzędziami i pięć rozważonych ulepszeń: PLAN_24H.md.

## Ślady wykonania i następny krok

Dowody lokalne: `data/audit/five-targets-final.json`, `five-flags.json`, `simbad-identities.json`, `wise0855-reference.tsv`, `independent-photutils.json`, `hourangle-search.json`, `runtime-final.json`, `submission-smoke.json`, `seed-restore.json`, `demo-seed.json`, `demo-evidence.json` oraz screenshoty UI. Część końcowych plików powstaje dopiero po zakończeniu odpowiedniego smoke; sprawdzać ich faktyczny wynik, nie samą obecność nazwy w tej liście.

Zespół musi jeszcze zapewnić publiczny backend, sprawdzić dostęp z drugiego urządzenia, zatwierdzić materiały i autorstwo, uzupełnić swoją nazwę oraz samodzielnie wysłać zgłoszenie. Publikację statycznego dema pozostawiono niewykonaną zgodnie z wyraźną decyzją użytkownika. Lokalny pakiet zawiera wszystko potrzebne do jego przeglądu. Automatyczna kontrola wcześniej odrzuciła wysłanie do konkretnego adresu Sites; nie obchodzono tej decyzji i po odmowie użytkownika nie ponawiano publikacji.
