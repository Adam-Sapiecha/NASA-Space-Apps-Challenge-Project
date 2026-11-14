# Wyniki pięciu wymaganych obiektów

**Nowszy dobór lokalnych pasm i jakości:** [wyniki z 36 kandydatów na pole](WDROZENIE_EN_I_DOBORU_OBSERWACJI.md). Poniższy raport zachowuje wcześniejszą próbkę do porównania.

**Uwaga o wersji:** zachowano poniższe wyniki wcześniejszej metody audytowej. Nowe obliczenia z mapą powierzchni pikseli i stan po poprawkach: [NAPRAWY_AUDYTU_MATEMATYCZNEGO.md](NAPRAWY_AUDYTU_MATEMATYCZNEGO.md) i `data/audit/math_fixes_20261114/offline-validation.json`.

Kontrola: 14 listopada 2026. Dane SPHEREx DR1; nowe zapytania i pola 6′ wokół katalogowych przewidywań J2026.0. Wybrano do ośmiu produktów D2 na pole i D6 dla WISE 0855, rozłożonych według czasu. W rzadkich lub skupionych terminach dobór dał mniej niż osiem ekspozycji. To próbka, nie pełny przegląd archiwum.

**Wniosek: zweryfikowano katalogowe tożsamości i obrazy poprawionych pól. Nie potwierdzono identyfikacji wszystkich źródeł w SPHEREx, ruchu ani zmienności.**

Wcześniejsze testy zawierały błędne centra Epsilon Indi B i R Draconis. Ich liczb i wyników nie należy traktować jako testów prawidłowych obiektów. Dotychczasowy Barnard’s Star był centrowany na starej pozycji, bez uwzględnienia dużego ruchu własnego.

| Obiekt | Centrum pola J2026.0 (RA / Dec °) | Rekordy archiwum | Przygotowano / wybrano | Ważne apertury przy przewidywaniu | Pary o zbliżonych pasmach |
|---|---|---:|---:|---:|---:|
| Barnard’s Star | 269.4462679 / 4.7682044 | 260 | 4 / 4 | 0 | 0 |
| Epsilon Indi B | 331.0966688 / -56.8006492 | 368 | 6 / 6 | 0 | 0 |
| WISE 0855 | 133.7597618 / -7.2421869 | 280 | 5 / 7 | 4 | 1 |
| RW Aurigae | 76.9565866 / 30.4012914 | 237 | 4 / 4 | 0 | 0 |
| R Draconis | 248.1672331 / 66.7550238 | 456 | 3 / 4 | 0 | 0 |

Ważna apertura nie jest potwierdzoną detekcją. Zgodność pasm to próg połowy węższej szerokości z WCS-WAVE; nie dowodzi zgodności pełnych odpowiedzi spektralnych. Pomiar w każdej ekspozycji wykonano przy osobnym katalogowym przewidywaniu, nie w starej stałej pozycji.

## Tożsamości i wyniki szczegółowe

### Barnard’s Star

Katalog: **NAME Barnard's star**. [Źródło](https://simbad.cfa.harvard.edu/simbad/sim-id?Ident=GJ+699), odniesienie `2020yCat.1350....0G`. Pozycja odniesienia ICRS 269.45207696°, 4.69336497°; epoka MJD 51544.50 (J2000.0000). Ruch własny μα* / μδ: -801.551 / 10362.394 mas/rok.

Analiza: `65f24c5b4a7245459d81b4f7ae95bcf1` · [otwórz lokalnie](http://127.0.0.1:8000/?analysis=65f24c5b4a7245459d81b4f7ae95bcf1). Detektor SPHEREx-D2; daty przygotowanych produktów 2025-08-20T23:03:20.074 — 2026-03-22T05:29:34.498 UTC.

| Data UTC | Przewidywane RA / Dec ° | Ważny pomiar | λ (µm) | Strumień apertury ± błąd losowy (mJy) | Ograniczenie |
|---|---|---|---|---|---|
| 2025-08-20T23:03:20.074 | 269.4463493 / 4.7671560 | nie | — | — | Pierścień tła wykracza poza wycinek FITS. |
| 2025-08-30T16:11:25.958 | 269.4463433 / 4.7672325 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2026-03-15T00:47:02.645 | 269.4462232 / 4.7687800 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2026-03-22T05:29:34.498 | 269.4462188 / 4.7688367 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |

Kontrola natywnych flag przy przewidywanej pozycji: BLOOM, OVERFLOW, SUR_ERROR, TRANSIENT. Liczby pikseli SOURCE w pierścieniu tła: 73/73, 74/74, 71/71. SOURCE pozostaje dozwolone w aperturze celu, ale jest wykluczane z tła.

Brak pary spełniającej jednocześnie przyjęte warunki apertury i lokalnego pasma w tej próbce. Nie oznacza to, że w całym archiwum taka para nie istnieje.

**Wynik astronomiczny: nierozstrzygnięty.** Katalogowa pozycja, pokrycie i flaga SOURCE nie są niezależnym potwierdzeniem tożsamości źródła. Nie raportujemy ruchu, zmienności ani prawdopodobieństwa odkrycia.

### Epsilon Indi B

Katalog: *** eps Ind B**. [Źródło](https://simbad.cfa.harvard.edu/simbad/sim-id?Ident=eps+Ind+B), odniesienie `2020yCat.1350....0G`. Pozycja odniesienia ICRS 331.04414659°, -56.78284420°; epoka MJD 51544.50 (J2000.0000). Ruch własny μα* / μδ: 3981.977 / -2466.832 mas/rok.

Analiza: `5bbf47dc2673437a86c2026abac19f03` · [otwórz lokalnie](http://127.0.0.1:8000/?analysis=5bbf47dc2673437a86c2026abac19f03). Detektor SPHEREx-D2; daty przygotowanych produktów 2025-04-24T20:32:54.643 — 2026-04-30T14:07:45.235 UTC.

| Data UTC | Przewidywane RA / Dec ° | Ważny pomiar | λ (µm) | Strumień apertury ± błąd losowy (mJy) | Ograniczenie |
|---|---|---|---|---|---|
| 2025-04-24T20:32:54.643 | 331.0952791 / -56.8001786 | nie | — | — | Za mało pikseli tła po wykluczeniu znanych źródeł. |
| 2025-06-07T12:56:45.758 | 331.0955208 / -56.8002604 | nie | — | — | Za mało pikseli tła po wykluczeniu znanych źródeł. |
| 2025-10-01T17:55:05.290 | 331.0961638 / -56.8004782 | nie | — | — | Za mało pikseli tła po wykluczeniu znanych źródeł. |
| 2025-11-08T08:58:54.422 | 331.0963721 / -56.8005487 | nie | — | — | Za mało pikseli tła po wykluczeniu znanych źródeł. |
| 2026-04-24T21:18:51.149 | 331.0972990 / -56.8008626 | nie | — | — | Pierścień tła wykracza poza wycinek FITS. |
| 2026-04-30T14:07:45.235 | 331.0973305 / -56.8008732 | nie | — | — | Za mało pikseli tła po wykluczeniu znanych źródeł. |

Kontrola natywnych flag przy przewidywanej pozycji: brak dodatkowych flag w sprawdzonych aperturach. Liczby pikseli SOURCE w pierścieniu tła: 76/76, 75/75, 72/72, 74/74, 73/73. SOURCE pozostaje dozwolone w aperturze celu, ale jest wykluczane z tła.

Brak pary spełniającej jednocześnie przyjęte warunki apertury i lokalnego pasma w tej próbce. Nie oznacza to, że w całym archiwum taka para nie istnieje.

**Wynik astronomiczny: nierozstrzygnięty.** Katalogowa pozycja, pokrycie i flaga SOURCE nie są niezależnym potwierdzeniem tożsamości źródła. Nie raportujemy ruchu, zmienności ani prawdopodobieństwa odkrycia.

### WISE 0855

Katalog: **WISE J085510.83-071442.5**. [Źródło](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJS/253/7), odniesienie `2021ApJS..253....7K`. Pozycja odniesienia ICRS 133.78098400°, -7.24393200°; epoka MJD 57633.39 (J2016.6705). Ruch własny μα* / μδ: -8123.700 / 673.200 mas/rok.

Analiza: `4812094a2ce843a8b787837eb13ec845` · [otwórz lokalnie](http://127.0.0.1:8000/?analysis=4812094a2ce843a8b787837eb13ec845). Detektor SPHEREx-D6; daty przygotowanych produktów 2025-05-05T20:02:32.986 — 2026-05-11T02:19:42.226 UTC.

| Data UTC | Przewidywane RA / Dec ° | Ważny pomiar | λ (µm) | Strumień apertury ± błąd losowy (mJy) | Ograniczenie |
|---|---|---|---|---|---|
| 2025-05-05T20:02:32.986 | 133.7612575 / -7.2423099 | tak | 4.85989 | 0.37714 ± 0.2242 | SOURCE |
| 2025-11-10T07:08:21.710 | 133.7600838 / -7.2422134 | tak | 4.41781 | 0.54283 ± 0.1731 | SOURCE |
| 2025-12-13T00:42:54.634 | 133.7598800 / -7.2421966 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2026-04-21T04:45:58.997 | 133.7590755 / -7.2421304 | tak | 4.42375 | 0.59366 ± 0.1508 | SOURCE |
| 2026-05-11T02:19:42.226 | 133.7589516 / -7.2421202 | tak | 4.96728 | 0.54639 ± 0.2575 | SOURCE |

Kontrola natywnych flag przy przewidywanej pozycji: NONFUNC. Liczby pikseli SOURCE w pierścieniu tła: 18/72, 21/74, 22/72, 24/69, 20/71. SOURCE pozostaje dozwolone w aperturze celu, ale jest wykluczane z tła.

Zbliżona para przy osobnych przewidywaniach: `4432acd4afc90868d16b` / `79ad233baf786e452cbd`, 161.901 dni, λ 4.41781 / 4.42375 µm.
Nieudane pobranie `b25ffa3e7f91864418e3`: HTTPStatusError: Server error '503 Service Unavailable' for url 'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W19_1B/l2b-v27-2026-197/6/level2_2025W19_1B_0116_1D6_spx_l2b-v27-2026-197.fits?center=133.75976184%2C-7.24218689d&size=0.1'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503
Nieudane pobranie `40ec0e464fdcdc0d0b68`: HTTPStatusError: Server error '503 Service Unavailable' for url 'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W50_2A/l2b-v27-2026-210/6/level2_2025W50_2A_0232_1D6_spx_l2b-v27-2026-210.fits?center=133.75976184%2C-7.24218689d&size=0.1'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503

**Wynik astronomiczny: nierozstrzygnięty.** Katalogowa pozycja, pokrycie i flaga SOURCE nie są niezależnym potwierdzeniem tożsamości źródła. Nie raportujemy ruchu, zmienności ani prawdopodobieństwa odkrycia.

### RW Aurigae

Katalog: **V* RW Aur**. [Źródło](https://simbad.cfa.harvard.edu/simbad/sim-id?Ident=RW+Aur), odniesienie `2007A&A...474..653V`. Pozycja odniesienia ICRS 76.95652603°, 30.40143817°; epoka MJD 51544.50 (J2000.0000). Ruch własny μα* / μδ: 7.230 / -20.330 mas/rok.

Analiza: `3d4aab1ac66041ba87f774ae76c3f609` · [otwórz lokalnie](http://127.0.0.1:8000/?analysis=3d4aab1ac66041ba87f774ae76c3f609). Detektor SPHEREx-D2; daty przygotowanych produktów 2025-09-08T06:37:09.293 — 2026-03-09T05:13:26.947 UTC.

| Data UTC | Przewidywane RA / Dec ° | Ważny pomiar | λ (µm) | Strumień apertury ± błąd losowy (mJy) | Ograniczenie |
|---|---|---|---|---|---|
| 2025-09-08T06:37:09.293 | 76.9565858 / 30.4012931 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2025-09-10T18:57:54.619 | 76.9565859 / 30.4012931 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2026-03-01T04:56:42.029 | 76.9565870 / 30.4012904 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2026-03-09T05:13:26.947 | 76.9565870 / 30.4012903 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |

Kontrola natywnych flag przy przewidywanej pozycji: BLOOM, OVERFLOW, SUR_ERROR, TRANSIENT. Liczby pikseli SOURCE w pierścieniu tła: 73/73, 73/73, 73/73, 74/74. SOURCE pozostaje dozwolone w aperturze celu, ale jest wykluczane z tła.

Brak pary spełniającej jednocześnie przyjęte warunki apertury i lokalnego pasma w tej próbce. Nie oznacza to, że w całym archiwum taka para nie istnieje.

**Wynik astronomiczny: nierozstrzygnięty.** Katalogowa pozycja, pokrycie i flaga SOURCE nie są niezależnym potwierdzeniem tożsamości źródła. Nie raportujemy ruchu, zmienności ani prawdopodobieństwa odkrycia.

### R Draconis

Katalog: **V* R Dra**. [Źródło](https://simbad.cfa.harvard.edu/simbad/sim-id?Ident=R+Dra), odniesienie `2020yCat.1350....0G`. Pozycja odniesienia ICRS 248.16761083°, 66.75497942°; epoka MJD 51544.50 (J2000.0000). Ruch własny μα* / μδ: -20.643 / 6.149 mas/rok.

Analiza: `d38309c3d7384c27ae9888c5f491169f` · [otwórz lokalnie](http://127.0.0.1:8000/?analysis=d38309c3d7384c27ae9888c5f491169f). Detektor SPHEREx-D2; daty przygotowanych produktów 2025-06-08T18:55:19.229 — 2025-12-14T17:44:32.539 UTC.

| Data UTC | Przewidywane RA / Dec ° | Ważny pomiar | λ (µm) | Strumień apertury ± błąd losowy (mJy) | Ograniczenie |
|---|---|---|---|---|---|
| 2025-06-08T18:55:19.229 | 248.1672413 / 66.7550229 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2025-07-02T21:49:59.678 | 248.1672403 / 66.7550230 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |
| 2025-12-14T17:44:32.539 | 248.1672338 / 66.7550237 | nie | — | — | Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła. |

Kontrola natywnych flag przy przewidywanej pozycji: BLOOM, OVERFLOW, SUR_ERROR, TRANSIENT. Liczby pikseli SOURCE w pierścieniu tła: 74/74, 73/73, 74/74. SOURCE pozostaje dozwolone w aperturze celu, ale jest wykluczane z tła.

Brak pary spełniającej jednocześnie przyjęte warunki apertury i lokalnego pasma w tej próbce. Nie oznacza to, że w całym archiwum taka para nie istnieje.
Nieudane pobranie `0cee4c31bf43bd73e89b`: HTTPStatusError: Server error '503 Service Unavailable' for url 'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W47_1A/l2b-v27-2026-208/2/level2_2025W47_1A_0388_1D2_spx_l2b-v27-2026-208.fits?center=248.16723307%2C66.75502383d&size=0.1'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503

**Wynik astronomiczny: nierozstrzygnięty.** Katalogowa pozycja, pokrycie i flaga SOURCE nie są niezależnym potwierdzeniem tożsamości źródła. Nie raportujemy ruchu, zmienności ani prawdopodobieństwa odkrycia.

## Kontrole i granice

- SIMBAD ma jawne współrzędne odniesienia ICRS/J2000. WISE 0855 dodatkowo sprawdzono w pierwotnej tabeli Kirkpatrick 2021: RA 133.780984°, Dec −7.243932°, MJD 57633.39. Nie pomylono epoki pozycji z równonocą.
- Propagacja Astropy uwzględnia ruch własny, bez paralaksy, ruchu orbitalnego i przyspieszenia perspektywicznego. To wystarcza do pola przeglądowego; nie do precyzyjnej astrometrii. Epsilon Indi B nie jest tu rozdzielany na dwa potwierdzone składniki.
- WCS, jednostki MJy/sr, przezroczystość braków i źródłowe SHA są zachowane w manifestach; fotometria jest na natywnych IMAGE/VARIANCE/FLAGS. Błąd apertury jest losowy, bez pełnej systematyki.
- Niezależna biblioteka Photutils 3.1.1: 30 porównań na tym samym rzeczywistym polu D6, także w czterech pozycjach kontrolnych poza celem. Maksymalna różnica 0,1076 mJy, mediana bezwzględnej różnicy 0,01580 mJy. Różnice brzegowych masek i tła pozostają jawne. Pól kontrolnych nie sklasyfikowano jako astrofizycznie puste ani stabilne.
- Dla pojedynczej pary po wyłączeniu jednej ekspozycji pozostaje jeden termin: brak niezależnego potwierdzenia na odłożonej epoce o tym samym paśmie. Nie przedstawiono tego jako udanego testu odzysku.
- Brak eksportu IRSA Tractor dopasowanego do tych samych ekspozycji. Lokalnego ePSF nie uznajemy za zewnętrznie zwalidowaną fotometrię.

## Odtworzenie

```powershell
.\.venv\Scripts\python.exe scripts/validate_five_targets.py
.\.venv\Scripts\python.exe scripts/independent_photometry_check.py
.\.venv\Scripts\python.exe scripts/report_five_targets.py
```

Pierwsze polecenie ponawia zapytania i tworzy nowe analizy. Nie usuwa cache. Photutils jest opcjonalnym narzędziem walidacji w `.cache/validation-libs`, a nie zależnością aplikacji produkcyjnej. Surowe dowody: `data/audit/five-targets-final.json`, `five-flags.json`, `independent-photutils.json`, `simbad-identities.json` i `wise0855-reference.tsv`. Snapshoty i FITS zawiera lokalny katalog danych; seed wdrożeniowy zachowuje potrzebne produkty. Liczby rekordów SIA oznaczają pokrycie pól, nie liczbę detekcji obiektów.
