# Automatyczna predykcja ruchu

[Pokaz lokalny](http://127.0.0.1:8000/?prediction=1&motion=0&lang=pl) dodaje prognozę na rzeczywistym zdjęciu. Nie generujemy przyszłych pikseli. Przerywana strzałka, krzyżyk i formalna elipsa 2σ są nakładkami; czas i napis „Predykcja” pozostają widoczne. Suwak pozwala wybrać późniejszy czas w ograniczonym horyzoncie. Prognoza poza kadrem jest jawnie oznaczana.

## Co działa automatycznie

1. SEP wykrywa źródła w natywnych FITS z wariancją i maskami jakości.
2. W przykładzie znanej 3I/ATLAS pozycje z IRSA MOST ograniczają kojarzenie źródła do 20″; współrzędne dopasowania pochodzą z centroidów w obrazach, nie z efemeryd. Nie jest potrzebne ręczne klikanie ani etykietowanie.
3. Dla innych pól automat próbuje połączyć źródła na pierwszych zdjęciach liniową trajektorią. Odrzuca wieloznaczne i zbyt małe przesunięcia. Bounded search sprawdza do 30 kandydatów w pierwszych dwóch zdjęciach oraz do 100 na późniejszych, maksymalnie 12 zdjęć.
4. Ostatnia ekspozycja jest wydzielana przed wyborem trajektorii. Co najmniej trzy wcześniejsze terminy służą do dopasowania ważonego modelu liniowego na lokalnej sferze nieba.
5. Model przewiduje pozycję na ostatniej ekspozycji. Przycisk odsłania prawdziwe zdjęcie i porównuje predykcję z automatycznym pomiarem. Dla nieznanej trajektorii kojarzenie źródła kontrolnego używa okna wokół prognozy; to słabszy test tożsamości niż niezależny katalog.
6. Po udanym sprawdzeniu osobny model jest ponownie dopasowany do wszystkich pomiarów. Ten model służy do późniejszej prognozy na tle ostatniego zdjęcia.

## Rzeczywisty test 3I/ATLAS

SPHEREx DR1, D6, 14 grudnia 2025. Wizyty treningowe zaczynają się o 11:00:48, 12:38:45 i 17:28:15 UTC. Odłożona wizyta kontrolna zaczyna się o 19:07:32 UTC. Obliczenia używają środków ekspozycji; etykiety nakładki podają ten czas. Źródło: [IRSA MOST](https://irsa.ipac.caltech.edu/applications/MOST/) i [oficjalne obserwacje 3I/ATLAS](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/comet3iatlas/).

Automatyczny test dał **3,485″** odległości między predykcją a centroidem kontrolnym, czyli **0,563 piksela** wspólnej siatki 30′ / 291 pikseli. RMS dopasowania trzech pozycji: 5,983″. Formalny błąd jednej osi prognozy kontrolnej: 9,367″. To wynik jednego przykładu, a nie skuteczność dla dowolnych danych ani pomiar dokładności centroidu względem prawdziwego jądra komety.

Centroid SEP może być przesunięty przez komę, sąsiadów lub różnice pasma/PSF. Stosujemy eksploracyjną podłogę błędu 6,2″. Model nie wyznacza orbity, nie uwzględnia przyspieszenia ani pełnej kowariancji błędów systematycznych. Elipsa jest formalna, nie gwarantuje kalibrowanego pokrycia. Horyzont prognozy nie przekracza jednej rozpiętości czasu danych treningowych. Nieudany test blokuje prognozowanie dalej.

## Implementacja i odtwarzanie

- `backend/auto_motion.py`: ekstrakcja, kojarzenie, dopasowanie, test czasowy, formalna kowariancja i współrzędne nakładki.
- `POST /api/analyses/{id}/auto-motion`: zadanie w istniejącym procesie obliczeniowym; wynik przez `/api/irsa/results/{job_id}`. Obecna seria może zostać sprawdzona jednym przyciskiem. Brakujące dane lub niejednoznaczność zwracają status `unavailable`, bez wymyślonej trajektorii.
- `scripts/prepare_prediction_demo.py`: pobranie czterech produktów z zapisanej oficjalnej odpowiedzi MOST, zapis pola i referencji kojarzenia.
- `scripts/export_prediction_demo.py`: wykonanie automatycznej analizy i eksport przenośnych obrazów, FITS, raportu, sum SHA-256 oraz informacji o przetwarzaniu do `frontend/public/prediction-demo/`.
- Przenośny pokaz działa bez IRSA; ponowne obliczenie wymaga zachowanych natywnych FITS i analizy. Skrypt pakowania uwzględnia tę analizę.
- Testy: `backend/tests/test_auto_motion.py` sprawdzają brak przecieku zdjęcia kontrolnego do modelu, odmowę przy niejednoznaczności, blokadę prognoz po nieudanym teście, automatyczne kojarzenie bez katalogu, przejście RA przez zero, wzrost niepewności i rzeczywisty zestaw FITS.

Wszystkie wcześniejsze narzędzia pozostają w aplikacji. Ten moduł nie jest siecią neuronową ani modelem wytrenowanym na ręcznie opisanych klasach.
