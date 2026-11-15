import {locale,t} from './i18n';
import type {Frame} from './types';
import {pixelFlagSummary} from './viewerStatus';

export default function ImageQualityLegend({frames,a,b,mode,qualities,masks,showMissing,onMissing,split=false}:{frames:Frame[];a:number;b:number;mode:'side'|'series';qualities:[string,string];masks:[boolean,boolean];showMissing:boolean;onMissing:(value:boolean)=>void;split?:boolean}){
 const rows=pixelFlagSummary(frames,a,b,mode);
 const percent=(value:number)=>value>0&&value<.0001?'<0.01':(value*100).toLocaleString(locale(),{maximumFractionDigits:2});
 const definitions=[...new Set(frames.flatMap(frame=>frame.masked_flags))];
 return <div className="image-quality-legend">
  <div className="image-legend"><span className={`missing-legend${showMissing?'':' plain'}`}>{t(showMissing?'Ukośne kreski:':'Jednolite tło:')} {rows.every(row=>qualities[row.index]==='all')?t('brak danych z obserwacji'):t('brak danych lub piksel odrzucony')}</span>
   <span>{t('Pokrycie pola:')} {rows.map((row,i)=><span key={row.label}>{i?' · ':''}{mode==='side'?`${row.index===a?'A':'B'} — `:''}{((frames[row.index].display_coverage??frames[row.index].coverage)*100).toLocaleString(locale(),{maximumFractionDigits:1})}%</span>)}</span>
  </div>
  <label className="check-label missing-display-toggle"><input type="checkbox" checked={showMissing} onChange={event=>onMissing(event.target.checked)}/>{t('Zaznacz braki kreskowaniem')}</label>
  {rows.some(row=>(frames[row.index].display_coverage??frames[row.index].coverage)<.5)&&<p className="low-field-coverage">{t('W tym podglądzie dostępna jest mniej niż połowa pola. Zmień datę lub pasmo albo wybierz mniejszy obszar nieba.')}</p>}
  <div className="pixel-mask-summary">
   <span>{rows.map((row,i)=><span key={row.label}>{i?' · ':''}{row.label}: {qualities[row.index]==='all'?`${t('Piksele z flagami błędów:')} ${row.fraction===null?'…':`${percent(row.fraction)}%`} ${t('pola')}`:t('Piksele z flagami błędów są odrzucone w tym widoku.')}</span>)}{masks.some((value,index)=>value&&qualities[index]==='all')&&<> · <span className="warning-legend">{t('Pomarańczowe ramki pokazują te piksele')}</span></>}{split&&<> · {t('Osobne ustawienia A/B')}</>}</span>
   <details className="pixel-mask-help"><summary>{t('Co oznaczają flagi?')}</summary><p>{t('To oznaczenia konkretnych pikseli w masce FITS, a nie ocena całej gwiazdy ani potwierdzenie artefaktu. Podgląd może je pokazywać; pomiary nadal korzystają z kontroli jakości.')}</p>{definitions.length>0&&<p>{t('Maska uwzględnia flagi:')} <code>{definitions.join(', ')}</code></p>}</details>
  </div>
 </div>;
}
