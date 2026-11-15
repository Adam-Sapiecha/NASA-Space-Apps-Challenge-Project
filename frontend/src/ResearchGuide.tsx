import {assetUrl} from './urls.ts';
import {t} from './i18n.ts';
export default function ResearchGuide(){
 return <aside className="help-panel" aria-label={t('Pomoc i źródła danych')}>
  <h2>{t('Obsługa i dane')}</h2>
  <ol>
   <li>{t('Ruch komety: dwie zapisane obserwacje 3I/ATLAS obok siebie. Znaczniki pochodzą z efemeryd.')}</li>
   <li>{t('Wybierz pole, przesuwaj czas wraz z godziną i wybieraj pasma dostępne w tym dniu. Przypięcie zdjęcia jako A pozwala porównać je z kolejnymi obserwacjami.')}</li>
  </ol>
  <details><summary>{t('Obraz i ustawienia A/B')}</summary><p>{t('Kliknięcie obrazu wybiera tę samą pozycję nieba w obu zdjęciach. Ustawienia wyświetlania mogą być wspólne lub osobne dla A/B. Umowny kolor oznacza długość fali; nie jest naturalnym kolorem nieba. Jednolite tło oznacza brak danych; kreskowanie można włączyć pod zdjęciem. Włączenie maski dodaje obrysy pikseli z flagami błędów.')}</p></details>
  <details><summary>{t('Pełne narzędzia i eksport')}</summary><p>{t('Przycisk „Wszystkie narzędzia” udostępnia widmo, składanie, kalibracje i kontekst katalogowy. Mapa, pomiary zaznaczonego punktu i eksport parametrów pozostają przy bieżącej analizie. „Kopiuj link” zapisuje parę A/B, punkt i ustawienia wyświetlania.')}</p></details>
  <details><summary>{t('Źródła i ograniczenia')}</summary><p>{t('SPHEREx: NASA/IPAC IRSA. Mapa: 2MASS i AllWISE. Katalog: Gaia DR3. Pomiary apertury są eksploracyjne; różnice obrazów są jakościowe, bez dopasowania PSF. Aplikacja nie potwierdza odkryć.')}</p><div className="source-links"><a href="https://irsa.ipac.caltech.edu/Missions/spherex.html" target="_blank" rel="noreferrer">{t('Archiwum SPHEREx')}</a><a href="https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/" target="_blank" rel="noreferrer">{t('Dokumentacja FITS')}</a><a href={assetUrl('/demo/')}>{t('Zapisana prezentacja')}</a></div></details>
 </aside>;
}
