# Materiały wizualne

## Demo finalizacji

Pliki `frontend/public/demo/index.html` i `evidence.html` osadzają PNG utworzone przez istniejący pipeline z rzeczywistych FITS SPHEREx DR1. Nie są to obrazy AI ani ilustracje udające obserwacje. Każdy zestaw ma wspólną skalę asinh; brakujące/odrzucone piksele pozostają przezroczyste z kreskowanym tłem. Metadane dema zawierają oryginalny URL i SHA-256 natywnego FITS, datę, detektor i lokalizację odczytu pasma. Współrzędne oraz podpisy katalogowe nie stanowią identyfikacji źródła. Karta dodaje wyłącznie znacznik interfejsu; nie modyfikuje pomiarów. Pełne acknowledgement NASA/JPL-Caltech/IPAC jest widoczne w obu plikach.

Weryfikacja: 14 listopada 2026. Nie użyto generowania obrazów AI.

## Obrazy SPHEREx

Wszystkie trzy obrazy pochodzą z oficjalnego artykułu JPL: [How NASA’s SPHEREx Mission Will Share Its All-Sky Map With the World](https://www.jpl.nasa.gov/news/how-nasas-spherex-mission-will-share-its-all-sky-map-with-the-world/). Każdy plik źródłowy zwrócił HTTP 200 i został sprawdzony jako poprawny obraz.

| Plik w public/images | Materiał | Autorstwo | Użycie |
|---|---|---|---|
| spherex-vela.webp | Vela Molecular Ridge, materiał PIA26354 | NASA/JPL-Caltech | Podpisana ilustracja wprowadzająca |
| spherex-329um.webp | Pole obserwowane przy 3,29 μm | NASA/JPL-Caltech | Przykład wpływu długości fali |
| spherex-098um.webp | To samo pole przy 0,98 μm | NASA/JPL-Caltech | Przykład wpływu długości fali |

Podstawa wykorzystania: [JPL Image Use Policy](https://www.jpl.nasa.gov/jpl-image-use-policy/), z oznaczeniem autorstwa i bez sugerowania poparcia NASA, JPL ani Caltech. Nie przypisujemy tym materiałom licencji Creative Commons. Na stronie źródłowej przy wybranych obrazach nie wskazano zewnętrznego właściciela praw. Warunki pozwalają na wykorzystanie zgodnie z polityką JPL; podpisy oraz odnośnik do polityki są widoczne w interfejsie.

Pliki zakodowano do WebP bezstratnie. Sprawdzono identyczność wszystkich zdekodowanych pikseli RGBA przed i po konwersji. Nie zmieniano treści, kolorów ani kontrastu. Obraz wprowadzający może być kadrowany przez CSS; oba obrazy porównania spektralnego są pokazywane w całości. Oryginały PNG są w lokalnym, ignorowanym katalogu `data/editorial-originals/`.

Dokładne źródłowe adresy CDN, wymiary i sumy SHA-256 oryginałów oraz plików publikowanych zapisano w `frontend/public/images/sources.json`. Skrypt odtwarzający zasoby: `scripts/fetch_editorial_assets.py`.

Obrazy użyte w samym viewerze nadal pochodzą z rzeczywistych FITS pobieranych z IRSA. Materiały redakcyjne nie zastępują obserwacji ani nie udają danych dla wybranych współrzędnych.

## Typografia

IBM Plex Sans oraz Source Serif 4 są dostarczane lokalnie przez pakiety Fontsource. Zastosowano podzbiory Latin i Latin Extended, w tym polskie znaki. Przeglądarka nie odpytuje Google Fonts. Oba fonty mają SIL Open Font License 1.1; pełne teksty licencji znajdują się w `frontend/public/licenses/`.

## Ikony i diagram

Ikony pochodzą z istniejącego w projekcie pakietu Lucide React (ISC). Schemat osi pustego pola jest prostym SVG interfejsu, bez fikcyjnych źródeł astronomicznych. Etykiety w viewerze oznaczają orientację i wskazania użytkownika.
# Biblioteka mapy planu 4.0

Integracja SPHEREx HiPS używa oryginalnych PNG i metadanych z `https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube`. Backend udostępnia wybrany kanał jako zwykły HiPS i przechowuje ograniczony cache w pamięci. To mozaika archiwalna, nie jednoczesne widmo. Mapy kalibracyjne są pobierane z publicznego archiwum `https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com`; ich wersje i SHA-256 trafiają do raportu. Modele ePSF pochodzą ze źródłowych FITS. Ekstrakcja wykorzystuje bibliotekę SEP (BSD-3-Clause); nie skopiowano całego pakietu notebooka IRSA ani nie dołączono programu SExtractor.

Aladin Lite 3.9.2-beta, CDS, przypięty pakiet npm `aladin-lite`, ładowany w osobnym chunku. Źródła: https://github.com/cds-astro/aladin-lite. Pakiet deklaruje LGPL-3.0-or-later; kopie LICENSE i COPYING są dostarczane w `frontend/public/licenses/Aladin-Lite-LICENSE.txt` i `Aladin-Lite-GPL-3.0.txt`. Warstwy 2MASS i AllWISE pobiera przeglądarka z oficjalnego drzewa HiPS IRSA (https://irsa.ipac.caltech.edu/data/hips/list); nie są kopiowane ani mirrorowane w repozytorium. 2MASS J/H/K i AllWISE W4/W2/W1 są historycznym kontekstem, nie pomiarem SPHEREx.
