import {t} from './i18n.ts';
import {useEffect,useRef,useState} from 'react';
import {api,date,type Analysis,type Point} from './types';

type Candidate={id:string;name:string;ra:number;dec:number;propagated:boolean;separation_arcsec:number};
type Identification={id:string;status:string;candidates:Candidate[];limitations:string[];truncated:boolean};
type QualityRow={frame_id:string;status:string;snr:number|null;warnings:string[]};
type Quality={id:string;source_id:string;rows:QualityRow[];limitations:string[]};
type Label={id:string;frame_id:string;label:string;reason:string};
const statuses:Record<string,string>={unusable:t('Pomiar nieważny'),review:t('Sprawdź obserwację'),no_rule_warning:t('Brak ostrzeżenia reguł')};
const labels:Record<string,string>={source:t('Wiarygodne źródło'),artifact:t('Artefakt'),blend:t('Zlane źródła'),uncertain:t('Nie da się ocenić')};

function ReviewLabel({id}:{id:string}){
 const [reviewer,setReviewer]=useState(''),[reason,setReason]=useState(''),[saved,setSaved]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const review=async()=>{setBusy(true);setError('');try{await api(`/api/artifacts/labels/${id}/review`,{reviewer,reason});setSaved(true)}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 return <details><summary>{t("Zweryfikuj ocenę do zbioru uczącego")}</summary><p>{t("Najpierw obejrzyj źródło, maski, sąsiadów i inne epoki. Zatwierdzenie jest ręcznym przeglądem, nie automatyczną prawdą referencyjną.")}</p><label>{t("Recenzent")}<input maxLength={100} value={reviewer} onChange={e=>setReviewer(e.target.value)}/></label><label>{t("Uzasadnienie przeglądu")}<textarea maxLength={2000} value={reason} onChange={e=>setReason(e.target.value)}/></label><button disabled={busy||saved||reviewer.trim().length<3||reason.trim().length<3} onClick={()=>void review()}>{t("Zatwierdź przegląd")}</button>{saved&&<p role="status">{t("Przegląd zapisany. Odśwież stan zbioru w panelu uczenia.")}</p>}{error&&<p role="alert">{t(error)}</p>}</details>;
}

function LabelEditor({reportId,frameId,onSaved}:{reportId:string;frameId:string;onSaved:(label:Label)=>void}){
 const [label,setLabel]=useState('uncertain'),[reason,setReason]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const save=async()=>{setBusy(true);setError('');try{onSaved(await api<Label>(`/api/quality/${reportId}/labels`,{frame_id:frameId,label,reason}));setReason('')}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 return <details><summary>{t("Dodaj własną ocenę")}</summary><label>{t("Ocena")}<select value={label} onChange={e=>setLabel(e.target.value)}>{Object.entries(labels).map(([value,text])=><option key={value} value={value}>{t(text)}</option>)}</select></label><label>{t("Uzasadnienie")}<textarea maxLength={2000} value={reason} onChange={e=>setReason(e.target.value)}/></label><button disabled={busy||reason.trim().length<3} onClick={()=>void save()}>{t("Zapisz ocenę")}</button>{error&&<p role="alert">{t(error)}</p>}</details>;
}

export default function SourceAssessment({expert,analysis,point,frameId,hasPoint}:{expert:boolean;analysis:Analysis;point:Point;frameId:string;hasPoint:boolean}){
 const [identity,setIdentity]=useState<Identification|null>(null),[quality,setQuality]=useState<Quality|null>(null),[saved,setSaved]=useState<Label[]>([]),[radius,setRadius]=useState(12.4),[busy,setBusy]=useState(''),[error,setError]=useState('');
 const generation=useRef(0);
 useEffect(()=>{generation.current++;setIdentity(null);setQuality(null);setSaved([]);setError('');setBusy('');return()=>{generation.current++}},[analysis.id,point.x,point.y,frameId,hasPoint]);
 const run=async(kind:'identification'|'quality')=>{
  const token=++generation.current;setBusy(kind);setError('');
  try{
   if(kind==='identification'){
    const result=await api<Identification>(`/api/analyses/${analysis.id}/identification`,{...point,frame_id:frameId,radius_arcsec:radius});
    if(token===generation.current)setIdentity(result);
   }else{
    const result=await api<Quality>(`/api/analyses/${analysis.id}/quality`,{...point,radius_arcsec:12.4});
    if(token===generation.current){setQuality(result);setSaved([])}
    const history=await api<Label[]>(`/api/quality/${result.id}/labels`);
    if(token===generation.current)setSaved(history);
   }
  }catch(e){if(token===generation.current)setError((e as Error).message)}finally{if(token===generation.current)setBusy('')}
 };
 return <section className="spectral-section" aria-labelledby="source-assessment-title"><h2 id="source-assessment-title">{t("Źródło i jakość obserwacji")}</h2>
  <p>{hasPoint?t('Sprawdź obiekty katalogowe w pobliżu zaznaczonego punktu oraz jakość jego pomiarów.'):t('Najpierw zaznacz punkt na zdjęciu.')}</p>
  <div className="context-actions"><label hidden={!expert}>{t("Promień szukania w Gaia (arcsec)")}<input type="number" min="1" max="60" step=".1" value={radius} onChange={e=>{generation.current++;setBusy('');setRadius(Number(e.target.value));setIdentity(null)}}/></label><button disabled={!hasPoint||!!busy||!Number.isFinite(radius)||radius<1||radius>60} onClick={()=>void run('identification')}>{t("Co to może być?")}</button><button disabled={!hasPoint||!!busy} onClick={()=>void run('quality')}>{t("Sprawdź jakość punktu")}</button></div>
  {busy&&<p role="status">{busy==='identification'?t('Pobieranie katalogu Gaia…'):t('Pomiar natywnych FITS i kontrola jakości…')}</p>}{error&&<p role="alert" className="notice error">{t(error)}</p>}
  {identity&&<div><h3>{t("Możliwe odpowiedniki katalogowe")}</h3><p>{t("Pozycje odniesiono do ekspozycji")} {date(analysis.frames.find(f=>f.id===frameId)!.date)}{t(". Kolejność według odległości od kliknięcia; identyfikacja niepotwierdzona.")}</p>{identity.candidates.length===0?<p>{t("Brak dopasowania w wybranym promieniu. Nie oznacza to odkrycia nowego obiektu.")}</p>:<ul>{identity.candidates.map(c=><li key={c.id}><a target="_blank" rel="noreferrer" href={`https://simbad.cds.unistra.fr/simbad/sim-id?Ident=${encodeURIComponent(c.name)}`}>{t(c.name)}</a> · {c.separation_arcsec.toFixed(2)}″ · RA {c.ra.toFixed(6)}°, Dec {c.dec.toFixed(6)}° · {c.propagated?t('ruch własny uwzględniony'):t('brak ruchu własnego: pozycja katalogowa 2016.0')}</li>)}</ul>}{identity.truncated&&<p>{t("Osiągnięto limit katalogu; lista może być niepełna.")}</p>}<p>{t("Typ obiektu nie jest ustalany w tej wersji. Odnośnik otwiera wyszukiwanie identyfikatora w SIMBAD.")}</p><a href={`/api/identifications/${identity.id}`}>{t("Pobierz raport identyfikacji JSON")}</a><details><summary>{t("Metoda i ograniczenia")}</summary><ul>{identity.limitations.map(s=><li key={s}>{s}</li>)}</ul></details></div>}
  {quality&&<div><h3>{t("Jakość pomiarów zaznaczonego punktu")}</h3><p>{t("Ocena regułowa; klasyfikator ML nie jest włączony. Twoje oceny są zapisywane jako nieweryfikowane adnotacje.")}</p>{quality.rows.map(row=><div key={row.frame_id} className="notice"><div><strong>{date(analysis.frames.find(f=>f.id===row.frame_id)!.date)} · {t(statuses[row.status])}</strong><p>{t("SNR apertury:")} {row.snr===null?t('brak'):row.snr.toFixed(2)}</p>{row.warnings.length>0&&<ul>{row.warnings.map(s=><li key={s}>{s}</li>)}</ul>}<LabelEditor reportId={quality.id} frameId={row.frame_id} onSaved={value=>setSaved(v=>[...v,value])}/>{saved.filter(l=>l.frame_id===row.frame_id).map(l=><div key={l.id}><p>{t("Zapisana ocena:")} {labels[l.label]} — {l.reason}</p><ReviewLabel id={l.id}/></div>)}</div></div>)}<div className="context-actions"><a href={`/api/quality/${quality.id}`}>{t("Pobierz jakość JSON")}</a><a href={`/api/quality/${quality.id}/labels`}>{t("Pobierz oceny JSON")}</a></div><details><summary>{t("Ograniczenia")}</summary><ul>{quality.limitations.map(s=><li key={s}>{s}</li>)}</ul></details></div>}
 </section>;
}
