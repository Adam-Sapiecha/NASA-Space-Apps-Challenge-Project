import {t} from './i18n.ts';
import {date} from './types';

export type RobustRow={id:string;date:string;position?:{ra:number;dec:number};robustness?:{epsf_position_range_mjy:[number,number]|null;aperture_minus_epsf_mjy:number|null;background_model_delta_mjy:number|null};aperture?:{valid:boolean;reason?:string;background_pixels?:number;plane_background?:{flux_mjy?:number;error_mjy?:number;reason?:string}}};
const value=(n:number|null|undefined)=>n==null||!Number.isFinite(n)?'—':n.toLocaleString('pl-PL',{maximumSignificantDigits:5});

export default function PhotometryRobustness({rows}:{rows:RobustRow[]}){
 return <details className="reference-import"><summary>{t("Sprawdź centrowanie i model tła")}</summary>
  <p>{t("Każdy pomiar dotyczy tej samej wskazanej pozycji ICRS. Sprawdzamy dodatkowo cztery ustalone przesunięcia: ±0,5 piksela w osi X lub Y. Zakres obejmuje też pierwotny wynik. Nie wybieramy najjaśniejszego wariantu. Centroid z osobnej diagnostyki nie zmienia tej pozycji.")}</p>
  <p>{t("Porównania korzystają z tych samych pikseli i mają skorelowane błędy. Różnice pokazują zależność od modelu; nie są testem zmienności ani całkowitą niepewnością.")}</p>
  <div className="observation-scroll" tabIndex={0}><table className="observation-table"><thead><tr><th>{t("Data / pozycja ICRS")}</th><th>{t("Zakres ePSF po przesunięciach (mJy)")}</th><th>{t("Apertura − ePSF (mJy)")}</th><th>{t("Tło: płaszczyzna − średnia (mJy)")}</th><th>{t("Pierścień tła")}</th></tr></thead><tbody>{rows.map(r=><tr key={r.id}>
   <td>{date(r.date)}{r.position&&<small className="mono"> {r.position.ra.toFixed(7)}°, {r.position.dec.toFixed(7)}°</small>}</td>
   <td>{r.robustness?.epsf_position_range_mjy?.map(value).join(' … ')??'—'}</td>
   <td>{value(r.robustness?.aperture_minus_epsf_mjy)}</td>
   <td>{value(r.robustness?.background_model_delta_mjy)}</td>
   <td>{r.aperture?.valid?`${r.aperture.background_pixels} czystych pikseli`:r.aperture?.reason??'Brak diagnostyki w archiwalnej metodzie'}</td>
  </tr>)}</tbody></table></div>
 </details>;
}
