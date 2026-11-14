# Naprawy po audycie matematycznym — 14 listopada 2026

Wdrożono poprawki po poleceniu „popraw”. Aplikacja działa lokalnie pod http://127.0.0.1:8000. Nie opublikowano projektu, nie zmieniono hostingu i nie uruchomiono treningu ML. Zachowano wcześniejsze wyniki i notatki; kopia SQLite sprzed restartu: `data/audit/math_fixes_20261114/workspace-before-restart.sqlite`.

## Co poprawiono

| Problem | Zmiana i kontrola |
|---|---|
| Różne pozycje odczytu i pomiaru | `coordinates.py` definiuje wspólny ciągły punkt dla odczytu RA/Dec, apertury, centroidu i eksportu. WCS-WAVE jest interpolowane w tym punkcie, a indeks piksela flag zapisany osobno. Brak λ nie jest uzupełniany centrum. Niezależne testy TAN dla N=59/60 i RA blisko 0; działające API dla (0,509;0,507) daje **zerową różnicę współrzędnych** pomiędzy odczytem i pomiarem. |
| Błędne pasmo przy markerze trasy | Eksport używa kotwicy lub jawnej liniowej prognozy właściwej klatki. Przy braku położenia trasy nie przypisuje pasma centrum. JSON v2 zapisuje punkt i RA/Dec każdej klatki. Testy z i bez osobnego stałego punktu. |
| Mieszanie trasy i stałej apertury | JSON/HTML podają osobno pozycję powiązanej fotometrii i markerów. `independent_epoch=null`; inna data nie jest deklarowana jako niezależne potwierdzenie. |
| Fałszywe dopasowanie referencji | Wymagane są zgodne `lvf_id`, wydanie, detektor, pozycja/czas, λ oraz `lambda_width`. Sprawdzany jest także detektor wewnątrz nazwy pliku; ułamkowe ID są odrzucane. Kontrolne CSV ze złym λ/wydaniem/ekspozycją/szerokością dają 0 dopasowań. To kontrole syntetyczne, nie eksporty Tractor. |
| Stała powierzchnia CD | Metoda `native-aperture-area-3` stosuje kalibracyjne Ωᵢ dla każdego natywnego piksela i propaguje niepewność średniego tła. Sprawdzono znany sygnał i niezależny wektor kontrastu z różnymi Ωᵢ oraz 22 rzeczywiste FITS. |
| Normalizacja ePSF zależna od fazy | Próbkowany profil jest normalizowany na pełnym skończonym modelu, niezależnie od maski i brzegu danych. Nie wykonuje się ponownego splotu z pikselem. W 25 fazach rzeczywistego modelu suma wynosi **0,9999999999999997–1,0000000000000004**. Kontrola brzegu nie renormalizuje brakującego pokrycia do 1. |
| Kowariancja z macierzy normalnych | SVD i kontrola uwarunkowania w ePSF, płaszczyźnie tła, kowariancji centroidu, modelu ruchu i kontinuum. Testy znanych amplitud, pozycji, ruchu i niepewności. |
| Wspólna bramka apertury i ePSF | Estymatory mają osobną ważność. Złe χ² ePSF blokuje dalsze użycie amplitudy, ale pozostawia wynik diagnostyczny. Brak dobrego pierścienia apertury nie blokuje automatycznie modelu z własnym tłem. Masek artefaktów nie usunięto. |
| Ukryta zależność od pozycji/tła | Nowy panel pokazuje cztery ustalone przesunięcia ±0,5 px, zakres wraz z pierwotnym punktem, różnicę apertura−ePSF oraz płaszczyzna−średnie tło. Nie wybiera najlepszego strumienia i nie traktuje wariantów jako niezależnych pomiarów. |
| Niepełne zabezpieczenia kalibracji | Wymagane HDU i jednostki, kontrola detektora, geometrii WCS-A i dokładnego całkowitego przesunięcia. Usunięto fallback do przypadkowego HDU. Sprawdzana jest też zgodność CBAND z przybliżeniem. Testy błędnych map oraz prawdziwe mapy D2/D6. |
| Za mocna deklaracja walidacji ML | Grupy łączone także po oryginalnej ekspozycji między różnymi wycinkami. Aktywacja wymaga jednostronnych dolnych granic 95% na poziomie grup. Status lokalny/eksperymentalny, `scientifically_validated=false`. Stare modele i cechy pozostają zachowane, lecz są ignorowane przez nową wersję. Model w rzeczywistej bazie nadal wyłączony. |
| Mieszanie starych i nowych obliczeń | Nowe wersje metod/cache. Archiwalne wyniki można oglądać z ostrzeżeniem; do nowej referencji, średniej, widma i wag wymagane jest przeliczenie. API odrzuca wcześniejszą metodę komunikatem 422. |
| Nadinterpretacja filtra pasma | Filtr nadal jest jawnie heurystyczny. Diagnostyka pokazuje modelową wrażliwość koloru dla Fν∝λᵖ, bez deklarowania zmierzonej korekcji źródła. Wynik pozostaje `requires_validation`. |

## Rzeczywiste wyniki po poprawkach

Nowe apertury przy osobnej prognozie PM każdej daty: Barnard **0/4**, Epsilon Indi B **0/6**, WISE **4/5**, RW Aur **0/4**, R Dra **0/3**. Kryteriów nie zmieniano, aby uzyskać dodatni wynik. Pozostają flagi, brzegi i brak czystego tła.

WISE z Ωᵢ, przy osobnych prognozach PM:

| Data UTC | Kontrast apertury ± błąd losowy, mJy |
|---|---:|
| 2025-05-05 | 0,37489 ± 0,22288 |
| 2025-11-10 | 0,54771 ± 0,17465 |
| 2025-12-13 | apertura nieważna: NONFUNC |
| 2026-04-21 | 0,60012 ± 0,15242 |
| 2026-05-11 | 0,54181 ± 0,25533 |

To inne pozycje niż stały punkt karty demo. W stałym punkcie (0,5;0,5) ePSF listopad/kwiecień daje **0,80606±0,12792** i **0,37812±0,10439 mJy**. Rozbieżność z aperturą nadal istnieje: poprawka normalizacji nie usuwa fizycznej zależności od modelu i pozycji. Panel pokazuje ją wprost.

Grudniowy model ePSF może mieć wynik pomimo nieważnej apertury: korzysta z pozostałych dobrych pikseli i wymaga dostatecznej części profilu. Nie uzupełniono brakującego piksela w obrazie. Jest to warunkowa amplituda modelu, z ostrzeżeniem otoczenia, bez wniosku o zmianie jasności.

## Weryfikacja

- **104 testy backendu** przeszły; `data/audit/math_fixes_20261114/backend-tests.xml`.
- **30 testów frontendu** i końcowy build TypeScript/Vite przeszły. Pozostało znane ostrzeżenie rozmiaru chunka Aladin.
- `scripts/verify_math_fixes.py`: odczytowa kontrola 22 FITS i kalibracji. Oryginalne obrazy pozostały identyczne, brak zapisów do bazy podczas tej kontroli. Wynik `offline-validation.json`.
- `scripts/smoke_math_fixes.py`: działające API, zgodne współrzędne, kalibracja zgodna z obliczeniami offline, blokowanie starej metody w nowym łańcuchu analizy, jawne pozycje eksportu i brak aktywnego niezwalidowanego ML. Wynik `live-validation.json`; fingerprint backendu `fba7fefabc047da18a7da4ddcdc9734fb497044754a4e346471fb9d412ea0e04`, `code_changed=false`.
- Przeglądarka: archiwalny raport z komunikatem, nowe zadanie na rzeczywistych FITS, nowy wynik i panel odporności. Zrzut `data/audit/math_fixes_20261114/photometry-ui.jpg`.

[Otwórz poprawiony raport WISE lokalnie](http://127.0.0.1:8000/?analysis=4812094a2ce843a8b787837eb13ec845&view=irsa&point=%7B%22x%22%3A0.5%2C%22y%22%3A0.5%7D&irsa=81560764686b47db8c178f47c55edd86).

## Pozostałe ograniczenia naukowe

Nie uzyskano pełnych odpowiedzi filtrów, niezależnego eksportu Tractor ani kalibracji astrometrii pola. Nie potwierdzono ruchu/zmienności, molekuł, skuteczności ML ani poprawy wykrywalności. Pełna pozycja obserwowana wymaga m.in. spójnej paralaksy, orbity i pozycji obserwatora; prognozy PM pozostają tak oznaczone. Modelowanie sąsiadów, całkowita niepewność i pomiarowe różnice obrazów wymagają dalszej walidacji.

Dobre χ² i przejście bramek technicznych nie są dowodem astrofizycznym. Trzecia data i analiza wrażliwości nie zastępują ślepego potwierdzenia. Wynikiem napraw jest usunięcie niespójności oraz ujawnienie ograniczeń istniejących pomiarów.
