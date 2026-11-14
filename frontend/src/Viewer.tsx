import {t} from './i18n.ts';
import {useEffect,useId,useRef,useState} from 'react';
import type {Anchor,Frame,Point} from './types';
import {prediction} from './types';
import {panes,imageRect,imagePoint} from './viewport';

type Props={frames:Frame[];a:number;b:number;mode:'side'|'lens'|'blink'|'route'|'series'|'spectral';radius:number;pinned:boolean;point:Point;onPoint:(p:Point)=>void;onPick:(p:Point)=>void;anchors:Anchor[];zoom:number;routeStep:number;panMode:boolean;showQuality:boolean;animating:boolean;interval:number;spectralTint?:string;frameTints?:(string|undefined)[];label?:string;interactionHelp?:string;interactive?:boolean};
export default function Viewer(p:Props){
 const keyboardHelp=useId();
 const canvas=useRef<HTMLCanvasElement>(null),images=useRef<(HTMLImageElement|null)[]>([]),quality=useRef<(HTMLImageElement|null)[]>([]),drag=useRef<Point|null>(null),tinted=useRef(new Map<string,HTMLCanvasElement>());
 const imageCache=useRef(new Map<string,HTMLImageElement>()),[imageVersion,setImageVersion]=useState(0);
 const [size,setSize]=useState({w:800,h:400}),[loaded,setLoaded]=useState(false),[blink,setBlink]=useState(false),[pan,setPan]=useState({x:0,y:0}),[error,setError]=useState(''),[keyboardFocus,setKeyboardFocus]=useState(false);
 useEffect(()=>{const observer=new ResizeObserver(([entry])=>{if(entry.contentRect.width>0&&entry.contentRect.height>0)setSize({w:entry.contentRect.width,h:entry.contentRect.height})});observer.observe(canvas.current!);return()=>observer.disconnect()},[]);
 useEffect(()=>{
  let active=true;setError('');
  const cached=(src?:string)=>src?imageCache.current.get(src)??null:null;
  images.current=p.frames.map(f=>cached(f.image));quality.current=p.frames.map(f=>cached(f.quality_image));
  setLoaded(images.current.some(Boolean));setImageVersion(v=>v+1);
  const load=async(src:string)=>{const ready=cached(src);if(ready)return ready;return new Promise<HTMLImageElement>((resolve,reject)=>{const img=new Image();img.onload=()=>{imageCache.current.set(src,img);resolve(img)};img.onerror=()=>reject(new Error(t('Nie udało się wczytać zdjęcia. Spróbuj ponownie.')));img.src=src})};
  p.frames.forEach((f,i)=>{void load(f.image).then(img=>{if(active){images.current[i]=img;setLoaded(true);setImageVersion(v=>v+1)}}).catch(e=>{if(active)setError(e.message)});if(f.quality_image)void load(f.quality_image).then(img=>{if(active){quality.current[i]=img;setImageVersion(v=>v+1)}}).catch(()=>{})});
  return()=>{active=false};
 },[p.frames]);
 useEffect(()=>{if(p.mode!=='blink'||!p.animating)return;const timer=setInterval(()=>setBlink(v=>!v),p.interval);return()=>clearInterval(timer)},[p.mode,p.animating,p.interval]);
 useEffect(()=>setPan({x:0,y:0}),[p.zoom,p.mode]);
 const areas=panes(size.w,size.h,p.mode==='side');
 useEffect(()=>{
  const c=canvas.current!,dpr=window.devicePixelRatio||1;c.width=Math.round(size.w*dpr);c.height=Math.round(size.h*dpr);
  const ctx=c.getContext('2d')!;ctx.scale(dpr,dpr);ctx.fillStyle='#080d12';ctx.fillRect(0,0,size.w,size.h);ctx.imageSmoothingEnabled=false;
  if(!loaded)return;
  const tile=document.createElement('canvas');tile.width=12;tile.height=12;const tc=tile.getContext('2d')!;tc.fillStyle='#111b25';tc.fillRect(0,0,12,12);tc.strokeStyle='#334557';tc.lineWidth=1;tc.beginPath();tc.moveTo(-6,12);tc.lineTo(6,0);tc.moveTo(6,12);tc.lineTo(18,0);tc.stroke();const pattern=ctx.createPattern(tile,'repeat')!;
  const render=(index:number,area:typeof areas[number],lens=false)=>{
   const rect=imageRect(area,p.zoom,pan),screen=(q:Point)=>({x:rect.x+q.x*rect.width,y:rect.y+q.y*rect.height});
   ctx.save();ctx.beginPath();ctx.rect(area.x,area.y,area.width,area.height);ctx.clip();
   const draw=(i:number)=>{ctx.fillStyle=pattern;ctx.fillRect(rect.x,rect.y,rect.width,rect.height);const source=images.current[i];if(source){let display:CanvasImageSource=source;const frameTint=p.frameTints?.[i]??p.spectralTint;if(frameTint){const key=`${source.src}:${frameTint}`;let tile=tinted.current.get(key);if(!tile){tile=document.createElement('canvas');tile.width=source.naturalWidth;tile.height=source.naturalHeight;const tint=tile.getContext('2d')!;tint.drawImage(source,0,0);tint.globalCompositeOperation='multiply';tint.fillStyle=frameTint;tint.fillRect(0,0,tile.width,tile.height);tint.globalCompositeOperation='destination-in';tint.drawImage(source,0,0);if(tinted.current.size>=24)tinted.current.clear();tinted.current.set(key,tile)}display=tile}ctx.drawImage(display,rect.x,rect.y,rect.width,rect.height)}if(p.showQuality&&quality.current[i])ctx.drawImage(quality.current[i]!,rect.x,rect.y,rect.width,rect.height)};
   draw(index);
   if(lens){const q=screen(p.point);ctx.save();ctx.beginPath();ctx.arc(q.x,q.y,p.radius,0,Math.PI*2);ctx.clip();draw(p.b);ctx.restore();ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(q.x,q.y,p.radius,0,Math.PI*2);ctx.stroke();}
   if((p.pinned||keyboardFocus)&&(!lens||p.pinned)){const q=screen(p.point);ctx.strokeStyle='#ffd17e';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(q.x,q.y,8,0,Math.PI*2);ctx.moveTo(q.x-13,q.y);ctx.lineTo(q.x+13,q.y);ctx.moveTo(q.x,q.y-13);ctx.lineTo(q.x,q.y+13);ctx.stroke();}
   if(p.anchors.length){ctx.strokeStyle='#fff';ctx.fillStyle='#fff';ctx.setLineDash([4,4]);ctx.beginPath();p.anchors.forEach((q,i)=>{const s=screen(q);i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y)});ctx.stroke();ctx.setLineDash([]);p.anchors.forEach((q,i)=>{const s=screen(q);ctx.strokeRect(s.x-6,s.y-6,12,12);ctx.font='12px monospace';ctx.fillText(String(i+1),s.x+10,s.y-8)});}
   ctx.restore();
   const f=p.frames[index];ctx.fillStyle='#080d12dd';ctx.fillRect(area.x+6,area.y+6,124,23);ctx.fillStyle='#edf4fa';ctx.font='11px monospace';ctx.fillText(p.mode==='spectral'?f.date.slice(0,10):`${index===p.a?'1':'2'} · ${f.date.slice(0,10)}`,area.x+13,area.y+22);
  };
  if(p.mode==='side'){render(p.a,areas[0]);render(p.b,areas[1]);}
  else render(p.mode==='series'?p.b:p.mode==='blink'?(blink?p.b:p.a):p.mode==='route'?(p.routeStep===0?p.a:p.b):p.a,areas[0],p.mode==='lens');
 },[p,size,pan,blink,loaded,keyboardFocus,imageVersion]);
 const at=(e:React.PointerEvent)=>{const r=canvas.current!.getBoundingClientRect();return imagePoint({x:e.clientX-r.left,y:e.clientY-r.top},areas,p.zoom,pan)};
 return <div className={`canvas-wrap comparison-canvas ${p.mode==='side'?'two-images':'one-image'}`} style={{aspectRatio:p.mode==='side'?(areas[1].y>0?'1 / 2':'2 / 1'):'1 / 1'}}><canvas ref={canvas} tabIndex={p.interactive===false?undefined:0} role="img" aria-label={p.label??(p.mode==='spectral'?t('Obraz wybranego pasma SPHEREx. Kliknij punkt, aby sprawdzić jego lokalną długość fali.'):t('Całe zdjęcia tego samego obszaru nieba. Kliknij ten sam punkt na dowolnym zdjęciu.'))} aria-describedby={keyboardHelp} style={{cursor:p.interactive===false?'default':p.panMode?'grab':'crosshair'}} onFocus={()=>setKeyboardFocus(true)} onBlur={()=>setKeyboardFocus(false)} onKeyDown={e=>{if(!loaded||p.interactive===false)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();e.stopPropagation();const step=e.shiftKey ? .025 : .005;p.onPoint({x:Math.max(0,Math.min(1,p.point.x+(e.key==='ArrowRight'?step:e.key==='ArrowLeft'?-step:0))),y:Math.max(0,Math.min(1,p.point.y+(e.key==='ArrowDown'?step:e.key==='ArrowUp'?-step:0)))})}if(e.key==='Enter'){e.preventDefault();e.stopPropagation();p.onPick(p.point)}}} onPointerMove={e=>{if(drag.current){const dx=e.clientX-drag.current.x,dy=e.clientY-drag.current.y;setPan(v=>({x:v.x+dx,y:v.y+dy}));drag.current={x:e.clientX,y:e.clientY};return}const q=at(e);if(q&&!p.pinned&&p.mode==='lens'&&!p.panMode)p.onPoint(q)}} onPointerDown={e=>{if(p.interactive===false)return;if((e.shiftKey||p.panMode)&&p.zoom>1){drag.current={x:e.clientX,y:e.clientY};e.currentTarget.setPointerCapture(e.pointerId);return}const q=at(e);if(q&&loaded)p.onPick(q)}} onPointerUp={()=>drag.current=null} onPointerCancel={()=>drag.current=null}/>{!loaded&&<div className="canvas-message">{error||t('Wczytywanie zdjęć…')}</div>}<span className="image-hint">N ↑ · E ←</span><span className="sr-only" id={keyboardHelp}>{p.interactionHelp??t('Strzałki przesuwają znacznik, Enter wybiera punkt. Shift i przeciągnięcie przesuwa powiększone zdjęcie.')}</span></div>;
}

export function TrackStrip({frames,anchors,onFrame}:{frames:Frame[];anchors:Anchor[];onFrame:(i:number)=>void}){
 return <div className="track-strip">{frames.map((f,i)=>{const q=prediction(anchors,f.mjd);return <button key={f.id} onClick={()=>onFrame(i)} className="track-tile"><TrackImage src={f.image} point={q}/><span>{f.date.slice(0,10)}</span>{q&&(q.x<0||q.x>1||q.y<0||q.y>1)&&<small>{t("Poza polem")}</small>}</button>})}</div>;
}
function TrackImage({src,point}:{src:string;point:Point|null}){
 const ref=useRef<HTMLCanvasElement>(null);
 useEffect(()=>{const img=new Image();let alive=true;img.onload=()=>{if(!alive||!point)return;const ctx=ref.current!.getContext('2d')!;ctx.clearRect(0,0,100,100);ctx.imageSmoothingEnabled=false;const crop=24;ctx.drawImage(img,point.x*img.width-crop/2,point.y*img.height-crop/2,crop,crop,0,0,100,100);ctx.strokeStyle='#edead6';ctx.strokeRect(47,47,6,6)};img.src=src;return()=>{alive=false}},[src,point]);
 return <canvas ref={ref} width={100} height={100}/>;
}
