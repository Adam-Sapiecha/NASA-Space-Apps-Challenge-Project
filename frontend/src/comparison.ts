import type {Analysis,Frame,Observation,Sample} from './types';
import {bestPair} from './types.ts';
import {closeBands,comparisonSeries} from './workflow.ts';

export type DisplaySettings={quality:'all'|'valid';range:'standard'|'faint'|'full';tint:boolean;mask:boolean};
export type PairPreset='auto'|'time'|'bands'|'custom';
export type PlaybackAxis='time'|'bands';
export const DEFAULT_DISPLAY:DisplaySettings={quality:'all',range:'standard',tint:false,mask:false};
export type AvailableObservation=Observation&{wavelength_um:number|null;bandwidth_um:number|null;ready:boolean};
export type BandChoice={id:string;band:string;wavelength:number;rows:AvailableObservation[]};

export function observationCatalogue(analysis:Analysis):AvailableObservation[]{
 const prepared=new Map(analysis.frames.map(frame=>[frame.id,frame]));
 const checked=new Map(analysis.selection?.candidates.map(row=>[row.id,row])??[]);
 return analysis.search.observations.map(row=>{
  const local=checked.get(row.id)??prepared.get(row.id);
  return {...row,wavelength_um:local?.wavelength_um??null,bandwidth_um:local?.bandwidth_um??null,ready:prepared.has(row.id)};
 }).sort((a,b)=>a.mjd-b.mjd||a.band.localeCompare(b.band)||a.id.localeCompare(b.id));
}

export function bandChoices(rows:AvailableObservation[]):BandChoice[]{
 const result:BandChoice[]=[];
 for(const row of [...rows].sort((a,b)=>(a.wavelength_um??Infinity)-(b.wavelength_um??Infinity)||a.id.localeCompare(b.id))){
  if(!closeBands(row,row))continue;
  let group=result.find(group=>group.band===row.band&&group.rows.every(other=>closeBands(row,other)));
  if(!group){group={id:row.id,band:row.band,wavelength:row.wavelength_um!,rows:[]};result.push(group)}
  group.rows.push(row);
 }
 return result;
}

export function pairForBand(group:BandChoice,rows:AvailableObservation[],ids:[string,string]):[string,string]{
 const times=ids.map(id=>rows.find(row=>row.id===id)?.mjd);
 const options=group.rows.flatMap(a=>group.rows.filter(b=>a.id!==b.id&&a.mjd!==b.mjd).map(b=>({a,b,cost:
  Math.abs(a.mjd-(times[0]??a.mjd))+Math.abs(b.mjd-(times[1]??b.mjd))})));
 options.sort((a,b)=>a.cost-b.cost||Math.abs(b.b.mjd-b.a.mjd)-Math.abs(a.b.mjd-a.a.mjd)||a.a.id.localeCompare(b.a.id));
 return options.length?[options[0].a.id,options[0].b.id]:[group.rows[0].id,group.rows[0].id];
}

export function defaultPair(analysis:Analysis):[string,string]{
 const available=new Set(analysis.frames.map(frame=>frame.id));
 const recommended=analysis.workspace?.recommended_pair_ids??analysis.selection?.pair_ids;
 if(recommended?.length===2&&recommended.every(id=>available.has(id)))return [recommended[0],recommended[1]];
 const pair=bestPair(analysis.frames);
 if(pair)return [analysis.frames[pair[0]].id,analysis.frames[pair[1]].id];
 return [analysis.frames[0].id,analysis.frames[Math.min(1,analysis.frames.length-1)].id];
}

export function spectralPair(rows:AvailableObservation[],reference:number):[string,string]|null{
 // Compare different detector ranges near the chosen epoch. Exact local bands
 // are displayed after preparing the FITS; missing channels are never invented.
 const groups=[...new Set(rows.map(row=>row.band))];
 const nearest=groups.map(band=>rows.filter(row=>row.band===band).sort((a,b)=>Math.abs(a.mjd-reference)-Math.abs(b.mjd-reference)||a.id.localeCompare(b.id))[0]);
 const pairs=nearest.flatMap((a,i)=>nearest.slice(i+1).map(b=>({a,b,span:Math.abs(a.mjd-b.mjd),distance:Math.abs(a.mjd-reference)+Math.abs(b.mjd-reference),width:Math.abs((a.wavelength_um??a.em_min_um)-(b.wavelength_um??b.em_min_um))})));
 pairs.sort((a,b)=>a.distance-b.distance||a.span-b.span||b.width-a.width);
 return pairs.length?[pairs[0].a.id,pairs[0].b.id]:null;
}

export function temporalPairForObservation(analysis:Analysis,anchorId:string):[string,string]|null{
 const rows=observationCatalogue(analysis),group=bandChoices(rows).find(group=>group.rows.some(row=>row.id===anchorId));
 if(!group)return null;
 const checked=new Map(analysis.selection?.candidates.map(row=>[row.id,row])??[]);
 const pairs=group.rows.flatMap((a,i)=>group.rows.slice(i+1).filter(b=>a.mjd!==b.mjd).map(b=>({a,b,
  quality:Number(checked.get(a.id)?.aperture_valid??false)+Number(checked.get(b.id)?.aperture_valid??false),baseline:Math.abs(a.mjd-b.mjd)})));
 pairs.sort((a,b)=>b.quality-a.quality||b.baseline-a.baseline||a.a.id.localeCompare(b.a.id));
 if(!pairs.length)return null;
 return [pairs[0].a,pairs[0].b].sort((a,b)=>a.mjd-b.mjd).map(row=>row.id) as [string,string];
}

export function playbackFrames(analysis:Analysis|null,sample:Sample|null,anchor:number,axis:PlaybackAxis,preset:PairPreset,strict=false):number[]{
 if(!analysis?.frames[anchor])return [];
 const frames=analysis.frames;
 const allChecked=!!analysis.selection&&frames.every(frame=>analysis.selection!.candidates.some(row=>row.id===frame.id));
 const local=(i:number)=>sample?sample.frames.find(row=>row.id===frames[i].id):
  allChecked?analysis.selection!.candidates.find(row=>row.id===frames[i].id):frames[i];
 if(axis==='bands'){
  let indices=frames.map((_,i)=>i).filter(i=>{const band=local(i);return band&&closeBands(band,band)});
  if(preset==='bands'){
   indices=indices.filter(i=>Math.abs(frames[i].mjd-frames[anchor].mjd)<=1);
   const nearest=new Map<string,number>();
   for(const i of indices){const prior=nearest.get(frames[i].band);if(prior===undefined||Math.abs(frames[i].mjd-frames[anchor].mjd)<Math.abs(frames[prior].mjd-frames[anchor].mjd))nearest.set(frames[i].band,i)}
   indices=[...nearest.values()];
  }
  return indices.sort((a,b)=>local(a)!.wavelength_um!-local(b)!.wavelength_um!||frames[a].mjd-frames[b].mjd);
 }
 if(strict)return comparisonSeries(frames,sample,analysis.selection??null);
 const source=local(anchor);if(!source||!closeBands(source,source))return [anchor];
 const preferred=new Set(analysis.workspace?.recommended_ids??analysis.selection?.selected_ids??[]);
 const candidates=frames.map((_,i)=>i).filter(i=>local(i)&&closeBands(source,local(i)!)&&
  (i===anchor||frames[i].mjd!==frames[anchor].mjd)&&(preset!=='auto'||!preferred.size||preferred.has(frames[i].id)));
 // Keep the anchor and add only mutually compatible, distinct epochs.
 const selected=[anchor];
 for(const i of candidates.sort((a,b)=>Math.abs(frames[b].mjd-frames[anchor].mjd)-Math.abs(frames[a].mjd-frames[anchor].mjd))){
  if(!selected.includes(i)&&selected.every(j=>frames[i].mjd!==frames[j].mjd&&closeBands(local(i)!,local(j)!)))selected.push(i);
 }
 return selected.sort((a,b)=>frames[a].mjd-frames[b].mjd);
}

export function displayFromQuery(query:URLSearchParams,suffix=''):DisplaySettings{
 return {quality:query.get(`quality${suffix}`)==='valid'?'valid':'all',range:['faint','full'].includes(query.get(`range${suffix}`)??'')?query.get(`range${suffix}`) as DisplaySettings['range']:'standard',
  mask:query.get(`mask${suffix}`)==='1',tint:query.get(`tint${suffix}`)==='1'};
}
