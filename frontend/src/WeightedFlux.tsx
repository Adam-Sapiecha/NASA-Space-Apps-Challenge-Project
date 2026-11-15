import {apiUrl} from './urls.ts';
import {t} from './i18n.ts';
import {useEffect,useRef,useState} from 'react';
import {api,date} from './types';

type Row={id:string;date:string;valid:boolean;wavelength_um:number};
type Result={id:string;flux_mjy:number;random_error_mjy:number;frame_ids:string[];weights:number[];limitations:string[]};
export default function WeightedFlux({reportId,rows}:{reportId:string;rows:Row[]}){
 const [selected,setSelected]=useState<string[]>([]),[hours,setHours]=useState(24),[result,setResult]=useState<Result|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const generation=useRef(0);
 useEffect(()=>()=>{generation.current++},[]);
 const invalidate=()=>{generation.current++;setResult(null);setError('');setBusy(false)};
 const combine=async()=>{const token=++generation.current;setResult(null);setError('');setBusy(true);try{const value=await api<Result>(`/api/irsa/results/${reportId}/weighted-flux`,{frame_ids:selected,max_hours:hours});if(token===generation.current)setResult(value)}catch(e){if(token===generation.current)setError((e as Error).message)}finally{if(token===generation.current)setBusy(false)}};
 return <details><summary>{t("Średnia ważona pomiarów ePSF")}</summary><p>{t("Eksperymentalny pomiar stałego źródła. Wybierz bliskie terminy i zbliżone lokalne pasma. Wagi wynikają z błędów losowych, bez ML. Sprawdź jakość dopasowania i sąsiadów w tabeli powyżej.")}</p>
 {rows.filter(r=>r.valid).map(r=><label key={r.id} className="check-label"><input type="checkbox" checked={selected.includes(r.id)} onChange={()=>{invalidate();setSelected(v=>v.includes(r.id)?v.filter(id=>id!==r.id):[...v,r.id])}}/>{date(r.date)} · {r.wavelength_um.toFixed(4)} μm</label>)}
 <label>{t("Maksymalne okno czasu (h)")}<input type="number" min=".01" max="48" step=".1" value={hours} onChange={e=>{invalidate();setHours(Number(e.target.value))}}/></label><button disabled={busy||selected.length<2||!Number.isFinite(hours)||hours<=0||hours>48} onClick={()=>void combine()}>{t("Oblicz średnią pomiarów")}</button>
 {busy&&<p role="status">{t("Obliczanie…")}</p>}{error&&<p role="alert">{error}</p>}{result&&<><p>{t("Strumień:")} {result.flux_mjy.toPrecision(5)} ± {result.random_error_mjy.toPrecision(3)}  {t("mJy (błąd losowy).")}</p><ul>{result.frame_ids.map((id,i)=><li key={id}>{date(rows.find(r=>r.id===id)!.date)}{t(": waga")} {(result.weights[i]*100).toFixed(1)}%</li>)}</ul><a href={apiUrl(`/api/weighted-flux/${result.id}`)}>{t("Pobierz wynik JSON")}</a><ul>{result.limitations.map(s=><li key={s}>{s}</li>)}</ul></>}
 </details>;
}
