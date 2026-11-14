import {locale,t} from './i18n';
import type {Frame} from './types';
import {pixelFlagSummary} from './viewerStatus';

export default function ImageQualityLegend({frames,a,b,mode,quality,showMask,onMask,qualities=[quality,quality],masks=[showMask,showMask],split=false,onSlotMask}:{frames:Frame[];a:number;b:number;mode:'side'|'lens'|'blink'|'route'|'series';quality:string;showMask:boolean;onMask:(value:boolean)=>void;qualities?:[string,string];masks?:[boolean,boolean];split?:boolean;onSlotMask?:(slot:0|1,value:boolean)=>void}){
 const rows=pixelFlagSummary(frames,a,b,mode);
 const percent=(value:number)=>value>0&&value<.0001?'<0.01':(value*100).toLocaleString(locale(),{maximumFractionDigits:2});
 const definitions=[...new Set(frames.flatMap(frame=>frame.masked_flags))];
 return <div className="image-quality-legend">
  <div className="image-legend"><span className="missing-legend">{t('Ukośne kreski:')} {qualities.every(value=>value==='all')?t('brak danych z obserwacji'):t('brak danych lub piksel odrzucony')}</span>
   <span>{t('Pokrycie pola:')} {rows.map((row,i)=><span key={row.label}>{i?' · ':''}{row.label} — {((frames[row.index].display_coverage??frames[row.index].coverage)*100).toFixed(1)}%</span>)}</span>
   {split?rows.map(row=><label key={row.index} className="pixel-mask-toggle"><input type="checkbox" checked={masks[row.index]} disabled={qualities[row.index]!=='all'} onChange={event=>onSlotMask?.(row.index as 0|1,event.target.checked)}/>{t('Maska')} {row.index===0?'A':'B'}</label>):<label className="pixel-mask-toggle"><input type="checkbox" checked={showMask} disabled={quality!=='all'} onChange={event=>onMask(event.target.checked)}/>{t('Pokaż maskę flag błędów')}</label>}
  </div>
  <div className="pixel-mask-summary">
   <span>{rows.map((row,i)=><span key={row.label}>{i?' · ':''}{row.label}: {qualities[row.index]==='all'?`${t('Piksele z flagami błędów:')} ${row.fraction===null?'…':`${percent(row.fraction)}%`} ${t('pola')}`:t('Piksele z flagami błędów są odrzucone w tym widoku.')}</span>)}{masks.some((value,index)=>value&&qualities[index]==='all')&&<> · <span className="warning-legend">{t('Pomarańczowe ramki pokazują te piksele')}</span></>}{split&&<> · {t('Osobne ustawienia A/B')}</>}</span>
   <details className="pixel-mask-help"><summary>{t('Co oznaczają flagi?')}</summary><p>{t('To oznaczenia konkretnych pikseli w masce FITS, a nie ocena całej gwiazdy ani potwierdzenie artefaktu. Podgląd może je pokazywać; pomiary nadal korzystają z kontroli jakości.')}</p>{definitions.length>0&&<p>{t('Maska uwzględnia flagi:')} <code>{definitions.join(', ')}</code></p>}</details>
  </div>
 </div>;
}
