import {t} from './i18n.ts';
export default function ResearchGuide(){
 return <aside className="help-panel" aria-label={t("Pomoc i źródła danych")}>
  <h2>{t("Jak zacząć")}</h2>
  <p><a href="/?guided=1">{t("Opcjonalny przewodnik krok po kroku")}</a></p>
  <ol><li>{t("Wybierz obiekt i kliknij „Wyszukaj obrazy”.")}</li><li>{t("Wybierz „Ruch i zmiany w czasie” albo „Obraz w różnych pasmach”. Aplikacja dobierze zdjęcia; kliknij przycisk przygotowania zestawu.")}</li><li>{t("Porównaj całe zdjęcia obok siebie lub włącz Animację. Kliknięcie zaznacza to samo miejsce na obu zdjęciach.")}</li></ol>
  <details><summary>{t("Co porównuję?")}</summary><p>{t("To ten sam fragment nieba z różnych dat. Zmiana wyglądu może wynikać także z innej długości fali lub jakości danych. Ostrzeżenie przy obrazie sygnalizuje różne pasma. Kreskowane miejsca to brak danych. Pomarańczowe ramki oznaczają piksele z ostrzeżeniami — w podglądzie są widoczne, ale pomiary nadal uwzględniają kontrolę jakości.")}</p></details>
  <details><summary>{t("Co robią pozostałe narzędzia?")}</summary><p>{t("„Wskaż ruch” pozwala wskazać obiekt na A i B i obejrzeć wycinki wzdłuż tej trasy. „Zobacz inne pasma” pokazuje obraz od krótszych do dłuższych fal podczerwieni. „Wybierz miejsce na mapie” pozwala wybrać obszar bez wpisywania współrzędnych. „Sprawdź punkt” zawiera automatyczną ocenę i porównanie jasności. Kalibracje i dokładne pomiary są w ustawieniach zaawansowanych.")}</p></details>
  <details><summary>{t("Źródła i ograniczenia")}</summary><p>{t("SPHEREx: NASA/IPAC IRSA. Mapa: 2MASS i AllWISE. Katalog: Gaia DR3. Pomiary apertury są eksploracyjne; różnice obrazów są jakościowe, bez dopasowania PSF. Aplikacja nie potwierdza odkryć.")}</p><div className="source-links"><a href="https://irsa.ipac.caltech.edu/Missions/spherex.html" target="_blank" rel="noreferrer">{t("Archiwum SPHEREx")}</a><a href="https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/" target="_blank" rel="noreferrer">{t("Dokumentacja FITS")}</a></div></details>
 </aside>;
}
