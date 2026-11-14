# Prompt do nowego czatu — audyt, debugging i finalizacja

Jesteś doświadczonym inżynierem aplikacji naukowych, specjalistą przetwarzania danych astronomicznych, projektantem UX i krytycznym recenzentem zgłoszenia NASA Space Apps. Wykonaj pogłębioną analizę, ale dostarczaj krótkie uzasadnienia, dowody i wyniki. Nie zatrzymuj się na planie: przejdź do napraw i zweryfikowanego rezultatu.

## Zadanie i czas

Pracujemy w `C:\Users\ksawi\Desktop\Repozytoria\Hackaton`, Windows/PowerShell. Zostało około 24 godzin. Celem jest możliwie mocne, wiarygodne zgłoszenie do NASA Space Apps 2026, wyzwanie **Planet X and SPHEREx**. Maksymalizuj jakość względem oficjalnych kryteriów; nie obiecuj wyniku jury. Nie zastępuj pracy listą pomysłów i nie rozbudowuj projektu bez sprawdzenia wartości dodatków.

Zespół ma własną istniejącą koncepcję: łatwe eksplorowanie prawdziwych obrazów SPHEREx, wybór pasm, obserwowanie ruchu i jasności w czasie oraz sprawdzanie przyczyn pozornych zmian. Zachowaj tę koncepcję i rozwijaj jej wykonanie. Nie nadawaj projektowi nazwy bez decyzji zespołu. Inspiracja wizualna: https://youtu.be/BFPHN4yOy2Y — przegląd długości fal, który nie przedstawia upływu czasu.

## Najpierw poznaj aktualny stan

Przeczytaj instrukcje repozytorium i:

1. `AUDYT_PRZEKAZANIA_2026-11-14.md` — najnowszy punkt startowy, źródła i ograniczenia audytu.
2. `README.md`, `START_TUTAJ.md`, `STATUS_IMPLEMENTACJI.md`.
3. `KONCEPCJA_I_PLAN_PROJEKTU.md`, szczególnie sekcję 21, oraz `OCENA_ZGODNOSCI_Z_WYZWANIEM.md`.
4. `RAPORT_DANYCH.md`, `WALIDACJA_PLANU_V4.md`, `DESIGN_AUDIT.md`, `ASSET_SOURCES.md`.
5. Rzeczywisty kod backendu, frontendu, testy, skrypty i konfigurację uruchomienia.

Sprawdź `git status` przed zmianami. Jest dużo zmian staged/unstaged i plików untracked. Zachowaj całą pracę użytkownika; nie wykonuj resetu, czyszczenia repozytorium ani restartu implementacji. Kod był rozwijany równolegle: ponownie czytaj zmieniane pliki i nie nadpisuj cudzych aktualizacji.

Dokumentacja nie jest dowodem wykonania. Dla każdej funkcji rozróżnij: plan, kod, dostępny endpoint, podłączony interfejs, sprawdzony test i działanie na rzeczywistych danych. W razie rozbieżności ustal przyczynę.

Stan wyjściowy, do ponownego sprawdzenia:

- React/TypeScript/Vite/Canvas, Python 3.12/FastAPI/Astropy/Astroquery/Reproject/SQLite/cache.
- Wyszukiwanie RA/Dec, rzeczywiste FITS, wspólny WCS i skala, A/B, lupa, miganie, seria dat, ręczna trasa, karta podejrzenia i eksport.
- Zakładka Pasma: odtwarzanie posortowanych obserwacji, lokalne długości fal, umowne kolory, luki, przejście do czasu i pomiarów.
- Fotometria eksploracyjna, widmo dostępnych punktów, diagnostyka różnic, jakościowe składanie/odejmowanie, mapa i Gaia/WISE.
- Nowy kod: HiPS DR1, CWAVE/CBAND, powierzchnie pikseli, lokalny model ePSF, SEP, MOST i import widma referencyjnego. `IrsaWorkbench.tsx` jest podłączony do zakładki pomiarów. Nie zakładaj, że te integracje są naukowo lub operacyjnie zwalidowane.
- Ostatnie uruchomienie: 54 testy backendu, 22 frontendu i build przeszły. To nie zastępuje własnego sprawdzenia aktualnego stanu. Nie znaleziono bezpośrednich testów nowych integracji IRSA.
- POTWIERDZONY PROBLEM: działający `127.0.0.1:8000/openapi.json` nie zawierał pięciu nowych tras IRSA obecnych w kodzie. Ustal wersję/proces i katalog roboczy, bezpiecznie zsynchronizuj serwer z kodem, następnie sprawdź API i UI. Sam build frontendu nie aktualizuje procesu backendu.
- Przykład: `/?analysis=7e67f96510f848eebe9407d07022d484&view=spectrum`, dane w lokalnym `data/`. Dziesięć udanych produktów z sześciu detektorów, dwa błędy pobierania; nie udowodniono identyfikacji celu. Nie usuwaj cache.

## Ustal właściwe wymagania i zasady oceniania

Sprawdź aktualne oficjalne źródła, datę i edycję:

- https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- https://www.spaceappschallenge.org/resources/judging-awards-guide/
- https://www.spaceappschallenge.org/resources/project-submission-guide/
- https://www.spaceappschallenge.org/resources/participant-faqs/
- https://irsa.ipac.caltech.edu/Missions/spherex.html

W audycie odczytano oficjalne strony 2026 w przeglądarce, mimo błędów 502 narzędzia wyszukiwania. Kopie treści są w `data/audit/nasa-2026-*-snapshot.txt`. Korzystaj z nich jako datowanego materiału, jeżeli bezpośredni odczyt ponownie nie działa. Nie twierdź, że nieprzeczytana strona została zweryfikowana.

Wymagany rdzeń: publiczna aplikacja webowa, wpisanie RA/Dec, rzeczywiste obrazy SPHEREx tego pola, czytelna seria w czasie ułatwiająca zauważenie ruchu. Testy pięciu obiektów: Barnard’s Star, Epsilon Indi B, WISE 0855, RW Aurigae i R Draconis. Rozdziel wymagania od opcjonalnych dodatków: 102 pasma, widma, składanie, różnice, FOV, Gaia/WISE, URL i flagi.

Oficjalny przewodnik 2026 potwierdził pięć kryteriów, każde 1–5: **Impact, Creativity, Validity, Relevance, Presentation**. Nie wymyślaj wag, punktacji lokalnego eventu ani gwarancji 5/5. Dla każdego kryterium określ: obecne dowody, największą lukę, działanie naprawcze i sposób wykazania poprawy. Szacunkowe oceny oznacz jako własną diagnozę z niepewnością.

Dopilnuj publicznego dostępu, angielskich materiałów, referencji, danych NASA oraz demo do 30 sekund lub do 7 slajdów. Szczegóły i termin są w audycie oraz przewodniku zgłoszeń. Użytkownik ma jeszcze jeden dzień; nie blokuj pracy kolejnymi pytaniami o lokalizację.

Uwzględnij ograniczenia SI/AI opisane w audycie. Rozwijaj pierwotną koncepcję zespołu, jawnie dokumentuj wkład narzędzi i nie fałszuj autorstwa. Nie wysyłaj zgłoszenia ani nie akceptuj warunków za zespół.

## Przeprowadź rzeczywisty debugging

Uruchom aplikację i wykonaj główne ścieżki. Zapisuj odtwarzalne błędy z krokami, przyczyną, poprawką i wynikiem ponownej próby. Zacznij od problemów, które uniemożliwiają użycie lub powodują błędną interpretację.

Sprawdź przynajmniej:

- Zgodność działającego API i aktualnego kodu, importy, zależności oraz obsługę zadań roboczych.
- Wyszukiwanie zwykłych współrzędnych i zapisu godzinowego; błędne dane, puste wyniki, pojedynczą klatkę, częściowy sukces, HTTP 422/503, ponowienie i utratę procesu.
- Wybór punktu, A/B, serię dat, play/pause, zmianę zakładek, trasę, reset, zapis karty, link i odtworzenie po restarcie.
- Rastry, mapę HiPS/WebGL, zmiany kanałów i brakujące warstwy; tryb spektralny ma być czytelnie oddzielony od czasu.
- Nowe integracje IRSA od kliknięcia w UI do rzeczywistego rezultatu: nie uznawaj ich za gotowe po samym imporcie.
- Dostępność klawiaturową, układ telefonu, zrozumiałość dla początkującego, czas pierwszego użycia i komunikaty podczas długiego pobierania.
- Publiczną ścieżkę działania, cache i trwałość zapisanych analiz; link lokalny nie jest dowodem publicznej dostępności.

Zielone testy są konieczne, ale nie dowodzą poprawności nieobjętych nimi integracji. Dodawaj testy dla konkretnych ryzyk i regresji. Nie pisz testów wyłącznie odwzorowujących implementację. Rób sensowne testy integracyjne i kontrolę wizualną. Nie mów „sprawdzone w przeglądarce”, jeśli nie oglądałeś wyniku.

Na Windows katalog TEMP/TMP może być blokowany w sandboxie. Użyj bezpiecznego katalogu tymczasowego w projekcie i osobnego katalogu pytest; ograniczenia środowiska odróżnij od regresji. Nie usuwaj cudzych danych i nie zatrzymuj niepowiązanych procesów. Korzystaj z `.venv`, `npm.cmd test`, `npm.cmd run build`, pytest i istniejących skryptów smoke, zamiast tworzyć odrębny stos.

## Skontroluj wiarygodność naukową

- Zweryfikuj identyfikację pięciu źródeł i ich pozycje we właściwych epokach. Pokrycie pola nie dowodzi detekcji, a brak detekcji nie oznacza nieistnienia obiektu.
- Sprawdź lokalne odpowiedzi spektralne, nie tylko nazwę detektora lub długość fali w centrum. WCS-WAVE do przeglądu nie zastępuje zwalidowanych produktów kalibracyjnych.
- Sprawdź WCS, orientację, reprojekcję, maski, przezroczystość braków, jednostki i powierzchnie pikseli. Nie traktuj brakujących danych jak zerowego strumienia.
- Skontroluj zgodność wersji CWAVE/CBAND, map powierzchni i ePSF z produktem oraz transformację współrzędnych wycinka do detektora. Zbadaj użycie modeli ePSF i poprawność fotometrii na natywnych danych.
- Odróżnij model i odjęcie tła od kontroli PSF, sąsiadów, centrowania i ruchu. Błąd losowy nie jest pełną niepewnością. Nie oznaczaj wyniku jako potwierdzonej zmienności lub prawdopodobieństwa odkrycia bez odpowiedniej walidacji.
- Widmo z różnych dat nie jest jednoczesnym widmem. Trasa dwóch kliknięć nie jest orbitą. MOST szuka znanych obiektów i nie wykrywa nieznanej Planet Nine. SEP znajduje kandydatów, nie potwierdza ich ruchu.
- Użyj źródeł kontrolnych, pustych pól, wyłączenia pojedynczej ekspozycji i niezależnego narzędzia/notebooka lub właściwie dopasowanego eksportu IRSA. Porównanie własnego kodu z tym samym kodem nie jest niezależną walidacją.
- Dane syntetyczne stosuj wyłącznie jako jawnie oznaczone testy. Nie pokazuj ich jako obserwacji lub odkryć.

## Znajdź wyróżnik w ramach istniejącej koncepcji

Porównaj aktualny produkt z WiseView, IRSA Data Explorer, narzędziami spektrofotometrii, Source Discovery i Backyard Worlds. Używaj źródeł pierwotnych. Nie twierdź, że standardowa animacja, fotometria lub użycie AI są same w sobie nowatorskie.

Zaproponuj maksymalnie pięć ulepszeń istniejącej koncepcji. Dla każdego określ problem użytkownika, różnicę względem dostępnych narzędzi, potrzebne dane, wpływ na kryteria, koszt, zależności i mierzalny test wartości. Rozróżnij przypuszczenie od potwierdzonej przewagi. Priorytetem jest wykonalność w pozostałym dniu i autorstwo/świadome decyzje zespołu.

Rozważ zwłaszcza połączenie pasma, czasu i hipotezy ruchu; diagnostykę alternatywnych przyczyn zmiany; śledzenie źródła; sprawdzanie wyniku na odłożonych obserwacjach; krótką, odtwarzalną kartę dowodową. Nie traktuj tej listy jako obowiązku implementacji. Wybierz najwyżej 1–2 dodatki, jeśli po usunięciu błędów istotnie poprawiają wynik i można je zwalidować. Gdy domknięcie rdzenia daje większą wartość, zrób je najpierw.

Nie dodawaj czatu AI, efektów 3D, pełnego nowego systemu ani marketingu tylko dla wrażenia innowacji. Zachowaj działającą architekturę. Nie usuwaj funkcji bez wyjaśnienia problemu, który to rozwiązuje.

## Pracuj do zweryfikowanego wyniku

W pierwszych 1–2 godzinach ustal stan i najważniejsze ryzyka. Ułóż plan reszty doby według wpływu na ocenę, pilności i zależności. Zostaw ostatnie 4–6 godzin na stabilizację, publiczną demonstrację i materiały. Są to granice planowania, nie polecenie czekania z działaniem.

Po audycie od razu realizuj potrzebne odwracalne naprawy i wybrane usprawnienia. Nie kończ po samym raporcie. Pytaj tylko o brakujące decyzje, które rzeczywiście blokują postęp; w pozostałych sprawach stosuj rozsądne założenia. Przygotowanie do wdrożenia i materiałów wykonuj równolegle z niezależną pracą; rzeczywiste publikowanie prowadź zgodnie z autoryzacją użytkownika i dostępnymi narzędziami. Nie wysyłaj wiadomości do organizatorów bez polecenia.

Aktualizuj dokumentację tak, aby starsze opisy nie przeczyły rzeczywistemu produktowi. Nie dodawaj pozornych gwarancji, że wszystkie funkcje działają. Dla pięciu wymaganych obiektów zapisz dane, identyfikację, porównywalność, wynik oraz ograniczenia. Przygotuj demonstrację także na wypadek chwilowej awarii IRSA, na prawdziwych zapisanych danych z jawnym pochodzeniem.

## Co ma zostać po Twojej pracy

1. Naprawiona, sprawdzona aplikacja z listą usuniętych regresji i rzeczywistymi wynikami testów.
2. `AUDYT_NAPRAWY.md`: stan funkcji, błędy i dowody, wymóg → implementacja → test, pozostałe blokady.
3. `PLAN_24H.md`: priorytety, wykonanie i świadomie odłożone rozszerzenia.
4. `WYNIKI_5_OBIEKTOW.md`: uczciwe wyniki pięciu prób na danych SPHEREx.
5. `PAKIET_ZGLOSZENIA_EN.md`: angielski opis, sposób użycia danych NASA, referencje i wkład AI, ograniczenia, scenariusz demo do 30 sekund lub plan do 7 slajdów; bez wymyślonych danych zespołu i nazwy projektu.
6. Macierz pięciu kryteriów: jakie konkretne dowody poprawiają każdą ocenę, co nadal ogranicza projekt i dlaczego wybrany wyróżnik ma wartość.
7. Końcowe krótkie podsumowanie: co działa, co naprawiono, jak to sprawdzono, jak otworzyć wynik i co faktycznie pozostaje do zrobienia przez zespół.

Twoja pierwsza odpowiedź ma krótko wskazać rozpoczęcie audytu, po czym przejdź do narzędzi. Nie odpowiadaj samą strategią ani obietnicą „mogę pomóc”. Pracuj na rzeczywistym repozytorium i doprowadź autoryzowany zakres do końca.
