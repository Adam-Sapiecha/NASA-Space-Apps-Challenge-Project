# Stan implementacji — 14 listopada 2026

## Analiza źródeł — pięć obszarów

Dodano kontekst Gaia/SIMBAD/AllWISE z obsługą awarii usług i wskazaniem pozycji na zdjęciu, diagnostykę centroidu/PSF na natywnych FITS, plan stałych wag na podstawie jakości i wariancji, porównanie modeli kontinuum i okien H₂O/CO₂/CO oraz prognozy Gaia, JPL Horizons i lokalnego ruchu liniowego. Wyniki mają raporty, ograniczenia i obsługę kolejki. Szczegóły: [WDROZENIE_ANALIZY_ZRODEL.md](WDROZENIE_ANALIZY_ZRODEL.md).

Zaimplementowano przegląd etykiet, eksport danych, trening regresji logistycznej, grupowy podział danych i warunkową aktywację klasyfikatora artefaktów. **Zbiór zawiera 0 zweryfikowanych przykładów; model ML nie został wytrenowany ani aktywowany.** Nie zastąpiono ich danymi syntetycznymi.

Weryfikacja: 94 testy backendu, 27 testów frontendu i build produkcyjny. Rzeczywista próba sprawdziła natywne FITS, trzy katalogi (SIMBAD przez oficjalne lustro, AllWISE z alternatywnym dostępem) oraz efemerydy Ceres. W przeglądarce sprawdzono diagnostykę i wykres efemeryd. Są to narzędzia eksploracyjne; nie potwierdzono składu, nowych orbit ani skuteczności klasyfikatora. Pozostają pełne krzywe transmisji, niezależna walidacja fotometrii/astrometrii i zweryfikowany zbiór do uczenia.

## Stan po finalizacji

Aktualny punkt odniesienia: **[AUDYT_NAPRAWY.md](AUDYT_NAPRAWY.md)**. Poniższe starsze sekcje opisują kolejne aktualizacje i wcześniejsze zakresy weryfikacji; nie są jedną zbiorczą deklaracją gotowości.

- Poprawione tożsamości i centra pięciu presetów, wspólne dane dla UI i skryptów, jawne epoki i właściwe dla dat przewidywania w nowym audycie.
- Nowe próby: 22/25 pobranych produktów, trzy jawne błędy 503, cztery ważne apertury WISE 0855 i jedna para o bliskich pasmach; bez potwierdzenia detekcji, ruchu lub zmienności. Starsze pola Epsilon Indi B i R Draconis były błędne.
- Fotometria v2 odrzuca dodatkowe flagi artefaktów i wyklucza SOURCE z tła. Stare pomiary pozostają zapisane, nowe mają osobny klucz metody. Brak czystego tła daje odmowę, bez wypełniania braków.
- Błąd procesu roboczego daje jawny status błędu/HTTP 503. Health zawiera fingerprint załadowanego kodu i flagę jego zmiany; build frontendu nie synchronizuje backendu.
- Samodzielna karta dowodowa HTML po angielsku, z obrazami, punktem, pomiarem i pochodzeniem; pełny JSON. Angielski replay prawdziwych obserwacji działa bez IRSA.
- Błędy odpowiedzi HTML/503 i utraty połączenia mają czytelne komunikaty; ograniczono przywracanie pomiaru niezgodnego z punktem oraz stare wyniki IRSA. Naprawiono przepełnienie mobilne podpowiedzi Aladin.
- Weryfikacja i ograniczenia aktualizowane są w audycie napraw. Publiczny backend, drugi fizyczny telefon, niezależna astrometria i porównanie ePSF z rzeczywistym Tractor nadal nie są ukończone. Pełny interfejs pozostaje polski; materiały demonstracyjne są angielskie.

## Uporządkowanie procesu od pola do zapisanej obserwacji

- Wstępna propozycja wybiera jeden detektor według liczby różnych terminów (bez stałej preferencji D2) i do ośmiu obserwacji rozłożonych według rzeczywistego czasu. Pokazuje daty, liczby obserwacji i uzasadnienie. To dobór przeglądowy; metadane archiwum nie potwierdzają lokalnego pasma.
- Po pobraniu wybierany jest największy zestaw wzajemnie zbliżonych pasm z różnych terminów. W centrum wymagane jest co najmniej 80% ważnego pokrycia każdej klatki; po kliknięciu sprawdzana jest ważność piksela oraz lokalne pasma. Użytkownik może wyłączyć filtr i oglądać wszystkie klatki. Próg połowy węższego pasma pozostaje heurystyką, bez kalibracji naukowej.
- Osobny pełnokadrowy widok „Seria dat” odtwarza kolejne obserwacje chronologicznie. Miganie A/B pozostaje osobnym trybem. Opis ostrzega, że równe tempo klatek nie odpowiada rzeczywistym odstępom dat.
- Wybór pojedynczego obrazu i częściowe powodzenie pobierania zachowują użyteczne klatki. Ponowienie nieudanych składników tworzy nową analizę, kopiuje gotowe FITS/NPZ, ponawia brakujące i przelicza wspólną skalę podglądu. Pierwotny manifest pozostaje zachowany.
- Rozdzielono sprawdzanie przesunięcia i jasności. Diagnostyka wskazuje następny krok i umożliwia poszukanie lokalnie zbliżonej pary. Pomiary dotyczą przypiętej pozycji, niezależnie od późniejszego ruchu lupy. Wykres czasu domyślnie pokazuje największą grupę zbliżonych pasm; wszystkie wartości pozostają w tabeli.
- Ręczna trasa ma opis modelu liniowego na wspólnym obrazie i ocenę użytkownika w kolejnych terminach: pasuje / nie pasuje / nie da się ocenić. Nie jest dopasowaniem astrometrycznym ani modelem orbity.
- Karta podejrzenia zapisuje na serwerze notatkę, rodzaj podejrzenia, klatki, punkt, trasę, oceny kolejnych terminów oraz podstawowe ustawienia widoku. Powstaje osobny identyfikator, link i eksport JSON. Karta może odwoływać się do pomiaru tego samego punktu oraz diagnostyki zapisanej pary. Walidacja odrzuca klatki i pomiary z innej analizy.

Walidacja tej zmiany: 54 testy backendu i 20 testów frontendu; kontrolowane przypadki wzajemnej zgodności pasm, lokalnych braków, rozkładu dat, częściowego pobrania i ponowienia bez ponownego przetwarzania udanej klatki. W przeglądarce sprawdzono rzeczywisty zapisany przykład, wybór punktu klawiaturą, zapis notatki oraz odtworzenie punktu i tekstu po odświeżeniu, odtwarzanie i zatrzymanie serii dat oraz zapis karty z odnośnikami do pomiaru i diagnostyki. Starsze pomiary z cache otrzymują brakujące współrzędne punktu bez ponawiania obliczeń. Build produkcyjny przechodzi; pozostaje ostrzeżenie Vite dotyczące rozmiaru chunka Aladin. Pełne badanie użyteczności, identyfikacja pięciu źródeł, walidacja fotometrii oraz publiczny hosting nadal pozostają osobnymi pracami. Wcześniejsze ograniczenia naukowe zachowują ważność.

## Kontrola wiarygodności różnicy A/B

Pod zdjęciami dodano panel „Czy ta zmiana jest wiarygodna?”. Na żądanie wykonuje lub odtwarza natywne pomiary apertury i porównuje wybrane A/B. Pokazuje różnicę strumieni z błędem losowym, lokalne pasma, odstęp czasu, flagi i diagnostykę sąsiadów. Osobno opisuje niezweryfikowane tło oraz PSF, centrowanie i ruch. Brak ważnych pomiarów, niezgodne lokalne pasma lub ten sam termin blokują interpretację. Panel nie potwierdza zmienności i nie wyznacza istotności statystycznej. Raport JSON zawiera identyfikatory źródeł, ustawienia oraz uzasadnienia i dalsze kroki. Starsze zapisane pomiary bez współrzędnych punktu na obrazie są obsługiwane przez zachowane RA/Dec.

Sprawdzono kontrolowane przypadki stałego źródła ze zmianą tła, wprowadzonej różnicy, niezgodności pasm, flag, sąsiadów, braków i niepoprawnych wartości; również odwrócenie A/B i eksport przez API. Test na zapisanej rzeczywistej parze z `data/smoke_api.json` zwrócił raport z ostrzeżeniami i statusem wymagającym weryfikacji. Build TypeScript/Vite i 8 testów frontendu przeszły. Nie wykonano wizualnego testu nowego panelu w przeglądarce ani badania skuteczności wykrywania zmienności.

## Wdrożenie planu 4.0 — pipeline 0.2.0

Rozwinięto istniejącą aplikację React/FastAPI zgodnie z sekcją 21 koncepcji. Zachowano lupę, miganie, animację, szkic ruchu i dotychczasowe analizy. Nie nadano projektowi odrębnej nazwy. Jest to lokalna implementacja rozszerzeń z opisanymi niżej ograniczeniami, a nie zakończenie całej walidacji naukowej ani publiczny hosting.

| Zakres | Stan kodu i ograniczenia |
|---|---|
| Rdzeń czasowy | Rzeczywiste RA/Dec, DR1/QR3, 2–30′, do 12 ekspozycji, wspólny WCS i skala, lupa, miganie, trasa, link |
| Gdzie patrzę? | Aladin Lite 3.9.2-beta z lokalnego buildu; ramka z 68 próbek brzegów WCS; wybór środka mapy aktualizuje formularz bez wyszukiwania FITS |
| Horyzont | Astropy 7.2.3, EarthLocation/SkyCoord/AltAz; ręczne miejsce lub geolokalizacja po kliknięciu; epoka B / teraz / własne UTC; bez refrakcji, komunikat o ograniczeniach IERS; schemat Ziemi i mapa horyzontu |
| Prywatność i linki | Miejsce domyślnie lokalne; dołączane do URL tylko po zaznaczeniu opcji. Link zachowuje tryb czasu, kolekcję, produkt i zapisany pomiar |
| Ręczne pasma | Wybór ekspozycji z sześciu grup detektorów; lokalne pasma po kliknięciu, filtr zakresu w centrum, ręczne stałe wagi |
| Pomiary | Eksploracyjna apertura na natywnym IMAGE/VARIANCE/FLAGS przed reprojekcją; średnie tło w pierścieniu 1,8–3 promieni, pełne pokrycie apertury, diagnostyka sąsiadów, mJy i formalny błąd losowy |
| Widmo i czas | Na żądanie, cache i eksport JSON; oddzielne punkty z datami, lokalnymi pasmami, flagami i błędami. Brak interpolowanego widma i obietnicy jednoczesności |
| Składanie | Stałe dodatnie wagi, okno do 48 h, wyłącznie wspólne ważne piksele o zbliżonych lokalnych pasmach. Wspólna skala standard / wynik; ręczne wyłączenie ekspozycji |
| Różnica | Jakościowe A−B na wspólnej siatce, zachowany znak, symetryczna czerwono-biała-niebieska skala i jednostki; bez PSF i pomiarów istotności |
| Asystent | Kontrola dostępności i warunków wiarygodności. Zwraca „brak wiarygodnej rekomendacji”, bez wag, dopóki nie ma kalibracji i niezależnej walidacji. Automatyczny ranking i dobór wag pozostają do wykonania |
| Gaia DR3 | Adapter VizieR z oficjalnymi lustrami Harvard/IDIA, cache, limit 500; liniowa propagacja ruchu własnego z epoki 2016.0 do B; brakujące ruchy pozostają w epoce katalogowej |
| WISE | Osobny historyczny podgląd AllWISE W4/W2/W1 przez HiPS IRSA; bez odejmowania od SPHEREx. Brak animacji WISE i doboru archiwalnych filtrów |
| Odtwarzalność | Nowe manifesty schema 2 z obrysem WCS i metodą; produkty mają osobne identyfikatory, parametry, daty, wagi, SHA-256 i eksport FITS/PNG/JSON. Powtórne obliczenie przywraca istniejący produkt |

## Sprawdzone w tej aktualizacji

- 33 testy pytest: wcześniejszy rdzeń, brzegi WCS przy RA=0 i biegunach, niezależny wzór sferyczny dla wysokości w dwóch miejscach, nad/pod horyzontem i zenit, odzyskanie kontrolowanego sygnału i propagacja wariancji apertury, flagi i sąsiedzi, stałe wagi, brak pokrycia, znak różnic oraz propagacja Gaia i fallback serwera.
- 5 testów frontendu i produkcyjny build TypeScript/Vite. Aladin jest osobnym chunkiem ładowanym na żądanie (około 2,6 MB, 840 kB gzip); Vite zgłasza ostrzeżenie o rozmiarze tego chunka.
- Test integracyjny działającego API na zapisanej rzeczywistej parze SPHEREx: ramka, AltAz, natywna apertura z wariancją, odmowa niezwalidowanej rekomendacji, różnica, PNG/FITS/manifest i odtworzenie niezmiennego produktu. Wynik: `data/smoke_plan_v4.json`; skrypt `scripts/smoke_plan_v4.py`.
- Próba składania dwóch rzeczywistych ekspozycji Epsilon Indi B oddalonych o około 129 s została poprawnie odrzucona: brak wspólnego ważnego pokrycia o zbliżonych lokalnych pasmach. Poprawność ważonego składania zweryfikowano na kontrolowanych tablicach; nie deklarujemy udanego składania tej pary.
- Nowe zapytania IRSA dla pięciu pól, pobranie i reprojekcja po dwóch FITS oraz pomiary apertury. Raport: [WALIDACJA_PLANU_V4.md](WALIDACJA_PLANU_V4.md), dane `data/audit/plan-v4.json`. Zbliżone pasma w centrum znaleziono w wybranej parze Epsilon Indi B. Dla pozostałych porównanie ogranicza lokalne pokrycie, flagi lub różnica pasm. To nie jest potwierdzenie detekcji obiektów.
- Rzeczywiste zapytanie Gaia przez Harvard: 266 źródeł w promieniu 2′ wokół startowej pozycji Barnard’s Star, 240 z ruchem własnym; propagacja do MJD 61000. Główne usługi CDS zwracały 404, dlatego użyto oficjalnych luster i warstw HiPS IRSA.

## Granice weryfikacji i prace pozostałe

- Nowy interfejs nie przeszedł pełnej kontroli wizualnej: narzędzie przeglądarki zwracało odmowę dostępu (`GetCursorPos`), a okno systemowe było niedostępne do bezpiecznej kontroli. Nie potwierdzono w tej aktualizacji renderowania Aladin/WebGL, mobilnego układu ani odmowy geolokalizacji w przeglądarce.
- Brak identyfikacji pięciu źródeł i korekty pozycji presetów do epok, niezależnej astrometrii oraz badania skuteczności użytkowników. Dostępność obrazu pola nie dowodzi detekcji źródła.
- Pomiary są eksploracyjne: bez kalibracji apertury/PSF, modelowania sąsiadów i pełnej kowariancji. WCS-WAVE ma dokładność do podglądu; do analizy naukowej potrzebne są kalibracyjne CWAVE/CBAND. Błąd losowy nie jest całkowitą niepewnością źródła.
- Brak dopasowania PSF i tła między epokami, ilościowej różnicy i skalibrowanego asystenta z oceną na odłożonych danych. Nie wykonano testu poprawy wykrywalności.
- WISE dostarcza kontekstu, bez animacji historycznych epok i automatycznego dopasowania filtrów. Gaia nie zapewnia pełnej pozycji pozornej ani paralaksy; zapytanie może ominąć szybkie źródła spoza promienia katalogowego.
- IERS działa offline na lokalnej tabeli; czas poza jej zakresem obniża dokładność i wyświetla ostrzeżenie. Nie rekonstruujemy pozycji SPHEREx.
- Brak publicznego hostingu HTTPS i testu odtworzenia linku na drugim urządzeniu. Kontener i responsywność nowych paneli wymagają osobnej weryfikacji. API ma jawne limity, cache i pojedynczy proces obliczeniowy; nie ma trwałej kolejki ani automatycznego czyszczenia danych.

## Wcześniejszy audyt interfejsu

Wdrożono jasny układ redakcyjny, lokalne fonty IBM Plex Sans i Source Serif 4, tabelę ekspozycji oraz autentyczne materiały SPHEREx z podpisami. Zachowano integracje i pipeline naukowy. Dodano fokus i wybór punktu klawiaturą oraz jawny tryb przesuwania obrazu. Sprawdzono widoki przy szerokościach 320, 390, 768 i 1440 px oraz kontrast tekstów w badanym stanie. Szczegóły krytycznego audytu i ograniczeń w DESIGN_AUDIT.md; źródła i prawa do materiałów w ASSET_SOURCES.md.

## Uproszczenie interfejsu po ocenie użytkownika

Usunięto hero, ilustracje i redakcyjne sekcje. Ekran zaczyna się od wyboru obiektu i wyszukania obrazów. Gotowy, istniejący przykład można otworzyć jednym przyciskiem; API nie pokazuje przykładu bez zapisanych klatek. Lista ekspozycji, współrzędne, metody i eksport są rozwijane. Porównanie, mapa i pomiary mają oddzielne zakładki. Przy obrazie jest jedna instrukcja zależna od trybu; pomiar wymaga zaznaczenia punktu. Zachowano ostrzeżenia o niezgodnych pasmach i ograniczenia wyników. Usunięto font nagłówkowy Source Serif z aktywnego interfejsu.

Sprawdzenie: build TypeScript/Vite, testy algorytmów frontendu i API. Pełna kontrola wizualna nadal zablokowana przez odmowę dostępu narzędzia przeglądarki.

## Obsługa dla początkujących i pełne kadry

Dodano przebieg 1: miejsce, 2: zdjęcia, 3: zmiana. Domyślny widok pokazuje dwa całe zdjęcia, obok siebie lub jedno pod drugim na wąskim ekranie. Dopasowanie nie ucina brzegów; przesuwanie jest ograniczone do powiększonego zdjęcia, a „Dopasuj” przywraca pełny kadr. Animację można zatrzymać. Zaznaczenie punktu jest wspólne dla obu zdjęć. Wielkość pola ma proste wybory Mały / Średni / Duży, z zachowaniem dokładnego FOV w szczegółach.

Podgląd wszystkich dostępnych pikseli powstaje z natywnego IMAGE przed odrzuceniem flag. Ostrzeżenia mają osobną nakładkę obrysów; brak obserwacji ma kreskowanie. Alternatywny widok po kontroli jakości nadal jest dostępny. Pomiary i naukowe FITS zachowują dotychczasowe maski. Można zmienić wspólną skalę wyświetlania, w tym wybrać pełne minimum–maksimum bez obcięcia jasnych wartości; ustawienia trafiają do linku.

Na zapisanej parze Barnard’s Star udział pikseli dostępnych do podglądu wzrósł z 97,59% / 98,23% po kontroli jakości do 98,84% / 99,61% w podglądzie oryginalnym. Ostrzeżenia dotyczą około 0,42% / 0,45% pikseli. Pozostałych braków nie wypełniono.

Walidacja: 38 testów backendu i 8 frontendu, w tym brak ucinania czterech brzegów, zgodność kliknięcia w obu widokach i zachowanie maskowanych wartości w FITS po wygenerowaniu oryginalnego podglądu. Build przeszedł. Nie deklarujemy przeprowadzonego testu użyteczności z laikami ani pełnego QA przeglądarkowego.


## Interaktywny przegląd długości fal — 14 listopada 2026

Dodano `SpectralExplorer.tsx`, algorytmy w `spectral.ts` i zakładkę Pasma, zachowując istniejące tryby porównania, serię dat, kartę podejrzenia oraz pomiary. Wdrożono suwak posortowanych obserwacji, odtwarzanie z tempem, opcjonalne zabarwienie podglądu, wspólne skalowanie, mapę pokrycia spektralnego, wybór punktu, lokalne pasma i flagi oraz przejście do panelu pomiarów. Braki długości fali i błędy pobierania są jawne. Zabarwienie zachowuje przezroczystość braków i nie modyfikuje FITS ani pomiarów. Odtwarzanie zatrzymuje się przy zmianie zakładki lub wyborze punktu.

Dobór spektralny proponuje do 12 produktów z różnych detektorów w możliwie bliskich terminach. Po pobraniu FITS dostępne lokalne pasma mogą być inne niż sugerowane przez zakres detektora. Przejście do czasu dobiera parę względem aktualnej klatki, zamiast przenosić użytkownika do największej grupy innego pasma. Zgodność pozostaje heurystyką przeglądową. Udostępniony URL zachowuje tryb spektralny, wybraną klatkę i punkt.

Walidacja: 22 testy frontendu i produkcyjny build TypeScript/Vite przeszły. Dodano 7 testów przypadków brzegowych: kolejność widmowa, lokalne braki bez fallbacku do centrum, niepoprawne metadane, dobór detektorów i terminów, limit produktów oraz para czasowa zakotwiczona w wybranym paśmie. Pełny zestaw backendu: 54 testy przeszły po uruchomieniu poza ograniczeniami sandboxu Windows z lokalnym katalogiem tymczasowym. Pierwotna próba w sandboxie napotkała odmowy dostępu; nie był to wynik końcowej weryfikacji.

Przez przeglądarkę otwarto rzeczywiste dane, przygotowano zestaw 12 produktów (10 udanych, dwa błędy IRSA HTTP 503/422), sprawdzono odtwarzanie pasm, ręczne przełączanie, wybranie punktu klawiaturą, lokalne pasma, przejście do pomiaru i wykonanie pomiarów FITS. Skopiowany link odtworzył wybraną klatkę i punkt po przeładowaniu. Sprawdzono komunikat o braku drugiej porównywalnej epoki. Przy szerokości viewportu 390 px dokument nie miał poziomego przepełnienia. Nie jest to pełny audyt pozostałych paneli, test użyteczności ani potwierdzenie detekcji źródła.

Przykład: analiza `7e67f96510f848eebe9407d07022d484`, sześć detektorów, około 0,744–4,876 µm w centrum, około 0,27 dnia. Manifesty i oryginalne FITS są zachowane w lokalnym `data/`. Pełna mapa całego nieba w kanałach oraz kalibracja naukowa odpowiedzi spektralnej pozostają poza tym wdrożeniem. Nie dodano publicznego hostingu.

## Dalsza integracja IRSA — 14 listopada 2026

Dodano osobną mapę całego nieba SPHEREx DR1 HiPS w „Gdzie patrzę?”, z wyborem długości fali, oficjalnymi metadanymi i pominięciem pustych kanałów 50/51. Backend mapuje kafelki kanałów i Allsky do wirtualnych warstw HiPS; ma limity rozmiaru i cache. Mapa nie zastępuje pojedynczych obserwacji ani ich fotometrii.

W „Dokładniejszej analizie” dodano kalibrowane lokalne pomiary aperturowe i ePSF z płaszczyzną tła. Mapy CWAVE/CBAND i powierzchni piksela są dobierane według wydania i detektora, przypinane z jednoznacznej listy S3 oraz weryfikowane geometrycznie względem WCS-WAVE. Zachowano wersje i SHA-256. Brak ważnych pikseli, pełnej apertury lub odpowiedniej kalibracji daje jawny powód odmowy pomiaru. Duże χ² jest oznaczane jako słabe dopasowanie. Nie wdrożono pełnych krzywych transmisji ani oficjalnego Tractor.

Dodano import eksportu spektrofotometrii IRSA z kontrolą jednostek, zgodności ekspozycji, detektora, pozycji i wydania. Obliczenia w Data Explorer nadal uruchamia użytkownik; aplikacja udostępnia plik celu i porównuje dostarczony wynik. Nie przedstawiono testu syntetycznego jako walidacji rzeczywistym eksportem IRSA. Odrzucane są zewnętrzne odwołania XML oraz niejednoznaczne dopasowania.

Ekstrakcja kandydatów korzysta z SEP, wariancji, flag i lokalnego tła; wynik można otworzyć na zdjęciu. To niezależny adapter przebiegu notebooka, nie cały oficjalny pakiet z zewnętrznym SExtractor. MOST wykonuje rzeczywiste zapytania o znane obiekty, z zakresem do 31 dni. Obsługiwane są jednoznaczne identyfikatory NAIF. Wyniki obu narzędzi nie potwierdzają detekcji ruchu. Operacje korzystają z istniejącej kolejki z postępem i trwałymi raportami.

Walidacja: 67 testów backendu i 22 testy frontendu przeszły; build produkcyjny TypeScript/Vite przeszedł. Testy obejmują odzyskanie znanego strumienia przy przesunięciu podpikselowym i zmiennej powierzchni piksela, maskowanie artefaktu w ekstrakcji, jednostki CSV/VOTable i odrzucenie błędnych dopasowań. Test przez działające API (`scripts/smoke_irsa.py`) potwierdził 102 kanały, prawdziwe PNG kafelka i Allsky, dwie poprawnie obliczone pozycje w raporcie kalibracji, 83 kandydatów oraz 160 rekordów MOST dla 3I, 1–20 sierpnia 2025. Są to kandydaci i przecięcia pól, nie potwierdzone obiekty. Osobno sprawdzono kalibrację rzeczywistego FITS D6 (około 4,840 µm). Wynik zbiorczy zapisano w `data/smoke_irsa_api.json`.

Nie wykonano walidacji lokalnego ePSF względem rzeczywistego eksportu Tractor. Błędy są losowe, bez pełnej systematyki i dopasowania sąsiadów. Kontrola wizualna nowych paneli w tej sesji była niedostępna: narzędzie CUA zwróciło `GetCursorPos: access denied`; nie deklarujemy jej wykonania. Aplikacja działa lokalnie na porcie 8000.


## Jedno wejście i prosty przebieg dla jury — 14 listopada 2026

Dodano główny widok `GuidedStart.tsx`: jeden przycisk do rzeczywistego przygotowanego przykładu, dwa terminy, zaznaczony punkt, miganie i jedno żądanie sprawdzenia. Komunikat wyniku rozróżnia niedostępne porównanie i niepotwierdzoną zmianę. Nie wyznacza istotności ani prawdopodobieństwa odkrycia. Dane, metody i istniejące obliczenia backendu nie były zmieniane w tym wdrożeniu.

Krótkie uzasadnienie jest widoczne, szczegółowe kontrole są rozwijane. `GuidedBands.tsx` pozwala obejrzeć rzeczywiste dostępne pasma na tej samej stronie; jawnie opisuje osobny przykład i różne daty. Widok główny ma PL/EN i zapisuje język w URL. Pełny warsztat nadal obsługuje własne współrzędne i dotychczasowe linki. Usunięto osobny link „Demo” z głównej nawigacji; zapasowy replay został w pomocy. Obecne przygotowane analizy i seed zawierają użyte identyfikatory z `showcase.json`.

Walidacja: 27 testów frontendu przeszło, w tym trzy nowe kontrole bezpiecznej prezentacji wyniku: duży iloraz różnicy i błędu nie jest odkryciem, blokada porównania nie daje wniosku o jasności, brak lub nieważny pomiar nie staje się sukcesem. Build TypeScript/Vite przeszedł. Pozostaje wcześniejsze ostrzeżenie o dużym opcjonalnym chunku Aladin. Pełnego audytu naukowego nie zastępują zmiany interfejsu.

Kontrola przeglądarkowa nowego wejścia: PL/EN, otwarcie prawdziwej pary, wynik −0,193 ± 0,243 mJy z niepotwierdzonym statusem, rozwijany przegląd 10 pasm i zmiana suwaka klawiaturą. Własne współrzędne otwierają pełne narzędzia. Przy viewport 390 px scrollWidth dokumentu wyniósł 375 px (brak poziomego przepełnienia). Zapisano data/guided-home-preview.jpg. Końcowy odczyt konsoli w sprawdzanym scenariuszu nie zawierał błędów. Nie przeprowadzono badania użyteczności z jurorami.


## Korekta nawigacji — pełna aplikacja jako domyślne wejście

Po uwadze użytkownika wycofano domyślne wejście do ograniczonego przewodnika. `/` ponownie pokazuje pełny warsztat i wczytuje prawdziwy zapisany przykład, aby wszystkie narzędzia były dostępne od razu. Nowe RA/Dec i jawny identyfikator analizy mają pierwszeństwo przed przykładem. Przewodnik jest wyłącznie opcją w pomocy.

Zachowano wszystkie podłączone komponenty, również SourceAssessment, WeightedFlux i ScienceModels. Sześć widocznych grup rozdziela obrazy/ruch, pasma, mapę, pomiary/składanie, kalibracje/źródła oraz wynik/eksport. Karta i diagnostyka są w grupie wyników; kalibracje, SEP, MOST i modele fizyczne w grupie kalibracji. Nie usuwano modeli, obliczeń, endpointów ani danych.

Wprowadzono zgodność nawigacji ze starymi linkami raportów IRSA i notatek. Testy frontendu: 30 przeszło, w tym trzy nowe regresje głównego wejścia, zachowania własnych współrzędnych i odtwarzania linków. Build TypeScript/Vite przeszedł. W przeglądarce sprawdzono dostęp do grup pomiarów, kalibracji wraz z nowymi narzędziami naukowymi, wyników, pasm i mapy. Diagnostyka rzeczywistej pary zwróciła wynik wymagający weryfikacji, −0,1931 ± 0,2426 mJy; nie jest to detekcja zmienności. To kontrola nawigacji, a nie ponowna walidacja wszystkich metod naukowych.

## Poprawki po niezależnym audycie matematycznym

Po poleceniu „popraw” wdrożono wspólną definicję ciągłego punktu, poprawiony eksport tras i jawne położenie stałej fotometrii, ścisłe dopasowanie metadanych referencji, mapy powierzchni w podstawowej aperturze, normalizację próbkowanego ePSF i SVD. Estymatory mają osobną ważność, a panel pokazuje czułość na ustalone przesunięcia i model tła. Doprecyzowano heurystykę pasma, archiwalne metody i niezależność obserwacji. ML wymaga grupowania po oryginalnych ekspozycjach i bramek ufności; stare modele są zachowane, ale nie aktywowane jako bieżące.

Przeszły 104 testy backendu, 30 frontendu, build oraz kontrola 22 prawdziwych FITS bez zmiany oryginałów. Działające API i przeglądarka potwierdziły nowy wynik, odtworzenie linku i panel odporności. Aplikacja pozostaje lokalna, bez publikacji i bez treningu ML. Szczegóły, nowe wyniki, wersje i nadal obowiązujące ograniczenia naukowe: [NAPRAWY_AUDYTU_MATEMATYCZNEGO.md](NAPRAWY_AUDYTU_MATEMATYCZNEGO.md). Nie potwierdzono ruchu, zmienności, molekuł ani odkrycia.
