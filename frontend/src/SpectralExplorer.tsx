import {t} from './i18n.ts';
import {useEffect,useMemo,useState} from 'react';
import {ArrowRight,ChevronLeft,ChevronRight,Pause,Play} from 'lucide-react';
import Viewer from './Viewer';
import {bandLabel} from './bandLabels';
import {date,type Frame,type Point,type Sample} from './types';
import {spectralFrames,wavelengthColor} from './spectral';

type Props={expert:boolean;frames:Frame[];sample:Sample|null;point:Point;pinned:boolean;onPick:(point:Point)=>void;onPoint:(point:Point)=>void;onTime:(index:number)=>void;onMeasure:()=>void;onMore:()=>void;active:boolean;frameId:string;onFrame:(id:string)=>void;showQuality:boolean;loading:boolean;error:string;failures:{observation:string;error:string}[];onRetry:()=>void;busy:boolean;rangeMode:string;onRange:(mode:string)=>void};
export default function SpectralExplorer(p:Props){
 const rows=useMemo(()=>spectralFrames(p.frames,p.sample),[p.frames,p.sample]);
 const [playing,setPlaying]=useState(false),[speed,setSpeed]=useState(1000),[colored,setColored]=useState(true),[zoom,setZoom]=useState(1);
 const selected=Math.max(0,rows.findIndex(row=>p.frames[row.index].id===p.frameId));
 const row=rows[selected],frame=row?p.frames[row.index]:null;
 useEffect(()=>{setPlaying(false)},[rows,p.active]);
 useEffect(()=>{if(!p.active||!playing||rows.length<2)return;const timer=setInterval(()=>{const next=rows[(selected+1)%rows.length];p.onFrame(p.frames[next.index].id)},speed);return()=>clearInterval(timer)},[p.active,playing,rows,selected,speed,p.onFrame,p.frames]);
 const choose=(index:number)=>{setPlaying(false);const next=rows[(index+rows.length)%rows.length];if(next)p.onFrame(p.frames[next.index].id)};
 const span=rows.length?Math.max(...rows.map(r=>p.frames[r.index].mjd))-Math.min(...rows.map(r=>p.frames[r.index].mjd)):0;
 return <section className="spectral-explorer" aria-label={t("Przegląd długości fal")}>
  <div className="spectral-heading"><div><h2>{t("Zobacz niebo w innym paśmie")}</h2><p>{t("Przesuwaj suwak, aby zobaczyć ten sam obszar w różnych zakresach niewidocznego dla oka światła.")}</p></div><button onClick={()=>{setPlaying(false);p.onMore()}}>{t("Dobierz więcej pasm")}</button></div>
  <div className="spectral-disclaimer"><strong>{t("Odtwarzanie pasm, nie upływu czasu.")}</strong>  {t("Każda klatka jest rzeczywistą obserwacją z podaną datą. Zestaw obejmuje")} {span.toFixed(2)}  {t("dni; zmienność i ruch mogą wpływać na wygląd.")}</div>
  {p.failures.length>0&&<div className="spectral-failures" role="status"><p>{t("Przygotowano")} {p.frames.length}  {t("z")} {p.frames.length+p.failures.length}  {t("obserwacji. Brakujących klatek nie uzupełniamy.")}</p><button disabled={p.busy} onClick={()=>{setPlaying(false);p.onRetry()}}>{t("Ponów nieudane klatki")}</button><details><summary>{t("Przyczyny braków")}</summary>{p.failures.map(f=><p key={f.observation}>{f.observation}: {t(f.error)}</p>)}</details></div>}
  {rows.length>0&&frame&&row?<>
   <div className="spectral-workspace">
    <div className="spectral-image">
     <div className="spectral-image-heading"><strong style={{color:wavelengthColor(row.wavelength)}}>{p.expert?`${row.wavelength.toFixed(4)} µm`:bandLabel(row.wavelength)}</strong><span>{p.expert?`${date(frame.date)} UTC · ${frame.band.replace('SPHEREx-','')}`:`${t('Pasmo')} ${selected+1} / ${rows.length}`}</span></div>
     <Viewer frames={p.frames} a={row.index} b={row.index} mode="spectral" radius={0} pinned={p.pinned} point={p.point} onPoint={p.onPoint} onPick={point=>{setPlaying(false);p.onPick(point)}} anchors={[]} zoom={zoom} routeStep={0} panMode={zoom>1} showQuality={p.showQuality} animating={false} interval={speed} spectralTint={colored?wavelengthColor(row.wavelength):undefined}/>
     <div className="spectral-image-footer"><span className="missing-legend">{t("Kreskowanie: brak danych lub odrzucony piksel")}</span>{p.showQuality&&<span>{t("Pomarańczowe ramki: ostrzeżenia jakości")}</span>}<label>{t("Powiększenie")}<select value={zoom} onChange={e=>setZoom(Number(e.target.value))}><option value="1">{t("Całe pole")}</option><option value="2">2×</option><option value="4">4×</option></select></label></div>
    </div>
    <aside className="spectral-controls">
     <strong>{t("Przejdź przez dostępne pasma")}</strong>
     <div className="spectral-player"><button aria-label={playing?t('Zatrzymaj pasma'):t('Odtwarzaj pasma')} disabled={rows.length<2} onClick={()=>setPlaying(v=>!v)}>{playing?<Pause size={18}/>:<Play size={18}/>}</button><button aria-label={t("Poprzednie pasmo")} disabled={rows.length<2} onClick={()=>choose(selected-1)}><ChevronLeft size={18}/></button><span>{selected+1} / {rows.length}</span><button aria-label={t("Następne pasmo")} disabled={rows.length<2} onClick={()=>choose(selected+1)}><ChevronRight size={18}/></button></div>
     <label className="spectral-slider-label">{p.expert?`${t('Długość fali')}: ${row.wavelength.toFixed(4)} µm`:t('Wybierz pasmo')}<input type="range" min="0" max={Math.max(0,rows.length-1)} step="1" value={selected} disabled={rows.length<2} aria-label={t("Długość fali — dostępne obserwacje")} aria-valuetext={`${bandLabel(row.wavelength)}, ${selected+1} / ${rows.length}`} onChange={e=>choose(Number(e.target.value))}/></label>
     <div className="spectral-endpoints"><span>{t("Krótsze fale")}</span><span>{t("Dłuższe fale")}</span></div>
     <details><summary>{t("Ustawienia podglądu")}</summary><label>{t("Tempo")}<select value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value="1600">{t("Wolno")}</option><option value="1000">{t("Normalnie")}</option><option value="500">{t("Szybko")}</option></select></label>
     <label>{t("Jasność podglądu")}<select value={p.rangeMode} onChange={e=>{setPlaying(false);p.onRange(e.target.value)}}><option value="standard">{t("Standardowa")}</option><option value="faint">{t("Uwydatnij słabe źródła")}</option><option value="full">{t("Pełny zakres")}</option></select></label>
     <label className="check-label"><input type="checkbox" checked={colored} onChange={e=>setColored(e.target.checked)}/>  {t("Umowny kolor pasma")}</label><small>{t("Kolor pomaga odróżnić pasma. Podczerwień jest niewidoczna dla oka; zabarwienie nie zmienia pomiarów.")}</small>
     </details>{p.expert&&<dl className="spectral-facts"><div><dt>{t("Długość fali")}</dt><dd>{p.sample?t('W zaznaczonym punkcie'):t('W centrum pola')}</dd></div><div><dt>{t("Szerokość pasma")}</dt><dd>{row.bandwidth?`${row.bandwidth.toFixed(4)} µm`:t('Brak wartości')}</dd></div><div><dt>{t("Jakość")}</dt><dd>{p.sample?row.valid?t('Ważny piksel'):t('Brak ważnego piksela'):t('Kliknij źródło, aby sprawdzić lokalnie')}</dd></div>{row.flags.length>0&&<div><dt>{t("Flagi punktu")}</dt><dd>{row.flags.join(', ')}</dd></div>}</dl>}
     <button className="primary" onClick={()=>{setPlaying(false);p.onTime(row.index)}}>{t("Sprawdź zmianę w czasie")} <ArrowRight size={15}/></button><button hidden={!p.expert} disabled={!p.pinned} onClick={()=>{setPlaying(false);p.onMeasure()}}>{t("Widmo i pomiary punktu")}</button>
    </aside>
   </div>
   {p.expert&&<><div className="spectral-coverage"><h3>{t("Pokrycie długości fal")}</h3><p>{t("Położenie znaczników odpowiada długości fali w zakresie instrumentu 0,75–5 µm. Puste miejsca nie są uzupełniane.")}</p><div className="spectral-coverage-track" aria-hidden="true">{rows.map((r,i)=><span key={p.frames[r.index].id} className={i===selected?'selected':''} style={{left:`${Math.max(0,Math.min(100,(r.wavelength-.75)/4.25*100))}%`,background:wavelengthColor(r.wavelength)}}/>)}</div><div className="spectral-endpoints"><span>0,75 µm</span><span>5 µm</span></div></div>
   <div className="spectral-channel-list" role="group" aria-label={t("Dostępne obserwacje według długości fali")}>{rows.map((r,i)=><button key={p.frames[r.index].id} aria-pressed={selected===i} onClick={()=>choose(i)}><i style={{background:wavelengthColor(r.wavelength)}}/><strong>{r.wavelength.toFixed(4)} µm</strong><small>{date(p.frames[r.index].date)} UTC</small>{!r.valid&&<small>{t("Brak ważnych danych")}</small>}</button>)}</div></>}
  </>:<p role="status">{t("Brak określonej długości fali")} {p.sample?t('w wybranym punkcie'):t('w centrum pola')}{t(". Wybierz inny punkt lub przygotuj inne obserwacje.")}</p>}
  {rows.length<p.frames.length&&<p role="status">{t("Pominięto")} {p.frames.length-rows.length}  {t("klatek bez określonej długości fali. Nie zastępujemy braków wartością z centrum.")}</p>}
  {rows.length<2&&<p>{t("Do animacji potrzeba przynajmniej dwóch obserwacji z określoną długością fali.")}</p>}
  {p.loading&&<p role="status">{t("Przygotowuję podglądy…")}</p>}{p.error&&<p role="alert">{t(p.error)}</p>}
  <details className="spectral-method"><summary>{t("Jak powstaje ten widok?")}</summary><p>{t("Wspólna skala jasności dla zestawu. Suwak przechodzi przez obserwacje posortowane według długości fali; odstępy między nimi mogą być nierówne. Długość fali zmienia się w obrębie klatki — opis i umowny kolor odnoszą się do zaznaczonego punktu lub centrum pola. To nie jest pełne ani jednoczesne widmo 102 kanałów. Długości fal służą do przeglądu.")}</p></details>
 </section>;
}
