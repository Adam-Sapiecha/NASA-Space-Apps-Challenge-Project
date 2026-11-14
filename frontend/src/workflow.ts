import type {Frame,Observation,Sample,Selection} from './types';

// Archive metadata describes a detector range, not the band at a source.
export function proposeSeries(observations:Observation[], limit=8):Observation[]{
 const groups=[...new Set(observations.map(o=>o.band))].map(band=>observations.filter(o=>o.band===band).sort((a,b)=>a.mjd-b.mjd));
 groups.sort((a,b)=>new Set(b.map(o=>o.mjd)).size-new Set(a.map(o=>o.mjd)).size || (b.at(-1)!.mjd-b[0].mjd)-(a.at(-1)!.mjd-a[0].mjd) || a[0].band.localeCompare(b[0].band));
 const group=groups[0]??[];
 const unique=group.filter((o,i)=>i===0||o.mjd!==group[i-1].mjd);
 if(unique.length<=limit)return unique;
 // Sample actual observation times, rather than indices in a dense cluster.
 const chosen=new Set([0,unique.length-1]);
 for(let k=1;k<limit-1;k++){
  const target=unique[0].mjd+(unique.at(-1)!.mjd-unique[0].mjd)*k/(limit-1);
  const candidates=unique.map((o,i)=>({i,d:Math.abs(o.mjd-target)})).filter(o=>!chosen.has(o.i)).sort((a,b)=>a.d-b.d||a.i-b.i);
  chosen.add(candidates[0].i);
 }
 return [...chosen].sort((a,b)=>a-b).map(i=>unique[i]);
}

type Band={wavelength_um:number|null;bandwidth_um:number|null};
export function closeBands(a:Band,b:Band):boolean{
 return [a.wavelength_um,b.wavelength_um,a.bandwidth_um,b.bandwidth_um].every(v=>v!==null&&Number.isFinite(v)) && a.bandwidth_um!>0 && b.bandwidth_um!>0 && Math.abs(a.wavelength_um!-b.wavelength_um!)<=Math.min(a.bandwidth_um!,b.bandwidth_um!)/2;
}

export function comparisonSeries(frames:Frame[], sample:Sample|null=null, selection:Selection|null=null):number[]{
 // Maximum mutually compatible subset; analyses are limited to twelve frames.
 const local=(i:number)=>sample?.frames.find(f=>f.id===frames[i].id);
 const checked=(i:number)=>selection?.candidates.find(row=>row.id===frames[i].id);
 const bands=(i:number)=>sample?local(i)!:selection?checked(i)!:frames[i];
 const eligible=frames.map((_,i)=>i).filter(i=>sample?!!local(i)?.valid:selection?
  !!checked(i)?.central_valid&&(checked(i)?.local_coverage??0)>=.8:frames[i].coverage>=.8);
 let best:number[]=[],bestSpan=-1;
 const consider=(subset:number[])=>{
  const span=subset.length?frames[subset.at(-1)!].mjd-frames[subset[0]].mjd:0;
  if(subset.length>best.length||subset.length===best.length&&span>bestSpan){best=subset;bestSpan=span}
 };
 const visit=(chosen:number[],remaining:number[])=>{
  consider(chosen);
  if(chosen.length+remaining.length<best.length)return;
  for(let k=0;k<remaining.length;k++){
   const i=remaining[k],x=bands(i);
   if(chosen.every(j=>frames[i].mjd!==frames[j].mjd&&closeBands(x,bands(j))))visit([...chosen,i],remaining.slice(k+1));
  }
 };
 visit([],eligible.sort((a,b)=>frames[a].mjd-frames[b].mjd));
 return best.length>=2?best:[];
}

export function nextFrame(current:number,indices:number[],step=1):number{
 if(!indices.length)return current;
 const position=indices.indexOf(current);
 return indices[position<0?(step>0?0:indices.length-1):(position+step+indices.length)%indices.length];
}

export function validPoint(value:unknown):value is {x:number;y:number}{
 if(!value||typeof value!=='object')return false;
 const p=value as {x:number;y:number};
 return Number.isFinite(p.x)&&Number.isFinite(p.y)&&p.x>=0&&p.x<=1&&p.y>=0&&p.y<=1;
}
