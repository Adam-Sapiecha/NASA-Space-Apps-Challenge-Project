import {useEffect,useMemo,useState} from 'react';
import {ArrowLeftRight,LoaderCircle,RotateCcw} from 'lucide-react';
import {t} from './i18n';
import {date,type Analysis} from './types';
import {bandChoices,observationCatalogue,pairForBand,type DisplaySettings,type PairPreset} from './comparison';

type Props={analysis:Analysis;a:number;b:number;busy:boolean;preset:PairPreset;
 shared:DisplaySettings;split:boolean;personal:[DisplaySettings,DisplaySettings];
 onApply:(ids:[string,string])=>Promise<boolean>;onPreset:(preset:PairPreset)=>void;onPause:()=>void;
 onShared:(patch:Partial<DisplaySettings>)=>void;onSplit:(split:boolean)=>void;onPersonal:(slot:0|1,patch:Partial<DisplaySettings>)=>void};

function DisplayEditor({name,value,onChange}:{name:string;value:DisplaySettings;onChange:(patch:Partial<DisplaySettings>)=>void}){
 return <fieldset className="display-editor"><legend>{name}</legend><div className="display-editor-grid">
  <label>{t('Jasność obrazu')}<select aria-label={`${name} · ${t('Jasność obrazu')}`} value={value.range} onChange={event=>onChange({range:event.target.value as DisplaySettings['range']})}><option value="standard">{t('Standardowa')}</option><option value="faint">{t('Uwydatnij słabe źródła')}</option><option value="full">{t('Pełny zakres')}</option></select></label>
  <label>{t('Pokazane piksele')}<select aria-label={`${name} · ${t('Pokazane piksele')}`} value={value.quality} onChange={event=>onChange({quality:event.target.value as DisplaySettings['quality']})}><option value="all">{t('Wszystkie dostępne')}</option><option value="valid">{t('Po kontroli jakości')}</option></select></label>
  <label className="check-label"><input type="checkbox" checked={value.tint} onChange={event=>onChange({tint:event.target.checked})}/>{t('Umowny kolor pasma')}</label>
  <label className="check-label"><input type="checkbox" disabled={value.quality!=='all'} checked={value.mask} onChange={event=>onChange({mask:event.target.checked})}/>{t('Pokaż maskę flag błędów')}</label>
 </div></fieldset>;
}

export function ComparisonDisplayControls(p:Props){
 return <div className="comparison-display-controls">
  <details className="combined-display"><summary>{t('Ustawienia wyświetlania')} · {p.split?t('osobno A/B'):t('wspólne A/B')}</summary>
   <label className="check-label"><input type="checkbox" checked={p.split} onChange={event=>p.onSplit(event.target.checked)}/>{t('Osobne ustawienia obrazu A i B')}</label>
   {p.split?<div className="independent-display"><DisplayEditor name="A" value={p.personal[0]} onChange={patch=>p.onPersonal(0,patch)}/><DisplayEditor name="B" value={p.personal[1]} onChange={patch=>p.onPersonal(1,patch)}/></div>:<DisplayEditor name={t('Wspólny podgląd A/B')} value={p.shared} onChange={p.onShared}/>}
   <small>{t(p.split?'Osobne skale jasności mogą zmieniać wygląd porównania. Pomiary korzystają z danych naukowych.':'Wspólna skala jasności ułatwia porównanie. Kolor pasma i maska są opcjonalne.')}</small>
  </details>
 </div>;
}

export default function ComparisonControls(p:Props){
 const rows=useMemo(()=>observationCatalogue(p.analysis),[p.analysis]);
 const groups=useMemo(()=>bandChoices(rows),[rows]);
 const current:[string,string]=[p.analysis.frames[p.a]?.id??'',p.analysis.frames[p.b]?.id??''];
 const [draft,setDraft]=useState<[string,string]>(current),[dirty,setDirty]=useState(false),[applying,setApplying]=useState(false),[pickerOpen,setPickerOpen]=useState(false);
 useEffect(()=>{setDraft(current);setDirty(false)},[current[0],current[1],p.analysis.id]);
 const loaded=new Set(p.analysis.frames.map(frame=>frame.id));
 const same=draft[0]===current[0]&&draft[1]===current[1];
 const pending=draft.filter((id,i)=>!loaded.has(id)&&draft.indexOf(id)===i).length;
 const apply=async(ids=draft)=>{p.onPause();setApplying(true);try{if(await p.onApply(ids))setDirty(false)}finally{setApplying(false)}};
 const edit=(ids:[string,string])=>{p.onPause();setDraft(ids);setDirty(true);if(ids.every(id=>loaded.has(id)))void apply(ids)};
 const setPreset=(preset:PairPreset)=>{setDirty(false);setDraft(current);setPickerOpen(preset==='custom');p.onPreset(preset)};
 const currentGroup=groups.find(group=>draft.every(id=>group.rows.some(row=>row.id===id)))?.id??'';
 return <section className="comparison-controls" aria-label={t('Czas, pasmo i wyświetlanie')}>
  <div className="combined-heading"><div><h2>{t('Dobór obserwacji')}</h2><p>{t('Obserwacje pola:')} {rows.length} · {t('Gotowe zdjęcia:')} {p.analysis.frames.length}</p></div><button disabled={p.busy} onClick={()=>setPreset('auto')}><RotateCcw size={15}/>{t('Najlepszy zestaw i ustawienia')}</button></div>
  <div className="combined-presets" role="group" aria-label={t('Sposób doboru zestawu')}>
   {([{id:'auto',label:t('Automatycznie')},{id:'time',label:t('Ruch w czasie')},{id:'bands',label:t('Różne pasma')},{id:'custom',label:t('Dowolne A/B')}] as const).map(item=><button disabled={p.busy} key={item.id} aria-pressed={p.preset===item.id} onClick={()=>setPreset(item.id)}>{item.label}</button>)}

  </div>
  <details className="combined-picker" open={pickerOpen||dirty} onToggle={event=>setPickerOpen(event.currentTarget.open)}><summary>{t('Zmień daty i pasma')}</summary>
   <label className="common-band">{t('Pasmo dla obu zdjęć')}<select aria-label={t('Pasmo dla obu zdjęć')} value={currentGroup} disabled={p.busy||!groups.length} onChange={event=>{const group=groups.find(group=>group.id===event.target.value);if(group)edit(pairForBand(group,rows,draft))}}><option value="">{t('Różne pasma lub własny zestaw')}</option>{groups.map(group=><option key={group.id} value={group.id}>{group.wavelength.toFixed(4)} µm · {group.band.replace('SPHEREx-','')} · {group.rows.length} {t('obrazów')}</option>)}</select></label>
  <div className="combined-observations">{([0,1] as const).map(slot=><label key={slot}><strong>{t(slot===0?'Zdjęcie A':'Zdjęcie B')}</strong><select aria-label={t(slot===0?'Obserwacja A: data i pasmo':'Obserwacja B: data i pasmo')} value={draft[slot]} disabled={p.busy} onChange={event=>edit(slot===0?[event.target.value,draft[1]]:[draft[0],event.target.value])}>
   {[...new Set(rows.map(row=>row.band))].sort().map(band=><optgroup key={band} label={band.replace('SPHEREx-','')}>{rows.filter(row=>row.band===band).map(row=><option key={row.id} value={row.id}>{date(row.date)} · {row.wavelength_um===null?`${row.em_min_um.toFixed(2)}–${row.em_max_um.toFixed(2)} µm*`:`${row.wavelength_um.toFixed(4)} µm`}{row.ready?` · ${t('gotowe')}`:''}</option>)}</optgroup>)}
  </select></label>)}<button className="subtle" disabled={p.busy} onClick={()=>edit([draft[1],draft[0]])} aria-label={t('Zamień zdjęcia')}><ArrowLeftRight size={17}/></button></div>
  <div className="combined-apply"><span>{dirty&&!same?(pending?`${t('Do przygotowania:')} ${pending}. ${t('Wybrane daty i pasma są pokazane powyżej.')}`:t('Wybrany zestaw jest gotowy.')):t('Domyślnie pokazujemy rekomendowaną parę. Pozostałe obserwacje są dostępne w polach A/B.')}</span><button disabled={p.busy||applying||same} onClick={()=>void apply()}>{(p.busy||applying)&&<LoaderCircle size={14} className="spin"/>}{pending?t('Przygotuj i otwórz zestaw'):t('Otwórz zestaw')}</button></div>
  </details>
  <details className="combined-data-note"><summary>{t('Dostępność dat i pasm')}</summary><p>{t('Lista obejmuje rzeczywiste obserwacje tego pola. Każde A można zestawić z każdym B. Pasmo obu zdjęć dobiera najbliższe dostępne daty; przed przygotowaniem widać je w polach A/B. Gwiazdka oznacza zakres detektora — lokalną długość fali sprawdzimy po pobraniu FITS.')}</p></details>
 </section>;
}
