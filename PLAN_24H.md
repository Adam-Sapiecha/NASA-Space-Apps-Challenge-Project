# Finalizacja w pozostałej dobie

Stan: 14 listopada 2026. To plan pracy zespołu z odnotowanym wykonaniem, a nie deklaracja ukończenia walidacji naukowej ani publicznego wdrożenia. Projekt zachowuje pierwotną koncepcję zespołu i pozostaje bez nadanej nazwy.

## Priorytety i wykonanie

| Okno od rozpoczęcia finalizacji | Priorytet | Odbiór | Stan |
|---|---|---|---|
| 0–2 h | Kod, działający proces, wymagania i identyfikacja celów | Testy, OpenAPI, katalogowe współrzędne, rozdzielenie faktów i planu | Wykonano: wykryto błędne presety dwóch pól; potwierdzono bieżące trasy IRSA i dodano fingerprint procesu |
| 2–8 h | Naprawy wpływające na interpretację i stabilność | Poprawne pola, jawne odrzucenia, brak wiszących zadań, wiarygodna karta | Wykonano poprawki pozycji/epoki, maskowania fotometrii, utraty procesu, odpowiedzi HTTP, starych wyników pomiaru i mobilnej mapy; karta HTML/JSON |
| 8–14 h | Pięć prób, niezależna kontrola, działające integracje | Zachowane prawdziwe FITS, identyfikatory, uczciwe wyniki | Wykonano nowe próby pięciu pól, kontrolę flag, 30 porównań Photutils i smoke IRSA; nie potwierdzono zjawisk |
| 14–18 h | Publiczny serwer i próba z drugim urządzeniem | HTTPS, świeże RA/Dec, zachowane dane po restarcie | Przygotowano konfigurację Docker/Caddy i seed; **brak hosta, domeny i publicznego URL** |
| Ostatnie 4–6 h | Zamrożenie zakresu, demo i zgłoszenie | Publiczne linki, EN, ≤30 s albo ≤7 slajdów, decyzje zespołu | Przygotowano EN replay i kartę offline, scenariusz oraz tekst zgłoszenia; zespół uzupełnia nazwę, autorów, linki i wysyła |

Okna są budżetem organizacyjnym. Gotowych prac nie trzeba powtarzać ani czekać na odpowiadającą im godzinę. Jeżeli do lokalnego pitchingu jest mniej czasu, pierwszeństwo mają hosting i krótka demonstracja istniejącego wyniku.

## Wybrany wyróżnik

**Od podejrzenia do odtwarzalnego sprawdzenia:** zmiana długości fali i zmiana czasu są osobnymi działaniami; użytkownik przypina punkt lub ręczną trasę, sprawdza alternatywne przyczyny różnicy i zapisuje kartę z datami, lokalnym pasmem, pochodzeniem FITS i nierozstrzygniętymi ograniczeniami. Rozwinięto istniejącą kartę o pełny eksport dowodów i samodzielny HTML po angielsku.

Drugi, ograniczony dodatek to **angielski replay offline na rzeczywistych danych**, dzięki któremu awaria IRSA nie przerywa pokazu. Replay nie zastępuje publicznego backendu wyszukującego nowe współrzędne.

## Rozważone ulepszenia — maksymalnie pięć

| Ulepszenie / problem użytkownika | Różnica wobec odczytanych narzędzi | Dane i zależności | Kryteria | Koszt / test wartości / decyzja |
|---|---|---|---|---|
| Karta dowodowa: trudno odtworzyć, co porównano | Łączy istniejącą diagnostykę SPHEREx z ludzką hipotezą i eksportem offline; nie twierdzimy, że inne narzędzia nie mają eksportów | Manifest, lokalne NPZ, notatka, opcjonalny pomiar | Validity, Presentation, Creativity | Kilka godzin; zapis → restart/odświeżenie → te same obrazy, punkt, SHA i diagnostyka. **Wdrożono** |
| Replay EN: pokaz zależy od sieci i polskiego interfejsu | Wyjaśnia oddzielnie czas i pasmo na tych samych produktach, z jawnymi ograniczeniami | Zachowane prawdziwe PNG i manifesty | Presentation, Relevance | Kilka godzin; działa bez API/IRSA, pokazuje 2 epoki i 10 obserwacji spektralnych. **Wdrożono** |
| Automatyczne śledzenie źródła w kolejnych epokach | Skróciłoby ręczne przenoszenie pozycji; przewaga użytkowa jest hipotezą | Rzeczywista astrometria, PSF, sąsiedzi, paralaksa, niezależne etykiety | Impact, Validity | >1 doba wiarygodnej walidacji; miara: błąd pozycji i fałszywe skojarzenia na odłożonych ekspozycjach. **Odłożono** |
| Ocena hipotezy na odłożonych obserwacjach | Istniejąca ręczna ocena trasy może stać się testem, jeśli dodać niezależne pomiary | Zgodne pasma i co najmniej trzeci termin; rozdział uczenia/oceny | Creativity, Validity | Ręczna ocena już istnieje; automatyczna ocena wymaga danych kontrolnych. **Nie rozbudowano** |
| Zwalidowany dobór pasm i wag | Mógłby pomóc przy słabych źródłach; sama animacja ani fotometria nie dowodzą nowości | Kalibracja odpowiedzi, PSF, definicja celu i niezależny zbiór | Impact, Creativity | Ryzyko optymalizacji szumu i zmieniania efektywnego pasma między datami; test odzysku przy stałym odsetku fałszywych wskazań. **Odłożono; asystent nadal odmawia rekomendacji** |

## Porównanie z istniejącymi rozwiązaniami

- **WiseView**: przeglądanie obrazów WISE, opracowane przez Dana Caseldena i Paula Westina. Animacja obrazów nie jest naszym wynalazkiem. Oficjalne potwierdzenie autorstwa: [NASA](https://science.nasa.gov/people/dan-caselden/); bezpośredni odczyt WiseView w tej sesji nie powiódł się, więc nie opisujemy pełnej listy jego aktualnych funkcji.
- **SPHEREx Data Explorer i Spectrophotometry**: oficjalne wyszukiwanie i przetwarzanie danych, wymuszana fotometria Tractor, obsługa sąsiadów i instrumentu. Lokalnego ePSF nie przedstawiamy jako odpowiednika naukowej walidacji tej usługi. [Dokumentacja IRSA](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html).
- **Source Discovery Tool**: oficjalny notebook już wykrywa źródła, porównuje obrazy i pozwala badać widma. SEP w naszym projekcie nie stanowi nowego algorytmu odkrywania. [Notebook](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/).
- **Backyard Worlds**: ugruntowany udział publiczności w szukaniu ruchu. Przewagą wymagającą zbadania jest krótsza droga od obserwacji SPHEREx do uzasadnionej, odtwarzalnej hipotezy; nie zastępujemy doświadczenia tej społeczności. [NASA](https://science.nasa.gov/citizen-science/backyard-worlds-planet-9/).

Potwierdzona jest obecność własnego przepływu i eksportu. Poprawa czasu pracy lub trafności początkujących pozostaje **hipotezą**, bez przeprowadzonego badania z użytkownikami.

## Co robi zespół jako następne

1. Udostępnia host i rzeczywisty hostname; uruchamia przygotowane wdrożenie według `DEPLOYMENT.md`. Nie publikować samego frontendu jako rzekomo działającego wyszukiwania SPHEREx.
2. Testuje publiczny adres na drugim urządzeniu, również po restarcie, i zapisuje wynik `smoke_submission.py`.
3. Wykonuje krótką próbę z 2–3 osobami: czy odróżniają czas od pasma i potrafią otworzyć kartę? Zapisać rzeczywiste obserwacje, bez dopisywania statystyk.
4. Wybiera nazwę i potwierdza autorstwo, referencje oraz wkład SI/AI. Materiały do zgłoszenia są w `PAKIET_ZGLOSZENIA_EN.md`.
5. Zespół sam akceptuje warunki i wybiera „Submit for Judging”. Oficjalny przewodnik: 15 listopada 2026, 23:59 w strefie eventu; lokalny pitching może być wcześniej. Nie wysłano zgłoszenia.
