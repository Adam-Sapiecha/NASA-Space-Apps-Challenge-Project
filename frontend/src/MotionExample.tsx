import {assetUrl} from './urls.ts';
import {t,locale,withLanguage} from './i18n.ts';
import {useEffect,useState} from 'react';
import {ArrowRight} from 'lucide-react';
import motion from './motionShowcase.json';

type Props={onInspect:()=>void;onField:()=>void};
export default function MotionExample({onInspect,onField}:Props){
 const [original,setOriginal]=useState(false);
 const [ready,setReady]=useState(false),[failed,setFailed]=useState(false);
 useEffect(()=>{let live=true;Promise.all(motion.frames.map(frame=>new Promise<void>((resolve,reject)=>{const img=new Image();img.onload=()=>resolve();img.onerror=reject;img.src=assetUrl(frame.image)}))).then(()=>{if(live)setReady(true)}).catch(()=>{if(live)setFailed(true)});return()=>{live=false}},[]);
 const time=(i:number)=>motion.frames[i].date.slice(11,19)+' UTC';
 const image=(i:number)=><div className="motion-photo">
  <img src={assetUrl(original?motion.frames[i].original:motion.frames[i].image)} alt={`${t('Obserwacja 3I/ATLAS')}, ${t('14 grudnia 2025')}, ${time(i)}`} width="117" height="117"/>
  {motion.frames.map((frame,j)=><span key={frame.id} className="motion-reference" style={{left:`${100*frame.point.x}%`,top:`${100*frame.point.y}%`}}><span>{j?'B':'A'}</span></span>)}
  <span className="motion-photo-date">{i?'B':'A'} · {time(i)}</span>
 </div>;
 return <section className="motion-example" id="motion-example" aria-labelledby="motion-title">
  <header className="motion-heading"><div><h1 id="motion-title">3I/ATLAS <span>· {Math.round(motion.minutes)} {t('minut między obserwacjami')}</span></h1><p>{t('Obserwuj zmianę położenia między znacznikami A i B.')}</p></div><span className="dataset-label">SPHEREx DR1 · D6</span></header>
  <div className="motion-demo-body">
   <div className="motion-image-column">
    <div className="motion-images motion-side" aria-busy={!ready&&!failed}>
     {image(0)}{image(1)}
     {!ready&&<span className="motion-loading" role={failed?'alert':'status'}>{t(failed?'Nie udało się wczytać pokazu. Otwórz zapisane obserwacje.':'Wczytuję dwie obserwacje…')}</span>}
    </div>
    <p className="motion-date-caption">{t('14 grudnia 2025')} · UTC</p>
   </div>
   <aside className="motion-result">
    <h2>{t('Co pokazuje obraz')}</h2><p>{t('Ten sam fragment nieba w dwóch terminach. Znaczniki pokazują stałe pozycje z efemeryd.')}</p>
    <dl><div><dt>{t('Odstęp czasu')}</dt><dd>{Math.round(motion.minutes)} {t('min')}</dd></div><div><dt>{t('Przesunięcie z efemeryd')}</dt><dd>{motion.predicted_separation_arcmin.toLocaleString(locale(),{maximumFractionDigits:2})}′</dd></div></dl>
    <p className="motion-caution">{t('To pokaz ruchu. Różne pasma i PSF nie pozwalają z tej pary ocenić zmiany jasności komety.')}</p>
    <div className="motion-next-actions">
     <button className="primary" onClick={onInspect}>{t('Otwórz w czasie i pasmach')}<ArrowRight size={15}/></button>
     <button onClick={onField}>{t('Wyszukaj własne współrzędne')}<ArrowRight size={15}/></button>
    </div>
   </aside>
  </div>
  <details className="motion-method"><summary>{t('Wyświetlanie, dane źródłowe i ograniczenia')}</summary>
   <p>{t('Zdjęcia SPHEREx DR1 z 14.12.2025, detektor D6, wspólna siatka współrzędnych nieba. Dla czytelności odjęto osobny, stały poziom tła w każdej klatce i użyto wspólnej skali kontrastu. Nie dodano ani nie przesunięto źródeł. Pozycje A/B pochodzą z efemeryd IRSA MOST; nie są wynikiem automatycznej detekcji.')}</p>
   <label><input type="checkbox" checked={original} onChange={event=>setOriginal(event.target.checked)}/>{t('Pokaż obrazy bez odejmowania poziomu tła')}</label>
   <p>λ A: {motion.frames[0].wavelength_um.toFixed(3)} µm · λ B: {motion.frames[1].wavelength_um.toFixed(3)} µm. {t('To pokaz znanego obiektu, bez nowego odkrycia ani precyzyjnej astrometrii.')}</p>
   <div className="context-actions"><a href="https://irsa.ipac.caltech.edu/data/SPHEREx/docs/comet3iatlas/" target="_blank" rel="noreferrer">{t('Oficjalne obserwacje 3I/ATLAS')}</a><a href={assetUrl('/motion-demo/evidence.json')} download>{t('Raport i pochodzenie danych')}</a>{motion.frames.map((frame,i)=><a key={frame.id} href={assetUrl(frame.fits)} download>FITS {i?'B':'A'}</a>)}<a href={withLanguage('/demo/')}>{t('Zapisana prezentacja')}</a></div>
  </details>
 </section>;
}
