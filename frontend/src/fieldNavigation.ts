import type {AvailableObservation} from './comparison';
export type FieldDay={id:string;rows:AvailableObservation[]};
export type DayBand={band:string;min:number;max:number;rows:AvailableObservation[]};
export const observationDay=(mjd:number)=>new Date((mjd-40587)*86400000).toISOString().slice(0,10);
const chronological=(a:AvailableObservation,b:AvailableObservation)=>a.mjd-b.mjd||a.id.localeCompare(b.id);
// Archive ranges, detector and time are immutable. Preparing a local wavelength
// must never move an observation or detector underneath a slider.
const spectralOrder=(a:AvailableObservation,b:AvailableObservation)=>a.em_min_um-b.em_min_um||a.em_max_um-b.em_max_um||a.band.localeCompare(b.band)||chronological(a,b);
export function observationDays(rows:AvailableObservation[]):FieldDay[]{
 const days=new Map<string,AvailableObservation[]>();
 for(const row of rows){
  if(!Number.isFinite(row.mjd))continue;
  const day=observationDay(row.mjd),list=days.get(day)??[];list.push(row);days.set(day,list);
 }
 return [...days].sort(([a],[b])=>a.localeCompare(b)).map(([id,values])=>({id,rows:values.sort(spectralOrder)}));
}
export function fieldTimeline(rows:AvailableObservation[],band:string,readyOnly=false,selectedId?:string):AvailableObservation[]{
 return rows.filter(row=>row.band===band&&Number.isFinite(row.mjd)&&(!readyOnly||row.ready||row.id===selectedId)).sort(chronological);
}
export function bandsOnDay(rows:AvailableObservation[],mjd:number):DayBand[]{
 const day=observationDay(mjd),groups=new Map<string,AvailableObservation[]>();
 for(const row of rows){
  if(!Number.isFinite(row.mjd)||observationDay(row.mjd)!==day)continue;
  const group=groups.get(row.band)??[];group.push(row);groups.set(row.band,group);
 }
 return [...groups].map(([band,values])=>({band,min:Math.min(...values.map(row=>row.em_min_um)),max:Math.max(...values.map(row=>row.em_max_um)),rows:values.sort(chronological)})).sort((a,b)=>a.min-b.min||a.max-b.max||a.band.localeCompare(b.band));
}
export function bandAtTime(rows:AvailableObservation[],band:string,mjd:number,preferReady=false):AvailableObservation|null{
 const group=bandsOnDay(rows,mjd).find(group=>group.band===band);
 const candidates=group?(preferReady&&group.rows.some(row=>row.ready)?group.rows.filter(row=>row.ready):group.rows):[];
 return candidates.length?[...candidates].sort((a,b)=>Math.abs(a.mjd-mjd)-Math.abs(b.mjd-mjd)||chronological(a,b))[0]:null;
}
export function skippedDays(rows:AvailableObservation[],band:string):number{
 return observationDays(rows).filter(day=>!day.rows.some(row=>row.band===band)).length;
}
