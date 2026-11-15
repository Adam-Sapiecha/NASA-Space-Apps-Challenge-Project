import {LoaderCircle,Search} from 'lucide-react';
import {t} from './i18n';
import SkyContext from './SkyContext';
import type {FieldMethod} from './workspace';

type Target={name:string;ra:string;dec:string;source:string};
type Props={method:FieldMethod;onMethod:(method:FieldMethod)=>void;targets:Target[];ra:string;dec:string;fov:number;collection:string;busy:boolean;onField:(ra:string,dec:string)=>void;onFov:(value:number)=>void;onCollection:(value:string)=>void;onSearch:()=>void};

export default function FieldSelection(p:Props){
 const target=p.targets.find(row=>Math.abs(Number(row.ra)-Number(p.ra))<1e-7&&Math.abs(Number(row.dec)-Number(p.dec))<1e-7);
 const ready=!!p.ra.trim()&&!!p.dec.trim()&&(p.method!=='object'||!!target);
 return <section className="field-selection" id="field-search" aria-label={t('Wybór własnego pola')}>
  <div className="field-methods" role="group" aria-label={t('Sposób wyboru pola')}>
   {([{id:'object',label:'Obiekt z listy'},{id:'map',label:'Mapa'},{id:'coordinates',label:'Współrzędne'}] as const).map(method=><button type="button" key={method.id} disabled={p.busy} aria-pressed={p.method===method.id} onClick={()=>p.onMethod(method.id)}>{t(method.label)}</button>)}
  </div>
  {p.method==='map'&&<SkyContext pickerOnly expert={false} ra={p.ra} dec={p.dec} fov={p.fov} collection={p.collection} analysis={null} onField={(ra,dec)=>{if(!p.busy)p.onField(ra,dec)}}/>}
  <form onSubmit={event=>{event.preventDefault();if(ready)p.onSearch()}}><fieldset className="field-inputs" disabled={p.busy}>
   {p.method==='object'&&<label className="field-object">{t('Obiekt z listy')}<select required aria-label={t('Wybierz obiekt')} value={target?.name??''} onChange={event=>{const row=p.targets.find(row=>row.name===event.target.value);if(row)p.onField(row.ra,row.dec)}}><option value="" disabled>{t('Wybierz obiekt…')}</option>{p.targets.map(row=><option key={row.name} value={row.name}>{row.name}</option>)}</select></label>}
   {p.method==='coordinates'&&<div className="field-coordinate-entry"><label>RA<input required aria-label={t('Rektascensja')} value={p.ra} onChange={event=>p.onField(event.target.value,p.dec)} placeholder="269.446268 / 17:57:00" spellCheck={false}/></label><label>Dec<input required aria-label={t('Deklinacja')} value={p.dec} onChange={event=>p.onField(p.ra,event.target.value)} placeholder="4.768204 / +04:46:05" spellCheck={false}/></label><small>{t('RA: stopnie 0–360 lub hh:mm:ss. Dec: stopnie −90 do +90 lub ±dd:mm:ss. Układ ICRS.')}</small></div>}
   {p.method!=='coordinates'&&<p className="field-position" role="status">{ready?(p.method==='object'?t('Wybrano obiekt:')+' '+target?.name:t('Środek pola jest ustawiony. Możesz wyszukać zdjęcia lub zmienić obszar na mapie.')):t(p.method==='map'?'Wskaż środek i kliknij „Wybierz ten obszar”.':'Wybierz obiekt, którego okolicę chcesz obejrzeć.')}</p>}
   <div className="field-search-action"><label>{t('Rozmiar pola (′)')}<input aria-label={t('Rozmiar pola (′)')} type="number" min="2" max="30" step="1" required value={p.fov} onChange={event=>p.onFov(Number(event.target.value))}/></label><button type="submit" className="primary" disabled={!ready||p.busy}>{p.busy?<LoaderCircle size={16} className="spin"/>:<Search size={16}/>} {t('Wyszukaj obrazy')}</button></div>
   <details className="field-technical"><summary>{t('Ustawienia techniczne i źródło pozycji')}</summary><label>{t('Wydanie danych')}<select value={p.collection} onChange={event=>p.onCollection(event.target.value)}><option value="spherex_dr1">DR1</option><option value="spherex_qr3">QR3</option></select></label><p>{t('Pozycje obiektów z listy są katalogowymi przybliżeniami na J2026.0, bez paralaksy ani potwierdzenia detekcji. Własne współrzędne pozostają stałe.')}</p>{target&&<a href={target.source} target="_blank" rel="noreferrer">{t('Źródło pozycji i epoki katalogowej')}</a>}</details>
  </fieldset></form>
 </section>;
}
