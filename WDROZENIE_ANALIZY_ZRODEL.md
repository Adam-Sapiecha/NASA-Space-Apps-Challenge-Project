# Analiza źródeł — pierwszy etap wdrożenia

Stan: wdrożono narzędzia dla wszystkich pięciu obszarów: identyfikacji, interpretacji widma, wag ekspozycji, prognozy położenia i oceny artefaktów. Trening i walidacja modelu ML są zaimplementowane, ale model pozostaje nieaktywny bez zweryfikowanego zbioru. Oceny użytkowników nie są automatycznie uznawane za prawdę referencyjną.

## Funkcje w aplikacji

Wybierz punkt na zdjęciu i przejdź do zakładki pomiarów. Panel „Źródło i jakość obserwacji” pozwala:

- wyszukać pobliskie identyfikatory Gaia DR3, uporządkowane według odległości od kliknięcia;
- odnieść pozycje katalogowe do daty wybranej ekspozycji przy dostępności ruchu własnego;
- przejrzeć regułową jakość pomiarów w aperturze 12,4 sekundy łuku;
- zapisać ocenę: wiarygodne źródło, artefakt, zlane źródła lub przypadek nierozstrzygnięty, z uzasadnieniem;
- pobrać raporty i historię ocen jako JSON.

Podstawowy panel Gaia pozostaje prostą listą pozycji. Rozszerzony panel opisany poniżej pobiera także typy SIMBAD. Link SIMBAD wyszukuje identyfikator Gaia; nie poświadcza znalezienia odpowiednika w SIMBAD. Pozycja punktu nie jest dopasowanym centroidem. Lista Gaia może zawierać kilka źródeł odpowiadających jednemu sygnałowi SPHEREx. Stożek wyszukiwania wynosi co najmniej 2 minuty łuku, a dopasowanie jest filtrowane wybranym promieniem 1–60 sekund łuku. Bardzo duży ruch własny i limit 500 wpisów mogą powodować pominięcia.

W panelu kalibracji, po przygotowaniu raportu ePSF, dostępna jest „Średnia ważona pomiarów ePSF”. Użytkownik wybiera co najmniej dwa pomiary i okno czasu do 48 godzin. Wagi wynikają z odwrotności wariancji losowej. Obliczenie odrzuca duplikaty, powtórzone sumy kontrolne FITS, nieważne błędy, przekroczenie okna i pary niezgodnych lokalnych pasm. Zgodność pasm pozostaje heurystyką. Wynik zakłada stały strumień i niezależność błędów; nie uwzględnia wspólnej systematyki. Nie zmienia wag obrazów ani dotychczasowego asystenta pasm.

## Dane i odtwarzalność

Rekord źródła wiąże analizę i dokładny punkt użytkownika. Raport identyfikacji dodatkowo zapisuje ekspozycję, epokę i identyfikator zapisanego katalogu. Raport jakości wskazuje pomiar, punkt, promień, wersję reguł i sumy kontrolne obrazów. Oceny są dopisywane z nowym identyfikatorem i czasem; poprzednia ocena nie jest nadpisywana. Bez kont użytkowników autor nie jest uwierzytelniony; provenance ma wartość `unverified_user_assessment`.

API:

| Operacja | Endpoint |
|---|---|
| Utworzenie rekordu punktu | `POST /api/analyses/{id}/sources` |
| Odczyt źródła | `GET /api/sources/{id}` |
| Kandydaci Gaia | `POST /api/analyses/{id}/identification` |
| Odczyt identyfikacji | `GET /api/identifications/{id}` |
| Ocena jakości apertury | `POST /api/analyses/{id}/quality` |
| Odczyt jakości | `GET /api/quality/{id}` |
| Dodanie / odczyt ocen | `POST / GET /api/quality/{id}/labels` |
| Średnia strumieni ePSF | `POST /api/irsa/results/{id}/weighted-flux` |
| Odczyt średniej | `GET /api/weighted-flux/{id}` |

Zapytania katalogowe i pomiar apertury korzystają z istniejących synchronicznych metod i cache. Dla większej liczby ekspozycji przeniesienie ich do istniejącej kolejki jest kolejnym zadaniem. Raporty można pobrać po identyfikatorze; nowy panel nie przywraca ich automatycznie z linku analizy. Ponowne uruchomienie kontroli jakości dla tego samego punktu odczytuje zapisane oceny.

## Rozszerzony panel — wszystkie obszary

W zakładce dokładniejszej analizy, poniżej narzędzi IRSA, znajduje się panel **Identyfikacja, widmo i ruch**. Operacje na FITS i usługi sieciowe korzystają z istniejącej kolejki. Wynik zapisuje się jako raport IRSA i może zostać przywrócony parametrem `science` w linku analizy.

### 1. Identyfikacja

Gaia, SIMBAD i AllWISE są pytane niezależnie. Błąd jednego katalogu nie usuwa wyników pozostałych. SIMBAD korzysta z oficjalnego lustra Harvard, jeśli główny serwer nie odpowiada. AllWISE ma alternatywny odczyt przez IRSA Gator. Zapisywane są parametry zapytania, data pobrania, lista kandydatów oraz dla nowych odpowiedzi SIMBAD/AllWISE URL i SHA-256 odpowiedzi.

Przed dopasowaniem wykonywana jest próba wyznaczenia centroidu z natywnego FITS. Pozycja jest używana tylko przy SNR ≥ 5 i χ²/dof ≤ 3; inaczej pozostaje kliknięcie, z ostrzeżeniem. SIMBAD dostarcza nazwę, typ obiektu i klasę widmową, gdy są dostępne. Pozycje katalogowe mogą być wyświetlone na zdjęciu. Listy katalogów nie są automatycznie scalane; pozycja AllWISE pozostaje historyczna.

### 2. Interpretacja widma

Wykonaj lokalny pomiar ePSF przyciskiem „Zmierz z kalibracją IRSA”, wybierz przynajmniej cztery różne długości fal i uruchom porównanie. Biblioteka fizycznego kontinuum obejmuje ciała doskonale czarne 300–12000 K i modele potęgowe Fν. Można zaimportować do trzech własnych wzorców JSON, z nazwą i pochodzeniem:

```json
[{"name":"Mój wzorzec","provenance":"Publikacja lub opis modelu i jednostek","wavelength_um":[0.5,1,3,6],"relative_fnu":[0.2,1,0.8,0.3]}]
```

Wzorzec wymaga rosnących fal, nieujemnego względnego Fν i pokrycia całego zakresu wybranych pasm. Import nie weryfikuje jego pochodzenia. Modele są uśredniane w prostokątnych przybliżeniach pasm CWAVE/CBAND. Dopasowanie normalizacji i ranking χ² nie są pełną interpretacją atmosfery lub typu źródła.

Kontrola okien H₂O (3,05 μm), CO₂ (4,27 μm) i CO (4,67 μm) wymaga co najmniej jednego pasma w środku i dwóch po każdej stronie, w całości mieszczących się w odpowiednich oknach. Dopasowuje liniowe kontinuum i propaguje losowy błąd kontrastu. Wynik „zagłębienie do weryfikacji” nie potwierdza związku chemicznego. Nie wyznaczamy składu procentowego. Potrzebne są pełne krzywe transmisji, wzorce laboratoryjne i niezależna walidacja przed wnioskami naukowymi.

### 3. Wagi na podstawie zdjęć

Plan wag wymaga raportu kalibracji i diagnostyki natywnych FITS dla dokładnie tego samego punktu. Użytkownik wybiera ekspozycję odniesienia A i okno do 48 h. Algorytm sprawdza ważność, sąsiadów, χ² PSF, wadliwe pokrycie, powtórzone FITS oraz wzajemną zgodność pasm i czasu wszystkich wybranych składników. Używa odwrotności wariancji losowej ePSF; nie maksymalizuje przypadkowego piku jasności. Progi pozostają eksploracyjne.

Plan pokazuje także wykluczone ekspozycje i powody. Można świadomie zastosować stałe wagi do istniejącego jakościowego składania. Jest to lokalny dobór dla źródła, bez gwarancji poprawy całego pola i bez ilościowego modelu niepewności obrazu wynikowego.

### 4. Przyszłe położenie

- **Gaia:** propagacja katalogowego ruchu własnego do wybranej daty, bez wymyślonej niepewności. Bez paralaksy i prędkości radialnej.
- **JPL Horizons:** efemerydy znanych obiektów, nazwa rozpoznana przez JPL, jawny obserwator i dostępne niepewności 3σ. Domyślnie Ceres i środek Ziemi (`500@399`). Pozycje ziemskie nie są perspektywą SPHEREx. Numery Horizons mogą oznaczać różne klasy obiektów; sprawdź nazwę rozpoznaną przez usługę.
- **Własne pomiary:** dodaj wybrany punkt źródła w co najmniej trzech różnych ekspozycjach i terminach. Każda pozycja jest ponownie dopasowywana na natywnym FITS. Ważony model lokalnego ruchu liniowego zwraca reszty, niepewność osi i — od czterech pomiarów — błędy pomijanych kolejno epok. Ekstrapolacja jest ograniczona do jednej bazy czasowej i 365 dni w przyszłość. To nie wyznaczenie orbity.

### 5. Artefakty i model ML

Diagnostyka dopasowuje źródło z ePSF i płaszczyzną tła w natywnym wycinku 17×17. Gdy brak ePSF, używa jawnie oznaczonego Gaussa do diagnostyki. Wyznacza pozycję, formalną niepewność, SNR, χ², wydłużenie, wadliwe pokrycie i strukturę reszt. Podłoga astrometryczna 2″ jest ustawieniem eksploracyjnym, nie kalibracją instrumentu.

Oceny w panelu jakości można jawnie zatwierdzić po przeglądzie, podając recenzenta i uzasadnienie. Do treningu trafiają tylko zatwierdzone najnowsze etykiety źródło/artefakt posiadające cechy FITS. Nowsza ocena nierozstrzygnięta lub zlane źródła wycofuje przykład. Bez kont recenzent nie jest uwierzytelniony.

Trening używa regularyzowanej regresji logistycznej (SciPy); nie dodaje ciężkiego frameworka. Minimum startowe: 60 przykładów, po 20 każdej klasy, 12 niezależnych grup. Analizy, źródła, wspólne FITS i pozycje bliższe niż 60″ są łączone w grupy. Stałe koszyki skrótu grup dzielą trening, walidację i test; brak obu klas w podzbiorach zatrzymuje trening.

Normalizacja jest uczona tylko na treningu; próg wybierany na walidacji. Aktywacja wymaga co najmniej 95% zachowania źródeł i 30% odzysku artefaktów w teście oraz przewagi nad porównywanym wynikiem reguł przy tym samym budżecie zachowania źródeł. Model odrzucony jest zapisywany, lecz nie zastępuje aktywnego. Parametry, etykiety, podział i metryki są zapisywane jako JSON, bez pickle. Wynik jest wskaźnikiem do przeglądu, nie skalibrowanym prawdopodobieństwem. Wielokrotne dostrajanie na obejrzanym teście wymaga nowego niezależnego testu.

W aktualnym lokalnym zbiorze nie ma zweryfikowanych przykładów. Model nie został wytrenowany ani aktywowany; nie zastępujemy tego treningiem na danych syntetycznych.

## Dodatkowe API

| Funkcja | Endpoint |
|---|---|
| Wielokatalogowy kontekst (zadanie) | `POST /api/analyses/{id}/context` |
| Diagnostyka FITS i cechy (zadanie) | `POST /api/analyses/{id}/profile` |
| Modele widmowe (zadanie) | `POST /api/irsa/results/{id}/interpret-spectrum` |
| Plan wag | `POST /api/irsa/results/{id}/weight-plan` |
| Zastosowanie planu do podglądu | `POST /api/irsa/results/{id}/stack-weight-plan` |
| Efemerydy JPL (zadanie) | `POST /api/ephemerides` |
| Propagacja Gaia | `POST /api/star-positions` |
| Własny ruch (zadanie) | `POST /api/analyses/{id}/motion` |
| Przegląd etykiety | `POST /api/artifacts/labels/{id}/review` |
| Stan / dane do treningu | `GET /api/artifacts/status`, `GET /api/artifacts/dataset` |
| Trening (zadanie) | `POST /api/artifacts/train` |
| Model i metryki | `GET /api/artifacts/models/{id}` |

Status zadania: `GET /api/jobs/{id}`, raport: `GET /api/irsa/results/{id}`.

## Sprawdzenie

Nowe testy: `backend/tests/test_source_assessment.py` i `backend/tests/test_scientific_models.py`. Sprawdzają reprodukowalność punktu, przejście RA przez zero, wiele odpowiedników, nieważne dane, interpretację flag, historię etykiet, przypisanie do ekspozycji i ograniczenia średniej ważonej. To testy syntetyczne algorytmów i API, nie ocena skuteczności astronomicznej.

Kontrole: pełny pytest backendu, testy frontendu i produkcyjny build. W sandboxie Windows TestClient może zawiesić się przy tworzeniu lokalnego socketpair; testy API wymagają wówczas wykonania poza tym ograniczeniem. Systemowy TEMP może również wymagać zastąpienia katalogiem wewnątrz `.cache/`.


Test rzeczywisty: `.venv\Scripts\python.exe scripts/smoke_scientific_models.py`. Zapisuje `data/smoke_scientific_models.json`, bez trenowania i aktywowania modelu. Próba na zapisanym przykładzie przetworzyła 10 ekspozycji, uzyskała 4 formalnie zbieżne dopasowania z ostrzeżeniami jakości i obsłużyła pozostałe jako nierozstrzygnięte. Gaia, SIMBAD przez lustro i AllWISE odpowiedziały bez utraty wyników częściowych. JPL poprawnie zwrócił Ceres. Nie jest to walidacja identyfikacji źródła, składu ani dokładności astrometrii.

W przeglądarce sprawdzono wykonanie diagnostyki przez kolejkę, tabelę ostrzeżeń i efemerydy z wykresem. Pełna walidacja naukowa na niezależnych obiektach pozostaje wymagana.
