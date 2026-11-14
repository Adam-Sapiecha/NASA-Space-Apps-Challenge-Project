# Ocena projektu względem objectives i kryteriów NASA Space Apps 2026

Ocena z 14 listopada 2026 r. dotyczy bieżącego kodu, lokalnie uruchomionej aplikacji i dostępnych dowodów. To niezależna, orientacyjna ocena z perspektywy jurora, a nie oficjalna punktacja NASA. Nie obejmuje wystąpienia zespołu, jego strony zgłoszenia ani nieznanego publicznego wdrożenia.

**Werdykt: rdzeń funkcjonalny objectives jest zrealizowany w lokalnym prototypie. Pełna realizacja publicznego narzędzia nie została wykazana.** Użytkownik może podać RA/Dec, pobrać rzeczywiste obrazy SPHEREx i porównywać obserwacje w czasie. Największa luka to brak zweryfikowanego publicznego adresu. Pozostałe słabości to niepełna angielska ścieżka, ograniczona walidacja pięciu wskazanych obiektów i brak pomiaru użyteczności dla początkujących.

**Co sprawdzono w tej ocenie**

- Przeczytano załączony tekst wyzwania oraz kod wyszukiwania, przetwarzania obrazów, wyboru serii, pomiarów i interfejsu.
- W przeglądarce obejrzano stronę główną, działający pokaz 3I/ATLAS i angielski replay `/demo/`.
- Bezpośrednio w przeglądarce odczytano oficjalny Judging & Awards Guide oraz Project Submission Guide z 13 listopada 2026. Narzędzie web zwracało dla nich 502; ocena nie opiera się na samym tym błędzie ani na starszych lokalnych opisach.
- Backend: **111 testów przeszło**, 3 ostrzeżenia. Raport: `.cache/jury-backend-tests-20261114.xml`. Początkowe próby w sandboxie nie były miarodajne z powodu ograniczeń katalogu tymczasowego i lokalnych gniazd; poprawne uruchomienie poza sandboxem zakończyło się powodzeniem.
- Frontend: **30 testów przeszło**; build TypeScript/Vite zakończył się powodzeniem. Pozostało ostrzeżenie o dużym pakiecie Aladin.
- `scripts/smoke_submission.py` przeszedł na lokalnym serwerze: walidacja współrzędnych, równoważność stopni i zapisu godzinowego, obrazy, pochodzenie danych, zapisany punkt, eksport i angielski replay. Backend zgłosił `code_changed=false`; nie restartowano serwera.
- Świeże `/api/search` dla pola WISE 0855, DR1 i 6′ zwróciło **280 obserwacji w około 4,33 s**, `cached=false`, identyfikator wyszukiwania `4a35e7a82ffd49718146d4bb3328bf99`. To jeden pomiar, nie benchmark wydajności całej aplikacji ani potwierdzenie detekcji WISE 0855.
- Niezależnie przeliczono maksima w zapisanych FITS pokazu 3I/ATLAS: wspólny WCS, rozmiar 117 × 117, przesunięcie źródła 46,819 piksela, pięć punktów kontrolnych 0–2,236 piksela. Jest to kontrola przeglądowa, nie precyzyjna astrometria.
- Nie powtarzano pobierania i pełnej walidacji pięciu pól. Ich ocenę oparto na manifestach i najnowszych zachowanych wynikach po poprawkach matematycznych.

**Zgodność z wymaganiami głównymi**

| Objective | Ocena | Uzasadnienie |
|---|---|---|
| Public-facing web tool | Częściowo | Aplikacja webowa działa lokalnie. README i DEPLOYMENT opisują brak publicznego wdrożenia; nie przedstawiono działającego publicznego URL. Sam Dockerfile lub statyczny replay nie zapewniają publicznego wyszukiwania dowolnych RA/Dec. |
| Wprowadzenie RA i Dec | Spełnione | Własne współrzędne, stopnie i zapis godzinowy/kątowy, walidacja błędów; sprawdzone API. |
| Rzeczywiste obrazy SPHEREx | Spełnione | IRSA SIA, DR1/QR3, natywne FITS, identyfikatory, daty i SHA-256. Obrazy NASA są podstawą działania. |
| Seria obrazów tego samego pola w czasie | Spełnione w prototypie | Wspólna siatka nieba, chronologiczne klatki, odtwarzanie, miganie i regulacja tempa. Braki danych pozostają oznaczone. |
| Łatwe dostrzeżenie ruchu przez zwykłego użytkownika | Działanie pokazane; użyteczność częściowo zweryfikowana | 3I/ATLAS daje czytelny pozytywny przykład ruchu. Główne wejście nadal otwiera słabszy wizualnie przykład WISE i rozbudowany warsztat. Nie przeprowadzono badania z początkującymi. |
| Test Barnard’s Star, Epsilon Indi B, WISE 0855, RW Aurigae, R Draconis | Wykonane testy pól; ograniczona walidacja wyniku astronomicznego | Są poprawione pozycje, rzeczywiste obserwacje i raport każdego pola. Nie potwierdzono identyfikacji wszystkich celów, ich ruchu ani zmienności. |

**Wymaganie testów nie oznacza obowiązku odkrycia nowego obiektu ani wykazania zmienności wszystkich pięciu celów.** Uczciwy wynik nierozstrzygnięty jest wynikiem testu. Nie należy jednak przedstawiać samego pokrycia pola jako detekcji celu lub skuteczności poszukiwania. Automatyczny detektor, ML, pełne 102-kanałowe widmo i ilościowy pomiar ruchu nie są obowiązkowymi objectives.

**Pięć celów: co wynika z zapisanych danych**

Najnowsze `data/audit/math_fixes_20261114/offline-validation.json` i `NAPRAWY_AUDYTU_MATEMATYCZNEGO.md` potwierdzają następujące liczby. Starsze wartości strumieni w `WYNIKI_5_OBIEKTOW.md` są oznaczone jako archiwalne.

| Cel | Przygotowane obrazy | Ważne apertury przy przewidywanej pozycji |
|---|---:|---:|
| Barnard’s Star | 4 | 0 |
| Epsilon Indi B | 6 | 0 |
| WISE 0855 | 5 | 4 |
| RW Aurigae | 4 | 0 |
| R Draconis | 3 | 0 |

Łącznie przygotowano 22 z 25 wybranych produktów. Nieważna apertura nie oznacza, że obraz jest bezużyteczny do oglądania; ważna apertura nie potwierdza tożsamości ani detekcji źródła. Przeszkody obejmują flagi, brzegi wycinków i zanieczyszczone tło. W próbce WISE istnieje para o zbliżonych lokalnych pasmach i odstępie około 161,9 dnia. Pozostałe niepowodzenia nie dowodzą braku odpowiednich danych w całym archiwum.

**3I/ATLAS zmienia ocenę demonstracji ruchu**

Projekt ma już rzeczywisty pozytywny przykład przesuwającego się źródła. Dwie obserwacje z 14 grudnia 2025 dzieli około 98 minut, a pozycje z efemeryd około 4,77′. Własna kontrola obrazów wykazuje znacznie większe przesunięcie jasnego źródła niż punktów tła. To dobry początek prezentacji. [Oficjalna strona IRSA](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/comet3iatlas/) potwierdza udostępnienie obserwacji komety z sierpnia i grudnia 2025.

Pasma obu klatek różnią się: około 4,482 i 4,614 µm. Pokaz uzasadnia obserwację ruchu, ale nie wniosek o zmianie jasności. Wartość 4,77′ pochodzi z efemeryd, nie z niezależnego pomiaru astrometrycznego aplikacji. Kometa nie jest nowym odkryciem zespołu.

IRSA ostrzega też, że 3I/ATLAS jest przestrzennie rozciągnięty w wielu pasmach, i odradza używanie dla niego oficjalnego narzędzia spektrofotometrii przeznaczonego dla źródeł punktowych. W prezentacji i pełnym warsztacie należy równie jasno ograniczyć interpretację dopasowania ePSF dla tej komety.

**Opcjonalne potential considerations**

| Rozwinięcie | Stan |
|---|---|
| Aktualizacja wydań danych | Adapter i zapytania sieciowe istnieją; lista DR1/QR3 jest obecnie jawnie zapisana w kodzie. Nowe wydanie wymaga dodania i sprawdzenia adaptera, nie tylko zmiany etykiety. |
| 102 pasma / sześć detektorów | Są wybór detektorów, odtwarzanie długości fali, lokalne metadane i mapa HiPS. To nie oznacza 102 dostępnych epok lub pełnego jednoczesnego widma każdego źródła. |
| Widmo na żądanie | Są natywne pomiary i wykresy; dane z różnych dat, flagi i brak pełnej walidacji ograniczają interpretację. |
| Dodawanie / odejmowanie | Jest jakościowe składanie i A−B, z kontrolą lokalnych pasm; bez pełnego dopasowania PSF i całkowitego modelu niepewności. |
| Zmienny FOV | Jest; API dopuszcza 2–30′. |
| Gaia / WISE | Są kontekst i nakładki; nie należy utożsamiać ich z jednorodną czasową serią SPHEREx. |
| Współrzędne w URL | Są parametry RA/Dec i odtwarzalne linki analiz. Działanie linków publicznie zależy od wdrożenia i trwałych danych. |
| Flagi / metadane / gotowe narzędzia | Są; Astropy, Astroquery, Reproject i Aladin są rzeczywiście wykorzystywane. |

Nie traktuję brakujących lub eksperymentalnych rozszerzeń jako niespełnienia obowiązkowego objective.

**Ocena jak u jurora: około 17/25**

Oficjalny [Judging & Awards Guide 2026](https://www.spaceappschallenge.org/resources/judging-awards-guide/) określa pięć kryteriów ocenianych po 1–5. Poniższa suma służy orientacji; nie ustalono dodatkowych wag, nie porównywano innych zespołów i nie prognozuje się awansu.

| Kryterium | Ocena | Uzasadnienie |
|---|---:|---|
| Impact | 3/5 | Obniża barierę pracy z rzeczywistymi FITS i pomaga unikać błędnej interpretacji. Brakuje publicznego dostępu i dowodu, że początkujący szybciej lub trafniej wykonują zadanie. |
| Creativity | 3/5 | Miganie, fotometria i reprojekcja są standardowe. Mocniejszy wyróżnik to połączenie lokalnych pasm, kontroli jakości i odtwarzalnej karty dowodowej. Trzeba pokazać korzyść tego połączenia na jednym przypadku. |
| Validity | 4/5 | Prawdziwe dane, wspólny WCS, jawne maski, brak sztucznego uzupełniania, testy i kontrola ruchu. Ocena dotyczy rdzenia jakościowego; ilościowe modele i fotometria mają dalsze ograniczenia. |
| Relevance | 4/5 | Bardzo bezpośrednio odpowiada na wyzwanie i istotnie wykorzystuje dane NASA. Do pełnej realizacji brakuje wykazanego publicznego działania oraz mocniejszej ścieżki dla wszystkich celów testowych. |
| Presentation | 3/5 | Pokaz komety jest zrozumiały, interfejs ma czytelne obrazy i daty. Pełna aplikacja jest po polsku, start pokazuje mniej oczywisty przykład, a materiały zawierają starsze opisy. Nie obejrzano pitchu; to ocena prowizoryczna. |

Jako juror widziałbym działający, rozbudowany prototyp, którego wartość wymaga jeszcze skupienia prezentacji na jednym zadaniu użytkownika. Liczba paneli i modeli nie jest sama w sobie argumentem za wyższą oceną. Najbardziej wiarygodna obietnica brzmi: „Oglądaj prawdziwe zmiany na obrazach SPHEREx i sprawdzaj, czy porównujesz odpowiednie dane”.

**Co zmienić — kolejność ma znaczenie**

1. **Wykazać publiczne działanie pełnej aplikacji.** Wdrożyć backend i frontend z przygotowanymi danymi, HTTPS i trwałym magazynem; sprawdzić z drugiego urządzenia bez logowania wyszukiwanie nowych RA/Dec, przygotowanie dwóch klatek, odtwarzanie i otwarcie linku po restarcie. Istniejąca konfiguracja wdrożenia jest punktem wyjścia, nie dowodem uruchomienia. Przed publicznym testem ograniczyć liczbę zadań i wzrost cache. Statyczny replay pozostawić jako zabezpieczenie prezentacji.
2. **Dać jurorowi pełną ścieżkę po angielsku.** Przetłumaczyć wybór pola, RA/Dec, wyszukiwanie, postęp, błędy, animację, opis pasm i eksport. Już istniejący angielski przewodnik i replay są przydatne, lecz nie pokrywają pełnego wyszukiwania. [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) wymaga angielskich materiałów i publicznych linków do demo oraz projektu; demo to film do 30 s albo prezentacja do 7 slajdów. Sam interaktywny replay nie jest jednym z tych dwóch formatów.
3. **Otwierać pokaz od 3I/ATLAS.** Pierwszy ekran lub pierwsza scena powinny szybko pokazać rzeczywisty ruch, z możliwością ukrycia znaczników, datami i wyjaśnieniem. Potem pokazać wpisanie własnych współrzędnych. Prosty tryb już istnieje, ale `/` domyślnie wybiera ustawienia zaawansowane; warto odwrócić ten wybór dla nowych użytkowników. Nie ukrywać RA/Dec ani nie zastępować narzędzia samą galerią.
4. **Wzmocnić dobór danych dla pięciu celów.** Dobierać detektor i ekspozycje według lokalnego pasma, ważnego pokrycia w pozycji celu, flag i bazy czasowej, a nie głównie liczebności grupy detektora. Powiększać wycinek, gdy nie mieści pierścienia tła. Dla jasnych lub zatłoczonych pól sprawdzić inne pasma i uzasadniony model tła/PSF; zachować ograniczenia i nie osłabiać masek tylko po to, by uzyskać wynik. Do każdego celu dołączyć zrzut, daty, przewidywaną pozycję i jasny werdykt: widoczny ruch, zmienność nierozstrzygnięta albo dane nieodpowiednie. Walidacja tożsamości źródła powinna być oddzielnym krokiem.
5. **Uporządkować obietnice i dokumentację.** Rozdzielić wynik pięciu wskazanych obiektów od pozytywnego pokazu komety. Uaktualnić angielski pakiet zgłoszenia, aby nie sugerował globalnego braku demonstracji ruchu. Wyraźnie odróżnić czas od długości fali, prognozę katalogową od detekcji i jakość obrazu od pomiaru. Utrzymać eksperymentalne modele poza główną ścieżką prezentacji.
6. **Pokazać choć mały pomiar użyteczności.** Poprosić 3–5 początkujących o odtworzenie ruchu komety, znalezienie dat i rozróżnienie animacji czasu od animacji pasm. Zapisać liczbę wykonanych zadań i czas; uczciwie opisać małą próbę. To pilotaż, nie dowód skuteczności w dużej populacji.

Najbliżej charakteru projektu jest kategoria **Best Use of Data**, ponieważ nacisk pada na dostępność i eksplorację danych kosmicznych. To dopasowanie do definicji nagrody, nie przewidywanie jej otrzymania. Dalsze rozbudowywanie ML, modeli chemicznych lub dodatkowych katalogów ma teraz mniejszy priorytet niż powyższe zmiany.

**Granice formalnej oceny**

Brak uruchomionego hostingu nie jest sam w sobie automatycznym dowodem niekwalifikowalności do konkursu: oficjalny przewodnik dopuszcza publiczny link do repozytorium jako link do projektu. Jest jednak istotną luką wobec celu publicznego narzędzia tego konkretnego wyzwania. Nie sprawdzano rejestracji zespołu, przesłania formularza ani jego dostępności. W lokalnej konfiguracji Git nie ma remote; nie dowodzi to braku repozytorium opublikowanego innym sposobem.

Ta ocena nie publikuje projektu, nie zmienia kodu aplikacji i nie zastępuje testu publicznego adresu. Zapisano wyłącznie raport oraz artefakty weryfikacji.
