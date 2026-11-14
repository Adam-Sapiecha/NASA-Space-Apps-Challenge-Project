import type {Frame,Observation,Sample} from './types';
import {closeBands} from './workflow.ts';

export type SpectralFrame={index:number;wavelength:number;bandwidth:number;valid:boolean;flags:string[]};

// Local wavelengths replace centre values completely, including missing values.
// Never interpolate a channel that was not observed.
export function spectralFrames(frames:Frame[],sample:Sample|null):SpectralFrame[]{
 return frames.flatMap((f,index)=>{
  const local=sample?.frames.find(row=>row.id===f.id);
  const wavelength=sample?local?.wavelength_um:f.wavelength_um;
  const bandwidth=sample?local?.bandwidth_um:f.bandwidth_um;
  if(wavelength==null||!Number.isFinite(wavelength)||wavelength<=0)return [];
  return [{index,wavelength,bandwidth:bandwidth!=null&&Number.isFinite(bandwidth)&&bandwidth>0?bandwidth:0,valid:sample?!!local?.valid:f.coverage>0,flags:local?.flags??[]}];
 }).sort((a,b)=>a.wavelength-b.wavelength||frames[a.index].mjd-frames[b.index].mjd||a.index-b.index);
}

// Detector metadata only gives broad wavelength ranges. Choose multiple detector
// groups near one reference visit; actual local channels are checked after FITS.
export function proposeSpectral(observations:Observation[],limit=12):Observation[]{
 const eligible=observations.filter(o=>Number.isFinite(o.mjd));
 const groups=[...new Set(eligible.map(o=>o.band))].sort();
 if(!groups.length||limit<1)return [];
 let best:Observation[]=[],bestSpan=Infinity;
 for(const pivot of eligible){
  const nearest=groups.map(group=>eligible.filter(o=>o.band===group).sort((a,b)=>Math.abs(a.mjd-pivot.mjd)-Math.abs(b.mjd-pivot.mjd)||a.id.localeCompare(b.id))[0]);
  const span=Math.max(...nearest.map(o=>o.mjd))-Math.min(...nearest.map(o=>o.mjd));
  if(span<bestSpan){best=nearest;bestSpan=span}
 }
 const picked=best.slice(0,limit);
 const pivot=picked.reduce((sum,o)=>sum+o.mjd,0)/picked.length;
 for(const group of groups){
  if(picked.length>=limit)break;
  const extra=eligible.filter(o=>o.band===group&&!picked.some(p=>p.id===o.id)).sort((a,b)=>Math.abs(a.mjd-pivot)-Math.abs(b.mjd-pivot)||a.id.localeCompare(b.id))[0];
  if(extra)picked.push(extra);
 }
 return picked.sort((a,b)=>a.mjd-b.mjd||a.band.localeCompare(b.band));
}

export function wavelengthColor(wavelength:number):string{
 const t=Math.max(0,Math.min(1,(wavelength-.75)/4.25));
 return `hsl(${265-265*t} 78% 68%)`;
}

export function spectralTemporalPair(frames:Frame[],sample:Sample|null,index:number):[number,number]|null{
 const band=(i:number)=>sample?sample.frames.find(row=>row.id===frames[i].id):frames[i];
 const valid=(i:number)=>sample?!!sample.frames.find(row=>row.id===frames[i].id)?.valid:frames[i].coverage>=.8;
 if(!frames[index]||!valid(index))return null;
 const source=band(index);if(!source)return null;
 const candidates=frames.map((_,i)=>i).filter(i=>i!==index&&valid(i)&&frames[i].mjd!==frames[index].mjd&&band(i)&&closeBands(source,band(i)!));
 candidates.sort((a,b)=>Math.abs(frames[b].mjd-frames[index].mjd)-Math.abs(frames[a].mjd-frames[index].mjd));
 return candidates.length?[index,candidates[0]]:null;
}
