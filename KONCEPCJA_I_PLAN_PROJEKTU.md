# Publiczne narzędzie do analizy zmian na niebie w danych SPHEREx

**Wersja:** 4.0 — analiza pasm, ruch w czasie i orientacja względem Ziemi

**Aktualizacja:** 14 listopada 2026 r.  
**Wyzwanie:** [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)  
**Forma:** publiczna aplikacja webowa  
**Nazwa projektu:** nieustalona; nie nadawać nazwy bez decyzji zespołu  
**Status:** istnieje pierwszy lokalny prototyp; bieżące wyniki w STATUS_IMPLEMENTACJI.md. Ten dokument zachowuje szerszą mapę rozwoju, nie listę funkcji gotowych.

### Aktualny zakres projektu

Aktualna koncepcja łączy zwiększanie wykrywalności źródeł przez dobór pasm z obserwacją ruchu i zmian jasności w czasie. Zachowujemy istniejącą lupę A/B, miganie, ręczną hipotezę ruchu i zapis analizy. Dodajemy do planu asystenta pasm, kontrolowane składanie i odejmowanie obrazów, widmo na żądanie, kontekst Gaia/WISE oraz panel „Gdzie patrzę?” z mapą nieba i kierunkiem względem Ziemi. Nie nadajemy projektowi nazwy bez decyzji zespołu.

To aktualizacja dokumentacji, nie deklaracja wdrożenia tych funkcji. Stan kodu i wykonanych testów opisuje STATUS_IMPLEMENTACJI.md, a uruchomienie README.md. Szczegółowy zakres, kolejność i warunki odbioru nowych funkcji określa sekcja 21; w razie różnic ma pierwszeństwo przed wcześniejszą mapą etapów.

> Wybierz fragment nieba. Zobacz jego zmiany w czasie. Sprawdź, czy zauważony ruch lub zmiana jasności przetrwa porównanie pasm, kontrolę jakości i analizę poszczególnych ekspozycji.

Ten dokument zastępuje wcześniejszy plan symulacji wysokości orbity. Jest samodzielnym kontekstem do rozpoczęcia implementacji w innym repozytorium. Nie trzeba znać historii rozmowy.

## 1. Cel i problem

### 1.1. Cel projektu

Ułatwić osobie bez doświadczenia w FITS znalezienie i sprawdzenie potencjalnej zmiany na rzeczywistych obrazach SPHEREx. Podstawą jest szybkie porównanie tego samego obszaru nieba z różnych dat. Dalsza analiza ma pomóc odróżnić podejrzany sygnał od skutków nieporównywalnych obserwacji.

Główne pytanie użytkownika:

**Czy ten obiekt rzeczywiście się przesunął lub zmienił jasność, czy zmieniły się warunki i sposób pomiaru?**

Projekt wspiera poszukiwanie kandydatów i naukę analizy danych. Nie obiecuje odkrycia Planet X ani automatycznego potwierdzania nowych obiektów.

### 1.2. Faktyczne trudności, na które odpowiadamy

| Problem pracy z obserwacjami | Odpowiedź projektu | Jak sprawdzimy działanie |
|---|---|---|
| Dane trzeba wyszukać, pobrać i przygotować przed porównaniem | Jedno zapytanie RA/Dec uruchamia cały przebieg | Test dowolnych współrzędnych oraz znanych obiektów |
| Obrazy mają różną geometrię i pokrycie | Wspólna siatka nieba oraz jawna maska pokrycia | Sprawdzenie WCS i nieruchomych źródeł |
| Różnica długości fali może wyglądać jak zmiana w czasie | Kontrola zgodności pasm w miejscu badanego obiektu | Przykład pokazujący wpływ doboru pasm |
| Artefakt lub wadliwa ekspozycja może udawać źródło | Flagi jakości i próba z pominięciem ekspozycji | Kontrolowany przypadek testowy |
| Ruch i zmienność jasności łatwo pomylić | Osobne narzędzia i opisy obu zjawisk | Osobne przypadki dla ruchu i fotometrii |
| Wyniku z ekranu trudno odtworzyć | Link do analizy i manifest przetwarzania | Odtworzenie na podstawie zapisanych identyfikatorów |
| Obrazy z różnych misji nie są bezpośrednio równoważne | Nakładki i kontekst z wyraźnymi ograniczeniami | Kontrola epok, pasm i rozdzielczości |

To nasza interpretacja problemów analitycznych i projektu rozwiązania. Nie przypisujemy NASA zapotrzebowania na zakup aplikacji ani potwierdzonego zainteresowania zespołem.

## 2. Dopasowanie do wyzwania

Podstawą wymagań jest opis Objectives i Potential Considerations przekazany przez uczestnika oraz wskazana strona wyzwania. Przy tej aktualizacji automatyczny odczyt strony zwrócił HTTP 502; nie traktujemy go jako ponownego potwierdzenia treści. Dokumentacja IRSA została odczytana. Przed zgłoszeniem trzeba porównać finalny projekt z aktualną stroną i zasadami wydarzenia.

### 2.1. Rdzeń zadania

| Wymaganie | Nasza realizacja | Warunek odbioru |
|---|---|---|
| Publiczne narzędzie webowe | Aplikacja dostępna przez przeglądarkę, podstawowa analiza bez konta | Uruchomienie na publicznym adresie |
| Wprowadzanie RA i Dec | Stopnie dziesiętne oraz zapis godzinowy/kątowy | Walidacja, normalizacja, jasne błędy |
| Obrazy SPHEREx danego obszaru | Wyszukiwanie rzeczywistych obserwacji | Identyfikatory, daty, źródło danych |
| Seria obrazów w czasie | Oś czasu, odtwarzanie, krokowanie i miganie A/B | Chronologiczna animacja wspólnego obszaru |
| Ułatwienie zauważenia ruchu | Stała geometria, znaczniki, porównanie epok | Ruch nie wynika ze zmiany kadrowania |
| Testy pięciu wskazanych obiektów | Osobny raport dla każdego obiektu | Wynik, ograniczenia i pokrycie zapisane uczciwie |

### 2.2. Wskazane obiekty testowe

- Barnard’s Star — analiza ruchu własnego i zgodności astrometrycznej.
- Epsilon Indi B — badanie dostępnych obserwacji układu; nie obiecujemy rozdzielenia jego składników przy rozdzielczości SPHEREx.
- WISE 0855 — współrzędne startowe z zadania: RA 08h55m10.831s, Dec −07°14′42.53″. Epokę pozycji i ruch własny trzeba sprawdzić; pozycja katalogowa nie musi odpowiadać pozycji w każdej dacie.
- RW Aurigae — analiza zmian jasności, jeśli dostępne pasma, jakość i kadencja na to pozwalają.
- R Draconis — analogiczny test zmienności z jawnym zakresem dat i długości fal.

Test oznacza rzeczywiste sprawdzenie danych, nie obowiązek uzyskania widocznego efektu na każdym obiekcie. Brak danych, za krótka baza czasowa, nasycenie lub zbyt mały SNR są poprawnymi wynikami raportu. Nie zastępujemy ich syntetycznym „odkryciem”.

### 2.3. Rozwinięcia wskazane w zadaniu

Realizujemy kolejno: wybór pola widzenia, dodawanie i odejmowanie obrazów, jakość danych, udostępniane współrzędne w URL, porównanie katalogowe Gaia DR3, kontekst WISE, widmo na żądanie, porównania w wielu zakresach długości fali oraz łatwe aktualizowanie danych. Nie wszystkie są obowiązkowym warunkiem zadania, ale każda powinna mieć działającą demonstrację, jeśli opisujemy ją w zgłoszeniu.

## 3. Co wyróżnia projekt

### 3.1. Główna idea: użytkownik sprawdza własne podejrzenie

**„Zaznacz zmianę — sprawdźmy, co mogłoby ją wyjaśnić”.**

Po zaznaczeniu obiektu aplikacja prowadzi od zauważonej zmiany do zestawu dowodów. Nie kończy się na efektownym filmie ani etykiecie „AI wykryło obiekt”.

Pierwsze trzy testy diagnostyczne:

1. **Zgodność spektralna:** czy porównujemy odpowiednio zgodne długości fal i szerokości pasm w miejscu źródła?
2. **Jakość danych:** czy istotne piksele lub obserwacje mają flagi wymagające odrzucenia bądź ostrożności?
3. **Zależność od jednej ekspozycji:** czy efekt pozostaje po wyłączeniu pojedynczego pomiaru i przy oglądaniu obserwacji składowych?

To początek systemu diagnostycznego, nie sztuczny limit funkcji. Później dodajemy kontrolę geometrii, tła, PSF, sąsiadujących źródeł i zgodności z katalogiem.

### 3.2. Forma wyniku

Karta analizy pokazuje:

- co zaznaczył użytkownik i jakie obserwacje porównano;
- jakie są alternatywne wyjaśnienia;
- które testy wykonano i co się po nich zmieniło;
- jakie pomiary oraz niepewności są dostępne;
- czego nie można rozstrzygnąć na podstawie danych;
- jak odtworzyć analizę.

Przykładowe statusy: „brak porównywalnych pomiarów”, „efekt zależy od jednej ekspozycji”, „różnica wymaga dalszej weryfikacji”. Nie pokazujemy procentowego prawdopodobieństwa odkrycia bez odpowiednio skalibrowanego modelu.

### 3.3. Uczciwy opis innowacji

Animacja nieba, reprojekcja, fotometria i odejmowanie obrazów są znanymi metodami. Innowacyjność proponujemy na poziomie zintegrowanego doświadczenia: publiczna, odtwarzalna analiza prowadząca od obserwacji zmiany do próby obalenia jej prostymi testami, z wykorzystaniem specyfiki danych SPHEREx. Nie twierdzimy, że nikt wcześniej nie stworzył podobnego rozwiązania.

## 4. Przebieg użytkownika

1. **Wybierz niebo:** wpisz RA/Dec albo wybierz jeden z pięciu obiektów zadania.
   Mapa kontekstu pokazuje granice pola. Opcjonalnie wybierz miejsce na Ziemi i czas, aby zobaczyć jego kierunek względem lokalnego horyzontu.
2. **Zobacz dostępność:** zakres dat, pokrycie, zakresy fal, liczba obserwacji i ograniczenia.
3. **Uruchom porównanie:** określ pole widzenia, daty i grupowanie spektralne.
4. **Oglądaj:** animacja, krokowanie, miganie, A/B i wspólna skala jasności.
5. **Zaznacz podejrzany obiekt:** kliknięcie tworzy region analizy we współrzędnych niebieskich.
6. **Sprawdź zmianę:** pasma, jakość, ekspozycje, geometria i dostępne pomiary.
   Asystent pasm proponuje kanały i stałe wagi; użytkownik porównuje tę samą sekwencję przed i po ich zastosowaniu.
7. **Sprawdź kontekst:** Gaia DR3, WISE i informacje katalogowe.
8. **Udostępnij:** link, manifest, wykresy i dane pomiarowe.

Tryb podstawowy tłumaczy RA/Dec, pasmo, epokę i flagi krótkim językiem. Tryb szczegółowy odsłania parametry przetwarzania. Nie ukrywamy braku danych za pustym odtwarzaczem.

## 5. Interfejs

### 5.1. Układ

- Góra: RA/Dec, pole widzenia, daty, przycisk wyszukania.
- Centrum: duży panel obrazu z podziałką, orientacją i datą.
- Dół: oś czasu, odtwarzanie, szybkość, A/B, wskazanie przerw między obserwacjami.
- Panel boczny: pasma, jakość, wybrany obiekt, wyniki testów.
- Rozwijany obszar: wykres jasności, widmo, informacje o źródle danych.
- Aladin Lite: mapa kontekstu i wybór fragmentu nieba, zsynchronizowane z głównym panelem.
- Panel „Gdzie patrzę?”: szeroka mapa nieba z ramką pola, schemat Ziemi i kierunku, lokalny horyzont oraz jawne miejsce i czas odniesienia. Szczegóły w sekcji 21.5.

### 5.2. Zasady wyświetlania

- Wspólny WCS i pole obrazu w porównywanych klatkach.
- Domyślnie wspólna funkcja rozciągania i zakres jasności dla porównania. Automatyczne skalowanie każdej klatki jest jawnie oznaczone, ponieważ może mylić przy ocenie zmienności.
- Obraz różnicowy ma symetryczną skalę wokół zera i legendę jednostek.
- Brak pokrycia nie jest zerowym sygnałem; ma osobne oznaczenie.
- Zmiana czasu i zmiana długości fali to oddzielne osie, nie jeden pomieszany „film”.
- Klatki pokazują daty i odstępy czasu; równa prędkość animacji nie oznacza równych odstępów obserwacji.
- Surowy podgląd i obraz po korektach mają rozpoznawalne etykiety.
- Sterowanie klawiaturą, czytelny kontrast i informacje niewymagające rozróżniania samych kolorów.

## 6. Dane i zasoby

### 6.1. SPHEREx — główne dane naukowe

Źródła: [IRSA SPHEREx](https://irsa.ipac.caltech.edu/Missions/spherex.html), [oficjalne notebooki](https://caltech-ipac.github.io/irsa-tutorials/spherex/), [wprowadzenie do obrazów](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/).

Adapter archiwum wyszukuje obserwacje przestrzennie i czasowo. Implementację zaczynamy od oficjalnego przykładu Astroquery/SIA i mechanizmu wycinków. Wersję kolekcji wybieramy jawnie. Według odczytanej dokumentacji DR1 i QR3 zastępują QR2; przed uruchomieniem należy sprawdzić bieżące wydania. Nie łączymy automatycznie powtórnie przetworzonych kopii tej samej ekspozycji.

Wykorzystujemy dane obrazu, wariancję, flagi, geometrię oraz długość fali i szerokość pasma w miejscu źródła. W razie potrzeby korzystamy z modeli tła i PSF. Sam identyfikator detektora nie gwarantuje zgodności spektralnej pomiarów. SPHEREx używa filtrów o zmiennej długości fali w polu detektora; „102 pasma” nie oznacza gotowych 102 równoczesnych obrazów każdego pola.

Nie odejmujemy modelu tła drugi raz. Nie odrzucamy wszystkich niezerowych flag bez znajomości ich znaczenia. Przechowujemy oryginalne jednostki, a każdą konwersję opisujemy w metadanych.

### 6.2. Gaia DR3

[Zasób Gaia wskazany w wyzwaniu](https://archive.stsci.edu/missions-and-data/gaia).

Wykorzystanie: nakładki znanych źródeł, pozycje i ruch własny, a gdzie zasadne także paralaksa i informacje o jakości rozwiązania. Uwzględniamy epokę katalogową i datę obserwacji. Zaawansowana pozycja pozorna wymaga dodatkowych korekt; nie utożsamiamy prostej propagacji ruchu własnego z pełnym modelem astrometrii.

Brak dopasowania katalogowego nie dowodzi odkrycia. Gaia i SPHEREx mają inne pasma i czułość.

### 6.3. WISE i WiseView

[WiseView](http://byw.tools/wiseview) to inspiracja dla porównywania epok. Dane WISE pozyskujemy przez właściwe archiwum i dokumentujemy ich pochodzenie. Porównanie wieloletnie może być cenniejsze niż krótka baza czasowa SPHEREx, ale wymaga kontroli pasm, PSF i dat.

W pierwszej integracji używamy kontekstu wizualnego i katalogowego. Fotometrię między misjami dodajemy dopiero po ustaleniu kalibracji i ograniczeń.

### 6.4. CSA, CADC i NEOSSat

Zasoby dodatkowe: [NEOSSat](https://www.asc-csa.gc.ca/eng/satellites/neossat/), [CADC](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/), [tutorial](https://github.com/asc-csa/NEOSSAT_Tutorial), [zbiór danych](https://data.asc-csa.gc.ca/dataset/neossat).

Sprawdzamy rzeczywiste pokrycie i zasadność porównania. Nie zakładamy obserwacji tych samych pól, terminów lub obiektów. Gdy brak użytecznego przecięcia, zasób może służyć osobnemu, podpisanemu przykładowi analizy ruchu. Rozbudowa ta nie zastępuje rdzenia SPHEREx i nie ma pierwszeństwa przed nim.

Maksymalne wykorzystanie danych oznacza wykorzystanie ich treści naukowej, nie liczbę podłączonych archiwów.

## 7. Pipeline naukowy

### 7.1. Wyszukiwanie i kwalifikacja

1. Normalizacja RA/Dec do ICRS i jednostek wewnętrznych.
2. Walidacja zakresów, pola widzenia i budżetu zapytania.
3. Wyszukanie obserwacji przecinających zadany obszar.
4. Zapis identyfikatorów, wydania, dat, pasm i metadanych dostępu.
5. Usunięcie duplikatów i określenie rzeczywistego pokrycia.
6. Pobranie wycinków albo niezbędnych plików według możliwości archiwum.
7. Sprawdzenie, które obserwacje da się sensownie porównać.

W przypadku dużego pola użytkownik widzi szacowany koszt danych i postęp. Limity mają chronić stabilność wdrożenia, a nie ukrywać ograniczenia.

### 7.2. Przygotowanie obrazów

- Odczyt FITS i niezbędnych rozszerzeń.
- Odczyt WCS przestrzennego i spektralnego zgodnie z produktem SPHEREx.
- Maska ważnych danych na podstawie dokumentacji flag i pokrycia.
- Jawna decyzja o odejmowaniu tła i zapis zastosowanego modelu.
- Grupowanie po czasie i zgodnych zakresach spektralnych.
- Reprojekcja na wspólną siatkę za pomocą sprawdzonej biblioteki.
- Przeniesienie informacji o pokryciu, maskach i niepewnościach z uwzględnieniem użytej metody.
- Dopasowanie PSF i normalizacji, gdy wymagają tego różnice obserwacji.

Nie stosujemy identycznej interpolacji do masek bitowych i wartości obrazu. Reprojekcja lub splot może wprowadzić korelację szumu. Nie zakładamy, że wariancję wystarczy przeliczyć jak zwykły obraz, aby otrzymać poprawną istotność statystyczną.

### 7.3. Grupowanie czasu i widma

Dla analizy ruchu i zmienności dobieramy możliwie zgodne zakresy fal oraz pokazujemy zakres czasu każdego połączonego obrazu. Dla widma pokazujemy, kiedy zebrano jego punkty. Widmo źródła zmiennego złożone z różnych dat nie jest automatycznie widmem jednoczesnym.

Szerokie połączenia w obrębie sześciu detektorów można wykorzystać do przeglądu i zwiększenia widoczności. Ich porównywalność trzeba ocenić na podstawie rzeczywistego pokrycia spektralnego. Nie sumujemy bezrefleksyjnie wszystkich 102 kanałów.

Dla źródeł poruszających się zbyt szeroki przedział składania może rozmyć źródło. Tryb składania w układzie poruszającego się obiektu jest późniejszym rozszerzeniem.

### 7.4. Dodawanie, odejmowanie i pomiary

- Składanie obrazów z uwzględnieniem masek, jednostek, wag i rzeczywistych czasów.
- Różnica A−B dopiero po sprawdzeniu geometrii, pasm, tła i PSF.
- Fotometria aperturowa na danych naukowych, z lokalnym tłem i odpowiednią konwersją jednostek.
- Krzywa jasności z datami, długościami fal, błędami i odrzuceniami.
- Początkowo widmo jako zestaw punktów pomiarowych z niepewnościami; bez obietnicy klasyfikacji chemicznej.
- Znaczniki pozycji i przesunięć z informacją o rozdzielczości i błędach astrometrii.

Podglądy PNG/WebP służą wyświetlaniu. Nie są źródłem pomiarów. Jeśli dopasowanie PSF lub propagacja błędów nie są gotowe, odpowiedni widok jest opisany jako jakościowy i nie pokazuje nieuzasadnionego „sigma”.

### 7.5. Próba usunięcia jednej ekspozycji

Użytkownik może wyłączyć ekspozycję i porównać wynik. Automatyczny wariant leave-one-out jest dostępny w ograniczonym zbiorze, jeśli koszt na to pozwala. Gdy pozostaje za mało danych, wynik brzmi „test nierozstrzygający”, a nie „artefakt”.

## 8. Stack i odpowiedzialności

| Warstwa | Wybór | Odpowiedzialność |
|---|---|---|
| Frontend | React + TypeScript + Vite | Interakcja, konfiguracja analizy i prezentacja wyników |
| Styl | Tailwind CSS | Spójny interfejs i responsywność |
| Kontekst nieba | Aladin Lite | Mapa, pozycje, katalogi, wybór pola |
| Główny viewer | Canvas 2D; WebGL po wykazaniu potrzeby | Klatki, A/B, miganie, różnice i maski |
| Wykresy | Plotly.js, ładowane na żądanie | Widmo, jasność, błędy |
| Stan zapytań | TanStack Query | Postęp zadań, cache odpowiedzi i ponawianie zapytań |
| API | Python + FastAPI + Pydantic | Kontrakty, zadania, metadane i wyniki |
| Dane i obliczenia | NumPy + SciPy + Astropy | FITS, jednostki, czas, WCS i operacje numeryczne |
| Archiwa | Astroquery; PyVO tam, gdzie potrzebne | Dostęp do SIA/TAP i katalogów |
| Reprojekcja | Reproject | Wspólna geometria obrazów |
| Fotometria | Photutils | Tło i pomiary źródeł |
| Podglądy | Pillow | Przygotowanie obrazów do prezentacji |
| Zapis | SQLite + lokalny cache plików | Analizy, zadania, pliki i metadane |
| Wykonanie obliczeń | Osobny proces / pula procesów | Ciężkie operacje poza obsługą żądań |
| Pakowanie | Docker | Backend z powtarzalnymi zależnościami |
| Zależności | uv + npm, lockfile w repozytorium | Powtarzalna instalacja |
| Testy | pytest + Playwright | Poprawność naukowa, API i pełny przebieg |
| Kontrola jakości kodu | Ruff, TypeScript, ESLint | Błędy statyczne i spójność |

Wersje dobieramy podczas instalacji do wspieranej wersji Pythona i Node; zapisujemy dokładne zależności. Nie zakładamy zgodności dowolnych najnowszych wydań.

Aladin Lite nie jest całym naszym silnikiem analizy. Pozostaje modułem mapy i kontekstu. Własny viewer dostaje przygotowane, zgodne przestrzennie klatki i metadane. Kod naukowy nie zależy od FastAPI ani od interfejsu.

Na początek nie potrzebujemy mikroserwisów, Redis, Celery, Kubernetes ani bazy wektorowej. Przejście na zewnętrzną kolejkę lub magazyn obiektowy wynika z pomiaru potrzeb wdrożenia, nie z chęci rozbudowania stacku.

## 9. Architektura i struktura repozytorium

```text
frontend/
  src/
    features/search/
    features/sky-context/
    features/timeline/
    features/viewer/
    features/diagnostics/
    features/photometry/
    features/sharing/
    api/
backend/
  app/
    api/
    schemas/
    archives/             # SPHEREx, Gaia, WISE
    science/              # niezależne funkcje obliczeniowe
    processing/           # pipeline i zarządzanie zadaniami
    storage/              # SQLite, cache, manifesty
  tests/
    unit/
    integration/
    reference/
    fixtures/
docs/
  sources.md
  scientific-methods.md
  validation.md
  demo.md
scripts/
  prepare_demo_cache.py
  verify_environment.py
STATUS_IMPLEMENTACJI.md
.env.example
compose.yaml
```

To docelowy układ. Nie tworzymy katalogów tylko po to, żeby wyglądały na ukończone moduły. Mały działający przekrój poprzedza rozbudowę.

### 9.1. Kontrakty danych

- **SearchRequest:** RA/Dec, układ odniesienia, FOV, daty, kolekcje, zakres fal.
- **Observation:** ID, wydanie, czas początku/końca, pokrycie, WCS, zakres fal, dane jakości, adres archiwalny.
- **AnalysisConfig:** wybrane obserwacje, grupowanie, siatka, maski, tło, PSF, sposób łączenia i parametry widoku.
- **Frame:** obserwacje składowe, przedział czasu, zakres fal, pokrycie, produkt naukowy i podgląd.
- **Measurement:** pozycja/region, czas, wartość, jednostka, błąd, metoda, jakość.
- **DiagnosticResult:** test, przesłanki, wynik, ograniczenia, produkty porównawcze.
- **AnalysisManifest:** wersja schematu i pipeline, konfiguracja, identyfikatory produktów, sumy kontrolne, stan wykonania.

Parametry widoku, takie jak kolorystyka, nie zmieniają wyniku pomiarowego. Rozróżniamy konfigurację przetwarzania i prezentacji.

### 9.2. Proponowane API

| Endpoint | Funkcja |
|---|---|
| POST /api/search | Wyszukanie obserwacji |
| POST /api/analyses | Utworzenie analizy, odpowiedź 202 z ID zadania |
| GET /api/jobs/{id} | Postęp, stan, komunikaty i błąd |
| GET /api/analyses/{id} | Manifest i metadane wyników |
| GET /api/analyses/{id}/frames/{frame_id} | Podgląd klatki |
| POST /api/analyses/{id}/diagnostics | Uruchomienie testu zaznaczonego regionu |
| POST /api/analyses/{id}/measurements | Fotometria lub pomiar pozycji |
| GET /api/analyses/{id}/export | Manifest, pomiary i dostępne produkty |
| GET /api/health | Kontrola działania usługi |

Długie wyszukiwanie także może otrzymać ID zadania. Frontend odpytuje status; WebSocket nie jest potrzebny do pierwszej integracji. Postęp opiera się na faktycznych etapach, nie sztucznym odliczaniu.

### 9.3. Wydajność i cache

Cache obejmuje metadane zapytań, pobrane dane, klatki i wyniki analiz. Klucz naukowego wyniku zależy od wydania, identyfikatorów plików, siatki, zakresów fal, masek i wersji przetwarzania. Sama para RA/Dec nie wystarcza.

Nowe wyszukiwanie może odświeżyć dostępność danych. Odtwarzanie istniejącej analizy używa przypiętych obserwacji. Usunięcie cache nie usuwa automatycznie manifestu; interfejs informuje, jeśli produktu nie da się odtworzyć.

Ciężkie obliczenia pracują w procesie roboczym. Async służy obsłudze oczekiwania na I/O; nie zastępuje równoległości CPU. Zadania mają limity zasobów i możliwość przerwania pomiędzy etapami. Nie przekazujemy dużych tablic przez JSON.

## 10. Udostępnianie i powtarzalność

Dwa typy linków:

1. **Link do wyszukiwania:** RA/Dec, FOV i opcjonalne daty w URL. Może pokazać nowe dane przy kolejnym otwarciu.
2. **Link do analizy:** identyfikator niezmiennego manifestu. Ma odtworzyć konkretne obserwacje i przetwarzanie.

Eksport JSON zawiera pochodzenie danych, wersje, parametry i ograniczenia. CSV zawiera pomiary z jednostkami i identyfikatorami obserwacji. Opcjonalny FITS zachowuje dane naukowe, WCS i opis korekt. Obraz lub film zawiera daty oraz oznaczenie źródła, ale nie zastępuje manifestu.

Publiczny link nie zależy od stanu localStorage. Wdrożenie musi zachować metadane i potrzebne pliki albo wyraźnie podać okres ich dostępności.

## 11. Weryfikacja i walidacja

### 11.1. Testy naukowe

- WCS: zgodność transformacji piksel–niebo i wspólnej siatki, z tolerancją ustaloną do skali piksela i zastosowania.
- Reprojekcja: obraz tożsamościowy, przesunięty i o innym pokryciu; brak sztucznego ruchu nieruchomych źródeł.
- Jednostki i fotometria: kontrola znanego sygnału, tła, konwersji oraz pola powierzchni piksela.
- Maski: brak traktowania braku danych jako zera, brak maskowania wszystkich niezerowych flag.
- Różnice: źródło stałe, zmienne i przesunięte; osobno wpływ pasma i PSF.
- Niepewności: założenia i ograniczenia propagacji, zwłaszcza po reprojekcji i składaniu.
- Odtwarzalność: ten sam manifest odtwarza numerycznie zgodne produkty w zadanej tolerancji.

Dane syntetyczne i wstrzyknięte sygnały służą kontrolowanym testom. Są trwale oznaczone i oddzielone od rzeczywistych obserwacji. Parametry ruchu, jasności i szumu są znane, dzięki czemu można zmierzyć błąd; nie służą do udawania sukcesu na danych NASA.

### 11.2. Niezależna kontrola

Porównujemy wybrane pozycje i pomiary z niezależnym narzędziem, notebookiem referencyjnym lub dostępną informacją katalogową. Ten sam kod uruchomiony ponownie nie jest niezależną walidacją. Znany katalogowy ruch też nie gwarantuje, że nasze dane mają wystarczającą rozdzielczość i bazę czasową, aby go zmierzyć.

### 11.3. Raport pięciu obiektów

Dla każdego zapisujemy: pozycję i epokę, kolekcję, obserwacje, daty, pasma, pokrycie, zastosowane korekty, oczekiwane zjawisko, zaobserwowany wynik, ograniczenia i link do manifestu. Nie dobieramy po cichu skali obrazu tak, by stworzyć efekt zmienności.

### 11.4. Test wpływu na użytkownika

Przeprowadzamy krótką próbę porównawczą: zwykła animacja kontra animacja z diagnostyką. Uczestnicy oceniają tę samą klasę przykładów, a kolejność wariantów w miarę możliwości zmieniamy.

Mierzymy czas, trafność rozpoznania oraz poprawność uzasadnienia. Zapisujemy liczbę osób i warunki. Wynik małej próby opisujemy jako wstępny; nie ogłaszamy udowodnionej przewagi na podstawie samej opinii zespołu. Nie wpisujemy wymyślonych wartości procentowych do prezentacji.

### 11.5. Testy produktu

Pełny przebieg: RA/Dec → wyszukanie → przetwarzanie → animacja → diagnostyka → udostępnienie. Osobno: brak obserwacji, błędne współrzędne, błąd archiwum, przerwane zadanie i odtworzenie linku na innym urządzeniu. Testy integracyjne z siecią oddzielamy od powtarzalnych testów na małych fixture'ach.

## 12. Etapy realizacji

Nie ustalamy z góry sztucznego końca zakresu. Każdy etap ma działający rezultat, a kolejne funkcje dokładamy z czasem na integrację i walidację. Kolejność wynika z ryzyka danych i zależności technicznych.

### Etap A — rozpoznanie danych i środowiska

- Sprawdzić instrukcje repozytorium i faktyczny stan plików.
- Uruchomić oficjalny przykład zapytania i odczytać rzeczywisty FITS.
- Zbadać dostępność wszystkich pięciu obiektów, bazę czasową i zakresy fal.
- Zidentyfikować parę porównywalnych obserwacji; jeśli takiej brak, zapisać przyczynę i zbadać inne obiekty bez fabrykowania wyników.
- Zainstalować zgodne zależności, utworzyć lockfile i sprawdzić uruchomienie backendu w Dockerze.

**Odbiór:** zapisany raport rozpoznania oraz mały, powtarzalny przykład pobrania prawdziwych danych. To pierwsza rzecz do wykonania, przed rozbudową interfejsu.

### Etap B — pierwszy pełny przebieg webowy

- Frontend RA/Dec i FOV, FastAPI, adapter SPHEREx.
- Wyszukiwanie, zadanie, cache, lista obserwacji i błędy.
- Wspólna geometria, podglądy, oś czasu, animacja i A/B.
- Pierwsze publiczne wdrożenie.

**Odbiór:** użytkownik na innym urządzeniu wpisuje współrzędne i dostaje rzeczywiste, opisane obserwacje. To podstawa dalszego rozwoju, nie finalny zakres projektu.

### Etap C — porównywalność i pomiary

- Dobór długości fal, jakość, pokrycie, tło i wspólne skalowanie.
- Dodawanie i odejmowanie z opisem ograniczeń.
- Fotometria, daty, błędy i pierwszy wykres.
- Testy geometrii i prostych przypadków kontrolnych.

**Odbiór:** potrafimy wyjaśnić, co porównujemy, i pokazać przypadek, w którym niewłaściwe porównanie wprowadza w błąd.

### Etap D — główny wyróżnik

- Zaznaczanie regionu we współrzędnych niebieskich.
- Test pasm, flag i wpływu pojedynczej ekspozycji.
- Karta przesłanek i ograniczeń, widok obserwacji składowych.
- Manifest i publiczny link do analizy.

**Odbiór:** druga osoba odtwarza analizę i rozumie, dlaczego podejrzenie pozostało, osłabło lub jest nierozstrzygające.

### Etap E — głębsze wykorzystanie danych

- Gaia DR3 z uwzględnieniem epoki.
- Kontekst WISE.
- Widmo na żądanie, szerokie grupy spektralne i pokrycie kanałów.
- Dalsza kontrola PSF i pozycji.
- Aktualizowanie kolekcji bez zmiany starego manifestu.

**Odbiór:** każda dodana integracja odpowiada na konkretne pytanie, a nie tylko dodaje warstwę do mapy.

### Etap F — wiarygodność i demonstracja

- Raport wszystkich pięciu obiektów.
- Niezależna kontrola pomiaru i oznaczone testy syntetyczne.
- Krótka próba z użytkownikami.
- Testy wydajności, obsługi błędów i odtwarzania.
- Przygotowanie demonstracji, materiałów źródłowych i opisu ograniczeń.

**Odbiór:** działający adres, repozytorium, rzeczywiste wyniki, powtarzalny pokaz i zgłoszenie opisujące wyłącznie gotowe funkcje.

### Kolejne rozszerzenia

Po ustabilizowaniu rdzenia: składanie w układzie poruszającego się obiektu, półautomatyczne wskazywanie kandydatów, bardziej zaawansowana propagacja niepewności, dodatkowe archiwa, osadzanie w innych stronach i narzędzia społecznościowe. Uczenie maszynowe tylko z konkretnym zadaniem, odpowiednimi danymi i sposobem oceny; nie jest warunkiem innowacyjności.

## 13. Organizacja pracy

Możliwe strumienie pracy: dane i pipeline; API i przechowywanie; frontend i viewer; walidacja i demonstracja. Przy mniejszym zespole role łączymy. Najpierw ustalamy kontrakty, a potem integrujemy na rzeczywistych obserwacjach.

Nie czekamy z połączeniem komponentów do końca hackathonu. Każdy etap kończy się uruchomieniem całości. Ostatnia część czasu jest zarezerwowana na poprawki, testy wdrożenia i pokaz; nowe funkcje nie mogą zająć całego czasu integracji.

STATUS_IMPLEMENTACJI.md rozróżnia: gotowe, sprawdzone, w trakcie, planowane i ograniczenia. Nie dopisujemy wyników testów, których nie uruchomiono.

## 14. Kryteria oceny i dowody dla jury

Roboczo korzystamy z pięciu wcześniej omawianych kryteriów: Impact, Creativity, Validity, Relevance, Presentation. Nie mamy tu potwierdzonych wag aktualnego regulaminu. Nie obiecujemy maksymalnej punktacji; pokazujemy konkretne dowody.

| Kryterium | Co pokazujemy | Co osłabia projekt | Działanie wzmacniające |
|---|---|---|---|
| Impact | Osoba bez FITS przechodzi od współrzędnych do uzasadnionej oceny zmiany | Sama deklaracja edukacyjności | Krótka próba z użytkownikami i uczciwy pomiar efektu |
| Creativity | Sprawdzanie alternatywnych wyjaśnień oraz odtwarzalna ścieżka analizy | Zwykły odtwarzacz zdjęć z nową skórką | Pokazać, jak test zmienia interpretację konkretnego przypadku |
| Validity | Rzeczywiste dane, WCS, pasma, maski, jednostki i kontrola wyników | Pozorna dokładność i brak walidacji | Raport testów, niezależna kontrola i jawne ograniczenia |
| Relevance | Publiczny web, RA/Dec, animacja SPHEREx i testy wskazanych obiektów | Galeria kilku przykładów lub dominacja danych innych misji | Dowolne współrzędne, działający adapter i raport pięciu obiektów |
| Presentation | Jasne pytanie, czytelny przebieg i dowód działania | Lista bibliotek zamiast pokazania celu | Krótki pokaz: zmiana → test → wniosek → link do analizy |

Projekt nie wymaga klientów, modelu biznesowego ani deklaracji, że NASA go kupi. Wartość uzasadniamy rozwiązaniem zadania i dowodem działania.

## 15. Demonstracja dla jurorów

1. Jedno zdanie: „Pomagamy zauważyć zmianę na obrazach SPHEREx i sprawdzić, czy jest fizyczna, czy wynika z porównania niezgodnych danych”.
2. Pokazać RA/Dec i prawdziwe dane z datami oraz źródłem.
3. Uruchomić animację i zaznaczyć źródło.
4. Pokazać test, który zmienia interpretację lub potwierdza stabilność efektu.
5. Otworzyć wykres lub informacje katalogowe, jeśli są naukowo zasadne.
6. Otworzyć udostępniony link na drugim urządzeniu.
7. Wskazać jeden wynik walidacji i jedno ograniczenie.

Przygotowujemy przypadek z realnym zjawiskiem oraz przykład mylącego porównania, jeśli dane pozwalają. Gdy przykład artefaktu jest syntetyczny, ekran i narracja mówią o tym wprost.

Cache demonstracyjny zawiera prawdziwe produkty z manifestem i oznaczeniem daty pobrania. Umożliwia pokaz przy awarii archiwum, ale nie zastępuje wyszukiwania dowolnych współrzędnych. Wcześniejsze nagranie opisujemy jako nagranie, nie demonstrację na żywo.

## 16. Ryzyka i reakcje

| Ryzyko | Reakcja |
|---|---|
| Brak odpowiednich epok lub pasm | Audyt na początku, jawny status, brak wymuszonej detekcji |
| Ruch mniejszy niż wiarygodna dokładność pomiaru | Pokazać ograniczenie i kontekst historyczny, nie sztuczne przesunięcie |
| Wąska baza czasowa | Nie obiecywać mierzalnego ruchu każdego obiektu |
| Nieporównywalne pasma | Osobne grupowanie spektralne i blokada ilościowych wniosków |
| Błędy PSF, tła lub rejestracji | Diagnostyka i tryb jakościowy do czasu walidacji |
| Nasycenie lub źródło zbyt słabe | Flagi, ograniczenia i brak nieuzasadnionej fotometrii |
| Długi transfer i obliczenia | Wycinki, cache, zadania i ograniczenie współbieżności |
| Zmiana wydań lub API | Adaptery, wersjonowanie i przypinanie manifestów |
| Utrata produktów po restarcie hosta | Trwały wolumin i sprawdzenie odtwarzania |
| Zbyt szeroki zakres | Etapy kończone działającą integracją; pierwszeństwo rdzenia |
| Wątpliwa nowość | Opis konkretnych różnic wobec istniejących narzędzi, bez absolutnych deklaracji |

## 17. Wdrożenie

Frontend jako statyczna aplikacja, backend w kontenerze na hoście obsługującym biblioteki naukowe i trwały dysk. Wybór dostawcy po sprawdzeniu limitów pamięci, czasu pracy procesu i miejsca na cache. Nie zakładamy, że krótka funkcja serverless obsłuży całe przetwarzanie FITS.

Wymagania: HTTPS, kontrola działania API, konfiguracja adresu backendu, limity pobierania i zadań, timeouty i rozsądne ponowienia. Backend korzysta z zaufanych adapterów archiwów, a nie pobiera dowolnego URL podanego przez użytkownika. Klucze, jeśli potrzebne, pozostają po stronie serwera.

README ma zawierać rzeczywiste komendy uruchomienia po ich sprawdzeniu. Docelowe czynności: instalacja zależności backendu przez uv, frontendu przez npm, uruchomienie API i Vite, testy pytest, build frontendu oraz start przez Docker Compose. Nie podajemy fikcyjnej komendy jako istniejącego skryptu.

## 18. Warunki ukończenia i uczciwego zgłoszenia

- [ ] Publiczna aplikacja działa bez lokalnej instalacji.
- [ ] Można wyszukać dowolne poprawne RA/Dec w ramach jawnych limitów.
- [ ] Widać rzeczywiste obrazy SPHEREx, daty, pasma i pokrycie.
- [ ] Animacja nie myli zmiany geometrii z ruchem źródła.
- [ ] Istnieje działająca diagnostyka i udostępnianie analizy.
- [ ] Ilościowe wyniki mają jednostki, metodę i opis błędów.
- [ ] Wszystkie pięć obiektów ma raport testu, także gdy wynik jest nierozstrzygający.
- [ ] Dane syntetyczne są jednoznacznie oddzielone.
- [ ] Udokumentowano zależności, źródła, licencje i wymagane podziękowania.
- [ ] Opis zgłoszenia rozróżnia funkcje gotowe od planowanych.
- [ ] Aktualny regulamin i sposób oceniania zostały sprawdzone przed zgłoszeniem.

Lista jest wewnętrzną definicją jakości, nie cytatem z regulaminu. Brak pojedynczego rozszerzenia nie przekreśla rdzenia; brak prawdziwych danych i podstawowego przebiegu przekreśla twierdzenie o gotowej realizacji zadania.

## 19. Źródła do implementacji

### Wyzwanie i dane

- [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/) — cele i zasoby; treść w tej wersji planu oparta na materiale przekazanym przez uczestnika.
- [NASA/IPAC IRSA — SPHEREx](https://irsa.ipac.caltech.edu/Missions/spherex.html) — aktualne produkty i dostęp.
- [SPHEREx Tutorial Notebooks](https://caltech-ipac.github.io/irsa-tutorials/spherex/) — punkt wyjścia do kodu naukowego.
- [Introduction to SPHEREx Spectral Images](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/) — zapytania, struktura FITS, WCS i interpretacja rozszerzeń.
- [SPHEREx Source Discovery Tool Demo](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/) — istniejące metody; nie mylić różnicy między pasmami z różnicą między epokami.
- [Gaia — zasób MAST](https://archive.stsci.edu/missions-and-data/gaia).
- [WiseView](http://byw.tools/wiseview).

### Biblioteki

- [Astropy](https://docs.astropy.org/en/stable/).
- [Astroquery IRSA](https://docs.astropy.org/projects/astroquery/en/latest/ipac/irsa/irsa.html).
- [Reproject](https://docs.astropy.org/projects/reproject/en/stable/).
- [Photutils](https://docs.astropy.org/projects/photutils/en/stable/).
- [Aladin Lite](https://cds-astro.github.io/aladin-lite/).
- [FastAPI — współbieżność i równoległość](https://fastapi.tiangolo.com/async/).

Dla każdego wykorzystanego kodu i zbioru sprawdzamy licencję oraz sposób cytowania. Zasób wymieniony na stronie NASA nie oznacza automatycznie dowolnych praw do jego redystrybucji.

## 20. Instrukcja rozpoczęcia w nowym repozytorium

Przeczytaj ten dokument i instrukcje repozytorium. Sprawdź istniejący kod i środowisko. Zacznij od etapu A: prawdziwe zapytanie SPHEREx, audyt danych pięciu obiektów i zgodne zależności. Następnie zbuduj pełny przebieg webowy etapu B i kontynuuj kolejne etapy. Nie zatrzymuj realizacji na szkielecie lub kolejnym planie. Zapisuj stan w STATUS_IMPLEMENTACJI.md. Nie nadawaj projektowi nazwy. Nie wracaj do symulatora wysokości orbity. Nie przedstawiaj zaplanowanych funkcji, hipotetycznych odkryć ani niewykonanych testów jako wyników.

## 21. Uzgodnione rozszerzenie: pasma + czas + orientacja na niebie

### 21.1. Cel i granice

Główny przebieg: RA/Dec → mapa kontekstu → rzeczywiste obserwacje → zaznaczenie źródła → dobór pasm → animacja porównywalnych epok → sprawdzenie zmiany → odtworzenie analizy.

„Zwiększanie wykrywalności” oznacza ograniczanie udziału nieprzydatnych pomiarów oraz kontrolowane ważenie sygnału. Nie obiecujemy usunięcia całego szumu, odzyskania informacji poniżej możliwości instrumentu ani automatycznego odkrywania planet. Dobór pasm i animacja to metody znane; przewagę projektu trzeba wykazać użytecznością i wynikami walidacji.

### 21.2. Funkcje i priorytety

| Priorytet | Funkcja | Rezultat i warunek odbioru |
|---|---|---|
| P0 | Rdzeń czasowy | Dowolne RA/Dec w jawnych limitach, FOV, rzeczywiste daty, animacja, lupa, miganie A/B i link; testy pięciu pól |
| P0 | Gdzie patrzę? | Mapa nieba i ramka zgodna z WCS; kierunek względem Ziemi i horyzontu przy jawnym miejscu i czasie |
| P1 | Ręczny wybór pasm | Sześć grup detektorów oraz lokalne zakresy fal; tylko dostępne i zgodne pomiary, zapis ustawień |
| P1 | Pomiar źródła i błędów | Tło, flagi, wariancja, pokrycie, kontrola sąsiadów i pozycji; jednostki i metoda |
| P1 | Asystent pasm | Ranking przydatności i propozycja stałych wag; porównanie standard / propozycja na niezależnych danych |
| P1 | Składanie i różnica | Jawne okna czasu i efektywne pasma, kontrola PSF i tła, symetryczna skala różnic; brak wniosków ilościowych bez walidacji |
| P2 | Widmo na żądanie | Wykres strumienia z błędami, długością fali i czasem pomiaru; postęp obliczeń i cache |
| P2 | Gaia / WISE | Nakładka katalogowa i archiwalny podgląd; daty, pasma i rozdzielczości opisane oddzielnie |
| P0–P2 | Aktualizacje i odtwarzalność | Konfigurowalne kolekcje, zapis produktów i wersji; nowa wersja analizy zamiast cichej podmiany |

Priorytet nie oznacza, że funkcja już istnieje. Publiczną wersję P0 można uruchomić przed ilościowym asystentem P1.

### 21.3. Asystent pasm i składanie

Użytkownik wybiera region lub źródło. Rozdzielamy cel „najlepsza widoczność” od celu „zmiana jasności”. Najpierw powstaje mapa dostępności: czas × lokalna długość fali, wraz z szerokościami odpowiedzi, pokryciem i jakością. Brak obserwacji nie jest zerowym strumieniem.

1. Pomiar na danych naukowych, nigdy na rozciągniętym PNG. Dla izolowanych źródeł można zacząć od fotometrii aperturowej z korektą apertury; docelowo dopasowanie PSF i sąsiadów. Regiony rozległe wymagają osobnej metody, nie automatycznego traktowania jak gwiazdy.
2. Obsługa VARIANCE, FLAGS i lokalnego tła. Propagacja błędów musi uwzględniać wagi interpolacji i korelacje; reprojekcja wariancji tak jak jasności jest niepoprawna. Przy odjęciu modelu ZODI uwzględniamy jego ograniczenia.
3. Kanały grupujemy po rzeczywistych pasmach w miejscu źródła, nie tylko po numerze detektora. Dla szerokiego pola zgodność oceniamy lokalnie; jedno pasmo w centrum nie opisuje całego obrazu.
4. Powtarzane pomiary tej samej wielkości można łączyć wagami odwrotności wariancji. Łączenie różnych długości fal jest osobnym indeksem lub dopasowaniem wzorca widmowego i wymaga zdefiniowania celu. Nie stosujemy automatycznie tej samej reguły do obu przypadków.
5. Dobór ustawień odbywa się na oddzielnej części obserwacji lub na ustalonym wzorcu; jakość oceniamy na niewykorzystanych danych. Kontrolujemy wielokrotne testowanie wielu kanałów i kombinacji.
6. Dla animacji utrzymujemy te same efektywne pasma, wagi i skalę jasności między epokami. Jeśli składniki są niedostępne, ograniczamy oba porównania do wspólnego zestawu lub zgłaszamy brak porównywalności. Nie przeważamy po cichu każdej klatki inaczej.
7. Czas składania ograniczamy ruchem i zmiennością źródła. Nie sumujemy wszystkich dat, bo można rozmazać ruch. Składanie po trajektorii jest dalszym rozszerzeniem; przy niepewnej trajektorii pokazujemy ekspozycje oddzielnie.

Wynik rekomendacji: proponowane pasma i wagi, źródło kryterium, liczba użytych pomiarów, zakres dat, niepewność i ograniczenia. „Brak wiarygodnej rekomendacji” jest poprawnym wynikiem. Efekt przy źródle nie gwarantuje poprawy całego pola.

### 21.4. Widmo, różnice epok i kontekst innych misji

Widmo pokazuje pomiary z ich datami; nie sugeruje jednoczesnej obserwacji wszystkich 102 kanałów. Ruchome źródło wymaga pozycji właściwej dla każdej ekspozycji. Przy zmienności zbiór z różnych terminów nie jest automatycznie jednym statycznym widmem. Pierwszy wynik może być rzadkim wykresem dostępnych punktów, a nie gładką krzywą z uzupełnionymi brakami.

Odejmowanie epok wymaga zgodnej geometrii, jednostek i pasm, modelu tła i kontroli PSF. Wyświetlamy dodatnie i ujemne pozostałości, nie sam ich moduł. Para pozostałości może sugerować ruch, ale błędy rejestracji również ją tworzą. Nie wyznaczamy istotności statystycznej bez poprawnego modelu niepewności.

Gaia dostarcza znaczników katalogowych z epoką i propagacją ruchu własnego, gdy dane na to pozwalają. WISE dostarcza osobny historyczny podgląd lub animację. Danych innych instrumentów nie odejmujemy domyślnie od SPHEREx. Dobór pasujących archiwalnych filtrów może uwzględniać zakres fal, pokrycie, datę i rozdzielczość; brak zdjęcia nie oznacza braku źródła. Sterowanie teleskopami i przydział obserwacji nie należą do zakresu.

### 21.5. Panel „Gdzie patrzę?” — niebo i Ziemia

Cel: użytkownik ma wiedzieć, gdzie znajduje się aktualnie przeglądany obszar nieba oraz w którą stronę należałoby patrzeć z wybranego miejsca na Ziemi.

**A. Mapa nieba — podstawowy widok orientacji**

- Szeroka mapa w Aladin Lite, zsynchronizowana z RA/Dec i polem głównego obrazu; orientacja, podziałka i nazwa warstwy.
- Ramka rzeczywistego wycinka wyznaczona z WCS, nie sam znacznik środka. Przy dużym oddaleniu powiększony znacznik ma etykietę, że nie przedstawia rozmiaru pola w skali.
- Wybór miejsca na mapie aktualizuje formularz. Samo przesuwanie mapy nie rozpoczyna kosztownego pobierania; użytkownik zatwierdza nowe pole.
- Przycisk „Pokaż szerszy kontekst”, a w późniejszej wersji granice gwiazdozbiorów. Mapa kontekstowa jest osobnym zbiorem z własną datą, nie podglądem na żywo ani automatycznie obrazem SPHEREx.

**B. Ziemia i lokalny horyzont — kierunek z punktu obserwatora**

- Prosty schemat Ziemi, osi obrotu, wybranego miejsca i strzałki w stronę środka pola, uzupełniony mapą horyzontu z N/E/S/W, zenitem i znacznikiem celu. Pierwsza wersja może być SVG/Canvas 2D; model 3D jest opcjonalny.
- Kierunek do odległego pola rysujemy jako kierunek, nie pozycję obiektu w umownej odległości od Ziemi. Schemat ma etykietę „nie w skali”. Nie symuluje orbity ani aktualnego ustawienia SPHEREx.
- Miejsce: ręcznie podane współrzędne geograficzne i opcjonalna wysokość. Geolokalizacja przeglądarki tylko po świadomym wybraniu tej funkcji; bez zgody nadal działa formularz. Bez miejsca pokazujemy mapę nieba, bez zgadywania azymutu.
- Czas: przełącznik „teraz” / „data wybranej obserwacji” / „własna data”. Domyślnie data aktywnej klatki, z widocznym opisem. W trybie daty obserwacji odtwarzanie aktualizuje kierunek dla kolejnych klatek; nie sugeruje ciągłej obserwacji pomiędzy nimi.
- Wyświetlamy wysokość nad horyzontem i azymut: 0° N, 90° E, 180° S, 270° W. Przy wysokości ujemnej cel oznaczamy „poniżej horyzontu”. Blisko zenitu azymut może być nieokreślony lub niestabilny; nie pokazujemy pozornej precyzji.
- Przeliczenie SkyCoord → AltAz z EarthLocation i Time w backendzie Astropy; jawny czas UTC z opcjonalnym lokalnym zapisem. W pierwszej wersji bez refrakcji atmosferycznej (pressure=0); podajemy tę informację. Kontrolujemy dostęp i aktualność danych orientacji Ziemi oraz komunikujemy ograniczoną dokładność przy niedostępnych danych.
- „Nad horyzontem” oznacza geometrię, nie gwarancję widoczności: nie uwzględnia automatycznie chmur, zabudowy, jasności nieba, czułości oka lub sprzętu ani transmisji atmosfery dla wybranego pasma podczerwieni.
- Bez modelu ruchu źródła kierunek dotyczy wybranego pola RA/Dec. Nie przedstawiamy go jako dokładnej bieżącej pozycji szybko poruszającego się obiektu.
- Lokalny czas i miejsce opisują perspektywę ziemskiego obserwatora, a nie punkt wykonania obrazu przez SPHEREx. Nie rekonstruujemy pozycji satelity bez rzeczywistych efemeryd.

**Warunki odbioru panelu:** zgodność ramki z narożnikami WCS, poprawne przejście RA przez 0° i pola blisko biegunów; porównanie AltAz z niezależnym punktem odniesienia; przypadki nad/pod horyzontem, zenitu i dwóch lokalizacji w tym samym czasie; jawne zachowanie po odmowie geolokalizacji; czytelność bez rozróżniania samych kolorów. Awaria mapy zewnętrznej nie blokuje obrazów SPHEREx.

### 21.6. Integracja techniczna i odtwarzalność

- Zachowujemy React/TypeScript i FastAPI. Rozbudowujemy istniejący adapter i pipeline zamiast tworzyć konkurencyjną aplikację.
- Wydzielamy pomiary, dobór pasm, operacje czasowe i kontekst nieba do osobnych modułów. Aladin Lite obsługuje mapę, Astropy transformacje, a backend pomiary na FITS.
- Oddzielamy szybki odczyt kierunku od kosztownych zadań pomiarowych. Zmiana czasu w panelu orientacji nie pobiera ponownie FITS. Długie zadania mają postęp, anulowanie lub jawne ograniczenia, cache i limit współbieżności.
- Link do wyszukiwania zawiera RA, Dec, FOV i kolekcję. Link analizy wskazuje zapisane produkty i ustawienia. Widok orientacji zachowuje tryb czasu; miejsce użytkownika pozostaje lokalne i trafia do linku wyłącznie przy świadomym włączeniu „dołącz miejsce obserwatora”. Tryb „teraz” nie jest odtwarzalnym historycznym czasem.
- Manifest nowej analizy zapisuje wydanie, identyfikatory i sumy kontrolne produktów, czasy, lokalne pasma, maski, metodę tła i PSF, wagi, grupowanie czasu, metodę niepewności, skalę wyświetlania i wersję pipeline. Pola nieobliczone są jawnie nieobecne lub oznaczone, nie wypełnione fikcyjnymi wartościami.

### 21.7. Kolejność wdrożenia i dowód wartości

1. Dokończyć rdzeń czasowy oraz walidację pięciu obiektów. Dodać mapę pola i panel lokalnego kierunku — niezależnie od fotometrii.
2. Obsłużyć wariancję i pomiary, z testami tła, flag i sąsiadów. Ustalić dostępność zgodnych grup czasowo-spektralnych na prawdziwych danych.
3. Dodać ręczny dobór pasm i składanie zgodnych obserwacji z podglądem standard / wynik. Zweryfikować niepewności i zachowanie źródeł kontrolnych.
4. Dodać asystenta i sprawdzić go na odłożonych obserwacjach. Dopiero po kontroli tła i PSF udostępnić różnice jako narzędzie pomiarowe; wcześniej wyłącznie jawny podgląd jakościowy.
5. Dodać widmo na żądanie, Gaia/WISE i dopasowanie archiwalnych filtrów; każdą integrację osobno zweryfikować.
6. Publiczny hosting rdzenia nie musi czekać na P2. Dla obliczeń potrzebny jest backend z bibliotekami naukowymi, trwałym magazynem i limitami. Test odtworzenia linku wykonujemy na drugim urządzeniu.

Porównujemy: najlepsze pojedyncze pasmo, proste składanie i propozycję asystenta. Przy tej samej liczbie fałszywych wskazań mierzymy odzyskiwanie znanych źródeł oraz czas i trafność zauważenia ruchu przez użytkowników. Dla gwiazd zmiennych osobno sprawdzamy zmiany jasności. Puste regiony i źródła kontrolne pozwalają ocenić fałszywe alarmy; syntetyczne wstrzyknięcia są jawnie opisanym dodatkiem. Brak poprawy lub brak danych zapisujemy jako wynik, nie maskujemy atrakcyjniejszym kontrastem.

### 21.8. Dokumentacja implementacyjna rozszerzeń

- [IRSA — wydania SPHEREx](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-releases/) — dobór aktualnych produktów i zgodność wydań.
- [IRSA — sposób obserwacji](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/overview.html) — lokalna zależność długości fali i czasu.
- [IRSA — spektrofotometria](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html) — model źródła, tła, PSF i błędów; obliczenia nie muszą być natychmiastowe.
- [Aladin Lite API](https://cds-astro.github.io/aladin-lite/Aladin.html) — mapa, pole i nakładki.
- [Astropy AltAz](https://docs.astropy.org/en/stable/api/astropy.coordinates.AltAz.html) — lokalny horyzont, miejsce, czas i refrakcja. Implementacja musi być sprawdzona z wersją Astropy przypiętą w projekcie.
