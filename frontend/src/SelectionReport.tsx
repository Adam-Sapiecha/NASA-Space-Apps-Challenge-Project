import {t} from './i18n.ts';
import {date,type Analysis} from './types';

export default function SelectionReport({analysis}:{analysis:Analysis}){
 const report=analysis.selection;
 if(!report)return null;
 return <section className="selection-report" aria-label={t('Kontrola doboru obserwacji')}>
  <strong>{t('Dobór na podstawie lokalnych danych')}</strong>
  <p role="status">{t(report.summary)}</p>
  <p>{t('Sprawdzone obserwacje:')} {report.inspected} · {t('Wybrane zdjęcia:')} {analysis.frames.length}
   {report.baseline_days!==undefined&&<> · {t('Odstęp dat:')} {report.baseline_days.toFixed(2)} {t('dni')}</>}
  </p>
  {report.position_method==='catalogue_proper_motion_per_epoch'&&<p>{t('Kontrole wykonano przy osobnej prognozie pozycji celu dla każdej daty. To nie potwierdza jego identyfikacji. Pomiary po kliknięciu dotyczą wskazanej stałej pozycji.')}</p>}
  <details><summary>{t('Dlaczego wybrano te obrazy?')}</summary>
   <p>{t('Dobór sprawdza lokalne pasmo, pokrycie apertury, flagi i tło. Jasność ani S/N celu nie wpływają na ranking. Niewybrane obserwacje mogą nadal zawierać przydatne dane.')}</p>
   <div className="observation-scroll"><table className="observation-table"><thead><tr><th>{t('Data UTC')}</th><th>{t('Detektor')}</th><th>λ (µm)</th><th>{t('Apertura')}</th><th>{t('Powód lub flagi')}</th></tr></thead><tbody>
    {report.candidates.map(row=><tr key={row.id} className={report.selected_ids.includes(row.id)?'selected':''}><td>{date(row.date)}</td><td>{row.band.replace('SPHEREx-','')}</td><td>{row.wavelength_um?.toFixed(4)??'—'}</td><td>{t(row.aperture_valid?'ważna':'nieważna')}</td><td>{t(row.reason??row.flagged?.join(', ')??'—')}{row.cutout_fov_arcmin>analysis.search.fov_arcmin&&<> · {t('Powiększony wycinek:')} {row.cutout_fov_arcmin}′</>}</td></tr>)}
   </tbody></table></div>
   <ul>{report.limitations.map(item=><li key={item}>{t(item)}</li>)}</ul>
   <a href={`/api/analyses/${analysis.id}/export`}>{t('Pobierz pełne parametry i kontrolę doboru (JSON)')}</a>
  </details>
 </section>;
}
