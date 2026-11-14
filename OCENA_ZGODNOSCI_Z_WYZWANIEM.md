# Ocena zgodności — Planet X and SPHEREx

**Aktualizacja:** 14 listopada 2026 r.  
**Przedmiot oceny:** aktualna lokalna aplikacja; dowody i pozostałe blokady w [AUDYT_NAPRAWY.md](AUDYT_NAPRAWY.md).

**Źródło wymagań:** oficjalna [strona wyzwania 2026](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/) odczytana w poprzednim audycie 14.11; w finalizacji przeczytano datowany snapshot. Ponowny odczyt narzędziem web zwrócił 502. FAQ odczytano bezpośrednio w przeglądarce; dokumentację IRSA odczytano.

**Status kryteriów:** oficjalny [Judging & Awards Guide 2026](https://www.spaceappschallenge.org/resources/judging-awards-guide/) potwierdza Impact, Creativity, Validity, Relevance, Presentation, każde 1–5. Nie ustalono dodatkowych wag. Aktualna macierz dowodów jest w AUDYT_NAPRAWY.md.

## 1. Wniosek

**Aktualny zakres:** RA/Dec, rzeczywiste FITS, animacja czasu, osobny przegląd pasm, lupa, ręczna trasa, karta dowodowa, eksploracyjne pomiary i diagnostyka oraz kontekst IRSA/Gaia/WISE. Nowe próby pięciu poprawionych pól są w WYNIKI_5_OBIEKTOW.md. Nie potwierdzono ruchu ani zmienności. Asystent wag pozostaje odłożony do walidacji. Wymóg publicznego adresu pozostaje niespełniony.

Pomysł bezpośrednio odpowiada zadaniu, jeśli dostarcza publiczny web, współrzędne RA/Dec oraz rzeczywistą animację obserwacji SPHEREx. Diagnostyka wiarygodności zmiany wzmacnia ten rdzeń. Nie może go zastąpić galeria przygotowanych przykładów, automatyczny klasyfikator ani przeglądarka danych innej misji.

Nie ma podstaw do obiecania maksymalnej oceny za sam plan. Potrzebne są działający produkt, kontrola poprawności i przekonująca demonstracja.

## 2. Wymagania główne

| Element zadania | Co wdrażamy | Dowód realizacji |
|---|---|---|
| Public-facing web tool | Publiczna aplikacja bez konieczności instalacji | Adres działający na drugim urządzeniu |
| RA i Dec | Stopnie oraz zapis godzinowy/kątowy | Poprawne wyszukiwanie i walidacja |
| Obrazy SPHEREx | Adapter archiwum i prawdziwe dane | Identyfikatory produktów, daty i wydania |
| Zmiany w czasie | Wspólna geometria, oś czasu i animacja | Obrazy uporządkowane chronologicznie |
| Wyszukiwanie ruchu | Miganie A/B, znaczniki, kontekst i pomiary | Brak pozornego ruchu wynikającego z kadrowania |
| Testy wskazanych obiektów | Barnard’s Star, Epsilon Indi B, WISE 0855, RW Aurigae, R Draconis | Osobny raport danych, wyniku i ograniczeń każdego obiektu |

Raport braku odpowiednich obserwacji jest uczciwym wynikiem testu, lecz nie dowodem wykrywania zjawiska. Nie twierdzimy, że samo uruchomienie przykładu potwierdza poprawność całego pipeline.

## 3. Rozwinięcia proponowane przez organizatora

| Możliwość | Nasze podejście | Co trzeba dopilnować |
|---|---|---|
| Aktualne wydania | Adapter kolekcji i odświeżanie wyszukiwania | Stare analizy pozostają przypięte do danych |
| Wykorzystanie 102 pasm | Dobór spektralny, grupy przeglądowe i widmo | Dane różnych fal nie są automatycznie porównaniem czasowym |
| Składanie sześciu zakresów detektorów | Podgląd po analizie pokrycia i kalibracji | Ten sam detektor nie gwarantuje zgodnych pasm źródła |
| Dodawanie i odejmowanie | Porównanie po przygotowaniu geometrii, tła i PSF | Odróżnienie widoku jakościowego od pomiaru |
| Zmienny FOV | Wybór pola z informacją o koszcie danych | Pokrycie, czas i wielkość transferu |
| Gaia DR3 | Katalog z uwzględnieniem epoki | Brak dopasowania nie oznacza odkrycia |
| WISE | Kontekst historyczny i ruch w długiej bazie czasu | Różna rozdzielczość i pasma |
| Współrzędne w URL | Link do wyszukiwania i osobno manifest analizy | Publiczny link nie zależy od localStorage |
| Metadane i flagi | Widoczne przesłanki i maski | Znaczenie poszczególnych bitów, nie dowolne maskowanie |
| Gotowe narzędzia | Astropy, Astroquery, Aladin Lite i biblioteki naukowe | Nie deklarujemy standardowych metod jako własnego wynalazku |

NEOSSat i CADC wykorzystujemy po sprawdzeniu, czy faktycznie dostarczają przydatnych danych. Nie wymuszamy wspólnego pokrycia ani nie odciągamy projektu od SPHEREx.

## 4. Kryteria — jak podnosić jakość zgłoszenia

### Impact

**Wartość:** skrócenie drogi od współrzędnych do uzasadnionej interpretacji, bez konieczności samodzielnego programowania obsługi FITS.

**Słabość:** samo istnienie aplikacji nie dowodzi, że pomaga ludziom trafniej oceniać obserwacje.

**Wzmocnienie:** porównać zwykłą animację z wariantem diagnostycznym. Zmierzyć czas, trafność odpowiedzi i jakość uzasadnienia. Podać wielkość i ograniczenia próby. Pokazać dostępność dla początkujących i odtwarzalność wyników.

### Creativity

**Wartość:** użytkownik nie tylko ogląda, ale sprawdza alternatywne wyjaśnienia zaznaczonej zmiany.

**Słabość:** animacja, reprojekcja i fotometria istnieją już w innych narzędziach; sam nowy interfejs to słabszy wyróżnik.

**Wzmocnienie:** pokazać kompletną ścieżkę: podejrzenie → test zgodności pasm → jakość → wyłączenie ekspozycji → wniosek i manifest. Wskazać konkretną różnicę względem WiseView oraz narzędzi IRSA, bez twierdzenia o absolutnej nowości.

### Validity

**Wartość:** wykorzystanie prawdziwych obserwacji i dokumentacji naukowej.

**Słabość:** łatwo stworzyć pozorny ruch lub zmienność przez geometrię, skalowanie, pasma, PSF i tło.

**Wzmocnienie:** testy kontrolne, niezależna kontrola, jednostki, maski, raport błędów i ograniczeń. Rozróżnienie porównania jakościowego od ilościowego. Dane syntetyczne tylko jako jawne testy.

### Relevance

**Wartość:** bezpośrednie dopasowanie do publicznej przeglądarki zmian na obrazach SPHEREx.

**Słabość:** galeria pięciu obiektów albo rozbudowany kontekst Gaia/WISE bez działającego SPHEREx nie realizują dobrze zadania.

**Wzmocnienie:** wyszukiwanie dowolnych współrzędnych w jawnych limitach, działająca animacja i raport wszystkich pięciu obiektów. Podczas pokazu jasno odróżnić cele główne od opcjonalnych rozszerzeń.

### Presentation

**Wartość:** jedno czytelne pytanie — czy zmiana jest rzeczywista, czy wynika z porównania danych?

**Słabość:** zbyt wiele wykresów, żargonu i bibliotek może zasłonić cel.

**Wzmocnienie:** prawdziwy przykład, zaznaczenie źródła, jeden rozstrzygający lub nierozstrzygający test, wyjaśnienie wyniku i odtworzenie linku na drugim urządzeniu. Pokazać jeden wynik walidacji i jedno ograniczenie.

## 5. Źródła i granice oceny

- [Pełny plan projektu](KONCEPCJA_I_PLAN_PROJEKTU.md).
- [IRSA SPHEREx](https://irsa.ipac.caltech.edu/Missions/spherex.html).
- [Oficjalne notebooki](https://caltech-ipac.github.io/irsa-tutorials/spherex/).
- [Struktura i dostęp do obrazów](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/).
- [Przykład istniejącego narzędzia wyszukiwania źródeł](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/).

Nie przyznajemy punktów za funkcje jeszcze niezbudowane. Ostateczny wynik zależy od aktualnych zasad i oceny jury. Plan określa działania oraz dowody, nie gwarantowaną punktację.
