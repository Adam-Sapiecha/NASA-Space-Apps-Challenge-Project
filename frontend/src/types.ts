import {locale,t} from './i18n.ts';
export type Observation={id:string;obs_id:string;date:string;mjd:number;band:string;url:string;em_min_um:number;em_max_um:number};
export type Search={id:string;ra:number;dec:number;fov_arcmin:number;collection:string;observations:Observation[];cached?:boolean;notice?:string;retrieved_at?:string};
export type Frame=Observation & {image:string;quality_image?:string;display_coverage?:number;warned_fraction?:number;wavelength_um:number;bandwidth_um:number;coverage:number;unit:string;masked_flags:string[]};
export type Selection={status:string;summary:string;inspected:number;planned?:number;complete?:boolean;available_ids?:string[];target_id?:string|null;radius_arcsec:number;pair_ids:string[];selected_ids:string[];baseline_days?:number;position_method:string;candidates:{id:string;band:string;date:string;aperture_valid:boolean;central_valid:boolean;local_coverage:number;wavelength_um:number|null;bandwidth_um:number|null;flagged?:string[];reason?:string;cutout_fov_arcmin:number}[];limitations:string[]};
export type ComparisonWorkspace={root_analysis_id:string;recommended_ids:string[];recommended_pair_ids:string[];requested_ids:string[];cache_order:string[];available_observations:number};
export type Analysis={id:string;provisional?:boolean;revision?:number;workspace?:ComparisonWorkspace;frames:Frame[];pixels:number;search:Search;limitations:string[];display:{low:number;high:number};failures:{observation:string;error:string}[];selection?:Selection};
export type Point={x:number;y:number};
export type Anchor=Point & {frameId:string;mjd:number};
export type Sample={ra:number;dec:number;frames:{id:string;valid:boolean;wavelength_um:number|null;bandwidth_um:number|null;flags:string[]}[]};
export async function api<T>(url:string, body?:unknown):Promise<T>{
 let response:Response;
 try{response=await fetch(url,body===undefined?undefined:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
 catch{throw new Error(t('Brak połączenia z serwerem. Sprawdź połączenie i spróbuj ponownie; zapisane analizy pozostają na serwerze.'))}
 let value;
 try{value=await response.json()}
 catch{throw new Error(response.ok?t('Serwer zwrócił nieoczekiwany format danych. Odśwież stronę.'):getUnavailable(response.status))}
 if(!response.ok)throw new Error(t(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail??'Nie udało się wykonać żądania.')));
 return value;
}
const getUnavailable=(status:number)=>locale()==='en-GB'?`The server is temporarily unavailable (HTTP ${status}). Try again; prepared results remain saved.`:`Serwer chwilowo niedostępny (HTTP ${status}). Spróbuj ponownie; gotowe wyniki pozostają zapisane.`;
export const date=(value:string)=>new Date(/[zZ]$|[+-]\d{2}:\d{2}$/.test(value)?value:value+'Z').toLocaleString(locale(),{timeZone:'UTC',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});
export function bestPair(frames:Frame[]):[number,number]|null{
 let best:[number,number]|null=null,baseline=0;
 for(let i=0;i<frames.length;i++)for(let j=i+1;j<frames.length;j++){
  const x=frames[i],y=frames[j],days=Math.abs(x.mjd-y.mjd);
  if(x.coverage<.8||y.coverage<.8)continue;
  if(days>baseline&&Math.abs(x.wavelength_um-y.wavelength_um)<=Math.min(x.bandwidth_um,y.bandwidth_um)/2){best=[i,j];baseline=days}
 }
 return best;
}
export function prediction(anchors:Anchor[],mjd:number):Point|null{
 if(anchors.length!==2||anchors[0].mjd===anchors[1].mjd)return null;
 const [a,b]=anchors,t=(mjd-a.mjd)/(b.mjd-a.mjd);
 return {x:a.x+t*(b.x-a.x),y:a.y+t*(b.y-a.y)};
}
