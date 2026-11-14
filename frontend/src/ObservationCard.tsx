import {t,getLanguage} from './i18n.ts';
import {useEffect,useState} from 'react';
import {api,type Analysis,type Anchor,type Point} from './types';

export type NoteView={frame_ids:string[];point:Point|null;anchors:Anchor[];route_checks:Record<string,'fits'|'misses'|'unknown'>;mode:'side'|'lens'|'blink'|'route'|'series';quality:'all'|'valid';range_mode:'standard'|'faint'|'full';series_only:boolean};
type Note=NoteView & {id:string;analysis_id:string;kind:'motion'|'brightness'|'uncertain';text:string;measurement_id?:string|null};
export default function ObservationCard({analysis,view,onRestore}:{analysis:Analysis;view:NoteView;onRestore:(note:NoteView)=>void}){
 const [kind,setKind]=useState<Note['kind']>('uncertain'),[text,setText]=useState(''),[saved,setSaved]=useState<Note|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const snapshot=JSON.stringify({...view,kind,text});
 const [savedSnapshot,setSavedSnapshot]=useState('');
 useEffect(()=>{
  const id=new URLSearchParams(location.search).get('note');if(!id)return;
  let alive=true;
  api<Note>(`/api/notes/${encodeURIComponent(id)}`).then(note=>{
   if(!alive)return;
   if(note.analysis_id!==analysis.id)throw new Error(t('Ta karta należy do innej analizy.'));
   setKind(note.kind);setText(note.text);setSaved(note);onRestore(note);
   const {frame_ids,point,anchors,route_checks,mode,quality,range_mode,series_only,kind,text}=note;
   setSavedSnapshot(JSON.stringify({frame_ids,point,anchors,route_checks,mode,quality,range_mode,series_only,kind,text}));
  }).catch(e=>{if(alive)setError(e.message)});
  return()=>{alive=false};
 },[analysis.id]);
 const save=async()=>{
  setBusy(true);setError('');const captured=snapshot;
  try{
   const measurement_id=new URLSearchParams(location.search).get('measurement')??(JSON.stringify(saved?.point)===JSON.stringify(view.point)?saved?.measurement_id:null);
   const note=await api<Note>(`/api/analyses/${analysis.id}/notes`,{...JSON.parse(captured),measurement_id});setSaved(note);setSavedSnapshot(captured);
   const url=new URL(location.href);url.search='';url.searchParams.set('lang',getLanguage());url.searchParams.set('analysis',analysis.id);url.searchParams.set('note',note.id);history.replaceState(null,'',url);
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 };
 const copy=async()=>{
  if(!saved)return;
  const url=new URL(location.pathname,location.origin);url.searchParams.set('analysis',analysis.id);url.searchParams.set('note',saved.id);
  try{await navigator.clipboard.writeText(url.href)}catch{setError(t('Nie udało się skopiować linku. Użyj odnośnika do zapisanej karty poniżej.'))}
 };
 return <section className="observation-card" aria-labelledby="note-title">
  <h3 id="note-title">{t("Karta podejrzenia")}</h3><p>{t("Zapisz wybrane zdjęcia, punkt lub hipotezę trasy oraz własne uzasadnienie.")}</p>
  <div className="context-actions"><label>{t("Co sprawdzasz?")}<select value={kind} onChange={e=>setKind(e.target.value as Note['kind'])}><option value="uncertain">{t("Nie wiem jeszcze")}</option><option value="motion">{t("Możliwe przesunięcie")}</option><option value="brightness">{t("Możliwa zmiana jasności")}</option></select></label></div>
  <label>{t("Notatka")}<textarea rows={3} maxLength={3000} value={text} onChange={e=>setText(e.target.value)} placeholder={t("Co zauważasz? Co sprawdzono, a czego nie udało się rozstrzygnąć?")}/></label>
  <div className="context-actions"><button disabled={busy||!view.point&&view.anchors.length!==2} onClick={save}>{busy?t('Zapisywanie…'):t('Zapisz kartę na serwerze')}</button>{saved&&<><button onClick={copy}>{t("Kopiuj link do zapisanej karty")}</button><a href={`/?analysis=${analysis.id}&note=${saved.id}`}>{t("Otwórz zapisaną kartę")}</a><a href={`/api/notes/${saved.id}`} download="observation-note.json">{t("Eksport JSON")}</a></>}</div>
  {!view.point&&view.anchors.length!==2&&<p>{t("Najpierw wskaż punkt lub narysuj trasę.")}</p>}
  {saved&&<p role="status">{snapshot===savedSnapshot?'Karta zapisana.':t('Bieżący widok lub notatka różnią się od zapisanej karty. Zapisz nową wersję, aby je udostępnić.')}</p>}
  {saved?.measurement_id&&<p><a href={`/api/measurements/${saved.measurement_id}`}>{t("Zapisany pomiar punktu (JSON)")}</a>{saved.frame_ids[0]!==saved.frame_ids[1]&&<> · <a href={`/api/measurements/${saved.measurement_id}/change-diagnostics?a=${encodeURIComponent(saved.frame_ids[0])}&b=${encodeURIComponent(saved.frame_ids[1])}`}>{t("Diagnostyka zapisanej pary (JSON)")}</a></>}</p>}
  {saved&&<div className="context-actions"><a href={`/api/notes/${saved.id}/evidence.html`} download>{t("Pobierz kartę dowodową (HTML, EN, offline)")}</a><a href={`/api/notes/${saved.id}/evidence`} download="spherex-evidence.json">{t("Pełne dowody i pochodzenie danych (JSON)")}</a></div>}
  {error&&<p role="alert">{t(error)}</p>}
  <small>{t("Obliczenia są zapisywane automatycznie na tym serwerze. Kartę i notatkę zapisujesz przyciskiem. Link wymaga dostępu do serwera; oceny użytkownika nie potwierdzają odkrycia.")}</small>
 </section>;
}
