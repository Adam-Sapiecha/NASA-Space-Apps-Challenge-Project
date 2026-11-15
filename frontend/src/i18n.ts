import {assetUrl} from './urls.ts';
import messages from './messages.en.ts';

export type Language='en'|'pl';
const initialLanguage=():Language=>{
 if(typeof window==='undefined')return 'en';
 const query=new URLSearchParams(window.location.search).get('lang');
 if(query==='en'||query==='pl')return query;
 try{return window.localStorage.getItem('spherex-language')==='pl'?'pl':'en'}catch{return 'en'}
};
let language:Language=initialLanguage();
const listeners=new Set<()=>void>();
const reverse=new Map(Object.entries(messages).map(([pl,en])=>[en,pl]));
const fragments=Object.entries(messages).filter(([key])=>key.length>=12).sort((a,b)=>b[0].length-a[0].length);
export const getLanguage=()=>language;
export const locale=()=>language==='en'?'en-GB':'pl-PL';
export const subscribeLanguage=(listener:()=>void)=>{listeners.add(listener);return()=>{listeners.delete(listener)}};
export function setLanguage(next:Language){
 language=next;
 if(typeof document!=='undefined'){document.documentElement.lang=next;document.title=next==='en'?'SPHEREx observations':'Obserwacje SPHEREx'}
 if(typeof window!=='undefined'){
  const url=new URL(window.location.href);url.searchParams.set('lang',next);window.history.replaceState(null,'',url);
  try{window.localStorage.setItem('spherex-language',next)}catch{/* Storage is optional. */}
 }
 listeners.forEach(listener=>listener());
}

/** Translate presentation text only; scientific responses and exports stay intact. */
export function t(source:string):string{
 if(language==='pl')return reverse.get(source)??source;
 const exact=messages[source];if(exact)return exact;
 let result=source;
 const patterns:[RegExp,string][]=[
  [/^Pobieranie i wyrównanie (\d+)\/(\d+)$/, 'Downloading and aligning $1/$2'],
  [/^Pobieranie FITS (\d+)\/(\d+) \(z cache, jeśli dostępny\)$/, 'Loading FITS $1/$2 (using the cache when available)'],
  [/^Wyrównywanie obrazu (\d+)\/(\d+)$/, 'Aligning observation $1/$2'],
  [/^Odstęp A–B: (.+) dni\.$/, 'A–B time gap: $1 days.'],
  [/Różnica ([-+\d.]+) μm; próg przeglądowy ([-+\d.]+) μm\./g, 'Difference $1 μm; browsing threshold $2 μm.'],
  [/Średnie tło A\/B: (.+); rozrzut: (.+) \(w jednostce powierzchniowej natywnego FITS\)\./g, 'Mean background A/B: $1; scatter: $2 (in native FITS surface-brightness units).'],
 ];
 for(const [pattern,replacement] of patterns)result=result.replace(pattern,replacement);
 // Runtime backend messages may combine a fixed explanation with numbers/flags.
 // Keep unknown text visible rather than discarding diagnostic information.
 for(const [pl,en] of fragments)if(result.includes(pl))result=result.split(pl).join(en);
 return result;
}
export function withLanguage(url:string):string{
 const parsed=new URL(assetUrl(url),typeof location==='undefined'?'http://localhost':location.origin);
 parsed.searchParams.set('lang',language);
 return parsed.pathname+parsed.search+parsed.hash;
}
