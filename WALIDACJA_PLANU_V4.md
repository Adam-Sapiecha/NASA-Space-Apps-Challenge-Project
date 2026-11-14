# Walidacja pól według planu 4.0

**Historyczny wynik pipeline, nie aktualny test pięciu obiektów.** W finalizacji wykryto błędne centra Epsilon Indi B i R Draconis oraz problem epok szybko poruszających się celów. Nowe wyniki z poprawionymi pozycjami: [WYNIKI_5_OBIEKTOW.md](WYNIKI_5_OBIEKTOW.md). Zachowano dawny raport i cache jako ślad audytu.

Rzeczywiste zapytania IRSA DR1, pola 4′, pierwsza i ostatnia dostępna ekspozycja D2. To kontrola pipeline, lokalnego pasma i pokrycia, bez identyfikacji źródeł. Pozycje startowe nie są propagowane. Apertura 12,4″ w centrum pola nie musi obejmować wskazanego obiektu. Wybór skrajnych dat nie gwarantuje zgodnych pasm.

| Pole | Rekordy SIA | Baza dni | Ważne apertury | Zbliżone pasma w centrum | Wynik |
|---|---:|---:|---:|---|---|
| Barnard’s Star | 255 | 213.27 | 1 | nie | Sprawdzono obrazy pola i aperturę w pozycji startowej; nie zidentyfikowano źródła ani nie potwierdzono ruchu/zmienności. |
| Epsilon Indi B | 400 | 370.73 | 2 | tak | Sprawdzono obrazy pola i aperturę w pozycji startowej; nie zidentyfikowano źródła ani nie potwierdzono ruchu/zmienności. |
| WISE 0855 | 279 | 373.18 | 2 | nie | Sprawdzono obrazy pola i aperturę w pozycji startowej; nie zidentyfikowano źródła ani nie potwierdzono ruchu/zmienności. |
| RW Aurigae | 228 | 181.94 | 0 | nie | Sprawdzono obrazy pola i aperturę w pozycji startowej; nie zidentyfikowano źródła ani nie potwierdzono ruchu/zmienności. |
| R Draconis | 453 | 188.95 | 2 | nie | Sprawdzono obrazy pola i aperturę w pozycji startowej; nie zidentyfikowano źródła ani nie potwierdzono ruchu/zmienności. |

## Odtworzenie

Szczegóły zapytań, identyfikatory analiz i pomiarów: `data/audit/plan-v4.json`. Analizę można otworzyć jako `/?analysis=ID`. Manifest analizy zawiera identyfikatory i SHA-256 źródłowych FITS. Pomiary: `/api/measurements/ID`. Pliki cache pozostają na tym samym serwerze.

## Nierozstrzygnięte

Brak niezależnej identyfikacji i astrometrii, modelu ruchu, kalibracji PSF/apertury i badania skuteczności. Nie potwierdzamy detekcji pięciu obiektów, wykrycia ruchu ani zmiany jasności. Asystent nie proponuje wag przed walidacją na niezależnych obserwacjach.

Odrzucenia apertury: Barnard’s Star — w jednej klatce pierścień tła wykracza poza wycinek; RW Aurigae — obie apertury nie spełniają kontroli ważnych pikseli/wariancji/tła. Przy tej metodzie odrzucamy pomiar zamiast uzupełniać brakujące dane.
