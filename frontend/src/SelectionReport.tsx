import {apiUrl} from './urls.ts';
import {t} from './i18n.ts';
import {date,type Analysis} from './types';

export default function SelectionReport({analysis,activeIds}:{analysis:Analysis;activeIds?:string[]}){
 const report=analysis.selection;
 if(!report)return null;
 const custom=activeIds&&report.pair_ids.length===2&&!(new Set(activeIds).size===2&&activeIds.every(id=>report.pair_ids.includes(id)));
 return <section className="selection-report" aria-label={t('Kontrola doboru obserwacji')}>
  <strong>{t(custom?'Własne porównanie A/B':analysis.provisional?'Zdjęcia pojawiają się w trakcie pobierania':'Dobór na podstawie lokalnych danych')}</strong>
  <p role="status">{t(custom?'Ten zestaw różni się od automatycznie rekomendowanej pary. Sprawdzaj daty, lokalne pasma i jakość wybranych obserwacji.':report.summary)}</p>
  <p>{t('Sprawdzone obserwacje:')} {report.inspected}{report.planned!==undefined&&` / ${report.planned}`} · {t('Dostępne zdjęcia:')} {analysis.frames.length} · {t('Rekomendowana seria:')} {report.selected_ids.length}
   {report.baseline_days!==undefined&&!custom&&<> · {t('Odstęp dat:')} {report.baseline_days.toFixed(2)} {t('dni')}</>}
  </p>
  {report.position_method==='catalogue_proper_motion_per_epoch'&&<p>{t('Kontrole wykonano przy osobnej prognozie pozycji celu dla każdej daty. To nie potwierdza jego identyfikacji. Pomiary po kliknięciu dotyczą wskazanej stałej pozycji.')}</p>}
  <details><summary>{t('Dlaczego wybrano te obrazy?')}</summary>
   {custom&&<p>{t('Rekomendacja automatyczna:')} {t(report.summary)}</p>}
   <p>{t('Dobór sprawdza lokalne pasmo, pokrycie apertury, flagi i tło. Jasność ani S/N celu nie wpływają na ranking. Niewybrane obserwacje mogą nadal zawierać przydatne dane.')}</p>
   <div className="observation-scroll"><table className="observation-table"><thead><tr><th>{t('Data UTC')}</th><th>{t('Detektor')}</th><th>λ (µm)</th><th>{t('Apertura')}</th><th>{t('Powód lub flagi')}</th></tr></thead><tbody>
    {report.candidates.map(row=><tr key={row.id} className={report.selected_ids.includes(row.id)?'selected':''}><td>{date(row.date)}</td><td>{row.band.replace('SPHEREx-','')}</td><td>{row.wavelength_um?.toFixed(4)??'—'}</td><td>{t(row.aperture_valid?'ważna':'nieważna')}</td><td>{t(row.reason??row.flagged?.join(', ')??'—')}{row.cutout_fov_arcmin>analysis.search.fov_arcmin&&<> · {t('Powiększony wycinek:')} {row.cutout_fov_arcmin}′</>}</td></tr>)}
   </tbody></table></div>
   <ul>{report.limitations.map(item=><li key={item}>{t(item)}</li>)}</ul>
   <a href={apiUrl(`/api/analyses/${analysis.id}/export`)}>{t('Pobierz pełne parametry i kontrolę doboru (JSON)')}</a>
  </details>
 </section>;
}
