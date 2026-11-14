import {t} from './i18n.ts';
import {useEffect,useState} from 'react';
import {LoaderCircle,Pause,Play} from 'lucide-react';
import Viewer from './Viewer';
import {bandLabel} from './bandLabels';
import {api,type Analysis} from './types';
import {spectralFrames,wavelengthColor} from './spectral';
import showcase from './showcase.json';

export default function GuidedBands({language}:{language:'pl'|'en'}){
 const [analysis,setAnalysis]=useState<Analysis|null>(null),[index,setIndex]=useState(0),[playing,setPlaying]=useState(false),[error,setError]=useState('');
 const rows=analysis?spectralFrames(analysis.frames,null):[];
 useEffect(()=>{let active=true;api<Analysis>(`/api/analyses/${showcase.spectral_analysis_id}`).then(value=>{if(active)setAnalysis(value)}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[]);
 useEffect(()=>{if(!playing||rows.length<2)return;const timer=setInterval(()=>setIndex(i=>(i+1)%rows.length),1000);return()=>clearInterval(timer)},[playing,rows.length]);
 const pl=language==='pl',row=rows[index],frame=row&&analysis?.frames[row.index];
 if(error)return <p role="alert">{error}</p>;
 if(!analysis)return <p className="guided-loading" role="status"><LoaderCircle className="spin" size={16}/>{pl?'Wczytuję zapisane pasma…':'Loading saved wavelengths…'}</p>;
 if(!row||!frame)return <p role="status">{pl?'Brak danych o długościach fal.':'Wavelength information is unavailable.'}</p>;
 return <section className="guided-bands" aria-label={pl?'Przegląd pasm':'Explore wavelengths'}>
  <div className="guided-band-heading"><div><h2>{pl?'Drugi przykład: różne pasma':'Another example: different wavelengths'}</h2><p>{pl?'Przesuwaj suwak. Zmieniasz zakres podczerwieni, nie czas.':'Move the slider. You are changing infrared wavelength, not time.'}</p></div><button disabled={rows.length<2} onClick={()=>setPlaying(v=>!v)}>{playing?<Pause size={16}/>:<Play size={16}/>} {playing?(pl?t('Zatrzymaj'):'Pause'):(pl?t('Odtwarzaj pasma'):'Play wavelengths')}</button></div>
  <div className="guided-band-readout"><strong style={{color:wavelengthColor(row.wavelength)}}>{bandLabel(row.wavelength,language)}</strong><span>{new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(frame.date)?frame.date:frame.date+'Z').toLocaleString(pl?'pl-PL':'en-GB',{timeZone:'UTC',day:'numeric',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})} UTC</span><span>{index+1} / {rows.length}</span></div>
  <Viewer interactive={false} label={pl?'Obraz SPHEREx w wybranym paśmie podczerwieni.':'SPHEREx image at the selected infrared wavelength.'} interactionHelp={pl?'Użyj suwaka długości fali pod obrazem.':'Use the wavelength slider below the image.'} frames={analysis.frames} a={row.index} b={row.index} mode="spectral" radius={0} pinned={false} point={{x:.5,y:.5}} onPoint={()=>{}} onPick={()=>{}} anchors={[]} zoom={1} routeStep={0} panMode={false} showQuality={false} animating={false} interval={1000} spectralTint={wavelengthColor(row.wavelength)}/>
  <label className="guided-band-slider">{pl?t('Wybierz pasmo'):'Choose a band'}<input type="range" min="0" max={rows.length-1} step="1" value={index} aria-label={pl?'Wybierz pasmo podczerwieni':'Choose an infrared wavelength'} aria-valuetext={bandLabel(row.wavelength,language)} onChange={e=>{setPlaying(false);setIndex(Number(e.target.value))}}/></label>
  <p className="guided-band-note">{pl?'Umowne kolory. Długość fali podana dla centrum pola; obserwacje pochodzą z różnych chwil. Braków nie uzupełniamy.':'Illustrative colours. Wavelength is given at the field centre; observations were taken at different times. Missing data are not filled in.'}</p>
 </section>;
}
