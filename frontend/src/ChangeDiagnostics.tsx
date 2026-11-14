import {t,locale} from './i18n.ts';
import {useEffect,useRef,useState} from 'react';
import {api,date,type Analysis,type Point} from './types';

type Report={summary:string;status:'blocked'|'requires_validation';radius_arcsec:number;checks:{name:string;status:'checked'|'blocked'|'caution'|'unknown';detail:string;action:string}[];metrics:null|{delta_mjy:number;random_error_mjy:number;flux_a_mjy:number;flux_b_mjy:number;days:number};limitations:string[]};
const labels={checked:t('Sprawdzono'),blocked:t('Przeszkoda'),caution:t('Uwaga'),unknown:t('Niezweryfikowane')};
const number=(n:number)=>n.toLocaleString(locale(),{maximumSignificantDigits:4});

// Parent keys this component by analysis, point and selected frames: old results
// cannot describe a newly selected pair, including while a request is running.
export default function ChangeDiagnostics({expert,analysis,point,a,b,hasPoint,onStart,onFindPair}:{expert:boolean;analysis:Analysis;point:Point;a:number;b:number;hasPoint:boolean;onStart:()=>void;onFindPair:()=>void}){
 const [radius,setRadius]=useState(12.4),[busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<{report:Report;url:string}|null>(null);
 const alive=useRef(true);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false}},[]);
 const inspect=async()=>{
  onStart();setBusy(true);setError('');setResult(null);
  try{
   const measurement=await api<{id:string}>(`/api/analyses/${analysis.id}/measurements`,{...point,radius_arcsec:radius});
   if(!alive.current)return;
   const params=new URLSearchParams({a:analysis.frames[a].id,b:analysis.frames[b].id});
   const url=`/api/measurements/${measurement.id}/change-diagnostics?${params}`;
   const report=await api<Report>(url);
   if(alive.current){setResult({report,url});const address=new URL(location.href);address.searchParams.set('measurement',measurement.id);history.replaceState(null,'',address)}
  }catch(e){if(alive.current)setError((e as Error).message)}
  finally{if(alive.current)setBusy(false)}
 };
 return <section className="change-diagnostics" aria-labelledby="change-title">
  <div className="change-heading"><div><h3 id="change-title">{t("Sprawdź możliwe przyczyny różnicy")}</h3><p>{t("Porównaj jasność w stałej pozycji A i B. To sprawdzenie ograniczeń, bez potwierdzania zmienności.")}</p></div><span className="change-tag">{t("Jasność punktu")}</span></div>
  <p className="muted">A: {date(analysis.frames[a].date)} · B: {date(analysis.frames[b].date)}{t(". Ta sama pozycja na niebie w obu obrazach.")}</p>
  <div className="context-actions"><label hidden={!expert}>{t("Promień apertury (arcsec)")}<input type="number" min="6.2" max="30" step=".1" value={radius} disabled={busy} onChange={e=>{setRadius(Number(e.target.value));setResult(null);setError('')}}/></label><button className="primary" disabled={busy||!hasPoint||a===b||!Number.isFinite(radius)||radius<6.2||radius>30} onClick={inspect}>{busy?t('Sprawdzam natywne pomiary…'):t('Sprawdź różnicę A i B')}</button></div>
  {!hasPoint&&<p>{t("Kliknij źródło na zdjęciu, aby przypiąć punkt do sprawdzenia.")}</p>}{a===b&&<p>{t("Wybierz dwa różne zdjęcia.")}</p>}
  {busy&&<p role="status">{t("Odczytuję FITS i mierzę aperturę oraz otaczające tło. Pierwszy pomiar może potrwać dłużej.")}</p>}
  {error&&<p className="notice error" role="alert">{t(error)}</p>}
  {result&&<><p className={`change-verdict ${result.report.status}`} role="status">{t(result.report.summary)}</p>
   <div className="next-step"><strong>{t("Następny krok")}</strong><p>{t(result.report.checks.find(c=>c.status==='blocked')?.action??t('Sprawdź centrowanie i kształt źródła, a potem powtórz porównanie w kolejnej epoce o zbliżonym paśmie. Błąd losowy nie obejmuje tych ograniczeń.'))}</p><button onClick={onFindPair}>{t("Znajdź parę o zbliżonych pasmach w tym punkcie")}</button></div>
   {result.report.metrics&&<div className="change-metrics"><div><span>{t("Różnica strumienia A−B")}</span><strong>{number(result.report.metrics.delta_mjy)} ± {number(result.report.metrics.random_error_mjy)} mJy</strong><small>{t("Błąd losowy, bez systematyki i korekty PSF")}</small></div><div><span>{t("Strumienie apertury")}</span><strong>A: {number(result.report.metrics.flux_a_mjy)} · B: {number(result.report.metrics.flux_b_mjy)} mJy</strong><small>{t("Promień:")} {result.report.radius_arcsec}{t("″ · po odjęciu lokalnego tła")}</small></div></div>}
   <p className="muted">{t("Wartość różnicy nie jest potwierdzeniem zmienności. Przy przeszkodach w porównaniu nie interpretuj jej jako zmiany źródła.")}</p>
   <div className="change-checks">{result.report.checks.map(c=><article key={t(c.name)} className={`change-check ${c.status}`}><div><h4>{t(c.name)}</h4><span>{t(labels[c.status])}</span></div><p>{t(c.detail)}</p><p className="change-action">{t(c.action)}</p></article>)}</div>
   <details><summary>{t("Założenia i ograniczenia")}</summary><ul>{result.report.limitations.map(l=><li key={t(l)}>{t(l)}</li>)}</ul></details><a className="change-export" href={result.url} download="change-diagnostics.json">{t("Pobierz raport JSON")}</a>
  </>}
 </section>;
}
