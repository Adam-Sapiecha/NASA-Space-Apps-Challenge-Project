# Kierunek wizualny i audyt

Data: 14 listopada 2026. Zakres: istniejąca przeglądarka SPHEREx; zachowano wyszukiwanie IRSA, wybór ekspozycji, lupę, miganie A/B, szkic ruchu, wycinki, pasma, flagi, eksport i udostępnianie. Backend i pipeline naukowy nie były zmieniane w ramach przeprojektowania.

## Analiza referencji przed implementacją

Wskazane strony przejrzano w przeglądarce, w tym ich rzeczywistą kompozycję i nawigację.

| Referencja | Obserwacja | Zastosowanie we własnym układzie |
|---|---|---|
| [Backyard Worlds: Planet 9](https://www.zooniverse.org/projects/marckuchner/backyard-worlds-planet-9) | Wyraźne rozdzielenie informacji o projekcie, właściwego zadania i jego stanu | Narzędzia pracy są odrębne od przewodnika; komunikaty o danych pozostają przy zadaniu |
| [NASA Science](https://science.nasa.gov/) | Mocna hierarchia typograficzna, instytucjonalna nawigacja, fotografie jako treść | Czytelny nagłówek, proste sekcje, podpisane obrazy bez dekoracyjnych nakładek |
| [Rubin Observatory](https://rubinobservatory.org/) | Rozpoznawalny akcent kolorystyczny i treść oparta na rzeczywistych materiałach obserwacyjnych | Jeden stonowany akcent, wyraźne przejście od kontekstu do pracy z danymi |
| [ESA/Hubble](https://esahubble.org/) | Dominacja autentycznych obrazów i uporządkowana nawigacja archiwalna | Materiały naukowe są prezentowane z opisem i źródłem; bez fikcyjnych ilustracji |
| [NASA’s Eyes](https://science.nasa.gov/eyes/) | Osobna warstwa informacyjna i interaktywne aplikacje eksploracyjne | Jasna strona dokumentacyjna oraz ciemne pole obserwacji, którego kontrast służy oglądaniu danych |

Nie kopiowano identyfikacji, logotypów ani layoutów referencji. Strona wprost informuje, że jest niezależnym narzędziem.

## System

- Papier: `#f8f8f4`; tekst: `#242a27`; akcent: `#285b49`.
- IBM Plex Sans do interfejsu; Source Serif 4 do nagłówków redakcyjnych; systemowy monospace do współrzędnych i identyfikatorów.
- Fonty serwowane lokalnie, z polskimi znakami i tekstami licencji.
- Linie działowe, proste krawędzie, maksymalnie 2 px zaokrąglenia kontrolek.
- Właściwe dane w tabeli ekspozycji, z nagłówkami i przewijaniem wewnętrznym.
- Ciemne tło ograniczone do obrazów. Po załadowaniu analizy wprowadzenie jest krótsze, by narzędzia pojawiały się wcześniej.
- Wąskie ekrany układają panel ustawień pod obrazem. Nawigacja i kolejność pracy pozostają dostępne.

## Krytyczny audyt i poprawki

| Problem | Zmiana |
|---|---|
| Całość przypominała futurystyczny dashboard | Jasna, redakcyjna struktura oraz ograniczony akcent |
| Poświata i jaskrawa miętowa kolorystyka | Usunięte; znaczniki obrazu mają neutralny kolor o czytelnym kontraście |
| Slogan i trzy podobne kafelki | Zastąpione opisem zadania i przewodnikiem w układzie ciągłym |
| Wszystkie treści w zaokrąglonych pojemnikach | Pozostawiono tylko uzasadniony panel ustawień, tabela i pole obrazu |
| Wzór braku danych dominował poza kadrem | Wzór ograniczono do rzeczywistego prostokąta obrazu; otoczenie jest jednolite |
| Trudne przesuwanie powiększenia na telefonie | Dodany jawny tryb przesuwania obrazu przez przeciąganie |
| Canvas niedostępny z klawiatury | Dodany fokus, strzałki, Enter, opis obsługi i widoczny punkt |
| Kilka tekstów pomocniczych miało kontrast poniżej 4,5:1 | Przyciemniono separatory, numery kroków, licznik i podpis autorstwa; ponowny odczyt nie wykazał odstępstw w sprawdzonym widoku |

## Weryfikacja

- Widoki ze zrealizowaną analizą sprawdzono przy szerokościach 320, 390, 768 i 1440 px. Brak poziomego przepełnienia dokumentu w tych pomiarach.
- Obejrzano w przeglądarce układ wejściowy, viewer z rzeczywistymi danymi, ustawienia, przewodnik i podpisane porównanie dwóch pasm.
- Klawiaturą wybrano punkt obrazu i uzyskano współrzędne z istniejącego API.
- Klawiaturą wskazano dwie pozycje hipotezy i uzyskano dziesięć wycinków dla istniejącej analizy. To test interfejsu, nie potwierdzenie detekcji astronomicznej.
- Sprawdzono przełączanie powiększenia oraz trybu przesuwania.
- Kontrast sprawdzono na podstawie obliczonych kolorów tekstu i tła elementów DOM. Po poprawkach w badanym widoku nie znaleziono tekstów poniżej 4,5:1 (3:1 dla dużego tekstu). To kontrola wybranego stanu, nie certyfikacja całej aplikacji według WCAG.
- Istniejące pięć testów frontendu przeszło. Produkcyjny build TypeScript/Vite przeszedł.

Nie przeprowadzono jeszcze badania z użytkownikami, testu na fizycznym telefonie ani pełnego audytu czytnikiem ekranu. Dalszej walidacji naukowej nie zastępuje dopracowanie wizualne.

## Pochodzenie materiałów

Szczegóły praw, autorstwa, źródeł i bezstratnej konwersji: [ASSET_SOURCES.md](ASSET_SOURCES.md). Fotografie redakcyjne są oddzielone od danych analizowanych w viewerze.
