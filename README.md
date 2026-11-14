# SPHEREx — porównanie epok

**Nowe: obsługa EN/PL, prosty start z kometą i dobór lokalnych danych:** [zakres zmian i wyniki pięciu pól](WDROZENIE_EN_I_DOBORU_OBSERWACJI.md). Domyślnie pokazujemy 3I/ATLAS i prosty interfejs; pełne narzędzia otwiera przycisk. Automatyczne przygotowanie sprawdza lokalne pasma, flagi, aperturę i tło przed wyborem dat.

**Poprawki po audycie matematycznym:** [zakres, wyniki i weryfikacja](NAPRAWY_AUDYTU_MATEMATYCZNEGO.md). Spójne pozycje i eksport, mapy powierzchni pikseli, normalizacja ePSF i panel wrażliwości na centrowanie/tło. Archiwalne obliczenia są zachowane i oznaczone; do nowej analizy wymagają przeliczenia.

Analiza źródeł obejmuje kontekst Gaia/SIMBAD/AllWISE, diagnostykę artefaktów na FITS, dobór wag, modele widmowe i prognozowanie położenia. Panel znajduje się w dokładniejszej analizie, poniżej narzędzi IRSA. Trening ML ma kontrolę danych i walidacji; bez zweryfikowanych etykiet model pozostaje wyłączony. Obsługa i ograniczenia: [WDROZENIE_ANALIZY_ZRODEL.md](WDROZENIE_ANALIZY_ZRODEL.md).

**Finalizacja 14.11.2026:** [AUDYT_NAPRAWY.md](AUDYT_NAPRAWY.md), [wyniki pięciu obiektów](WYNIKI_5_OBIEKTOW.md), [plan pozostałej doby](PLAN_24H.md) i [pakiet zgłoszenia EN](PAKIET_ZGLOSZENIA_EN.md). Naprawiono błędne presety Epsilon Indi B / R Draconis, uzupełniono epoki, kontrolę fotometrii i eksport dowodów. **Publiczny hosting nadal nie istnieje.** Przygotowanie: [DEPLOYMENT.md](DEPLOYMENT.md).

Angielskie demo z prawdziwymi obrazami: [http://127.0.0.1:8000/demo/](http://127.0.0.1:8000/demo/). Samodzielne pliki `frontend/public/demo/index.html` i `evidence.html` działają offline. Replay nie zastępuje wyszukiwania nowych współrzędnych. [English overview](README_EN.md).

Lokalna aplikacja React + FastAPI do porównywania rzeczywistych obrazów SPHEREx. Projekt nie ma odrębnej nazwy. Zakres planu 4.0: lupa i szkic ruchu, mapa pola i lokalny horyzont, ręczny wybór pasm i wag, eksploracyjny pomiar apertury i widmo na żądanie, jakościowe składanie i różnica A−B oraz kontekst Gaia/AllWISE. Szczegółowy stan i brakujące etapy: [STATUS_IMPLEMENTACJI.md](STATUS_IMPLEMENTACJI.md).

Interfejs otwiera ekran pracy: wybór obiektu, porównanie obrazów i osobne zakładki mapy oraz pomiarów. Metody, dane i pomoc są rozwijane; gotowy lokalny przykład można otworzyć jednym przyciskiem. Kierunek i audyt: [DESIGN_AUDIT.md](DESIGN_AUDIT.md). Źródła, warunki wykorzystania i licencje: [ASSET_SOURCES.md](ASSET_SOURCES.md).

## Uruchomienie w Windows / PowerShell

W katalogu projektu:

```powershell
$env:UV_CACHE_DIR = Join-Path $PWD '.cache\uv'
uv sync --python 3.12
cd frontend
npm.cmd ci
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Otwórz http://127.0.0.1:8000. Backend podaje również zbudowany frontend. Dostęp do IRSA wymaga Internetu. Po restarcie zachowane analizy działają bez ponownego pobierania, jeśli folder `data/` pozostaje na dysku. Folder zawiera bazę SQLite, FITS, PNG i manifesty; nie jest dodawany do repozytorium.

Kolejne uruchomienia: `./start.ps1`. Skrypt buduje frontend i uruchamia backend w bieżącym oknie terminala. Zatrzymanie: Ctrl+C.

Do pracy nad interfejsem uruchom backend oraz, w drugim terminalu, `npm.cmd run dev` z katalogu `frontend`. Vite przekazuje `/api` do portu 8000.

## Obsługa

Po wyszukaniu aplikacja proponuje zestaw według dostępnych terminów i pokazuje zakres dat. Po pobraniu sprawdza zbliżenie pasm oraz pokrycie. „Seria dat” odtwarza kolejne obserwacje, a „Miganie A/B” porównuje wybraną parę. Filtr serii można wyłączyć do przeglądania wszystkich klatek; jego spełnienie nie potwierdza naukowej porównywalności.

Kliknij punkt, aby sprawdzić lokalne pasma i porównać jasność w stałej pozycji, albo wybierz „Sprawdź przesunięcie”, aby narysować ręczną hipotezę trasy. Kartę podejrzenia z notatką zapisujesz osobnym przyciskiem. Jej link odtwarza wybrane klatki, punkt lub trasę i podstawowe ustawienia. Pojedynczą udaną klatkę można obejrzeć bez animacji; błędne składniki można ponowić z zachowaniem gotowych wyników.

1. Wpisz RA/Dec lub użyj obiektu z zadania. Presety pochodzą z katalogów, z ruchem własnym do J2026.0, bez paralaksy i identyfikacji w obrazach. Własne współrzędne są używane bez propagacji. Dane i epoki: `backend/targets.json`.
2. Wyszukaj obserwacje. Wybierz detektor i 1–12 ekspozycji; animacja wymaga co najmniej dwóch terminów. Wybrany detektor nie oznacza tego samego pasma w miejscu źródła.
3. Przygotuj porównanie. Pobieranie FITS i reprojekcja odbywają się w osobnym procesie. Pierwsze pobranie może potrwać kilka minut. Błędy pojedynczych ekspozycji są zapisane; pojedynczą udaną klatkę można obejrzeć, a animacja wymaga co najmniej dwóch.
4. Przesuwaj lupę. Kliknięcie przypina pozycję i odczytuje lokalne długości fal oraz flagi. Shift + przeciągnięcie przesuwa powiększony obraz.
5. Przycisk „Dobierz zgodne epoki” wybiera parę o najdłuższej bazie czasowej spośród par z co najmniej 80% ważnego pokrycia, spełniających przeglądowy próg zgodności w centrum pola. Gdy brak takiej pary, aplikacja to zgłasza. To nie gwarantuje zgodności całego pola ani identycznych odpowiedzi spektralnych.
6. W „Szkicu ruchu” wskaż źródło na obrazie A, a następnie na obrazie B. Wycinki pokazują pozycje przewidywane z Twojej hipotezy w kolejnych terminach. Nie wykonują automatycznej detekcji.
7. „Udostępnij” kopiuje link do zapisanej analizy i wybranych epok, a także trasy, jeśli ją wskazano. Link do lokalnego serwera działa na tym komputerze; publiczne udostępnianie wymaga wdrożenia backendu i trwałego magazynu.

Skróty poza polami formularzy: **X** zamienia A/B, **L** przypina lupę, **Spacja** odtwarza epoki B, **←/→** zmienia epokę B.

### Kontrola wiarygodności różnicy

Pod zdjęciami znajduje się panel „Czy ta zmiana jest wiarygodna?”. Kliknij źródło, wybierz różne ekspozycje A i B, ustaw promień apertury i wybierz „Sprawdź różnicę A i B”. Panel korzysta z pomiarów natywnych FITS, pokazuje różnicę strumieni A−B z błędem losowym oraz kontrole lokalnych pasm, terminów, flag, otoczenia, tła i PSF. Zmiana punktu lub pary usuwa poprzedni raport. Raport można pobrać jako JSON z identyfikatorem pomiaru, analizy, parą ekspozycji i ustawieniami apertury.

Niezgodne pasma, brak ważnego pomiaru lub ten sam termin blokują interpretację zmienności. Zgodność pasm jest jedynie heurystyką przeglądową. Flagi i jasne piksele w pierścieniu tła są ostrzeżeniami. Tło, PSF, centrowanie i ruch pozostają niezweryfikowane; nawet duża różnica względem błędu losowego nie potwierdza rzeczywistej zmiany. Panel nie wyznacza prawdopodobieństwa odkrycia ani istotności statystycznej.

Po ustawieniu fokusu na obrazie strzałki przesuwają punkt, **Shift + strzałka** zwiększa krok, a **Enter** wybiera pozycję. Przycisk z dłonią włącza przesuwanie obrazu przeciągnięciem, również bez klawisza Shift.

## Sprawdzenie

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm.cmd run build
```

Rzeczywisty audyt archiwum (zapytania sieciowe):

```powershell
.\.venv\Scripts\python.exe scripts\probe_archive.py
.\.venv\Scripts\python.exe scripts\prepare_demo.py
```

Drugi skrypt pobiera maksymalnie dwanaście ekspozycji z pola wokół pozycji startowej Barnard’s Star. Nie zakłada widocznego ruchu ani zgodności ich pasm. Zapisuje `data/demo.json` z identyfikatorem i wynikami; taki przykład nie zastępuje testów wszystkich obiektów. Obecność obserwacji pola nie dowodzi detekcji wskazanego obiektu.

## Nowe narzędzia planu 4.0

- „Gdzie patrzę?” pokazuje ramkę WCS na mapie Aladin Lite i kontekst 2MASS/AllWISE z IRSA. Przycisk środka mapy tylko wypełnia RA/Dec; pobranie zaczyna się po „Wyszukaj pole”.
- Wpisz szerokość/długość miejsca lub świadomie wybierz geolokalizację. Czas domyślnie pochodzi z epoki B; można wybrać teraz lub własne UTC. Miejsce zostaje lokalne, chyba że zaznaczysz dołączenie go do linku. Azymut liczony jest od N przez E, bez refrakcji. Położenie nad horyzontem nie gwarantuje widoczności.
- Kliknij źródło w lupie, wybierz promień apertury i „Zmierz / pokaż widmo”. Wynik pochodzi z natywnych FITS i zawiera tło, wariancję, flagi i diagnostykę sąsiada. Wykres pokazuje dostępne punkty z różnych dat; nie jest jednoczesnym widmem. Przycisk asystenta jawnie odmawia rekomendacji przed pełną walidacją.
- Wybierz klatki, stałe wagi i maksymalne okno czasu, aby złożyć zgodne lokalne pasma. Wyłącz ekspozycję i przelicz, aby zbadać jej wpływ. „Podgląd różnicy A−B” zachowuje dodatnie i ujemne pozostałości. To narzędzia jakościowe, bez dopasowania PSF i wnioskowania statystycznego.
- Gaia DR3 jest nakładana na mapę dla epoki B, z prostą propagacją ruchu własnego. Brak ruchu własnego pozostawia źródło w epoce 2016.0. AllWISE to osobny podgląd historyczny, bez bezpośredniego odejmowania od SPHEREx.
- Link zapisuje produkt i pomiar; manifest produktu zawiera stałe ustawienia i źródłowe sumy kontrolne. Eksport pomiarów JSON i wyników FITS/PNG jest dostępny przy wynikach. Starsze analizy nadal działają; pomiar wymaga zachowanego natywnego FITS w cache.

Dodatkowe kontrole (pierwszy skrypt pobiera dane z IRSA):

```powershell
.\.venv\Scripts\python.exe scripts/validate_plan_v4.py
.\.venv\Scripts\python.exe scripts/smoke_plan_v4.py --base-url http://127.0.0.1:8000
```

Raport pięciu pól: [WALIDACJA_PLANU_V4.md](WALIDACJA_PLANU_V4.md). Skrypt smoke wymaga zapisanej analizy z wcześniejszego `scripts/smoke_api.py`.

## Ograniczenia

- Porównanie obrazów jest jakościowe: bez dopasowania PSF, pomiaru ruchu i pełnej propagacji kowariancji. Osobne pomiary apertury mają formalny błąd losowy z natywnej VARIANCE; nie są skalibrowanym całkowitym strumieniem źródła.
- Obrazy mają wspólny WCS TAN, północ u góry, interpolację biliniową i wspólną skalę asinh. Maski flag są przenoszone najbliższym sąsiadem. Brak ważnych danych jest przezroczysty, nie zerowy.
- Maskowane są wyłącznie jawnie wybrane nazwy flag, odczytane z nagłówka FITS. SOURCE i FULLSAMPLE nie są automatycznie odrzucane. Pozostałe flagi można sprawdzić w zaznaczonym punkcie.
- Nie odjęto modelu tła ZODI. Różnice tła, PSF i pasm mogą imitować zmianę jasności.
- Pasma w centrum są jedynie pomocą przy wyborze. Sprawdź lokalne pasma po kliknięciu źródła. Próg połowy węższego pasma to heurystyka przeglądowa, nie zwalidowany warunek równoważności naukowej.
- API nie ma kont, trwałej kolejki ani automatycznego czyszczenia cache. Przerwane zadania dostają stan błędu po restarcie. Uruchamiaj pojedynczy proces Uvicorn. Publiczny hosting wymaga osobnego przeglądu limitów, trwałości danych, HTTPS i obsługi ruchu.
- Nie przeprowadzono badania skuteczności ani walidacji automatycznego doboru wag. Pełna kontrola wizualna nowych paneli pozostaje do wykonania.

## Kontener

```powershell
docker compose up --build
```

Adres: http://127.0.0.1:8000. Dane pozostają w nazwanym woluminie. Definicję kontenera należy sprawdzić w działającym Dockerze; sam build frontendu nie weryfikuje kontenera.

## Pochodzenie danych i kodu

- Wymagania: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- Archiwum i aktualne wydania: https://irsa.ipac.caltech.edu/Missions/spherex.html
- SIA i FITS: https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/
- Parametry wycinków i odczyt spektralnego WCS: https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/

Adapter wykorzystuje udokumentowane interfejsy IRSA. Manifest zawiera identyfikatory produktów, źródłowe URL, daty, wersje i SHA-256 pobranego FITS. PNG to wyłącznie podgląd; endpoint `.fits` zwraca wyrównany obraz naukowy bez propagowanej wariancji.

This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.

Domyślny podgląd pokazuje wszystkie dostępne piksele i oznacza ostrzeżenia pomarańczowymi ramkami. Kreskowanie oznacza brak danych; nic nie jest uzupełniane. W szczegółach „Wygląd zdjęć i jakość” można przełączyć się na piksele po kontroli jakości lub wybrać pełny zakres jasności. Te opcje nie zmieniają danych pomiarowych.


## Przegląd pasm — animacja długości fali

Zakładka **Pasma** pokazuje przygotowane obserwacje posortowane według długości fali. Suwak, odtwarzanie z regulowanym tempem i opcjonalne umowne kolory działają na rzeczywistych podglądach. Pokrycie 0,75–5 µm ma osobne znaczniki; brakujących kanałów nie interpolujemy. Kliknięcie punktu zastępuje długości fal w centrum wartościami lokalnymi; nieznane wartości nie są zastępowane wartościami centralnymi. Dostępne są daty UTC, flagi, wspólna skala jasności i powiększenie.

Po wyszukaniu pola wybierz **Dobierz pasma z różnych detektorów**, a następnie **Przygotuj pasma**. Dobór wybiera do dwóch produktów z każdej z sześciu grup detektorów, preferując bliskie terminy. Zakresy detektorów nie gwarantują określonego zestawu lokalnych kanałów. Przycisk **Dobierz więcej pasm** w gotowej analizie przygotowuje ten wybór bez nowego zapytania archiwum.

**Sprawdź zmianę w czasie** szuka drugiej epoki o zbliżonym lokalnym paśmie, odnosząc ją do wybranej klatki. Gdy takiej epoki nie ma, aplikacja zgłasza brak; nie wybiera innego zakresu jako substytutu. **Widmo i pomiary punktu** otwiera istniejący panel pomiarów natywnych FITS. Link udostępnienia zachowuje zakładkę `view=spectrum`, identyfikator klatki `channel`, zaznaczony punkt i ustawienia skali.

Zapisany na tym komputerze przykład: [pole Barnard’s Star — pasma](http://127.0.0.1:8000/?analysis=7e67f96510f848eebe9407d07022d484&view=spectrum). Wymaga uruchomionego backendu i zachowanego `data/`. Przygotowano 10 z 12 klatek z sześciu detektorów; dwie próby pobrania zwróciły HTTP 503 i 422. Zakres długości fal w centrum wynosi około 0,744–4,876 µm, a odstęp między skrajnymi datami około 0,27 dnia. Skrót zapisano w `data/spectral_demo.json`. To demonstracja przeglądania danych, bez potwierdzenia identyfikacji obiektu.

Jest to przegląd wybranego pola, a nie pełna mapa całego nieba ani kompletne, jednoczesne widmo 102 kanałów. Długość fali zmienia się również w obrębie klatki; umowny kolor i etykieta dotyczą centrum lub zaznaczonego punktu. Odtwarzanie pasm nie przedstawia upływu czasu.

## Mapa i narzędzia IRSA

W **Gdzie patrzę?** dostępna jest oficjalna mapa SPHEREx DR1 HiPS: 102 kanały z pominięciem dwóch pustych warstw. Wybór długości fali zmienia mozaikę wielu terminów; nie jest animacją czasu. Kafelki PNG i podgląd całego nieba są pobierane przez ograniczony adapter backendu z oryginalnego drzewa IRSA. Mapa służy orientacji, a pomiary korzystają z natywnych FITS.

Po zaznaczeniu źródła otwórz **Dokładniejsza analiza → Kalibracje i narzędzia IRSA**:

- **Zmierz z kalibracją IRSA** pobiera mapy CWAVE/CBAND i powierzchni piksela dla wydania i detektora, wybiera lokalny ePSF z FITS i porównuje aperturę z dopasowaniem źródła oraz płaszczyzny tła. Tabela pokazuje błędy losowe i jakość dopasowania. Raport zachowuje wersje, URL i SHA-256. To lokalna metoda, wymagająca walidacji względem oficjalnej usługi; nie uruchamia IRSA Tractor. Nie pobiera pełnych krzywych transmisji filtrów.
- **Porównaj z oficjalną spektrofotometrią** pozwala pobrać współrzędne celu, otworzyć Data Explorer i wczytać jego eksport VOTable/XML lub CSV. Obliczenie po stronie IRSA uruchamia użytkownik. Dopasowanie wymaga zgodnych ekspozycji, detektorów, pozycji i wydania; niejednoznaczne pomiary są odrzucane. Sam format pliku nie poświadcza jego pochodzenia.
- **Znajdź kandydatów** wykonuje ekstrakcję SEP z tłem, wariancją, maskami i rozdzielaniem sąsiadów. Kliknięcie kandydata otwiera zdjęcie i zaznacza jego pozycję. Jest to niezależny adapter przebiegu notebooka IRSA; nie wykonuje całego oryginalnego pakietu ani zewnętrznego SExtractor. Kandydaci nie oznaczają wykrycia ruchu.
- **MOST** wyszukuje obserwacje znanego obiektu w przedziale do 31 dni. Przy niejednoznacznej nazwie można podać NAIF z sufiksem `:NID`. Wynik dotyczy przewidywanego przecięcia pola, nie potwierdzonej detekcji źródła.

Wyniki długich operacji powstają w dotychczasowej kolejce z postępem, są zapisywane lokalnie i można je pobrać jako JSON. Kalibracje pozostają w `data/calibrations/`, a raporty w `data/irsa/`. Link z `irsa` odtwarza raport kalibracji, kandydatów lub MOST. Zmiana punktu nie przypisuje starego pomiaru nowej pozycji.

Test uruchomionej aplikacji na rzeczywistych danych: `.venv\Scripts\python.exe scripts/smoke_irsa.py`. Wymaga dostępu do IRSA; nie zleca zewnętrznej spektrofotometrii. Ostatni wynik lokalny: `data/smoke_irsa_api.json`.

Dokumentacja źródłowa: [HiPS SPHEREx](https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube/properties), [produkty kalibracyjne](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/), [modele PSF](https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/), [ekstrakcja źródeł](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/), [spektrofotometria](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html), [MOST](https://docs.astropy.org/projects/astroquery/en/latest/ipac/irsa/most.html).


## Pełny warsztat na stronie głównej

Adres `/` otwiera prosty widok z pokazem znanej komety 3I/ATLAS i rzeczywistym zapisanym polem. Przycisk ustawień zaawansowanych udostępnia pełny warsztat. Wszystkie narzędzia są dostępne w sześciu grupach: **Obrazy i ruch**, **Pasma**, **Mapa nieba**, **Pomiary i składanie**, **Kalibracje i źródła**, **Wynik i eksport**. Można od razu zmienić pole i wyszukać własne współrzędne. Dane przykładu są jawnie oznaczone, a ich identyfikatory zapisano w `frontend/src/showcase.json`.

Przewodnik PL/EN jest opcjonalny w pomocy pod `/?guided=1`; nie zastępuje pełnej aplikacji. Zapasowy replay `/demo/` pozostaje do prezentacji przy awarii serwera. Istniejące linki do analiz, notatek i raportów IRSA nadal otwierają odpowiednie narzędzia. Stare linki `view=measure&irsa=...` są kierowane do grupy kalibracji, a notatki do wyniku i eksportu.

Jeśli zapisany przykład nie jest obecny na innym serwerze, trzeba zaimportować seed albo wyszukać i przygotować własne obrazy. Wpisane RA/Dec nigdy nie są zastępowane domyślnym przykładem.

Przy awarii IRSA wyszukiwanie może użyć zapisanej listy z tego samego wydania, ze środkiem oddalonym najwyżej o 1″ (tolerancja zaokrąglenia współrzędnych). Pierwszeństwo ma zgodny rozmiar pola. Jeśli dostępny jest inny rozmiar, komunikat podaje wybrany i zapisany obszar; przygotowanie korzysta z rzeczywistej zapisanej geometrii. Lista jest oznaczona jako archiwalna i może nie zawierać nowych ekspozycji. Bez odpowiedniego zapisu aplikacja wyświetla komunikat o niedostępności, zamiast podstawiać inny cel lub wydanie.

## Widoczny ruch — gotowy przykład 3I/ATLAS

Na stronie głównej wybierz **Zobacz przykład ruchu** albo otwórz [pokaz ruchu](http://127.0.0.1:8000/?motion=1). Dwie rzeczywiste obserwacje komety z 14 grudnia 2025 dzieli 98 minut i około 4,77′ przesunięcia według efemeryd. Pokaz miga zdjęciami w tej samej geometrii nieba; można ukryć nieruchome znaczniki A/B, porównać obrazy obok siebie i otworzyć te dane w pełnym warsztacie. Przenośne obrazy i FITS są częścią frontendu. Pochodzenie, kontrola obrazu i ograniczenia: [RUCH_DEMO.md](RUCH_DEMO.md).
