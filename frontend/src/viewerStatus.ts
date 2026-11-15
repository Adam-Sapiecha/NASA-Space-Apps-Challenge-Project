import type {Frame,Sample,Selection} from './types';
import {closeBands} from './workflow.ts';

type Mode='side'|'series';
export type ComparisonNotice={kind:'same'|'missing'|'unknown'|'bands';location:'point'|'target'|'centre'}|null;

export function comparisonNotice(frames:Frame[],a:number,b:number,mode:Mode,sample:Sample|null,selection?:Selection):ComparisonNotice{
 if(a===b)return mode==='series'?null:{kind:'same',location:'centre'};
 const bothChecked=!!selection&&[a,b].every(index=>selection.candidates.some(row=>row.id===frames[index]?.id));
 const location=sample?'point':bothChecked?'target':'centre';
 const local=(index:number)=>sample?sample.frames.find(row=>row.id===frames[index]?.id):
  bothChecked?selection!.candidates.find(row=>row.id===frames[index]?.id):frames[index];
 const left=local(a),right=local(b);
 if(sample&&(!sample.frames.find(row=>row.id===frames[a]?.id)?.valid||!sample.frames.find(row=>row.id===frames[b]?.id)?.valid))return {kind:'missing',location};
 if(!left||!right||!closeBands(left,left)||!closeBands(right,right))return {kind:'unknown',location};
 return closeBands(left,right)?null:{kind:'bands',location};
}

export function pixelFlagSummary(frames:Frame[],a:number,b:number,mode:Mode){
 const indices=mode==='series'?[b]:a===b?[a]:[a,b];
 return indices.filter(index=>frames[index]).map(index=>({
  index,
  label:mode==='series'?'2':index===a&&index===b?'1 = 2':index===a?'1':'2',
  fraction:typeof frames[index].warned_fraction==='number'&&Number.isFinite(frames[index].warned_fraction)?
   Math.max(0,Math.min(1,frames[index].warned_fraction!)):null,
 }));
}
