import {useEffect,useMemo,useRef,useState} from 'react';
import {ChevronLeft,ChevronRight,Pause,Play} from 'lucide-react';
import {getLanguage} from './i18n';
import {date,type Analysis} from './types';
import {observationCatalogue} from './comparison';
import {bandsOnDay,bandAtTime,fieldTimeline,skippedDays} from './fieldNavigation';

export default function FieldExplorer({analysis,currentId,busy,active,pauseSignal,onApply,onState,onPlaying}:{analysis:Analysis;currentId:string;busy:boolean;active:boolean;pauseSignal:number;onApply:(id:string)=>Promise<boolean>;onState:(id:string|null,time:string)=>void;onPlaying:(playing:boolean)=>void}){
 const pl=getLanguage()==='pl',say=(a:string,b:string)=>pl?a:b;
 const [includeUnprepared,setIncludeUnprepared]=useState(false);
 const rows=useMemo(()=>observationCatalogue(analysis),[analysis]);
 const [wanted,setWanted]=useState(currentId),[playing,setPlaying]=useState(false),[failed,setFailed]=useState(false),[retry,setRetry]=useState(0),[bandTimeChanged,setBandTimeChanged]=useState(false);
 const selected=rows.find(row=>row.id===wanted)??rows.find(row=>row.id===currentId)??rows[0];
 const timeline=useMemo(()=>fieldTimeline(rows,selected?.band??'',!includeUnprepared,selected?.id),[rows,selected?.band,selected?.id,includeUnprepared]);
 const bands=useMemo(()=>selected?bandsOnDay(rows,selected.mjd):[],[rows,selected?.mjd]);
 const skipped=useMemo(()=>skippedDays(rows,selected?.band??''),[rows,selected?.band]);
 const index=timeline.findIndex(row=>row.id===selected?.id),bandIndex=bands.findIndex(group=>group.band===selected?.band);
 const timeLabel=selected?date(selected.date):'';
 const lastCurrent=useRef(currentId),apply=useRef(onApply),state=useRef(onState),notifyPlaying=useRef(onPlaying);
 apply.current=onApply;state.current=onState;notifyPlaying.current=onPlaying;
 useEffect(()=>{if(lastCurrent.current!==currentId){lastCurrent.current=currentId;if(currentId!==wanted){setPlaying(false);setBandTimeChanged(false)}setWanted(currentId);setFailed(false)}},[currentId]);
 useEffect(()=>{state.current(selected?.id??null,timeLabel)},[selected?.id,timeLabel]);
 useEffect(()=>{notifyPlaying.current(playing);return()=>notifyPlaying.current(false)},[playing]);
 useEffect(()=>{if(!active)setPlaying(false)},[active]);
 useEffect(()=>{setPlaying(false)},[pauseSignal]);
 const attempted=useRef('');
 useEffect(()=>{
  if(!active||!selected||selected.id===currentId||busy)return;
  const key=analysis.search.id+':'+selected.id+':'+retry;if(attempted.current===key)return;
  const request=async()=>{attempted.current=key;setFailed(false);const success=await apply.current(selected.id);if(!success){setFailed(true);setPlaying(false)}};
  if(selected.ready){void request();return}
  const timer=setTimeout(()=>void request(),550);
  return()=>clearTimeout(timer);
 },[active,selected?.id,currentId,busy,analysis.search.id,retry]);
 const move=(next:number,manual=true)=>{
  const choice=timeline[Math.max(0,Math.min(timeline.length-1,next))];if(!choice)return;
  if(manual)setPlaying(false);if(choice.id!==wanted)attempted.current='';setWanted(choice.id);setFailed(false);setBandTimeChanged(false);
 };
 const moveRef=useRef(move);moveRef.current=move;
 useEffect(()=>{
  if(!active||!playing||busy||!selected||currentId!==selected.id)return;
  const timer=setTimeout(()=>{if(index>=timeline.length-1)setPlaying(false);else moveRef.current(index+1,false)},1100);
  return()=>clearTimeout(timer);
 },[active,playing,busy,selected?.id,currentId,index,timeline.length]);
 const chooseBand=(band:string)=>{
  if(!selected)return;
  const choice=bandAtTime(rows,band,selected.mjd,!includeUnprepared);if(!choice)return;
  setPlaying(false);if(choice.id!==wanted)attempted.current='';setBandTimeChanged(Math.abs(choice.mjd-selected.mjd)>1/86400);setWanted(choice.id);setFailed(false);
 };
 if(!selected)return null;
 const waiting=selected.id!==currentId,detector=selected.band.replace('SPHEREx-','');
 const localWave=selected.wavelength_um===null?say('lokalna λ po pobraniu','local λ after download'):selected.wavelength_um.toFixed(4)+' µm';
 const bandLabel=(group:typeof bands[number])=>group.band.replace('SPHEREx-','')+' · '+group.min.toFixed(2)+'–'+group.max.toFixed(2)+' µm';
 return <section className="field-explorer" aria-label={say('Czas i pasmo pola','Field time and wavelength')}>
  <div className="explorer-row">
   <strong>{say('Czas','Time')}</strong>
   <button disabled={busy||timeline.length<2} onClick={()=>{if(!playing&&index===timeline.length-1)move(0,false);setPlaying(value=>!value)}} aria-label={say(playing?'Zatrzymaj czas':'Odtwarzaj czas',playing?'Pause time':'Play time')}>{playing?<Pause size={17}/>:<Play size={17}/>}</button>
   <button disabled={busy||index<=0} aria-label={say('Poprzedni termin','Previous time')} onClick={()=>move(index-1)}><ChevronLeft size={18}/></button>
   <input type="range" min="0" max={Math.max(0,timeline.length-1)} value={Math.max(0,index)} disabled={busy||timeline.length<2} aria-label={say('Czas obserwacji','Observation time')} aria-valuetext={timeLabel+' UTC'} onChange={event=>move(Number(event.target.value))}/>
   <button disabled={busy||index>=timeline.length-1} aria-label={say('Następny termin','Next time')} onClick={()=>move(index+1)}><ChevronRight size={18}/></button>
   <select aria-label={say('Wybierz termin','Choose observation time')} value={selected.id} disabled={busy} onChange={event=>move(timeline.findIndex(row=>row.id===event.target.value))}>{timeline.map(row=><option value={row.id} key={row.id}>{date(row.date)} UTC{row.ready?' · '+say('gotowe','ready'):''}</option>)}</select>
   <span>{index+1} / {timeline.length} · {detector}</span>
  </div>
  <label className="check-label archive-toggle"><input type="checkbox" checked={includeUnprepared} disabled={busy} onChange={event=>{setPlaying(false);setIncludeUnprepared(event.target.checked)}}/>{say('Uwzględnij zdjęcia do pobrania','Include images that need downloading')}</label>
  <p className="explorer-availability">{say((includeUnprepared?'Wszystkie terminy ':'Gotowe terminy ')+detector+'. Pominięte dni bez tego detektora: '+skipped+'.',(includeUnprepared?'All ':'Prepared ')+detector+' observations. Days without this detector skipped: '+skipped+'.')}</p>
  <div className="explorer-row">
   <strong>{say('Pasmo','Wavelength')}</strong>
   <input type="range" min="0" max={Math.max(0,bands.length-1)} value={Math.max(0,bandIndex)} disabled={busy||bands.length<2} aria-label={say('Pasmo w wybranym dniu','Wavelength on the selected day')} aria-valuetext={bands[bandIndex]?bandLabel(bands[bandIndex]):detector} onChange={event=>chooseBand(bands[Number(event.target.value)].band)}/>
   <select value={selected.band} aria-label={say('Wybierz pasmo w tym dniu','Choose wavelength on this day')} disabled={busy||bands.length<2} onChange={event=>chooseBand(event.target.value)}>{bands.map(group=><option key={group.band} value={group.band}>{bandLabel(group)}</option>)}</select>
  </div>
  {bandTimeChanged&&<p className="explorer-availability" role="status">{say('Wybrano dostępną obserwację tego pasma: ','Selected an available observation in this band: ')}{timeLabel} UTC.</p>}
  <div className="explorer-status" role="status">{failed?<>{say('Nie udało się przygotować obserwacji.','The observation could not be prepared.')} <button onClick={()=>setRetry(value=>value+1)}>{say('Ponów','Retry')}</button></>:waiting?say('Przygotowuję wybrany termin i pasmo…','Preparing the selected time and wavelength…'):say('Wyświetlono: ','Showing: ')+timeLabel+' UTC · '+detector+' · '+localWave}</div>
  <details className="field-data-note"><summary>{say('O czasie i pasmach','About time and wavelength')}</summary><small>{say('Domyślnie przewijasz tylko gotowe zdjęcia, bez pobierania FITS. Dodatkowe terminy włączysz opcją powyżej. Czas wybiera ekspozycje z godziną, także z jednego dnia. Odtwarzanie zachowuje detektor i pomija dni bez niego. Pasmo wybiera detektor dostępny w tym dniu, z najbliższą rzeczywistą godziną. Zakresy detektorów są stałe; lokalna λ jest podana przy obrazie. Ten sam detektor nie gwarantuje identycznej długości fali.','By default you browse prepared images without downloading FITS. Enable additional times using the option above. Time selects exposures with timestamps, including within one day. Playback keeps the detector and skips days without it. Wavelength selects an available detector on that day at the nearest actual time. Detector ranges stay fixed; local λ is shown with the image. The same detector does not guarantee an identical wavelength.')}</small></details>
 </section>;
}
