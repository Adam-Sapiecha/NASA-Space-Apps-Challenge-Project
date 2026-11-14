# Niezależny audyt matematyczny, fizyczny i astrofizyczny

**Aktualizacja po poleceniu „popraw”:** poniższy tekst zachowuje ustalenia dla wersji sprzed napraw. Wdrożone zmiany, nowe wyniki i pozostałe ograniczenia: [NAPRAWY_AUDYTU_MATEMATYCZNEGO.md](NAPRAWY_AUDYTU_MATEMATYCZNEGO.md). Poniższe numery linii odnoszą się do zachowanej wersji audytowej.

**Ocena:** aplikacja jest poprawnym narzędziem do eksploracji rzeczywistych obrazów SPHEREx, oglądania pokrycia i flag oraz zapisywania sprawdzalnych hipotez. **Warunkowo użyteczne** są natywne pomiary apertury, lokalne dopasowania ePSF i centroidy: przy znanej pozycji, odpowiednim modelu źródła, dobrym tle, poprawnych flagach i kontroli kalibracji. **Obecne wyniki nie dają podstaw do ogłoszenia zmienności, pomiaru ruchu o skalibrowanej istotności, nowego obiektu, identyfikacji molekuł ani poprawy wykrywalności.** To ograniczenie wnioskowania, nie stwierdzenie, że wszystkie obliczenia są błędne.

Nie znalazłem błędu o czynnik 1000 w jednostkach ani błędnego czynnika cos δ w ruchu własnym. Wzory na losowy błąd apertury wraz z estymacją tła są poprawne przy jawnych założeniach. Najważniejsze problemy dotyczą zgodności pozycji, odporności estymatora na model, niepełnego dopasowania danych referencyjnych i znaczenia słowa „walidacja”. Rozszerzenia o klasyfikator i interpretację widma nie zastępują rozwiązania tych problemów.

Audyt wykonano 14 listopada 2026. Przeczytano siedem dokumentów wskazanych w zleceniu i sprawdzono ich twierdzenia w kodzie. Podstawą oceny są **22 zachowane natywne FITS pięciu poprawionych pól**, ich flagi, wariancje, WCS, rzeczywiste ePSF i mapy kalibracyjne, a także nowe zapytania SIMBAD/VizieR. Poprzedni audyt nie był przyjęty jako dowód.

## 1. Zakres, stan repozytorium i ślad obliczeń

Nie zmieniałem kodu produkcyjnego, zapisanych pomiarów, manifestów ani bazy aplikacji. Nie uruchamiałem treningu, nowych zadań aplikacji, publikacji ani pobierania nowych obrazów. SQLite otwierano przez `mode=ro`. Porównanie importu referencji wywołano z zamockowanym jedynym zapisem. Kontrole centroidów podmieniały wyłącznie funkcję lokalizującą istniejący plik, bez pobierania i zapisywania pomiaru.

Repozytorium jest aktywnie modyfikowane przez inną pracę. Pierwsza kontrola wykryła zmianę `frontend/src/App.tsx` i `GuidedStart.tsx`; później pojawiły się m.in. `analysis_api.py`, `trajectory.py`, `spectral_models.py`, `exposure_weights.py` i `artifact_model.py`, a zmieniły `main.py`, `irsa_jobs.py`, `object_context.py`. Uwzględniłem nowe moduły w osobnym przeglądzie. **Rdzeń obliczeń `science.py`, `measurements.py`, `calibrated.py`, `irsa_resources.py`, `targets.py` i `temporal.py` pozostał zgodny z początkowymi hashami podczas tych kontroli.** Ostatnia kontrola rozszerzeń nie wykazała zmian plików w czasie jej obliczeń. Raport nie poświadcza przyszłych edycji.

Artefakty audytu:

- `scripts/audit_math_physics.py` → `data/audit/math_physics_20261114/results.json`: niezależne wzory, 22 FITS, jednostki, geometria, fotometria, ePSF, kontrole syntetyczne i błędna referencja.
- `scripts/audit_math_supplement.py` → `supplement.json`: paralaksa, osiem zadanych z góry pozycji kontrolnych na rzeczywistych obrazach, eksport trasy, diagnostyczna próba Epsilon Indi B bez warunku pierścienia.
- `scripts/audit_recent_extensions.py` → `recent_extensions.json`: 22 próby centroidów, nowy model ruchu, ryzyka grupowania ML, oryginalna epoka Gaia.
- W tym samym katalogu: świeże odpowiedzi `simbad_fresh.csv`, `wise_reference_fresh.tsv`, `barnard_gaia2016_fresh.tsv`, pomiar szerokości modeli `epsf_fwhm.json`, obraz `native_fields.png` i hashe wejściowych plików produkcyjnych.
- `source_snapshot_final/manifest.json` i kopie 31 plików: końcowy zapis audytowanych źródeł **17:00:52 UTC (18:00:52 CET)**. Pozwala ustalić treść i numery linii mimo dalszych edycji repozytorium. Końcowy odczyt klasyfikatora uwzględnia dodane porównanie z regułą heurystyczną; nie wykonano jego treningu.

Wyniki pierwszej serii zapisano około 17:35 CET, rozszerzenia sprawdzano później. Wersje wykonawcze: Python 3.12, NumPy 2.5.4, SciPy 1.18.1, Astropy **7.2.3**, Reproject **0.21.0**, Photutils **3.1.1**. Photutils i biblioteki wykresu znajdują się w osobnych katalogach `.cache`, bez zmiany zależności aplikacji. Dokumentacja Astropy „stable” wskazywała 8.0.2; dodatkowo odczytano rzeczywistą implementację `proj_plane_pixel_area` z zainstalowanej 7.2.3.

SHA wszystkich 22 FITS zgadzają się z manifestami. Ponowna kontrola 22 obrazów i obu map D6 nie wykazała zmiany zawartości. Kontrole nie potwierdzają autentyczności archiwum przez sam hash: hash poświadcza tożsamość lokalnego pliku z zachowanym wejściem.

## 2. Usterki i ryzyka według ważności

Ścieżki w tabeli są względem `C:\Users\ksawi\Desktop\Repozytoria\Hackaton`. P1 oznacza problem blokujący odpowiednie twierdzenie ilościowe albo mylący eksport; nie awarię całej przeglądarki. P2 oznacza istotne ograniczenie lub przybliżenie. Nie stwierdzono P0, czyli katastrofalnego błędu rachunkowego unieważniającego wszystkie wyniki.

| Ważność i rodzaj | Plik i zweryfikowane linie | Wzór / założenie | Dowód i skutek | Minimalna poprawka |
|---|---|---|---|---|
| **P1 — niespójność współrzędnych** | `backend/main.py:524–525`; `measurements.py:58`; `evidence.py:25–29,46` | Odczyt zwraca środek piksela `floor(xN)`, pomiar używa `xN−½`. | Dla N=59, punktu (0,509; 0,507): **3,813″** różnicy. Na rzeczywistym listopadowym D6 kontrast apertury 0,6931 wobec 0,7354 mJy. Środek (0,5; 0,5) ukrywa problem w tej analizie. | Jedna definicja ciągłego punktu dla RA/Dec, markerów i pomiarów; odczyt konkretnego piksela opisać osobno i zachować jego indeks. |
| **P1 — błędna lokalizacja metadanych eksportu trasy** | `backend/evidence.py:15–34` wobec `74–79` | Pasmo pochodzi z `note.point`, marker w trybie route z kotwicy. | Syntetyczna adnotacja na prawdziwych klatkach: podpis A **4,417819 µm**, pod markerem **4,416871 µm**. Dla trasy bez point podpisuje centrum pola. | Dla każdego panelu wyznaczyć pozycję zgodną z rysowanym markerem; jawnie oddzielić stałą aperturę od trasy. |
| **P1 — niepełna kontrola referencji** | `backend/reference_spectra.py:41–43,77–83,89–95` | Detektor + czas ± ekspozycja + 2″ mają oznaczać właściwy pomiar. | Wiersz **syntetyczny**, λ=1,2 µm, D6, zgodny czas/RA/Dec, bez wydania/LVF: `matched_count=1` dla lokalnego 4,41717 µm. Pasmo i LVF nie są porównywane; puste wydanie przepuszczane. | Weryfikować ID ekspozycji/LVF i wydanie, λ/szerokość/odpowiedź oraz jednostki; brak metadanych oznaczać „niezweryfikowane”, nie zgodność wydania. |
| **P1 — brak odporności fotometrii na pozycję/model** | `backend/calibrated.py:42–62,69,110–111`; osobno `native_diagnostics.py:16–78` | Fν i tło dopasowane przy zadanym x,y; późniejszy centroid nie aktualizuje tego pomiaru. | Kwietniowy D6: x−0,5 px zmienia ePSF **0,3778→0,5655 mJy**, χ²ν **1,218→1,011**. Dla tej samej pary znak różnicy apertury jest przeciwny do znaku różnicy ePSF. | Pokazywać wrażliwość na x,y i model tła; osobny, jawnie oznaczony pomiar przy zweryfikowanym centroidzie. Nie wybierać najlepszego strumienia z przesunięć. |
| **P1 dla deklaracji naukowej — „validated” ML za mocne** | `backend/artifact_model.py:43–70,73–80,122–157` | Punktowe retention≥0,95 i recall≥0,3 oraz warunek porównania z regułą dopuszczają aktywację modelu. | Przy dopuszczalnych 5 źródłach w teście wynik 5/5 ma dolną jednostronną granicę 95% jedynie **0,549**, nie 0,95. Osobne wycinki tej samej ekspozycji mogą trafić do różnych grup. Model aktywny w odczytanej bazie: **brak**. | Pozostawić wyłączony do danych kontrolnych; nazwać walidację lokalnym testem eksperymentalnym, grupować po oryginalnej ekspozycji/polu, podawać liczebności i przedziały. |
| **P2 — przybliżenie powierzchni piksela** | `backend/measurements.py:77,87`; poprawniejszy wariant `calibrated.py:91,98,107–109` | Jeden `|det CD|` zamiast Ωᵢ. | WISE: mapa zmienia kontrast apertury o około **−0,84% do +1,09%**. To rzeczywisty błąd przybliżenia, lecz mniejszy od obecnego błędu losowego. | Stosować mapę Ωᵢ także w podstawowym pomiarze lub jawnie nazwać go przybliżonym; zachować osobny identyfikator metody/cache. |
| **P2 — niepełna normalizacja ePSF po przesunięciu** | `backend/calibrated.py:45–46` | `sum(ePSF)/(ox oy)` zastępuje normalizację próbkowanego modelu. | W 25 sztucznych fazach rzeczywistego ePSF suma natywnego modelu **0,97859–1,01941**. Współczynnik amplitudy ma zależność od fazy i interpolatora. | Uzgodnić definicję strumienia i skończonego stempla z IRSA; kontrolować sumę po próbkowaniu, wstrzyknięcia oraz straty w skrzydłach. |
| **P2 — model tła i sąsiadów** | `measurements.py:32–42`; `calibrated.py:103–115`; `native_diagnostics.py:64–70` | Średnia z wyciętego pierścienia; sąsiad ostrzegany dopiero po wyłączeniu SOURCE. | Na prawdziwej pozycji kontrolnej (0,7; 0,3) w listopadzie zmiana modelu tła zmienia F o **0,136 mJy**, przy błędzie 0,168 mJy. Test sąsiada nie bada wykluczonych SOURCE ani wnętrza apertury. | Pokazać geometrię tła i jego czułość, porównać średnią/płaszczyznę, obejrzeć sąsiadów; nie znosić masek tylko po to, by uzyskać wynik. |
| **P2 — wspólna bramka apertury i ePSF** | `backend/calibrated.py:101–111` | Dobry pierścień apertury jest wymagany również przed dopasowaniem ePSF z własnym tłem. | Epsilon Indi B ma czyste rdzenie, lecz 0 pikseli tła po SOURCE. Ominięcie bramki tylko w audycie daje jednak złe stałopozycyjne χ²ν **17–89**. | Rozdzielić ważność estymatorów, zachowując osobne kryteria jakości PSF. Samo usunięcie bramki nie waliduje strumienia. |
| **P2 — uproszczenie astrometrii** | `targets.py:12–19`; `catalogs.py:23–39`; `trajectory.py:63–78`; `types.ts:28–31` | Ruch własny bez paralaksy, orbity i pełnej kowariancji. | WISE XI–IV: PM 3,613″, zmiana wektora paralaksy 0,856″, łącznie ok. 4,461″. Stożek katalogowy może pominąć źródło, które weszło do pola. | Etykieta „prognoza PM”; pokazać skalę brakujących efektów, używać poprawnej epoki i większego stożka przed propagacją. |
| **P2 — heurystyka pasma** | `frontend/src/workflow.ts:21–22,25–43`; `spectral.ts:45–52`; `temporal.py:18–21`; `change_diagnostics.py:28–35` | `|λ₁−λ₂|≤½ min Δλ` ma przybliżać porównywalność. | Zbieżność centrów nie gwarantuje tej samej ważonej całki widma; nachylenie i struktura widma mogą dać pozorną zmianę. | Zachować jako filtr przeglądu. Ilościowo: pełne odpowiedzi i jawny model SED / analiza wrażliwości, bez uniwersalnego „dobrego” progu. |
| **P2 — jakościowe obrazy różnicowe** | `science.py:102–107,149–176`; `temporal.py:14–26,64–87` | Interpolacja i A−B bez dopasowania tła/PSF oraz kowariancji. | Stała jasność powierzchniowa przechodzi kontrolę, lecz PSF i korelacje szumu zmieniają się. Brak mapy błędu różnicy. | Utrzymać jawne „podgląd”; do pomiaru używać natywnych modeli. Samo reprojektowanie VARIANCE nie wystarczy. |
| **P2 — błąd losowy nie jest całkowitą niepewnością** | `change_diagnostics.py:48–49,73`; `source_assessment.py:111–147`; `exposure_weights.py:16–61` | `σ²Δ=σ²A+σ²B`; wagi 1/σ². | Poprawne dla niezależnych losowych błędów i tej samej mierzonej wielkości; pomijają wspólne kalibracje, model, wybór pozycji i pasmo. | Nie zamieniać ilorazu F/σ w odkrycie; jawny budżet systematyki i próba kontrolna, wagi ustalone przed oceną zmiany. |
| **P2 — ograniczenia nowych modeli widma/ruchu** | `spectral_models.py:12–26,40–71,96–126`; `trajectory.py:31–58` | Prostokątne pasma, liniowe kontinuum, ranking wielu modeli; liniowa trasa z formalnym błędem. | Planck Fν jest zaimplementowany poprawnie jako kształt, ale ranking nie jest temperaturą fizyczną. Leave-one-out nie jest nowym niezależnym odkryciem; paralaksa zakrzywia trasę. | Wyraźna etykieta ilustracyjna; przed klasyfikacją pełne odpowiedzi, kontrola źródła i odłożone ekspozycje. |
| **P2 — zabezpieczenia kalibracji i numeryki** | `irsa_resources.py:86–126,133–150`; `calibrated.py:57–59,96–98` | Unikalny produkt wydania; całkowite przesunięcie; próg cond=10¹². | W aktualnych D6 mapy i geometria zgodne. Kod nie sprawdza jednostki mapy, całej macierzy WCS-A ani CBAND przy zgodności; brak rozszerzenia daje fallback. Normalne równania pogarszają uwarunkowanie. | Wymagać oczekiwanego HDU/jednostki/detektora, macierzy A i przypisanej wersji; kowariancja z QR/SVD. Nie zgłoszono błędnej mapy w tej próbce. |

## 3. Astrometria: poprawne rachunki i brakujące efekty

### Tożsamość, układ i epoka

Nowy odczyt SIMBAD potwierdza zamrożone współrzędne i ruchy Barnarda, Epsilon Indi B, RW Aur i R Dra. Dla WISE 0855 ponownie odczytano tabelę Kirkpatrick i in. (2021): **RA=133,780984°, Dec=−7,243932°, MJD=57633,39, μα*=−8123,7 i μδ=673,2 mas/rok, π=439,0±2,4 mas**. To jest właściwa epoka tej pozycji. Współrzędne SIMBAD/VizieR przeliczone do 2000 roku są inne: około 133,818908°, −7,247048°. Ich użycie z epoką 2016,67 byłoby dużym błędem; obecny preset tego błędu nie robi. Źródło: [katalog J/ApJS/253/7](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJS/253/7), świeży wiersz zachowano lokalnie.

ICRS jest układem odniesienia. „J2000” może opisywać epokę pozycji albo równonoc układu FK5; to różne pojęcia. W ICRS nie wykonujemy precesji współrzędnych tylko dlatego, że nadszedł 2026 rok. Propagujemy pozycję od właściwej epoki astrometrycznej. SIMBAD przechowuje pozycje odniesione do epoki 2000, mimo że `coo_bibcode` może wskazywać Gaia 2016. Zgodność potwierdzono na oryginalnym wpisie Gaia Barnarda. [Dokumentacja SIMBAD](https://simbad.u-strasbg.fr/Pages/guide/ch15.htx).

`pm_ra_cosdec` prawidłowo przyjmuje μα*=dα/dt cos δ. Nie należy drugi raz mnożyć przez cos δ; przy ręcznej aktualizacji RA należałoby przez niego podzielić. Kontrola niezależna używała wektorów jednostkowych:

\[
\mathbf n=(\cos\delta\cos\alpha,\cos\delta\sin\alpha,\sin\delta),\quad
\dot{\mathbf n}=\mu_{\alpha *}\mathbf e_\alpha+\mu_\delta\mathbf e_\delta,\quad
\mathbf n(t)=\frac{\mathbf n_0+\Delta t\dot{\mathbf n}}{|\mathbf n_0+\Delta t\dot{\mathbf n}|}.
\]

Mas przeliczono na radiany, lata na 365,25 dnia. Różnica względem `targets.position` jest najwyżej **1,65×10⁻⁶″** w tej próbce. To sprawdza implementację modelu PM, nie prawdziwość pełnej pozycji obserwowanej.

### Rzeczywiste bazy czasowe

| Obiekt | Pierwsza–ostatnia przygotowana data | Baza dni | Przesunięcie PM | Piksele przy nominalnych 6,2″/px | Zmiana wektora paralaksy Ziemi między końcami |
|---|---|---:|---:|---:|---:|
| Barnard | 2025-08-20 – 2026-03-22 | 213,268 | 6,069″ | 0,979 | 1,023″ |
| Epsilon Indi B | 2025-04-24 – 2026-04-30 | 370,733 | 4,754″ | 0,767 | 0,017″ |
| WISE 0855 | 2025-05-05 – 2026-05-11 | 370,262 | 8,263″ | 1,333 | 0,015″ |
| RW Aur | 2025-09-08 – 2026-03-09 | 181,942 | 0,01075″ | 0,00173 | 0,03080″ |
| R Dra | 2025-06-08 – 2025-12-14 | 188,951 | 0,01114″ | 0,00180 | 0,00250″ |

Mała paralaktyczna różnica końców rocznej serii nie oznacza małej paralaksy pośrodku roku. WISE 0855, para **2025-11-10 / 2026-04-21**: 161,901126 dnia; PM **3,6133″**, paralaktyczna zmiana wektora **0,8563″**, PM+paralaksa **4,4610″**. Wektory trzeba dodawać kierunkowo, a nie dodawać ich długości. Dla Barnarda łączne przybliżenie daje 5,9432″, a nie 7,0921″.

Paralaksę oszacowano z wbudowanej efemerydy Ziemi Astropy:

\[
\Delta\mathbf n_\pi=-\pi\,[\mathbf R_{\oplus}/\mathrm{AU}-\mathbf n(\mathbf n\cdot\mathbf R_{\oplus}/\mathrm{AU})].
\]

To **oszacowanie pierwszego rzędu**, nie rekonstrukcja obserwatora SPHEREx. Dla gwiazd różnica między geocentrum a satelitą na niskiej orbicie wnosi do paralaksy rzędu dziesiątek mikrosekund łuku; dla bliskiego obiektu Układu Słonecznego może być bardzo istotna. Aberracji nie należy bezmyślnie dodawać do już skalibrowanego WCS ICRS. Potrzebna jest spójna definicja astrometrii produktu i efemerydy.

### Perspektywa: istotne rozróżnienie epok

Pełny model prostoliniowego ruchu przestrzennego:

\[
\mathbf r(t)=d\mathbf n_0+\Delta t[d\dot{\mathbf n}+v_r\mathbf n_0],\quad
\mathbf n(t)=\mathbf r(t)/|\mathbf r(t)|.
\]

Test od J2000 z zamrożonym μ i RV Barnarda −110,11 km/s daje około **0,441″ wrażliwości na RV po 26 latach**. **Nie jest to oszacowanie rzeczywistego błędu aplikacji.** SIMBAD przeniósł pozycję Gaia do J2000, podczas gdy μ odnosi się do oryginalnego rozwiązania Gaia. Dlatego sprawdziłem oryginalny Gaia DR3 **4472832130942575872**, epoka 2016,0: RA 269,44850252544°, Dec 4,73942005111°, RV −110,47 km/s. Spójna propagacja od tej epoki różni się od aplikacji o **0,0598–0,0673″** w datach Barnarda. To właściwsza skala pominiętego efektu w tej konfiguracji, dużo mniejsza niż paralaksa. [Gaia DR3, dokumentacja parametrów](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html).

W `results.json` pole `perspective_offset_last_arcsec` opisuje pierwszą, warunkową kontrolę wrażliwości. Do interpretacji Barnarda używać **`recent_extensions.json → barnard_original_gaia2016`**, nie 0,441″. RV dla Epsilon Indi B i WISE nie ustalono z uzyskanej odpowiedzi. Scenariusz ±100 km/s daje jedynie skalę wrażliwości, nie pomiar ani ograniczenie statystyczne.

Epsilon Indi B jest ciasnym układem Ba/Bb; jego fotocentrum zależy od jasności składników i pasma, a ruch orbitalny nie jest wspólnym PM układu. Rozdzielenie około 0,7″ w literaturze nie jest rozdzielone przez SPHEREx; nie oznacza też stałej separacji w 2026. [McCaughrean i in., obserwacje układu](https://arxiv.org/abs/astro-ph/0309256), [Chen i in., rozwiązanie dynamiczne](https://arxiv.org/abs/2205.08077). RW Aur również wymaga ostrożności wobec złożoności źródła i zmienności; nie zakładałem izolowanej gwiazdy o stałym widmie.

### Czy można mierzyć ruch mniejszy niż piksel?

Tak, warunkowo. Dwa lokalne modele ePSF D6 mają FWHM w osiach **1,258–1,288 piksela**, czyli około **7,8–8,0″** przy nominalnej skali. Przy idealnym izolowanym źródle Gaussowskim `σ_centroid≈FWHM/(2,355 SNR)`: dla SNR=6 i 7,9″ daje około 0,56″ na oś. To przykład granicy losowej, nie obietnica instrumentu; niedopróbkowanie, tło i rejestracja ją pogarszają.

Nowy `native_diagnostics.py` rzeczywiście dopasowuje pozycję, ale **nie zmienia** pozycji starej fotometrii. Na WISE XI/IV otrzymał SNR około 6,06/5,85, błędy losowe osi 0,826/0,760″ i przesunięcie centroidów 5,496″. Po dodaniu skonfigurowanej podłogi 2″ błąd różnicy na oś wynosi około **3,043″**. Podłoga jest ustawieniem eksploracyjnym, nie zmierzoną kalibracją astrometrii. To nie jest potwierdzenie ruchu ani pełna analiza jego istotności.

Liniowa trasa pomiędzy dwiema kotwicami jest właściwą **wizualizacją hipotezy**. Dla samego modelu PM w tych małych polach odchylenie projekcji TAN od interpolacji liniowej jest <5×10⁻⁹ piksela — geometrycznie pomijalne. Większy problem to nieobecna paralaksa, orbita lub przyspieszenie oraz błędy kliknięć. Dla asteroid i ekstrapolacji liniowa trasa nie jest orbitą. Nowy `trajectory.linear_motion` poprawnie odtwarza kontrolowany ruch 0,8″/dzień na wschód i −0,3″/dzień na północ, także przy RA blisko 0; to test rachunku, nie walidacja prognoz rzeczywistego obiektu.

## 4. Geometria, reprojekcja i zgodność punktów

WCS obrazu wyjściowego ma RA malejące w prawo, Dec rosnące w górę. FITS jest indeksowany jako `[y,x]`, `pixel_to_world(x,y)` używa środka pierwszego piksela w (0,0), a PNG odwraca wiersze. `CRPIX=(N+1)/2` w konwencji FITS umieszcza środek w `(N−1)/2` w Pythonie. Te elementy są zgodne. Maksymalny błąd round-trip natywnych WCS to **6,999×10⁻⁷ piksela**. To kontrola wzajemnej zgodności transformacji, a nie zewnętrznej poprawności absolutnej astrometrii.

Transformacja wycinka do detektora `x_parent=1+x_cut−CRPIX1A` jest zgodna z instrukcją IRSA. Sprawdzone pliki mają liniowe osie alternatywne A, CRVAL=0, CDELT=1 i całkowite przesunięcia. Dla obecnych plików nie ma dowodu na błąd o jeden piksel. Kod nie sprawdza jednak pełnej macierzy A, mimo komentarza o odrzucaniu obrotów; nie powinien automatycznie obsługiwać innej geometrii bez dodatkowych kontroli.

Problem odczytu/ciągłego kliknięcia ma zakres najwyżej około pół piksela na każdej osi wewnątrz komórki, a nie zawsze jeden piksel. Dla pola 6′/59 pikseli górna granica to około **4,315″**. Środek piksela jest poprawnym wynikiem narzędzia „odczytaj piksel”, lecz nie tą samą pozycją co ciągły marker i apertura. Podpisy powinny to rozróżniać. Lokalna mapa λ i flagi są obecnie również pobierane z najbliższego piksela siatki wyjściowej; fotometria wyznacza je w ciągłym punkcie natywnego WCS.

Reprojekcja biliniowa działa na **jasności powierzchniowej**, co odpowiada jednostce IMAGE. Nie gwarantuje zachowania zintegrowanego strumienia przy dowolnej zmianie skali, obrocie i niedopróbkowanym źródle. [Dokumentacja Reproject 0.21](https://docs.astropy.org/projects/reproject/en/stable/celestial.html). W wykonanej kontroli przesunięcia o pół piksela:

- Stała jasność powierzchniowa 7 przechodzi bez błędu.
- Suma szerokiego, dobrze mieszczącego się modelu Gaussa zmienia się o około 4×10⁻¹² względnie. To szczególny przypadek tej samej skali i siatki, nie dowód ogólnego zachowania strumienia.
- Drugi moment radialny rośnie **2,1667→2,6667 px²**: obraz ulega wygładzeniu.
- Dla białego szumu o wariancji 1 i przesunięcia (½,½) wariancja pojedynczego wyjściowego piksela wynosi ¼, korelacja z sąsiadem ½. Suma 4×4 pikseli ma wariancję **12,25**, podczas gdy suma samych wariancji diagonalnych daje **4**. Błąd byłby zaniżony **1,75 raza**.

To kontrola syntetyczna dokładnej macierzy wag, nie pomiar korelacji SPHEREx. W ogólności `y=A x`, `C_y=A C_x Aᵀ`. Dlatego reprojekcja obrazu wariancji tym samym interpolatorem nie jest propagacją wariancji: potrzebne są kwadraty wag i kowariancje.

Braki danych pozostają NaN/przezroczyste, bez zastępowania strumieniem zero. Wspólne pokrycie jest wymagane dla wszystkich składników. Flagi nearest-neighbour zachowują słowa bitowe, lecz **nie są sumą flag czterech pikseli uczestniczących w biliniowej interpolacji**. Przy braku danych słowo flag jest zerowane, więc trzeba zawsze czytać również maskę valid. Podgląd ma łagodniejszą politykę flag niż fotometria; to nie jest mapa wszystkich wkładów do pomiaru.

## 5. Co mierzy fotometria i skąd bierze się jej błąd

### Jednostki i pole powierzchni

IMAGE to gęstość strumienia na kąt bryłowy. Przeliczenie:

\[
F_\nu[\mathrm{mJy}]=10^9\sum_i I_{\nu,i}[\mathrm{MJy/sr}]\,\Omega_i[\mathrm{sr}],\qquad
\Omega_i= A_i[\mathrm{arcsec}^2]\left(\frac\pi{180\cdot3600}\right)^2.
\]

Jeden piksel o powierzchni 6,2²=38,44 arcsec² i jasności 1 MJy/sr wnosi **0,90351 mJy**. `mJy` opisuje gęstość strumienia Fν, nie całkę energii po całym podczerwonym widmie. Zmierzona wartość jest zależna od pasma i konwencji kalibracji.

Zwykły pomiar używa Ω z liniowej macierzy WCS. Ta funkcja nie daje mapy lokalnego pola na sferze. [Astropy — znaczenie `proj_plane_pixel_area`](https://docs.astropy.org/en/stable/api/astropy.wcs.utils.proj_plane_pixel_area.html). Sprawdziłem osobno lokalny jakobian wektora jednostkowego na niebie:

\[
\Omega(x,y)=|\partial_x\mathbf n\times\partial_y\mathbf n|.
\]

Różniczkowanie centralne z krokiem 0,01 px zgadza się z mapami Ω D6 na poziomie około **0,003–0,041%**, nie identycznie. To mocniejszy test jednostek/geometrii niż użycie drugiego razu `proj_plane_pixel_area`. Mapy mają rzeczywistą jednostkę `arcsec2`. Dla stałej pozycji WISE:

| Data | Stała powierzchnia: F apertury mJy | Mapa Ωᵢ: F apertury mJy | Zmiana |
|---|---:|---:|---:|
| 2025-05-05 | 0,287740 | 0,286026 | −0,60% |
| 2025-11-10 | 0,523932 | 0,528643 | +0,90% |
| 2026-04-21 | 0,717064 | 0,724862 | +1,09% |
| 2026-05-11 | 0,572233 | 0,567444 | −0,84% |

Obecnie to mniejszy efekt niż błąd losowy, lecz może tworzyć zależny od położenia systematyk w lepszych danych. Nie należy opisywać go jako katastrofalnego błędu jednostek.

### Apertura, tło i wariancja

Źródło: środki pikseli w promieniu r. Tło: środki pikseli między 1,8r i 3r, bez odrzuconych flag i SOURCE. Dla r=12,4″ typowo 11–14 pikseli źródła i kilkadziesiąt tła. Są to **całe piksele wybrane po położeniu środka**, a nie dokładna całka koła ani metoda z wagami ułamkowymi. Przesunięcie środka może skokowo zmienić zestaw pikseli.

Dla tła będącego nieważoną średnią `b̂=Σ_B Iⱼ/N_B`, współczynników kᵢ=10⁹Ωᵢ oraz K=Σ_A kᵢ:

\[
\hat F=\sum_A k_iI_i-K\hat b,\qquad
\mathrm{Var}(\hat F)=\sum_A k_i^2 V_i+
\frac{K^2}{N_B^2}\sum_B V_j.
\]

Przy stałym k daje to dokładnie wzór w `measurements.aperture`. W `calibrated_report` wariant zmiennej powierzchni też jest poprawny. Sprawdzenie niezależne zbudowało pełny wektor kontrastu `wᵢ=kᵢ` w źródle, `wⱼ=−K/N_B` w tle: `F=wᵀI`, `Var F=wᵀ diag(V)w`. Zgodność z zachowanymi ważnymi wynikami jest na poziomie zaokrągleń. To potwierdza rachunek, nie poprawność modelu tła lub VARIANCE.

Warunki: rozłączne obszary, niezależne piksele, poprawne V, stałe wybrane maski i tło odpowiednie dla wnętrza apertury. W ogólności należy użyć **wᵀCw**, uwzględniając m.in. kowariancję źródło–tło. Wycinanie SOURCE może stworzyć niesymetryczny pierścień; wtedy gradient nie znosi się. Wagi 1/V byłyby wydajniejsze dla stałego tła o różnym szumie, ale wymagają innego wzoru i mogą mocniej reagować na błędne wariancje.

Kontrole **syntetyczne**, niezależny Gauss całkowany po granicach pikseli:

- Źródło o całkowitym F=100: kontrast apertury wynosi **84,2762**, nie 100, z powodu straty poza aperturą i małego wkładu skrzydeł do tła.
- Dodanie stałego tła +20 nie zmienia wyniku.
- Symetryczny gradient nie zmienia wyniku, ale jednostronnie zamaskowany pierścień zmienia go do **80,5686**.
- Sąsiad o F=100 w odległości 4 px zmienia wynik do **75,4922** przez zanieczyszczenie tła.
- Przewidywana wariancja 15,2237; 3000 realizacji niezależnego szumu dało **15,1562**, zgodnie z oczekiwaną fluktuacją Monte Carlo.

Kontrole **rzeczywistych** ośmiu zadanych punktów w listopadzie/kwietniu: trzy odrzucone przez OUTLIER w aperturze, pięć ważnych. Zmiana średniej tła na ważoną płaszczyznę zmienia F o **0,021–0,136 mJy**. Na kwietniowej pozycji (0,3;0,3) otrzymano **−1,930±0,386 mJy**; to ujemny lokalny kontrast obrazu, nie „ujemna gwiazda” ani dowód statystycznego odkrycia. Płaszczyzna daje −1,909 mJy, więc sam gradient tego nie wyjaśnia. Nie ustalono, czy przyczyną jest struktura obrazu, kalibracja czy inny efekt. Tych punktów nie uznano za certyfikowane puste pola ani stabilne gwiazdy.

SOURCE jest informacją o znanym źródle, nie uniwersalnym defektem. Dopuszczenie go w aperturze celu jest sensowne. Wykluczanie go z tła jest konserwatywne, ale może uniemożliwić pomiar. Flagi artefaktów i ich definicje należy wersjonować; polityka nie obejmuje automatycznie każdej nowej nazwy (np. osobnych GHOST_FPA/GHOST_EXT). W ważnych aperturach WISE nie stwierdzono takich flag, więc nie przypisuję im wykazanego skażenia tych czterech pomiarów.

Nazwa **„strumień apertury po odjęciu lokalnego średniego tła”** jest właściwa. „Całkowita jasność WISE 0855” nie jest uzasadniona. Korekcja apertury wymaga encircled energy dla pozycji, fazy, pasma i przyjętego tła, a nie jednego uniwersalnego mnożnika.

## 6. ePSF i kalibracje

W sprawdzonych obrazach D6: **DR1, pipeline 7.0.5**, EPSF 441 stref, 33×33, oversampling **5×5**, `DETCOORD=sky`. Tabela ePSF już uwzględnia konwencję kierunku osi MWIR. Wybrano najbliższy środek strefy w macierzystym detektorze zgodnie z instrukcją IRSA; nie wykazano pomylenia stref ani niepotrzebnego odwrócenia modelu.

ePSF jest modelem **już splecionym z odpowiedzią piksela**, próbkowanym podpikselowo. Nie należy traktować go jak optycznego PSF i całkować ponownie po pikselu. Notebook IRSA używa `ImagePSF.evaluate` w środkach pikseli oraz normalizacji uzyskanego stempla. [Oficjalna instrukcja ePSF](https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/).

Kod SciPy używa interpolacji sześciennej, zerowania poza skończonym modelem i stałej normalizacji sumą siatki oversamplowanej. W 25 fazach modelu listopadowego suma próbkowanego profilu wynosi **0,978585–1,019411**. Maksymalna różnica pojedynczego piksela wobec znormalizowanego `Photutils.ImagePSF` to 0,00763 udziału jednostkowego strumienia. To wykazana zależność modelu od interpolatora i normalizacji; nie dowód błędu absolutnego strumienia o dokładnie tę wartość. Trzeba również ustalić, czy „jednostkowy strumień” oznacza skończony stempel czy fizyczny strumień zewnętrznych skrzydeł.

Udział modelu w aperturze r≈2 px w tych fazach: **0,9311–0,9788**. W czterech rzeczywistych konfiguracjach stałego punktu: około **0,955–0,964**. To tylko diagnostyka modelu, nie gotowa empiryczna korekcja apertury źródła.

### Model i estymacja

Przy danych przeliczonych do mJy:

\[
y_i=k_iI_i=F p_i+k_i(b_0+b_x\Delta x_i+b_y\Delta y_i)+\epsilon_i,
\quad \sigma_i=k_i\sqrt{V_i}.
\]

Macierz `[pᵢ,kᵢ,kᵢΔxᵢ,kᵢΔyᵢ]` jest poprawna dla punktowego izolowanego źródła i liniowego tła w jasności powierzchniowej. `lstsq` daje rozwiązanie ważone. Kowariancja `(XᵀWX)⁻¹` i ν=N_good−4 są poprawne warunkowo, gdy pozycja/model/kalibracja są znane, błędy niezależne i ich wariancje poprawne. Przy znanych wariancjach nie ma obowiązku automatycznego mnożenia tej kowariancji przez χ²ν; przy złym modelu samo takie mnożenie też nie naprawia wyniku.

W czterech rzeczywistych ważnych dopasowaniach cond ważonej macierzy to **38,9–48,0**. Niezależne wyznaczenie kowariancji z QR daje te same σF do precyzji maszynowej. Nie ma tu wykazanego problemu uwarunkowania. Ochrona do cond=10¹² jest natomiast zbyt luźna jako reguła ogólna: odwracanie macierzy normalnej kwadratuje uwarunkowanie.

Parametry stałego punktu WISE:

| Data | Apertura z mapą Ω, mJy | ePSF, mJy | χ²ν ePSF | N fit |
|---|---:|---:|---:|---:|
| 2025-05-05 | 0,2860±0,2296 | 0,3655±0,1505 | 1,049 | 63 |
| 2025-11-10 | 0,5286±0,1815 | 0,8090±0,1284 | 1,306 | 62 |
| 2026-04-21 | 0,7249±0,1646 | 0,3778±0,1043 | 1,218 | 66 |
| 2026-05-11 | 0,5674±0,2516 | 0,3667±0,1461 | 1,278 | 64 |

**Ta sama para listopad−kwiecień:** apertura −0,1962±0,2450 mJy, ePSF +0,4313±0,1654 mJy. Różne estymatory dają nawet przeciwny znak zmiany. Nie wolno traktować tych błędów jako niezależnych ani wybrać bardziej „interesującego” wyniku. Różnice estymatorów pokazują wpływ pozycji, kształtu, tła i otoczenia, których formalne σ nie obejmuje.

Dlaczego dobre χ² nie dowodzi poprawnej jasności: słabe źródło może być źle wycentrowane, model tła może pochłaniać część sygnału, sąsiad może imitować profil, a tło w licznych pikselach może dominować statystykę. W kontroli syntetycznej Gaussa σ=1 px, F=10 i szumie jednostkowym przesunięcie źródła o 1 px daje dopasowanie w starej pozycji **F=7,8399**, a oczekiwane χ²ν nadal tylko **1,0094**. Dobra wartość nie identyfikuje obiektu i nie waliduje rozkładu VARIANCE.

Nowe centroidowanie używa 17×17 pikseli, interpolacji liniowej ePSF, amplitudy w jednostce jasności powierzchniowej i osobnego tła. Nie jest tym samym modelem ani zakresem co sześcienny fit fotometrii w promieniu 4,5 px. Jego χ² nie może bezpośrednio „zatwierdzić” starego strumienia. Momenty elongacji liczone z dodatniej części obrazu po odjęciu mediany są podatne na sąsiadów i dodatni szum; nie są odszumioną miarą samego PSF.

### Wersje i pochodzenie

Sprawdzone mapy D6:

- CWAVE/CBAND **cal-swcs-v5-2026-191**, SHA-256 `19195d253892883586aa2183cb66238b32f6032ade62d490b36b85b0dd18f212`.
- Powierzchnia **cal-sapm-v3-2026-191**, SHA-256 `0986595851aab50dcc984b2d2f1c66a57d7726c5996368ed449bf89cf44346f7`.
- W przykładach ePSF wybrane strefy 108, 429, 438 i 24, z odpowiednio 388, 511, 492 i 387 gwiazdami budującymi model. Liczba gwiazd nie jest liczbą niezależnych walidacji naszego celu.

Przypisanie map przez unikalny produkt w katalogu DR1, ich metadane, jednostki, zgodność przestrzenna i λ wspierają poprawność **tych** wyborów. Zapis hashy nie poświadcza sam w sobie zgodności całego łańcucha przetwarzania. Tolerancja zgodności `max(0,003 µm;0,15 Δλ)` jest technicznym bezpiecznikiem, nie walidacją fotometrii. Brakuje pełnej kontroli CBAND i funkcji odpowiedzi oraz jawnego sprawdzenia jednostek mapy przy każdym odczycie. Oficjalne produkty opisuje [IRSA — Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/).

### Co rzeczywiście sprawdza wcześniejsze porównanie Photutils

`scripts/independent_photometry_check.py` korzysta z produkcyjnego `measure`, przejmuje jego pozycję oraz używa **tej samej stałej powierzchni `proj_plane_pixel_area`** i tej samej polityki tła. Niezależny jest częściowo sposób geometrycznego sumowania apertury. Nie są niezależnie sprawdzone: absolutne jednostki i powierzchnia, identyfikacja, epoka, paralaksa, normalizacja ePSF, odpowiedź pasma, izolacja ani prawdziwa niepewność źródła.

„30 porównań” to pomiary kilku pozycji na pięciu obrazach, nie 30 niezależnych źródeł ani odłożona próba skuteczności. Odchylenia dwóch mocno skorelowanych estymatorów porównane do σ pojedynczego wyniku nie stanowią testu ich różnicy. To przydatna kontrola regresji sumowania, zbyt wąska do walidacji fizycznej. Nowy audyt dodał niezależny jakobian, macierz kontrastu i kontrole modelu właśnie dlatego.

## 7. Pasmo, czas i interpretacja widma

W filtrze LVF położenie na detektorze zmienia λ. Numer D1–D6 jest szerokim zakresem, nie identyfikatorem tej samej wąskiej odpowiedzi. WCS-WAVE służy przeglądowi; w naukowej analizie należy używać CWAVE/CBAND. W rzeczywistym punkcie WISE:

| Data | λ z kalibracji, µm | CBAND, µm | WCS-WAVE w centrum, µm |
|---|---:|---:|---:|
| 2025-11-10 | 4,417174 | 0,034852 | 4,417819 |
| 2026-04-21 | 4,423067 | 0,033908 | 4,423782 |

Różnice λ wobec przybliżenia są poniżej 1 nm w tej parze. Szerokości także trzeba sprawdzać; ich zbieżność nie daje jeszcze identycznych skrzydeł transmisji. [IRSA — opis WCS-WAVE i kalibracji](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/).

Ogólny model pomiaru w danym paśmie:

\[
M_i[S]=\frac{\int K_i(\lambda)\,F_\nu(\lambda)\,d\lambda}{N_i}.
\]

Kᵢ obejmuje rzeczywistą odpowiedź, właściwą wagę detektora i konwencję kalibracji, a Nᵢ jej ustaloną normalizację dla widma odniesienia. Nie należy dowolnie wstawiać wagi fotonowej λ do już skalibrowanego Fν bez sprawdzenia definicji produktu. CWAVE i CBAND nie wystarczają do odtworzenia Kᵢ.

Dla ilustracyjnego gładkiego `Fν∝λᵖ` i przybliżenia wąskiego pasma `M₂/M₁≈(λ₂/λ₁)ᵖ`. Dla rzeczywistych centrów tej pary daje to **−0,266% dla p=−2, +1,342% dla p=10, +2,702% dla p=20**. To oszacowania zależne od założonego SED, nie zmierzona poprawka koloru WISE 0855. Na progu dopuszczającym przesunięcie pół szerokości różnica może być większa. Wąskie zagłębienie przy krawędzi pasma unieważnia przybliżenie samym nachyleniem.

Kontrola syntetyczna dwóch odpowiedzi o tym samym centrum i FWHM, lecz innych skrzydłach, daje średnią widma **0,92545 vs 0,92176**. Nie użyto wymyślonej transmisji jako rzeczywistych danych SPHEREx; przykład pokazuje, dlaczego dwa momenty odpowiedzi nie określają całki.

Lepsza ocena ilościowa wymaga K₁,K₂ w pozycji celu, kalibracji oraz rodziny dopuszczalnych widm S. Wtedy liczymy np. `B=max_S |M₁[S]/M₂[S]−1|`, a porównanie dopuszczamy do konkretnego celu naukowego, gdy B mieści się w **zadeklarowanym budżecie błędu**. Dla znanej granicy nachylenia L można w ograniczonym gładkim zakresie użyć `|Δ ln Fν|≤L |Δ ln λ|`; różne kształty odpowiedzi wymagają osobnego członu. L i tolerancja nie są prawami instrumentu. Pozyskanie/zweryfikowanie odpowiedzi i wiarygodnego SED nie jest pewnym zadaniem na pozostały dzień. Minimalnie należy pokazać analizę wrażliwości dla kilku jawnych SED i status „porównanie przeglądowe”.

Zestaw punktów z różnych dat jest **wieloterminową spektrofotometrią**, nie automatycznie jednoczesnym widmem. Okno 24/48 h nie dowodzi stałości źródła. Nie wolno łączyć rocznej serii WISE w widmo do klasyfikacji bez modelu zmienności. Przykład dziesięciu klatek z sześciu detektorów obejmujący około 0,27 dnia jest zestawem obserwacji starego pola, nie identyfikacją widma Barnarda ani pełnymi 102 kanałami jednego źródła.

Nowy `spectral_models.py` ma poprawny kształt **Bν**, nie myli go z Bλ; amplituda jest umowna i dopasowywana. Prostokąty z CWAVE/CBAND, zaledwie kilka punktów i ranking 13 temperatur oraz siedmiu nachyleń nie dają fizycznej temperatury. χ²/(N−1) jest warunkowym wynikiem dla ustalonego kształtu; najlepszy wynik po przejrzeniu wielu kształtów nie ma tego samego rozkładu co jeden ustalony test. Okna H₂O/CO₂/CO i lokalny kontrast >3σ są tylko **kandydatem zagłębienia w założonym kontinuum**. Bez pełnych odpowiedzi, niezależnego kontinuum, kontroli pyłu/temperatury/kalibracji i potwierdzenia nie identyfikują molekuł. Obecna próbka WISE ma za mało prawidłowych pomiarów w bliskich terminach do takiej interpretacji.

## 8. Czas, składanie, różnice i skala obrazu

`archive.py:54–60` używa środka `t_min/t_max`; nie myli go z początkiem ekspozycji. W sprawdzonych WISE FITS `MJD-OBS/MJD-END` odpowiadają początkom/końcom. Ekspozycje trwają około **115,12 s**; MJD z manifestów ma drobniejsze różnice zaokrąglenia poniżej części sekundy. UTC jest wystarczające dla tego przeglądu. Precyzyjna astrometria/czas barycentryczny wymagają właściwej skali czasu i pozycji obserwatora.

`temporal.combine` oblicza **średnią ważoną**, nie sumę: `Ī=ΣwᵢIᵢ/Σwᵢ`. Zachowuje MJy/sr i stałe wagi; wszystkie wybrane składniki muszą mieć pokrycie i przejść parowe kryterium λ. Nie wypełnia braków ani nie zmienia składu średniej zależnie od piksela. To zaleta odtwarzalności, kosztem mniejszego pokrycia.

Dla niezależnych ekspozycji `Var Ī=Σwᵢ²Vᵢ/(Σwᵢ)²`; ogólnie dochodzi `2Σ_{i<j}wᵢwⱼ Cov(Iᵢ,Iⱼ)/(Σw)²`. Tego produktu niepewności aplikacja nie wyznacza. Nowa średnia pomiarów ePSF w `source_assessment.weighted_flux` poprawnie realizuje wagi 1/σ² oraz `σ_mean=(Σ1/σ²)⁻½`, jeżeli porównuje ten sam stały strumień i niezależne błędy losowe. Sprawdzenie różnych hashy nie dowodzi niezależności kalibracji; filtr λ pozostaje heurystyczny.

Nowy `exposure_weights.weight_plan` wybiera lokalne pomiary po jakości i błędach, nie po największym dodatnim F. To lepsze niż maksymalizacja SNR wyniku, ale selekcja po resztach/kształcie również może zależeć od szumu celu. Nie dowodzi optymalności ani poprawy wykrywalności. Trzeba zamrozić procedurę i zbadać odzysk na odłożonych danych.

Ruch rozmywa średnią, gdy jego droga w oknie jest istotna wobec PSF; przy stałej prędkości dodatkowa wariancja w kierunku ruchu to `(μT)²/12`. W 48 h Barnard przebywa około **0,057″**, WISE około **0,045″** — tu pomijalnie wobec PSF, o ile chodzi o sam PM. Dla bliskiej asteroidy limit 48 h może być wielokrotnie za duży; powinien wynikać z efemerydy, nie jednej liczby godzin dla wszystkich obiektów. W ekspozycji 115 s rozmycie tych gwiazd przez PM jest poniżej 0,00004″.

Różnica to dokładnie **A−B** w MJy/sr. Dodatnia plama oznacza większą jasność powierzchniową w A; dipol może oznaczać ruch, ale również rejestrację lub zmianę PSF. Różnica tła tworzy rozległy offset; zmiana pasma daje reszty koloru. Bez wspólnego modelu PSF/tła i szumu jest to **podgląd jakościowy**, co obecny kod i nagłówki FITS poprawnie deklarują.

Wspólny stretch 1–99,7 percentyla oraz asinh ogranicza fałszywe różnice z niezależnego automatycznego kontrastu. Nadal obcina jasne wartości, nieliniowo wzmacnia słaby kontrast i może ukryć nasycenie. Zmiana zakresu „faint/full”, masek lub obcięcia zmienia wygląd bez zmiany fizyki. Symetryczna skala różnicy zachowuje znak, ale jest ustalana osobno dla produktu; koloru pomiędzy różnymi produktami nie należy porównywać jako identycznej liczby mJy. Pomiary korzystają z natywnego FITS, więc sam stretch nie zmienia F.

## 9. Statystyka i granice wnioskowania

Wynik `F/σ_random` jest warunkowym stosunkiem do modelu szumu, nie prawdopodobieństwem prawdziwego źródła. Dla różnicy:

\[
\mathrm{Var}(F_A-F_B)=\sigma_A^2+\sigma_B^2-2\mathrm{Cov}(F_A,F_B).
\]

`hypot` jest poprawne przy zerowej kowariancji losowej. Kalibracja, wspólne modele, układ pozycji i odpowiedź pasma wnoszą inne błędy. Systematyk nie należy po prostu dodawać jako dwóch niezależnych liczb, jeśli są wspólne. Porównanie z Tractor na tych samych obrazach również ma skorelowane błędy. [IRSA — model spektrofotometrii i stałe pozycje wejściowe](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html).

Detekcja źródła, przypisanie tożsamości, detekcja zmienności, pomiar ruchu i odkrycie nowego obiektu są różnymi zadaniami. Jedna dodatnia amplituda przy wymuszonej pozycji nie wykonuje wszystkich pięciu. SEP z progiem 5 i minarea=3 daje kandydatów pojedynczej klatki, z lokalnym tłem i mapą wariancji. Nie jest to globalne 5σ po całym przeszukaniu i nie jest nieobecnością źródła, jeżeli kandydat nie przeszedł ekstrakcji.

Przy przeglądaniu wielu pikseli, par dat, filtrów, promieni i tras wybieramy maksimum z wielu prób. Ilustracyjnie: dla 10 000 **niezależnych, wcześniej określonych** jednostronnych testów Gaussowskich próg 3σ daje średnio około 13,5 przekroczenia pod hipotezą zerową. Nasze piksele i trasy są zależne, więc nie wolno podstawiać tej liczby jako rzeczywistej liczby prób aplikacji; potrzebna jest kalibracja całej procedury.

`workflow.comparisonSeries` maksymalizuje liczbę wzajemnie zbliżonych pasm, potem bazę czasu, a nie amplitudę. Nie ma tu wykazanego bezpośredniego dobierania największej fluktuacji F. Człowiek może jednak po obejrzeniu danych wybrać „najciekawszą” pozycję i promień. Wynik pozostaje wtedy eksploracyjny.

`evidence.py:39–42` nazywa epokę niezależną, gdy jej MJD różni się od MJD dwóch kotwic. To tylko **inna data**, nie dowód, że danych nie oglądano przy wyborze hipotezy. W `trajectory.py` leave-one-out jest kontrolą stabilności małej próby, a nie ślepym potwierdzeniem w nowym zbiorze. Potwierdzające ekspozycje trzeba wybrać lub odłożyć przed dostrajaniem i zachować zapis procedury.

Nowy klasyfikator ma sensowne elementy techniczne: rozdział train/validation/test według grup, standaryzację tylko na train, próg bez użycia etykiet testowych, regularizację, porównanie z regułą heurystyczną i brak deklaracji prawdopodobieństwa odkrycia. Brak mu jednak naukowo uzasadnionej skuteczności. Przy 5/5 poprawnie zachowanych źródłach punktowy wynik 100% ma jednostronną dolną granicę 95% `0,05^(1/5)=0,5493`. Aby przy zerze błędów uzyskać taką granicę ≥0,95, potrzeba **59 niezależnych przypadków**; zależność wewnątrz grup pogarsza sytuację. To rachunek dwumianowy, nie zalecenie magicznej liczby 59 dla całego projektu. Dodatkowy warunek porównania z regułą nie zastępuje przedziałów niepewności ani niezależności zbioru.

Kontrola syntetycznych metadanych wykazała, że dwie analizy w odległości 180″, mające różne SHA wycinków, ale ten sam oryginalny `obs_id`, mogą pozostać osobnymi grupami. Pole wycinka ma 6′, więc możliwe jest nakładanie pikseli i wspólne artefakty. Nazwa `independent_groups` jest deklaracją procedury, nie dowodem niezależności. `artifact_active` w odczytanej bazie jest puste; **nie trenowano ani nie aktywowano modelu w audycie**. Nie wolno prezentować go jako sprawdzonego detektora artefaktów.

## 10. Pięć obiektów: co pokazują rzeczywiste pliki

![Rzeczywiste natywne obrazy; znaczniki są prognozami katalogowymi, nie identyfikacją](C:/Users/ksawi/Desktop/Repozytoria/Hackaton/data/audit/math_physics_20261114/native_fields.png)

Panele mają osobne skale prezentacji, służą kontroli pola/pozycji, nie porównaniu jasności między obiektami. Jasny odpowiednik blisko prognozy wzmacnia hipotezę identyfikacji, ale sam nie jest niezależnym dopasowaniem katalogowym i astrometrycznym.

| Cel / analiza | Właściwe pole i kandydat | Ważność apertur produkcyjnych przy osobnej prognozie daty | Porównywalne epoki | Uzasadniony wniosek |
|---|---|---|---|---|
| **Barnard** `65f24c5b4a7245459d81b4f7ae95bcf1` | Centrum poprawionego pola blisko pozycji 2026; jasny obiekt przy prognozie w trzech klatkach. Pierwszy wycinek ma tylko 16 kolumn i nie zawiera celu. | **0/4**. Pozostałe apertury 11/14/14 px w całości mają BLOOM i liczne OVERFLOW/SUR_ERROR; pierścienie 73/74/71 px w całości SOURCE. | Różne daty są; brak ważnej pary tych pomiarów. | Pokaż rzeczywiste ograniczenie nasyceniem i maską. Dopasowane do skrzydeł centroidy mają χ²ν≈416–478 i przesunięcia 11–16″, więc są nieakceptowalne jako astrometria. Nie mierzyć ruchu z tych wyników. |
| **Epsilon Indi B** `5bbf47dc2673437a86c2026abac19f03` | Poprawne pole B, a nie dawny preset A. Wyraźny bliski odpowiednik; dopasowania centroidów zwykle <1,6″ od prognozy, co wspiera identyfikację pozycyjną układu. | **0/6**. Pięć czystych apertur celu, ale całe pierścienie SOURCE: 76/75/72/74/73 px. Szósta klatka wycięta do 5 wierszy, poza celem. | Bez ważnej fotometrii nie ma zatwierdzonej pary. Różne λ trzeba sprawdzać osobno. | To najbardziej obiecujący jasny kandydat do astrometrycznej demonstracji po kalibracji pola. Nowe centroidy mają χ²ν 1,62–4,63; trzy przechodzą próg 3. Przesunięcie pierwszej–ostatniej dopasowanej pozycji 4,874″ przy zadanej skali błędu różnicy osi 2,829″ nie jest jeszcze potwierdzeniem ruchu. |
| **WISE 0855** `4812094a2ce843a8b787837eb13ec845` | Pole prawidłowe, pozycja odniesienia z właściwej epoki. Słaby kandydat w pobliżu prognozy; brak potwierdzonego niezależnego przypisania całej emisji do WISE. | **4/5**. W grudniu jeden NONFUNC w aperturze unieważnia pomiar. Pozostałe SOURCE w rdzeniu są dozwolone; tło po maskach 44–52 px przy osobnych prognozach. | Para XI/IV przechodzi heurystykę λ, **nie pełną równoważność odpowiedzi**. Pozostałe daty mają inne pasma. | Można pokazać natywne kontrasty apertury, modelową zależność od pozycji i nierozstrzygniętą hipotezę. Brak podstaw do zmienności, temperatury, molekuł lub odkrycia. |
| **RW Aur** `3d4aab1ac66041ba87f774ae76c3f609` | Właściwe pole, jasny kandydat przy prognozie; model jednego izolowanego źródła wymaga ostrożności. | **0/4**. W każdej aperturze OVERFLOW, w części BLOOM/SUR_ERROR; cały pierścień SOURCE. | Brak ważnej pary pomiarów w tej próbce. | Dobre pole demonstracji flag i złożoności źródła. Centroidy χ²ν≈22–27, mimo bardzo dużych formalnych SNR: nie wolno interpretować SNR jako jakości modelu ani stwierdzać zmienności. |
| **R Dra** `d38309c3d7384c27ae9888c5f491169f` | Poprawione pole przy właściwym identyfikatorze; jasny obraz przy prognozie. | **0/3**. Całe apertury 14/13/11 px OVERFLOW i BLOOM; tło całe SOURCE. | Brak ważnej pary. | Pokrycie i ograniczenia instrumentu są wynikiem. Centroidowanie odmawia przez zbyt małe ważne pokrycie. Nie stwierdzać braku źródła ani amplitudy zmienności. |

Próba Epsilon Indi B bez bramki pierścienia została wykonana **wyłącznie diagnostycznie**: pięć dopasowań ePSF przy prognozach daje formalnie bardzo dokładne amplitudy 13–37 mJy, lecz χ²ν **17,27–88,95**. Nie są to ważne pomiary naukowe i nie są krzywą jasności; pasma są różne. Osobne recenterowane centroidy mają lepsze χ², lecz inną interpolację i większy stempel. Wynik uzasadnia sprawdzenie centrowania/modelu, a nie automatyczne przywrócenie odrzuconej fotometrii.

Przy osobnych prognozach PM, zwykła apertura WISE XI/IV: **0,54283±0,17309** oraz **0,59366±0,15078 mJy**; różnica około **−0,05083±0,22955 mJy**. To inne pozycje niż stały punkt karty demo, a wciąż bez paralaksy. Nie mieszać tych liczb z tabelą stałej pozycji. Sama zmiana sposobu centrowania zmienia wniosek bardziej niż poprawka powierzchni piksela.

Nie wykonano kompletnego przeszukania całego archiwum ani pełnej identyfikacji z niezależną rejestracją pola. Nieobecność ważnej pary w małej próbce nie dowodzi, że odpowiednia para nie istnieje. Jasne odpowiedniki Barnarda/RW Aur/R Dra są wiarygodnymi kandydatami pozycyjnymi, lecz nasycenie unieważnia proponowane pomiary.

## 11. Niezależność kontroli i ich ograniczenia

| Kontrola wykonana | Co sprawdza niezależnie | Czego nie poświadcza |
|---|---|---|
| Nowe SIMBAD, oryginalna tabela WISE, Gaia 2016 | Tożsamość presetów, epoki, jednostki μ i kontrola spójności źródła | Tożsamości emisji w konkretnym pikselu SPHEREx |
| Wektorowa propagacja 3D i geocentryczna paralaksa | Rachunek PM, skalę brakujących efektów | Pełnej astrometrii satelity i orbit |
| Lokalny jakobian sferyczny vs mapa powierzchni | Jednostkę i geometrię konwersji Ω, wielkość błędu stałego CD | Absolutnego zerowego punktu strumienia i kalibracji SED |
| Wektor kontrastu i QR | Suma/apertura, propagacja losowego błędu, numeryka WLS | Tego, że model tła/PSF jest rzeczywistością |
| Photutils ImagePSF vs SciPy dla rzeczywistych modeli i sztucznych faz | Zależność próbkowania/normalizacji od implementacji | Nieznanych skrzydeł PSF i prawdziwego strumienia źródła |
| 22 FITS: flagi, geometria, 22 próby centroidów | Faktyczne pokrycie i przydatność tej próbki | Niezaobserwowanych ekspozycji, pełnego wykresu skuteczności |
| 8 zadanych pozycji kontrolnych na dwóch prawdziwych FITS | Odrzucenia, tło, wrażliwość pomiaru w rzeczywistym polu | Certyfikowanej stałości lub pustki tych miejsc |
| Gauss całkowany po pikselach, szum MC, sąsiad, gradient, przesunięcie | Wzory i mechanizmy błędów o znanej prawdzie | Detekcji i charakterystyk realnego instrumentu |
| Macierz biliniowa i modelowe pasma/SED | Korelacje i możliwą degenerację koloru/czasu | Zmierzonej kowariancji SPHEREx lub transmisji filtrów |
| Fałszywy CSV i syntetyczne grupy ML | Konkretne luki w dopasowaniu/grupowaniu | Prawdziwego eksportu Tractor lub skuteczności modelu ML |

Nie uruchamiano pełnego zestawu testów aplikacji: nie zmieniono produkcji, a liczba przechodzących testów nie stanowi celu tego audytu. Przeprowadzono ukierunkowane obliczenia z własnymi wzorami, prawdziwymi FITS i kontrolowanymi wejściami. Nie wykonano prawdziwego eksportu Tractor ani badania stabilnej gwiazdy z niezależnym znanym strumieniem. Te braki są istotne.

Mały następny zestaw walidacji powinien obejmować **jeden dobrze zidentyfikowany, nienasycony, izolowany odpowiednik** w co najmniej trzech ekspozycjach o zbliżonych pasmach i odpowiednich datach, z niezależną kontrolą pozycji; ekspozycję kontrolną odłożyć przed wyborem parametrów. Do jego rzeczywistych stempli osobno wstrzyknąć sygnał o znanym strumieniu i przesunięciu 0/0,5/1 px, stałe tło i gradient, sąsiada oraz maskę. Wyniki odzysku/odmów pokazywać osobno dla wstrzyknięć i oryginalnych danych. Nie zakładać, że wybrana gwiazda jest stała wyłącznie na podstawie braku znanej etykiety zmienności.

## 12. Co można powiedzieć w prezentacji

**Dopuszczalne:**

- „Przeglądamy rzeczywiste obrazy DR1, zachowując identyfikatory, daty, lokalne przybliżenie pasma, flagi i hash wejścia.”
- „Oddzielamy zmianę długości fali od zmiany czasu, a kartę traktujemy jako zapis hipotezy wymagającej sprawdzenia.”
- „Liczymy kontrast apertury na natywnych danych, z lokalnym tłem i formalnym błędem losowym; mamy też eksperymentalne dopasowanie ePSF i centroidu.”
- „W tej próbce cztery pomiary WISE przeszły politykę apertury. Pozostałe cztery pola ograniczyły flagi, geometria albo model tła.”
- „Niezależne kontrole potwierdziły rachunek jednostek i propagacji losowego błędu; ujawniły zależność strumienia od modelu i pozycji.”
- „Przesunięcie mniejsze od piksela może być mierzalne, lecz wymaga kontroli SNR, PSF i astrometrii pola.”

**Niedopuszczalne na podstawie obecnych wyników:**

- „Wykryliśmy ruch/zmienność WISE 0855”, „zmierzyliśmy jasność całkowitą tych pięciu obiektów” lub „odkryliśmy Planet X”.
- „Dobre χ² potwierdza źródło”, „brak flag dowodzi poprawności”, „brak Gaia/SEP oznacza nowy obiekt”.
- „Podobne λ oznacza identyczne pasmo”, „widmo z wielu terminów mierzy temperaturę/skład molekularny”.
- „30 kontroli Photutils waliduje astrofizykę całej aplikacji”, „inną datę sprawdziliśmy niezależnie”, jeśli wcześniej użyto jej do wyboru hipotezy.
- „Klasyfikator jest naukowo zwalidowany”, „wynik logistyczny jest prawdopodobieństwem odkrycia”, „ważenie poprawia wykrywalność”, zanim zostanie to wykazane na odłożonych danych.

## 13. Priorytety i maksymalnie trzy usprawnienia

**Konieczne przed pokazem:** zachować jawny status eksploracyjny; skorygować niespójność pozycji/eksportu i kontrolę referencji, jeśli te ścieżki są pokazywane; nie przedstawiać nieaktywnego modelu ML jako skutecznego klasyfikatora; rozróżniać stały punkt i śledzoną prognozę; wybrać demonstrację, która pokazuje realną niepewność, zamiast obiecywać zjawisko. Zmiany produkcyjne wymagają odrębnego polecenia użytkownika — w tym audycie ich nie wdrożono.

**Wartościowe w dzień:** jedno pole kontrolne, jawna diagnostyka centrowania/tła i spójna karta wyników; mapa Ω w podstawowej aperturze; prawdziwe porównanie z eksportem IRSA, jeżeli jest dostępne. Gdy kontroli nie da się uzyskać na czas, pokaz pozostaje jakościowy. Nie usuwać masek nasycenia, nie podnosić progu akceptacji χ² dla uzyskania „sukcesu”.

**Dalsze badania:** pełna odpowiedź spektralna i korekcje koloru; wspólna astrometria pola i kowariancja; rozdzielanie sąsiadów, skalibrowane różnice PSF, ruch obserwatora i orbity; walidacja ML z niezależnymi polami i przedziałami niepewności. Trening lub nowa interpretacja chemiczna nie są priorytetem przed naprawą podstaw.

| Usprawnienie | Problem i dlaczego obecnie nie wystarcza | Minimum na jeden dzień / dane | Walidacja | Koszt, ryzyko, wartość demonstracji |
|---|---|---|---|---|
| **1. Jedna pozycja z pełnym śladem pomiaru** | Piksel odczytu, ciągły marker, kotwica trasy i apertura mogą wskazywać różne miejsca; nowy centroid nie aktualizuje starego F. | Wspólna funkcja transformacji; w karcie osobno kliknięcie, środek odczytanego piksela, prognoza, dopasowany centroid i dokładna pozycja każdego estymatora. Pasmo liczyć tam, gdzie znajduje się dany marker. Istniejące FITS/WCS/ePSF wystarczą. | N parzyste i nieparzyste, punkty poza centrum i przy krawędzi, obie osie, eksport route z/bez point; porównanie RA/Dec i λ z bezpośrednim WCS natywnym. | **3–5 h**, małe ryzyko matematyczne, średnie ryzyko starych linków/cache. Największa bezpośrednia wartość: karta rzeczywiście odtwarza porównanie. |
| **2. Panel odporności istniejącej fotometrii** | Pojedyncze F±σ ukrywa centrowanie, wybór tła, straty apertury i różnicę estymatorów. | Użyć Ωᵢ w obu aperturach; dla jednego wybranego źródła pokazać maskę/pierścień, F przy pozycji kliknięcia i osobno centroidzie, średnie/płaszczyznowe tło, dwa promienie i reszty. Nie wybierać automatycznie najjaśniejszego wariantu. Zachować konwencję normalizacji ePSF i ostrzec o fazie, zanim zmieni się definicję F. | Jedno rzeczywiste nienasycone pole + odłożona ekspozycja, eksport IRSA jeżeli dostępny; znane wstrzyknięcia i dotychczasowe kontrole Gaussa, gradientu, sąsiada/maski. Kryteria odzysku ustalić przed testem. | **4–7 h**, średnie ryzyko zmiany wyników i cache. Mocny pokaz: użytkownik widzi, dlaczego pozorna zmiana wymaga sprawdzenia. Nie obiecuje całkowitej kalibracji. |
| **3. Karta „czas czy pasmo?” z jednym ślepym sprawdzeniem** | Heurystyczne grupowanie nie wyklucza koloru, a inna data nie gwarantuje niezależnego potwierdzenia. | Dodać Δλ/λ, szerokości, daty i krótką, oznaczoną analizę wrażliwości np. dla p=−2,0,2,10. Z góry zapisać hipotezę/parametry i identyfikator trzeciej niewykorzystanej ekspozycji; wynik może brzmieć „nierozstrzygający”. Bez molekuł i procentowego discovery score. | Przykład syntetycznej zmiany wyłącznie pasma oraz jeden rzeczywisty zestaw z ≥3 odpowiednimi ekspozycjami; jeżeli brak, jawna odmowa i zapis przyczyny. Pełne Kᵢ potrzebne dopiero do twierdzenia ilościowego o kolorze. | **2–4 h** po punkcie 1, małe ryzyko kodu, wysokie ryzyko niedostępności porównywalnej trzeciej epoki. Wzmacnia istniejącą koncepcję sprawdzalnej hipotezy; nie jest nowym algorytmem odkrywania. |

Szacunki są kosztami pracy, nie gwarancją ukończenia wszystkich trzech dodatków w pozostałym czasie. Najpierw naprawić punkt 1 i bezpieczeństwo interpretacji; następnie wybrać ograniczony wariant punktu 2. Jeżeli nie ma czasu lub danych do walidacji, lepszym wynikiem naukowym jest uczciwy pokaz ograniczeń niż nowa funkcja chemiczna albo trening na przypadkowych etykietach.
