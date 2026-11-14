# Angielska obsługa, start z kometą i lokalny dobór obserwacji

Wdrożenie wskazanych punktów 2–4, 14 listopada 2026. Zmiany dotyczą lokalnej aplikacji. Nie zmieniano masek jakości ani definicji ważnej apertury, aby uzyskać korzystniejsze wyniki.

**Obsługa i ekran startowy**

- Domyślny język nowego użytkownika: angielski; przełącznik English / Polski i parametr `lang` zachowują wybór.
- Przetłumaczono współrzędne, wyszukiwanie, postęp, błędy, odtwarzanie, pomoc, pasma, mapę, wyniki i etykiety narzędzi zaawansowanych. Tłumaczenie dotyczy prezentacji; nie zmienia naukowych danych ani zapisanych eksportów. Nieznane komunikaty z zewnętrznych usług pozostają widoczne w oryginale.
- `/` otwiera prosty widok z rzeczywistym pokazem 3I/ATLAS, odtwarzaniem, znacznikami i przejściem do własnych współrzędnych. Narzędzia zaawansowane są dostępne przyciskiem. Jawne linki analiz, notatek i własnych pól zachowują odpowiednie wejście.
- Parametr `motion=0` zamyka pokaz również po odświeżeniu. `interface=advanced` otwiera pełne narzędzia.

**Dobór obserwacji**

Operacja `POST /api/analyses/auto` działa w istniejącej kolejce. Domyślnie sprawdza do 36 kandydatów z różnych detektorów; API ogranicza próbkę do 12–48 obserwacji. Zgodnie z przywróconym sposobem doboru przygotowuje tylko rekomendowaną serię do ośmiu klatek, zamiast całej galerii kandydatów. Pobieranie i kontrola nadal działają w czterech wątkach. Przeglądarka wybiera rekomendowane klatki także przy otwieraniu starszych pełnych galerii. Ręczny wybór nadal działa.

Dla każdego kandydata sprawdzane są natywne IMAGE/VARIANCE/FLAGS, lokalna długość i szerokość pasma, pokrycie apertury, flagi, dostępność czystego tła i termin. Dla jawnie wybranego katalogowego celu pozycja jest prognozowana osobno dla każdej daty z ruchem własnym. Własne współrzędne pozostają stałe w ICRS.

Ranking preferuje pary z ważnymi aperturami i bez ostrzeżeń sąsiada, następnie pokrycie i bazę czasową. Nie wykorzystuje zmierzonego strumienia ani S/N. Każdy dodatkowy obraz musi być zgodny pasmowo z całym wybranym zestawem. Ten sam termin lub różne niezgodne pasma nie tworzą pary czasowej.

Gdy pierścień tła nie mieści się w natywnym wycinku, pobierany jest większy wycinek, najwyżej 30′. Geometria i FOV obrazu wynikowego pozostają zgodne z wyborem użytkownika. Większy wycinek nie przywraca pikseli poza detektorem; takie ograniczenie jest zapisane.

Jeśli fotometria celu jest odrzucona, można przygotować obrazy do oglądania z wyraźnym statusem `image_pair_only`. Nie są one przedstawiane jako ważna fotometria. Gdy odpowiedniej pary nie ma, raport to zgłasza. Pełne kontrole i powody odrzucenia są w manifeście i pod `GET /api/selections/{id}`.

Odtwarzanie nowych analiz korzysta z kontroli lokalnego pokrycia przy celu; nie wymaga 80% ważnego całego kadru, gdy dane przy celu są dobre. Kliknięcie punktu zastępuje te kontrole danymi dla nowej, stałej pozycji. Starsze analizy zachowują dotychczasowy filtr.

**Rzeczywiste wyniki pięciu pól**

Sprawdzono po 36 kandydatów, łącznie 180. Listy obserwacji pochodzą z zachowanych zapytań DR1 z tego samego dnia; brakujące FITS pobrano z IRSA. Końcowa kontrola ponownie oceniła te same identyfikatory z cache. Błędy pobierania są zachowane. To ograniczona próbka, nie pełny przegląd archiwum.

| Cel | Detektor nowego zestawu | Ważne apertury: wcześniej | Ważne apertury: nowy zestaw | Baza pary (dni) | Analiza lokalna |
|---|---|---:|---:|---:|---|
| Barnard’s Star | D6 | 0/4 | 0/3 | 15.14 | [Otwórz](http://127.0.0.1:8000/?analysis=3e46812645234bc982722272bfdc7faa&lang=en) |
| Epsilon Indi B | D4 | 0/6 | 2/2 | 14.87 | [Otwórz](http://127.0.0.1:8000/?analysis=155a9c2a3fc74f7d9761498af9db7000&lang=en) |
| WISE 0855 | D6 | 4/5 | 2/2 | 370.40 | [Otwórz](http://127.0.0.1:8000/?analysis=049a3f81cfb3416b9fe6330e34861068&lang=en) |
| RW Aurigae | D2 | 0/4 | 0/2 | 8.01 | [Otwórz](http://127.0.0.1:8000/?analysis=46024be381d947b3b5507f977481d9e4&lang=en) |
| R Draconis | D5 | 0/3 | 0/3 | 188.95 | [Otwórz](http://127.0.0.1:8000/?analysis=12e4e5d4a34b4f039311aac23a880102&lang=en) |

Liczebności zestawów różnią się, ponieważ nowy dobór wybiera porównywalne obrazy zamiast stałej liczby zdjęć D2. W próbce kandydatów Epsilon Indi B ma cztery ważne apertury, a WISE 0855 osiemnaście; wybrano po dwie do spójnej pary. Epsilon Indi B: D4, około 3,6422/3,6425 µm. WISE: D6, około 4,9674/4,9673 µm.

**Nie potwierdzono identyfikacji tych źródeł na obrazach, ruchu ani zmienności pięciu celów.** Dla Barnard’s Star, RW Aurigae i R Draconis nowa próbka nadal nie daje ważnych apertur. Pozostają flagi, niepełne pokrycie lub niewystarczające czyste tło. Nie zmieniano progów w celu wymuszenia sukcesu. Widoczny ruch w osobnym przykładzie 3I/ATLAS dotyczy znanej komety, nie tych pięciu celów.

**Weryfikacja i odtworzenie**

- Po przywróceniu doboru: 121 testów backendu i 37 testów frontendu bez błędów. Obejmuje to ograniczenie równoległości do czterech zadań, kontrolę 36 kandydatów przy przygotowaniu wyłącznie wybranej pary, przywracanie rekomendacji ze starszych pełnych galerii oraz ponowienie atomowego zapisu przy chwilowej blokadzie Windows.
- Build TypeScript/Vite przechodzi. Pozostaje znane ostrzeżenie wielkości pakietu Aladin.
- Test prawdziwej kolejki API: `scripts/smoke_main_updates.py`, wynik `data/audit/main-updates-api.json`. Skrypt sprawdza ograniczenie do ośmiu przygotowanych klatek i ich zgodność z listą rekomendacji, przy kontroli do 36 kandydatów. Wcześniejszy wariant galerii przygotowywał 34 obrazy Epsilon Indi B, lecz został zastąpiony doborem wyłącznie rekomendowanej serii.
- Przeglądarka: nowy ekran z kometą, przełączenie PL/EN, angielski błąd RA=360, rzeczywiste wyszukiwanie Epsilon Indi B (368 obrazów), raport nowego doboru i odtwarzanie.
- Pierwsze próby w sandboxie napotykały ograniczenia gniazd lub plików tymczasowych. Końcowe testy i reprojekcja zostały wykonane z właściwym dostępem. Nie traktowano błędów sandboxa jako błędów naukowych danych.

```powershell
.\.venv\Scripts\python.exe scripts/improve_five_targets.py --prepare --candidates 36
.\.venv\Scripts\python.exe scripts/improve_five_targets.py --offline --prepare --reuse-candidates data/audit/five-targets-selection-v1.json --output data/audit/five-targets-selection-final.json
.\.venv\Scripts\python.exe scripts/smoke_main_updates.py
```

Pierwsze polecenie może pobrać nowe FITS i tworzy nowe analizy. Drugie zachowuje dokładnie wcześniejszą próbkę kandydatów; pomiary wymagają dostępnych kalibracji. Wyniki historyczne i wcześniejsze analizy pozostają zachowane.
