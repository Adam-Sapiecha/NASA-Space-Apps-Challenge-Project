import {t} from './i18n';
import {date,type Analysis} from './types';

export default function FrameGallery({analysis,a,b,seriesOnly,series,onSelect,onScope,onRecommended}:{analysis:Analysis;a:number;b:number;seriesOnly:boolean;series:number[];onSelect:(index:number)=>void;onScope:(only:boolean)=>void;onRecommended:()=>void}){
 const visible=analysis.frames.map((_,i)=>i).filter(i=>!seriesOnly||series.includes(i));
 return <section className="frame-gallery" aria-label={t('Galeria obserwacji')}>
  <div className="gallery-heading"><div><h2>{t(analysis.selection?'Wybrane zdjęcia':'Wszystkie przygotowane zdjęcia')} <span>{analysis.frames.length}</span></h2><p>{t(analysis.provisional?'Gotowe klatki możesz oglądać od razu. Kolejne pojawią się automatycznie.':'Kliknij miniaturę, aby pokazać ją jako zdjęcie B.')}</p></div>
   <div className="gallery-actions"><button aria-pressed={!seriesOnly} onClick={()=>onScope(false)}>{t('Wszystkie zdjęcia')} ({analysis.frames.length})</button><button aria-pressed={seriesOnly} onClick={()=>onScope(true)}>{t('Zgodna seria')} ({series.length})</button><button disabled={analysis.selection?.pair_ids.length!==2} onClick={onRecommended}>{t('Pokaż rekomendowaną parę')}</button></div>
  </div>
  {!analysis.selection&&<p className="gallery-warning">{t('Wszystkie zdjęcia obejmują różne pasma. Różny wygląd nie oznacza zmiany źródła. Do porównania w czasie wybierz zgodną serię.')}</p>}
  <div className="gallery-grid">{visible.map(i=>{const f=analysis.frames[i],recommended=analysis.selection?.selected_ids.includes(f.id);return <button key={f.id} className={`gallery-frame ${i===b?'active':''}`} aria-pressed={i===b} aria-label={`${t('Pokaż zdjęcie B')}: ${date(f.date)}, ${f.band}, ${f.wavelength_um.toFixed(4)} µm`} onClick={()=>onSelect(i)}>
   <div className="gallery-image"><img src={f.image} alt="" loading="lazy"/>{(i===a||i===b)&&<span>{i===a&&i===b?'A · B':i===a?'A':'B'}</span>}</div>
   <strong>{date(f.date)}</strong><span>{f.band.replace('SPHEREx-','')} · {f.wavelength_um.toFixed(4)} µm</span>{recommended&&<small>{t('Rekomendowana seria')}</small>}
  </button>})}</div>
  {!visible.length&&<p role="status">{t('Brak zgodnej serii w dotychczas przygotowanych zdjęciach. Możesz oglądać wszystkie zdjęcia.')}</p>}
 </section>;
}
