import {apiUrl,assetUrl} from './urls.ts';
import {t,getLanguage,setLanguage,subscribeLanguage} from './i18n.ts';
import {useEffect,useMemo,useRef,useState,useSyncExternalStore} from 'react';
import {ArrowRight,Check,Hand,Link,LoaderCircle,TriangleAlert,X} from 'lucide-react';
import ResearchGuide from './ResearchGuide';
import showcase from './showcase.json';
import MotionExample from './MotionExample';
import motionShowcase from './motionShowcase.json';
import SelectionReport from './SelectionReport';
import FrameGallery from './FrameGallery';
import FieldExplorer from './FieldExplorer';
import FieldStart from './FieldStart';
import FieldSelection from './FieldSelection';
import ComparisonNotice from './ComparisonNotice';
import ImageQualityLegend from './ImageQualityLegend';
import {comparisonNotice} from './viewerStatus';
import {workspaceEntry,workspaceDefaults,workspacePanel,displayMode,fieldStep,initialFieldMethod,type FieldMethod,type FieldStep,type WorkspaceTab,type WorkspacePanel} from './workspace';
import Viewer from './Viewer';
import SkyContext from './SkyContext';
import SpectralAnalysis from './SpectralAnalysis';
import IrsaWorkbench from './IrsaWorkbench';
import ComparisonControls,{ComparisonDisplayControls} from './ComparisonControls';
import {DEFAULT_DISPLAY,defaultPair,displayFromQuery,observationCatalogue,playbackFrames,spectralPair,temporalPairForObservation,type DisplaySettings,type PairPreset,type PlaybackAxis} from './comparison';
import {proposeSpectral,wavelengthColor} from './spectral';
import {proposeSeries,comparisonSeries,validPoint,recommendedAnalysis} from './workflow';
import {api,date,bestPair,type Analysis,type Point,type Sample,type Search} from './types';
import catalogueTargets from '../../backend/targets.json';

const targets=catalogueTargets.map(t=>({...t,ra:String(t.field_ra),dec:String(t.field_dec)}));
const initial=new URLSearchParams(location.search);
const entry=workspaceEntry(initial,showcase.analysis_id);
export default function App(){
 const language=useSyncExternalStore(subscribeLanguage,getLanguage,getLanguage);
 const defaults=workspaceDefaults(initial);
 useEffect(()=>{document.documentElement.lang=language;document.title=language==='en'?'SPHEREx observations':'Obserwacje SPHEREx'},[language]);
 const [panel,setPanel]=useState<WorkspacePanel>(()=>workspacePanel(initial));
 const [step,setStep]=useState<FieldStep>(()=>fieldStep(initial));
 const [fieldMethod,setFieldMethod]=useState<FieldMethod>(()=>initialFieldMethod(initial));
 const [searchFailed,setSearchFailed]=useState(false);
 const selectPanel=(value:WorkspacePanel)=>{
  setPanel(value);setPlaying(false);
  const url=new URL(location.href);url.searchParams.set('panel',value);url.searchParams.delete('guided');url.searchParams.delete('prediction');history.replaceState(null,'',url);
 };
 const showField=(empty=false)=>{if(empty){setRa('');setDec('')}setFieldMethod(empty?'object':'coordinates');setSearchFailed(false);selectPanel('compare');pauseExplorer();setStep('field');setSearch(null);setError('');const url=new URL(location.href);url.search='';url.searchParams.set('lang',language);url.searchParams.set('ra',empty?'':ra);url.searchParams.set('dec',empty?'':dec);url.searchParams.set('fov',String(fov));url.searchParams.set('collection',collection);history.replaceState(null,'',url)};
 const chooseField=()=>{pauseExplorer();setStep('choose');setSearch(null);setError('');const url=new URL(location.href);url.search='';url.searchParams.set('lang',language);history.replaceState(null,'',url)};
 const [expert,setExpert]=useState(defaults.expert);
 const [ra,setRa]=useState(initial.get('ra')??targets[0].ra),[dec,setDec]=useState(initial.get('dec')??targets[0].dec),[fov,setFov]=useState(Number(initial.get('fov'))||12),[collection,setCollection]=useState(initial.get('collection')==='spherex_qr3'?'spherex_qr3':'spherex_dr1');
 const [automaticSelection,setAutomaticSelection]=useState(true);
 const [search,setSearch]=useState<Search|null>(null),[band,setBand]=useState(''),[selected,setSelected]=useState<string[]>([]),[analysis,setAnalysis]=useState<Analysis|null>(null),[busy,setBusy]=useState(''),[error,setError]=useState('');
 const [a,setA]=useState(0),[b,setB]=useState(1),[mode,setMode]=useState<'side'|'series'>(displayMode(initial.get('mode'))),[point,setPoint]=useState<Point>({x:.5,y:.5}),[zoom,setZoom]=useState([1,2,4].includes(Number(initial.get('zoom')))?Number(initial.get('zoom')):1),[playing,setPlaying]=useState(false),[sample,setSample]=useState<Sample|null>(null),[copied,setCopied]=useState(false);
 const [workspaceTab,setWorkspaceTab]=useState<WorkspaceTab>(entry.tab),[help,setHelp]=useState(false);
 const [selectionPurpose,setSelectionPurpose]=useState<'time'|'spectrum'>('time');
 const [seriesOnly,setSeriesOnly]=useState(initial.get('series')==='1'),[samplePoint,setSamplePoint]=useState<Point|null>(null),[sampleBusy,setSampleBusy]=useState(false),[jobProgress,setJobProgress]=useState<{completed:number;total:number}|null>(null);
 const [pairPreset,setPairPreset]=useState<PairPreset>(['auto','time','bands','custom'].includes(initial.get('preset')??'')?initial.get('preset') as PairPreset:initial.get('view')==='spectrum'?'bands':'auto');
 const [playbackAxis,setPlaybackAxis]=useState<PlaybackAxis>(initial.get('axis')==='bands'||initial.get('view')==='spectrum'?'bands':'time');
 const [splitDisplay,setSplitDisplay]=useState(initial.get('splitDisplay')==='1'),[tinted,setTinted]=useState(initial.get('tint')==='1');
 const [personalDisplay,setPersonalDisplay]=useState<[DisplaySettings,DisplaySettings]>([displayFromQuery(initial,'A'),displayFromQuery(initial,'B')]);
 const [showMissing,setShowMissing]=useState(initial.get('hatch')==='1');
 const [explorerPauseSignal,setExplorerPauseSignal]=useState(0);
 const pauseExplorer=()=>{setPlaying(false);setExplorerPauseSignal(value=>value+1)};
 const [explorerTarget,setExplorerTarget]=useState<{id:string|null;time:string}|null>(null);
 const personalInitialized=useRef(initial.get('splitDisplay')==='1');
 const comparisonGeneration=useRef(0);
 const liveView=useRef({analysis,a,b});liveView.current={analysis,a,b};
 const series=useMemo(()=>comparisonSeries(analysis?.frames??[],sample,analysis?.selection??null),[analysis,sample]);
 const playback=useMemo(()=>playbackFrames(analysis,sample,b,playbackAxis,pairPreset,seriesOnly),[seriesOnly,analysis,sample,b,playbackAxis,pairPreset]);
 useEffect(()=>{if(seriesOnly&&series.length>=2){setA(v=>series.includes(v)?v:series[0]);setB(v=>series.includes(v)?v:series.at(-1)!)}},[series,seriesOnly]);
 type Preview={analysis_id:string;quality:string;range_mode:string;frame_ids?:string[];frames:{id:string;image:string;quality_image:string;display_coverage:number;warned_fraction:number}[]};
 const [previewSlots,setPreviewSlots]=useState<[Preview|null,Preview|null]>([null,null]),[previewBusy,setPreviewBusy]=useState(false),[previewError,setPreviewError]=useState(''),[quality,setQuality]=useState(initial.get('quality')==='valid'?'valid':'all'),[rangeMode,setRangeMode]=useState(['faint','full'].includes(initial.get('range')??'')?initial.get('range')!:'standard'),[showQuality,setShowQuality]=useState(initial.get('mask')==='1');
 const sharedDisplay:DisplaySettings={quality:quality as DisplaySettings['quality'],range:rangeMode as DisplaySettings['range'],tint:tinted,mask:showQuality};
 const effectiveDisplay:[DisplaySettings,DisplaySettings]=splitDisplay?personalDisplay:[sharedDisplay,sharedDisplay];
 const commonContrastIds=[...new Set((mode==='series'&&analysis?analysis.frames.map((_,index)=>index).filter(index=>analysis.frames[index].band===analysis.frames[b]?.band):[a,b]).map(index=>analysis?.frames[index]?.id).filter((id):id is string=>!!id))].sort();
 const contrastIds:[string[],string[]]=splitDisplay?[[analysis?.frames[a]?.id??''],mode==='series'?commonContrastIds:[analysis?.frames[b]?.id??'']]:[commonContrastIds,commonContrastIds];
 const contrastKeys=contrastIds.map(ids=>ids.join(','));
 const setPreview=(value:null)=>setPreviewSlots([value,value]);
 useEffect(()=>{
  if(!analysis||analysis.provisional)return;let active=true;setPreviewBusy(true);setPreviewError('');
  const requests=new Map<string,Promise<Preview>>();
  const request=(settings:DisplaySettings,slot:number)=>{const key=`${settings.quality}:${settings.range}:${contrastKeys[slot]}`;let pending=requests.get(key);if(!pending){pending=api<Preview>(`/api/analyses/${analysis.id}/previews`,{quality:settings.quality,range_mode:settings.range,frame_ids:contrastIds[slot]});requests.set(key,pending)}return pending};
  Promise.all(effectiveDisplay.map(request)).then(values=>{if(active)setPreviewSlots(values as [Preview,Preview])}).catch(e=>{if(active)setPreviewError(e.message)}).finally(()=>{if(active)setPreviewBusy(false)});
  return()=>{active=false};
 },[analysis,effectiveDisplay[0].quality,effectiveDisplay[0].range,effectiveDisplay[1].quality,effectiveDisplay[1].range,contrastKeys[0],contrastKeys[1]]);
 const matchingPreview=(slot:0|1)=>{const value=previewSlots[slot],settings=effectiveDisplay[slot];return value?.analysis_id===analysis?.id&&value?.quality===settings.quality&&value?.range_mode===settings.range&&value.frame_ids?.join(',')===contrastKeys[slot]?value:null};
 const displayPair=analysis?([a,b] as const).map((index,slot)=>{const settings=effectiveDisplay[slot],preview=matchingPreview(slot as 0|1),frame=analysis.frames[index];return {...frame,...preview?.frames.find(row=>row.id===frame.id),quality_image:settings.mask?preview?.frames.find(row=>row.id===frame.id)?.quality_image:undefined}}):[];
 const actualQualities:[string,string]=[matchingPreview(0)?.quality??'valid',matchingPreview(1)?.quality??'valid'];
 const frameTints=displayPair.map((frame,slot)=>{const wave=sample?sample.frames.find(row=>row.id===frame.id)?.wavelength_um:frame.wavelength_um;return effectiveDisplay[slot].tint&&wave!=null&&Number.isFinite(wave)?wavelengthColor(wave):undefined});
 const poll=useRef<ReturnType<typeof setTimeout>|null>(null),sampleGeneration=useRef(0);
 const jobGeneration=useRef(0);
 useEffect(()=>()=>{jobGeneration.current++;comparisonGeneration.current++;if(poll.current)clearTimeout(poll.current)},[]);
 useEffect(()=>{if(initial.has('job')){setBusy(t('Downloading observations in parallel'));void watchJob(initial.get('job')!,initial.get('view')==='spectrum'?'spectrum':'time');return}const id=entry.analysisId;if(!id||fieldStep(initial)==='choose')return;setBusy(t('Otwieranie zapisanej analizy…'));api<Analysis>(`/api/analyses/${encodeURIComponent(id)}`).then(saved=>{const result=recommendedAnalysis(saved);setAnalysis(result);setRa(String(result.search.ra));setDec(String(result.search.dec));setFov(result.search.fov_arcmin);setCollection(result.search.collection);setA(initial.has('a_id')?Math.max(0,result.frames.findIndex(frame=>frame.id===initial.get('a_id'))):Math.max(0,Math.min(result.frames.length-1,Number(initial.get('a'))||0)));setB(initial.has('b_id')?Math.max(0,result.frames.findIndex(frame=>frame.id===initial.get('b_id'))):Math.max(0,Math.min(result.frames.length-1,Number(initial.get('b')??1)||0)));if(result.workspace&&!initial.has('preset'))setPairPreset('custom');if(!initial.has('a')&&!initial.has('b')&&!initial.has('a_id')&&!initial.has('b_id')){const restored=result.workspace?.requested_ids;if(restored&&restored.length>=2&&restored.slice(0,2).every(id=>result.frames.some(frame=>frame.id===id))){setA(result.frames.findIndex(frame=>frame.id===restored[0]));setB(result.frames.findIndex(frame=>frame.id===restored[1]))}const prepared=showcase.frame_ids.map(id=>result.frames.findIndex(f=>f.id===id));const recommended=result.selection?.pair_ids.map(id=>result.frames.findIndex(f=>f.id===id));const pair=recommended?.length===2&&recommended.every(i=>i>=0)?recommended:result.id===showcase.analysis_id&&prepared.every(i=>i>=0)?prepared as [number,number]:bestPair(result.frames);if(pair&&!restored){setA(pair[0]);setB(pair[1])}if(initial.get('view')==='spectrum'&&!restored){const spectral=spectralPair(observationCatalogue(result).filter(row=>row.ready),result.frames[0].mjd);if(spectral){setA(result.frames.findIndex(frame=>frame.id===spectral[0]));setB(result.frames.findIndex(frame=>frame.id===spectral[1]))}}if(initial.has('channel')){const channel=result.frames.findIndex(frame=>frame.id===initial.get('channel'));if(channel>=0)setB(channel)}}}).catch(e=>setError(e.message)).finally(()=>setBusy(''))},[]);
 useEffect(()=>{const listener=(event:KeyboardEvent)=>{if(panel!=='compare'||workspaceTab!=='compare'||event.defaultPrevented||(event.target as HTMLElement).matches('input,select,textarea,button')||!analysis)return;if(event.key.toLowerCase()==='x'&&mode==='side'){setA(b);setB(a)}};window.addEventListener('keydown',listener);return()=>window.removeEventListener('keydown',listener)},[analysis,a,b,workspaceTab,mode,panel]);
 const searchField=async()=>{
  const url=new URL(location.href);url.search='';url.searchParams.set('lang',language);url.searchParams.set('ra',ra);url.searchParams.set('dec',dec);url.searchParams.set('fov',String(fov));url.searchParams.set('collection',collection);url.searchParams.set('picker',fieldMethod);history.replaceState(null,'',url);
  setStep('field');pauseExplorer();setSearch(null);setError('');setSearchFailed(false);setBusy(t('Szukam obrazów…'));
  try{const result=await api<Search>('/api/search',{ra,dec,fov_arcmin:fov,collection});setSearch(result);setAutomaticSelection(true);setSelectionPurpose('time');const proposal=proposeSeries(result.observations);setBand(proposal[0]?.band??'');setSelected(proposal.map(o=>o.id));setTimeout(()=>document.getElementById('search-results')?.scrollIntoView({block:'start'}),0)}
  catch(e){setError((e as Error).message);setSearchFailed(true)}finally{setBusy('')}
 };
 const watchJob=async(id:string,purpose:'time'|'spectrum'='time')=>{
  if(poll.current)clearTimeout(poll.current);
  const generation=++jobGeneration.current;let revision=-1;
  const check=async()=>{try{
   const status=await api<{status:string;message:string;completed?:number;total?:number;analysis_id?:string;revision?:number}>(`/api/jobs/${id}`);
   if(generation!==jobGeneration.current)return;
   setBusy(status.message);if(status.total)setJobProgress({completed:status.completed??0,total:status.total});
   if((status.analysis_id&&status.revision!==revision)||status.status==='complete'){
    const result=recommendedAnalysis(await api<Analysis>(`/api/analyses/${id}`));if(generation!==jobGeneration.current)return;
    revision=result.revision??0;
    const previous=liveView.current;
    const indices=[previous.a,previous.b].map((index,k)=>{
     const old=previous.analysis?.id===result.id?previous.analysis.frames[index]?.id:null;
     const found=result.frames.findIndex(f=>f.id===old);
     return found>=0?found:Math.min(k,result.frames.length-1);
    });
    if(previous.analysis?.id===id&&previous.analysis.frames.length===1&&result.frames.length>1&&indices[0]===indices[1])indices[1]=indices[0]===0?1:0;
    if(status.status==='complete'&&result.selection){const pair=result.selection.pair_ids.map(id=>result.frames.findIndex(f=>f.id===id));if(pair.length===2&&pair.every(i=>i>=0)){indices[0]=pair[0];indices[1]=pair[1]}}
    setA(indices[0]);setB(indices[1]);setAnalysis(result);setRa(String(result.search.ra));setDec(String(result.search.dec));setFov(result.search.fov_arcmin);setCollection(result.search.collection);
    if(previous.analysis?.id!==result.id)setWorkspaceTab('compare');
    if(status.status==='complete'&&purpose==='spectrum'){setPlaybackAxis('bands');setPairPreset('bands')}else if(status.status==='complete'){setPlaybackAxis('time');setPairPreset('auto')}
    const url=new URL(location.href);url.searchParams.set('analysis',id);if(status.status==='complete'){url.searchParams.delete('job');url.searchParams.delete('channel');url.searchParams.set('a_id',result.frames[indices[0]].id);url.searchParams.set('b_id',result.frames[indices[1]].id);url.searchParams.set('view','compare');url.searchParams.set('preset',purpose==='spectrum'?'bands':'auto');url.searchParams.set('axis',purpose==='spectrum'?'bands':'time')}history.replaceState(null,'',url);
   }
   if(status.status==='failed')throw new Error(status.message);
   if(status.status==='complete'){setBusy('');setJobProgress(null);return}
   poll.current=setTimeout(check,750);
  }catch(e){if(generation===jobGeneration.current){setError((e as Error).message);setBusy('');setJobProgress(null)}}};
  await check();
 };
 const prepare=async(retry=false,purpose=selectionPurpose)=>{
  if(retry&&analysis?.workspace){await applyObservationPair(analysis.workspace.requested_ids.slice(0,2) as [string,string]);return}
  const source=retry?analysis?.search:search;if(!source)return;
  const ids=retry&&analysis?[...analysis.frames.map(f=>f.id),...analysis.failures.map(f=>f.observation)]:selected;
  setBusy(t('Tworzenie analizy…'));setJobProgress(null);setError('');setPlaying(false);
  try{
   const auto=retry?!!analysis?.selection:purpose==='time'&&automaticSelection;
   const target=targets.find(target=>target.name===chosenTarget);
   const job=await api<{id:string}>(auto?'/api/analyses/auto':'/api/analyses',auto?{search_id:source.id,target_id:retry?analysis?.selection?.target_id??null:target?.id??null,candidate_limit:36}:{search_id:source.id,observation_ids:ids,...(retry?{retry_of:analysis?.id}:{})});
   sampleGeneration.current++;setAnalysis(null);setPreview(null);setPreviewBusy(false);setPreviewError('');setSample(null);setSamplePoint(null);setSampleBusy(false);setSeriesOnly(false);setA(0);setB(0);
   setStep('explore');setExplorerTarget(null);setPoint({x:.5,y:.5});setZoom(1);setMode('series');setWorkspaceTab('compare');setPairPreset(purpose==='spectrum'?'bands':'auto');setPlaybackAxis(purpose==='spectrum'?'bands':'time');
   const url=new URL(location.href);url.search='';url.searchParams.set('lang',language);url.searchParams.set('interface',expert?'advanced':'simple');url.searchParams.set('job',job.id);url.searchParams.set('ra',String(source.ra));url.searchParams.set('dec',String(source.dec));url.searchParams.set('fov',String(source.fov_arcmin));url.searchParams.set('collection',source.collection);if(purpose==='spectrum')url.searchParams.set('view','spectrum');history.replaceState(null,'',url);
   document.getElementById('workspace')?.scrollIntoView({block:'start'});
   await watchJob(job.id,purpose);
  }catch(e){setError((e as Error).message);setBusy('');setJobProgress(null)}
 };
 const applyObservationPair=async(ids:[string,string],preset:PairPreset='custom',axis:PlaybackAxis=playbackAxis):Promise<boolean>=>{
  const source=liveView.current.analysis;if(!source||ids.some(id=>!source.search.observations.some(row=>row.id===id)))return false;
  setPlaying(false);setPairPreset(preset);setSeriesOnly(false);setError('');setWorkspaceTab('compare');
  const adopt=(result:Analysis)=>{
   const previous=liveView.current,requested=ids.map(id=>result.frames.findIndex(frame=>frame.id===id));
   const success=requested.every(index=>index>=0);
   const fallback=[previous.a,previous.b].map(index=>Math.max(0,result.frames.findIndex(frame=>frame.id===previous.analysis?.frames[index]?.id)));
   setAnalysis(result);setA(success?requested[0]:fallback[0]);setB(success?requested[1]:fallback[1]);
   if(result.id!==previous.analysis?.id){sampleGeneration.current++;setSample(null);setSampleBusy(false);setPreview(null)}
   const url=new URL(location.href);url.searchParams.set('analysis',result.id);url.searchParams.set('a_id',result.frames[success?requested[0]:fallback[0]].id);url.searchParams.set('b_id',result.frames[success?requested[1]:fallback[1]].id);url.searchParams.set('preset',preset);if(preset==='auto'){for(const key of ['quality','range','mask','tint','qualityA','qualityB','rangeA','rangeB','maskA','maskB','tintA','tintB','splitDisplay','zoom','speed','lensRadius','mode','series'])url.searchParams.delete(key)}url.searchParams.set('view','compare');url.searchParams.set('axis',axis);for(const key of ['measurement','irsa','science','product','note'])url.searchParams.delete(key);history.replaceState(null,'',url);
   if(!success)setError(t('Nie udało się przygotować całego wybranego zestawu. Zachowano poprzednie porównanie; wybierz inne obserwacje lub ponów próbę.'));
   return success;
  };
  if(ids.every(id=>source.frames.some(frame=>frame.id===id)))return adopt(source);
  const generation=++comparisonGeneration.current;setBusy(t('Przygotowuję wybrane daty i pasma…'));setJobProgress(null);
  try{
   const response=await api<{id?:string;analysis_id?:string;status:string}>(`/api/analyses/${source.id}/comparison`,{observation_ids:ids,previous_ids:[source.frames[liveView.current.a].id,source.frames[liveView.current.b].id]});
   let resultId=response.analysis_id;
   if(response.id){
    for(;;){
     if(generation!==comparisonGeneration.current)return false;
     const status=await api<{status:string;message:string;completed?:number;total?:number}>(`/api/jobs/${response.id}`);setBusy(status.message);if(status.total)setJobProgress({completed:status.completed??0,total:status.total});
     if(status.status==='failed')throw new Error(status.message);
     if(status.status==='complete'){resultId=response.id;break}
     await new Promise(resolve=>setTimeout(resolve,650));
    }
   }
   if(!resultId)throw new Error(t('Brak przygotowanego zestawu.'));
   const result=await api<Analysis>(`/api/analyses/${resultId}`);if(generation!==comparisonGeneration.current)return false;
   return adopt(result);
  }catch(e){setError((e as Error).message);return false}finally{if(generation===comparisonGeneration.current){setBusy('');setJobProgress(null)}}
 };
 const setSharedDisplay=(patch:Partial<DisplaySettings>)=>{pauseExplorer();if(patch.quality!==undefined)setQuality(patch.quality);if(patch.range!==undefined)setRangeMode(patch.range);if(patch.mask!==undefined)setShowQuality(patch.mask);if(patch.tint!==undefined)setTinted(patch.tint)};
 const setDisplaySplit=(value:boolean)=>{pauseExplorer();setSplitDisplay(value);if(value&&!personalInitialized.current){setPersonalDisplay([{...sharedDisplay},{...sharedDisplay}]);personalInitialized.current=true}};
 const resetComparison=async(preset:PairPreset)=>{
  if(!analysis||busy)return;setPlaying(false);setPairPreset(preset);setSeriesOnly(false);
  if(preset==='auto'){personalInitialized.current=false;setSplitDisplay(false);setSharedDisplay(DEFAULT_DISPLAY);setPersonalDisplay([{...DEFAULT_DISPLAY},{...DEFAULT_DISPLAY}]);setZoom(1);setMode('side');setPanMode(false)}
  if(preset==='custom')return;
  if(preset==='bands'){
   setPlaybackAxis('bands');const pair=spectralPair(observationCatalogue(analysis),analysis.frames[b]?.mjd??analysis.frames[0].mjd);
   if(pair)await applyObservationPair(pair,'bands','bands');return;
  }
  setPlaybackAxis('time');
  if(preset==='time'){const pair=temporalPairForObservation(analysis,analysis.frames[b].id);if(pair)await applyObservationPair(pair,'time','time');else setError(t('W sprawdzonych obserwacjach brakuje drugiej daty tego lokalnego pasma. Wybierz inne zdjęcie B lub wróć do automatycznego doboru.'));return}
  if(analysis.selection){await applyObservationPair(defaultPair(analysis),preset,'time');return}
  setBusy(t('Dobieram najlepszą parę do porównania w czasie…'));
  try{const target=targets.find(target=>Math.abs(Number(target.ra)-analysis.search.ra)<1e-7&&Math.abs(Number(target.dec)-analysis.search.dec)<1e-7);const job=await api<{id:string}>('/api/analyses/auto',{search_id:analysis.search.id,target_id:target?.id??null,candidate_limit:36});const url=new URL(location.href);url.searchParams.set('job',job.id);url.searchParams.set('view','compare');history.replaceState(null,'',url);await watchJob(job.id,'time')}catch(e){setError((e as Error).message);setBusy('')}
 };
 const sampleAt=async(p:Point)=>{
  if(!analysis||analysis.provisional)return;setPoint(p);setSample(null);setSamplePoint(null);setSampleBusy(true);setPlaying(false);const url=new URL(location.href);url.searchParams.delete('measurement');history.replaceState(null,'',url);
  const generation=++sampleGeneration.current;
  try{const result=await api<Sample>(`/api/analyses/${analysis.id}/sample?x=${p.x}&y=${p.y}`);if(generation===sampleGeneration.current){setSample(result);setSamplePoint(p)}}
  catch(e){if(generation===sampleGeneration.current)setError((e as Error).message)}finally{if(generation===sampleGeneration.current)setSampleBusy(false)}
 };
 useEffect(()=>{if(analysis&&samplePoint)void sampleAt(samplePoint)},[analysis?.id]);
 const share=async()=>{const url=new URL(location.href);const retained=new URLSearchParams(url.search);url.search='';for(const key of ['skyTime','skyUtc','observer','lat','lon','height','product','measurement','irsa','science','quality','range','interface','lang','job']){const value=retained.get(key);if(value!==null)url.searchParams.set(key,value)}if(analysis){url.searchParams.set('interface',expert?'advanced':'simple');url.searchParams.set('analysis',analysis.id);url.searchParams.set('a',String(a));url.searchParams.set('b',String(b));url.searchParams.set('a_id',analysis.frames[a].id);url.searchParams.set('b_id',analysis.frames[b].id);url.searchParams.set('preset',pairPreset);url.searchParams.set('axis',playbackAxis);url.searchParams.set('splitDisplay',splitDisplay?'1':'0');url.searchParams.set('zoom',String(zoom));url.searchParams.set('tint',tinted?'1':'0');personalDisplay.forEach((value,slot)=>{const suffix=mode==='side'&&slot===0?'A':'B';url.searchParams.set('quality'+suffix,value.quality);url.searchParams.set('range'+suffix,value.range);url.searchParams.set('mask'+suffix,value.mask?'1':'0');url.searchParams.set('tint'+suffix,value.tint?'1':'0')});if(samplePoint)url.searchParams.set('point',JSON.stringify(samplePoint));url.searchParams.set('mode',mode);if(showMissing)url.searchParams.set('hatch','1');if(['measure','irsa','sky'].includes(workspaceTab))url.searchParams.set('view',workspaceTab);url.searchParams.set('series',seriesOnly?'1':'0')}else{url.searchParams.set('ra',ra);url.searchParams.set('dec',dec);url.searchParams.set('fov',String(fov));url.searchParams.set('collection',collection)}url.searchParams.set('lang',language);url.searchParams.set('quality',quality);url.searchParams.set('range',rangeMode);url.searchParams.set('mask',showQuality?'1':'0');history.replaceState(null,'',url);try{await navigator.clipboard.writeText(url.href);setCopied(true);setTimeout(()=>setCopied(false),2500)}catch{setError(t('Link jest w pasku adresu. Skopiuj go ręcznie.'))}};
 const [panMode,setPanMode]=useState(false);
 const frames=analysis?.frames||[],fa=frames[a],fb=frames[b];
 const selectSpectrum=(source:Search)=>{setAutomaticSelection(false);const proposal=proposeSpectral(source.observations);setSelected(proposal.map(o=>o.id));setBand('');setSelectionPurpose('spectrum')};
 const notice=comparisonNotice(frames,a,b,mode,sample,analysis?.selection);
 const selectedObs=search?.observations.filter(o=>selected.includes(o.id))??[];
 const filtered=search?.observations.filter(o=>!band||o.band===band)||[];
 const chosenTarget=targets.find(t=>Math.abs(Number(t.ra)-Number(ra))<1e-7&&Math.abs(Number(t.dec)-Number(dec))<1e-7)?.name??'custom';
 const openPreparedAnalysis=async(id:string,ids?:string[],selectedPoint:Point|null=null)=>{
  selectPanel('compare');setSearchFailed(false);setBusy(t('Otwieranie zapisanej analizy…'));setError('');
  try{
   const result=recommendedAnalysis(await api<Analysis>(`/api/analyses/${id}`));
   const bandExample=id===showcase.spectral_analysis_id;
   const suggested=bandExample?spectralPair(observationCatalogue(result).filter(row=>row.ready),result.frames[0].mjd):null;
   const pair=(ids??suggested)?.map(value=>result.frames.findIndex(frame=>frame.id===value));
   const chosen=pair?.length===2&&pair.every(index=>index>=0)?pair:defaultPair(result).map(value=>result.frames.findIndex(frame=>frame.id===value));
   sampleGeneration.current++;setSample(null);setSampleBusy(false);setPreview(null);setSearch(null);
   setAnalysis(result);setA(chosen[0]);setB(chosen[1]);setRa(String(result.search.ra));setDec(String(result.search.dec));setFov(result.search.fov_arcmin);setCollection(result.search.collection);
   setStep('explore');setExplorerTarget(null);setSamplePoint(selectedPoint);setPoint(selectedPoint??{x:.5,y:.5});setMode('series');setZoom(1);setSeriesOnly(false);setWorkspaceTab('compare');setPairPreset('custom');setPlaybackAxis(bandExample?'bands':'time');
   setSplitDisplay(false);setSharedDisplay(DEFAULT_DISPLAY);personalInitialized.current=false;
   const url=new URL(location.href);url.search='';url.searchParams.set('analysis',id);url.searchParams.set('a_id',result.frames[chosen[0]].id);url.searchParams.set('b_id',result.frames[chosen[1]].id);url.searchParams.set('panel','compare');url.searchParams.set('axis',bandExample?'bands':'time');url.searchParams.set('preset','custom');url.searchParams.set('interface',expert?'advanced':'simple');url.searchParams.set('lang',language);if(selectedPoint)url.searchParams.set('point',JSON.stringify(selectedPoint));history.replaceState(null,'',url);
   if(analysis?.id===result.id&&selectedPoint)void sampleAt(selectedPoint);
  }catch(e){setError((e as Error).message)}finally{setBusy('')}
 };
 const activeTarget=analysis?(analysis.id===showcase.spectral_analysis_id?targets.find(target=>target.id==='barnard'):targets.find(target=>Math.abs(Number(target.ra)-analysis.search.ra)<1e-7&&Math.abs(Number(target.dec)-analysis.search.dec)<1e-7)):null;
 useEffect(()=>{
  const restoredId=entry.analysisId;if(!analysis||analysis.provisional||analysis.id!==restoredId||initial.has('note')||initial.has('job'))return;
  try{const p=JSON.parse(initial.get('point')??(!initial.has('analysis')&&analysis.id===showcase.analysis_id?JSON.stringify(showcase.point):'null'));if(validPoint(p))void sampleAt(p)}catch{}
  setMode(displayMode(initial.get('mode')));
  if(initial.get('series')==='0'||initial.has('a')||initial.has('b'))setSeriesOnly(false);
 },[analysis?.id]);
 return <div className="epoch-app">
  <a className="skip-link" href={panel==='motion'?'#motion-example':'#task-content'}>{t('Przejdź do obrazu')}</a>
  <header className="app-header">
   <a className="app-title" href={assetUrl('/')}><b>SPHEREx</b><span>{t('Porównywanie obserwacji SPHEREx')}</span></a>
   <div className="context-actions"><label className="language-control"><span>Language / Język</span><select aria-label="Language / Język" value={language} onChange={event=>setLanguage(event.target.value as 'en'|'pl')}><option value="en">English</option><option value="pl">Polski</option></select></label><button className="subtle" aria-expanded={help} onClick={()=>setHelp(value=>!value)}>{t(help?'Zamknij pomoc':'Pomoc i dane')}</button></div>
  </header>
  <main className={`workbench ${expert?'expert-mode':'simple-mode'}`} id="task-content">
   <nav className="task-navigation" aria-label={t('Zadanie obserwacyjne')}>
    {([{id:'compare',label:t('Czas i pasmo')},{id:'motion',label:t('Ruch komety')}] as const).map(item=><button key={item.id} aria-pressed={panel===item.id} onClick={()=>selectPanel(item.id)}>{item.label}</button>)}
   </nav>
   {help&&<ResearchGuide/>}
   <div hidden={panel!=='motion'}><MotionExample onInspect={()=>void openPreparedAnalysis(motionShowcase.analysis_id,motionShowcase.frames.map(frame=>frame.id))} onField={showField}/></div>
   <div hidden={panel!=='compare'} className="research-workspace">
    <nav className="field-steps" aria-label={t('Etapy pracy')}>
     <button disabled={!!busy} aria-current={step!=='explore'?'step':undefined} onClick={chooseField}><span>1</span>{t('Wybór pola')}</button><ArrowRight size={16} aria-hidden="true"/><button disabled={!analysis||!!busy||step==='field'} aria-current={step==='explore'?'step':undefined} onClick={()=>{setStep('explore');setWorkspaceTab('compare');const url=new URL(location.href);url.search='';url.searchParams.set('analysis',analysis!.id);url.searchParams.set('lang',language);history.replaceState(null,'',url)}}><span>2</span>{t('Analiza czasu i pasm')}</button>
    </nav>
    {step==='choose'&&<FieldStart busy={!!busy} onOpen={id=>void openPreparedAnalysis(id)} onOwn={()=>showField(true)}/>}
    {step!=='choose'&&<>
    <div className="observation-heading"><div><h1>{step==='field'?t('Wybierz fragment nieba'):analysis?(analysis.id===motionShowcase.analysis_id?'3I/ATLAS':activeTarget?`${t('Pole wokół')} ${activeTarget.name}`:t('Porównanie obserwacji')):t(busy?'Przygotowanie obserwacji':'Wyszukaj obserwacje SPHEREx')}</h1>{analysis&&step==='explore'&&<p className="mono">ICRS {analysis.search.ra.toFixed(5)}°, {analysis.search.dec.toFixed(5)}° · {analysis.search.fov_arcmin}′ · {analysis.search.collection.replace('spherex_','').toUpperCase()}</p>}</div><button hidden={step==='field'} className="subtle" aria-pressed={expert} onClick={()=>{setExpert(value=>!value);if(expert&&['measure','irsa'].includes(workspaceTab))setWorkspaceTab('compare');const url=new URL(location.href);url.searchParams.set('interface',expert?'simple':'advanced');history.replaceState(null,'',url)}}>{t(expert?'Podstawowe narzędzia':'Wszystkie narzędzia')}</button></div>
   {step==='field'&&<FieldSelection method={fieldMethod} onMethod={method=>{setFieldMethod(method);const url=new URL(location.href);url.searchParams.set('picker',method);history.replaceState(null,'',url)}} targets={targets} ra={ra} dec={dec} fov={fov} collection={collection} busy={!!busy} onField={(r,d)=>{setRa(r);setDec(d);setSearch(null);setError('');setSearchFailed(false)}} onFov={value=>{setFov(value);setSearch(null);setError('')}} onCollection={value=>{setCollection(value);setSearch(null);setError('')}} onSearch={()=>void searchField()}/>}
   </>}
   {error&&<div className="notice error" role="alert"><TriangleAlert size={16}/><span>{t(error)}</span><button onClick={()=>setError('')} aria-label={t("Zamknij komunikat")}><X size={14}/></button></div>}
   {error&&searchFailed&&step==='field'&&<div className="search-recovery"><button disabled={!!busy} onClick={()=>void searchField()}>{t('Ponów wyszukiwanie')}</button><button className="primary" disabled={!!busy} onClick={()=>void openPreparedAnalysis(showcase.analysis_id)}>{t('Otwórz gotowy przykład')}</button></div>}
   {busy&&<div className="notice" role="status"><LoaderCircle className="spin" size={16}/><span>{t(busy)}</span>{jobProgress&&<progress aria-label={t("Postęp przygotowania klatek")} value={jobProgress.completed} max={jobProgress.total}/>}</div>}
   {step==='field'&&search&&<section className="observations" aria-label={t("Wyniki wyszukiwania")} id="search-results">
    {search.cached&&<p className="notice" role="status">{t(search.notice??'')}{search.retrieved_at?` ${t('Pobrano:')} ${date(search.retrieved_at)}.`:''}</p>}
    <div className="result-bar"><div><strong>{search.observations.length}  {t("obrazów")}</strong><span>{automaticSelection?t("Wstępny zestaw"):t("Wybrano")} {selected.length}  {t("zdjęć ·")} {new Set(selectedObs.map(o=>o.mjd)).size}  {t("różnych terminów")}</span></div><button className="primary" onClick={()=>void prepare()} disabled={selected.length<1||!!busy}>{t('Otwórz czas i pasma')} <ArrowRight size={15}/></button></div>
    <p>{t('Przygotujemy początkowy zestaw zdjęć. Pozostałe dostępne daty i pasma wybierzesz już w podglądzie.')}</p>
<details className="initial-selection" open={search.observations.length===0}><summary>{t('Dobór początkowych zdjęć (opcjonalnie)')}</summary>
    {search.observations.length>0&&<>{selectionPurpose==='time'&&<label className="check-label automatic-selection"><input type="checkbox" checked={automaticSelection} disabled={!!busy} onChange={e=>setAutomaticSelection(e.target.checked)}/>{t('Sprawdź lokalne pasma i jakość przed wyborem dat')}</label>}<div className="search-purpose" role="group" aria-label={t("Co chcesz obejrzeć?")}><button aria-pressed={selectionPurpose==='time'} disabled={!!busy} onClick={()=>{const proposal=proposeSeries(search.observations);setBand(proposal[0]?.band??'');setSelected(proposal.map(o=>o.id));setSelectionPurpose('time');setAutomaticSelection(true)}}>{t("Ruch i zmiany w czasie")}</button><button aria-pressed={selectionPurpose==='spectrum'} disabled={!!busy} onClick={()=>selectSpectrum(search)}>{t("Obraz w różnych pasmach")}</button><p>{t("Dobierzemy zdjęcia automatycznie. Otwórz zestaw przyciskiem powyżej.")}</p></div><details className="availability-summary"><summary>{t("Zaawansowany dobór zdjęć i detektorów")}</summary><p><strong>{t("Dostępność:")}</strong> {date(search.observations[0].date)} — {date(search.observations.at(-1)!.date)} · {search.collection.replace('spherex_','').toUpperCase()}.</p><div className="availability-bands">{[...new Set(search.observations.map(o=>o.band))].map(group=>{const rows=search.observations.filter(o=>o.band===group);return <button disabled={!!busy} key={group} onClick={()=>{setBand(group);setSelected(proposeSeries(rows).map(o=>o.id));setSelectionPurpose('time');setAutomaticSelection(false)}}>{group.replace('SPHEREx-','')} · {rows.length}  {t("zdjęć ·")} {new Set(rows.map(o=>o.mjd)).size}  {t("terminów")}</button>})}</div><p>{t("Wstępny dobór wybiera jeden detektor z największą liczbą terminów, a potem rozkłada do 8 klatek w czasie. Lokalne pasma i pokrycie sprawdzimy po pobraniu FITS. To propozycja do przeglądania.")}</p>{new Set(selectedObs.map(o=>o.mjd)).size<2&&<p role="status">{t("W tym zestawie brakuje zdjęć z różnych dat. Wybierz inne miejsce lub dobierz zdjęcia w ustawieniach zaawansowanych.")}</p>}<button className="text-button" disabled={!!busy} onClick={()=>{const proposal=proposeSeries(search.observations);setBand(proposal[0]?.band??'');setSelected(proposal.map(o=>o.id));setSelectionPurpose('time');setAutomaticSelection(true)}}>{t("Przywróć proponowany zestaw")}</button><button className="subtle" disabled={!!busy} onClick={()=>selectSpectrum(search)}>{t("Dobierz pasma z różnych detektorów")}</button>{selectionPurpose==='spectrum'&&<p role="status">{t("Wybrano do 12 obserwacji z różnych detektorów, możliwie blisko w czasie. Po pobraniu sprawdzimy rzeczywiste długości fal. Nie gwarantuje to pełnego widma ani zgodnych epok.")}</p>}</details></>}
    {search.observations.length===0?<p role="status">{t("Brak obserwacji dla tego pola w wybranym wydaniu. Sprawdź współrzędne, wybierz inne wydanie lub otwórz dostępny przykład.")}</p>:<details className="exposure-options"><summary>{t("Ręczny wybór zdjęć (zaawansowane)")}</summary><div className="exposure-filter"><label>{t("Detektor")} <select value={band} onChange={e=>setBand(e.target.value)}><option value="">{t("Wszystkie")}</option>{[...new Set(search.observations.map(o=>o.band))].map(v=><option key={v}>{v}</option>)}</select></label><span>{t("Wybierz 1–12 obrazów; animacja wymaga co najmniej 2 terminów.")}</span></div><div className="observation-scroll" tabIndex={0} role="region" aria-label={t("Lista obrazów")}><table className="observation-table"><thead><tr><th><span className="sr-only">{t("Wybór")}</span></th><th>{t("Data UTC")}</th><th>{t("Obserwacja")}</th><th>{t("Detektor")}</th></tr></thead><tbody>{filtered.map(o=><tr key={o.id} className={selected.includes(o.id)?'selected':''}><td><input type="checkbox" aria-label={`${t('Wybierz')} ${o.obs_id} · ${date(o.date)}`} checked={selected.includes(o.id)} disabled={!selected.includes(o.id)&&selected.length>=12||!!busy} onChange={()=>{setAutomaticSelection(false);setSelected(v=>v.includes(o.id)?v.filter(id=>id!==o.id):[...v,o.id])}}/></td><td>{date(o.date)}</td><td className="mono">{o.obs_id}</td><td>{o.band.replace('SPHEREx-','')}</td></tr>)}</tbody></table></div></details>}
</details>
   </section>}
   <section hidden={step!=='explore'} className="workspace-section" id="workspace" aria-label={t("Obszar pracy")}>
    <div className="workspace-heading"><nav className="workspace-tabs workbench-tools" aria-label={t("Narzędzia")}>{([{id:'compare',label:t('Obrazy')},{id:'sky',label:t('Mapa')},{id:'measure',label:t('Widmo i składanie')},{id:'irsa',label:t('Kalibracje i źródła')}] as const).filter(tab=>expert||!['measure','irsa'].includes(tab.id)).map(tab=><button key={tab.id} disabled={(!analysis||analysis.provisional)&&tab.id!=='compare'&&tab.id!=='sky'} aria-pressed={workspaceTab===tab.id} onClick={()=>{setWorkspaceTab(tab.id);setPlaying(false)}}>{t(tab.label)}</button>)}</nav><button className="subtle" onClick={share}>{copied?<Check size={14}/>:<Link size={14}/>} {copied?t('Skopiowano'):t('Kopiuj link')}</button></div>
    <div hidden={workspaceTab!=='compare'}>
    <div className={`workspace ${!analysis?'workspace-empty':''}`}>
     <div className="viewer-column"><div className="viewer-shell">
      {analysis&&<div className="viewer-toolbar"><div className="view-modes" role="group" aria-label={t('Sposób porównania')}><button aria-pressed={mode==='series'} onClick={()=>setMode('series')}>{t('Jedno zdjęcie')}</button><button aria-pressed={mode==='side'} onClick={()=>setMode('side')}>{t('Porównaj z A')}</button><button disabled={!!busy||!!explorerTarget&&explorerTarget.id!==analysis.frames[b].id} onClick={()=>{pauseExplorer();setA(b);setMode('side')}}>{t('Przypnij obecną datę jako A')}</button></div><div className="viewer-navigation"><button disabled={zoom===1} aria-label={t('Przesuwaj obraz')} aria-pressed={panMode} onClick={()=>setPanMode(value=>!value)}><Hand size={16}/></button><select aria-label={t('Powiększenie')} value={zoom} onChange={event=>setZoom(Number(event.target.value))}><option value="1">{t('Całe zdjęcie')}</option><option value="2">2×</option><option value="4">4×</option></select><button disabled={zoom===1} onClick={()=>{setZoom(1);setPanMode(false)}}>{t('Dopasuj')}</button></div></div>}
      {analysis?<>
       <div className="epoch-overlay">{(mode==='side'?[fa,fb]:[fb]).map((frame,slot)=>{const wave=sample?sample.frames.find(row=>row.id===frame.id)?.wavelength_um:frame.wavelength_um;return <span key={slot}><i className={mode==='side'&&slot===0?'badge-a':'badge-b'}>{mode==='side'&&slot===0?'A':'B'}</i><span>{date(frame.date)} UTC<small>{frame.band.replace('SPHEREx-','')} · {wave?.toFixed(4)??'—'} µm · {t(sample?'w punkcie':'w centrum')}</small></span></span>})}</div>
       <div className="viewer-stage">
       <Viewer key={analysis.search.id} interactive={!analysis.provisional&&!busy} frames={displayPair} frameTints={frameTints} a={0} b={1} mode={mode} selected={!!samplePoint} point={point} onPoint={setPoint} onPick={sampleAt} zoom={zoom} panMode={panMode} preloadImages={matchingPreview(1)?.frames.map(frame=>frame.image)} showMissing={showMissing} showQuality={true}/>
        {explorerTarget&&explorerTarget.id!==fb.id&&<div className="explorer-image-pending" role="status">{explorerTarget.id?(error&&!busy?t('Nie udało się wczytać wybranej obserwacji. Wybierz inne pasmo lub ponów próbę.'):t('Wczytuję wybraną obserwację…')):t('Brak wybranego pasma w tej dacie. Wybierz inne pasmo w panelu.')}<small>{explorerTarget.time} UTC</small></div>}
        {mode==='side'&&<ComparisonNotice notice={notice} playing={playing} intent={playbackAxis} displayComparison={splitDisplay&&JSON.stringify(effectiveDisplay[0])!==JSON.stringify(effectiveDisplay[1])}/>}
        {sampleBusy&&<div className="viewer-sampling" role="status">{t('Sprawdzam dane dla wybranego miejsca…')}</div>}
       </div>
       <div className="interaction-note">{panMode?t('Przeciągnij obraz, aby przesunąć widok.'):mode==='side'?t('Kliknij interesujący punkt — ten sam znacznik pojawi się na obu zdjęciach.'):t('To samo pole nieba. Termin i pasmo zmienisz suwakami obok obrazu.')}</div>
       <ImageQualityLegend frames={displayPair} a={0} b={1} mode={mode} qualities={actualQualities} showMissing={showMissing} onMissing={setShowMissing} split={splitDisplay} masks={[effectiveDisplay[0].mask,effectiveDisplay[1].mask]}/>
       {previewBusy&&<p className="preview-status" role="status">{t("Przygotowuję podgląd zdjęć…")}</p>}{previewError&&<p className="preview-status" role="alert">{previewError}</p>}
      </>:<div className="empty-view"><svg viewBox="0 0 100 100" width="80" height="80" fill="none" aria-hidden="true"><rect x="20" y="20" width="60" height="60" stroke="currentColor"/><path d="M50 10v80M10 50h80" stroke="currentColor" strokeDasharray="2 4"/><circle cx="44" cy="42" r="3" stroke="currentColor"/><circle cx="58" cy="58" r="3" stroke="currentColor"/></svg><h2>{t(busy?'Oczekiwanie na pierwsze zdjęcie…':'Zacznij od gotowego przykładu')}</h2><p>{t(busy?'Gotowe klatki pojawią się tutaj automatycznie.':'Otwórz dwa zdjęcia tego samego miejsca z różnych dat.')}</p>{!busy&&<button className="primary" onClick={chooseField}>{t('Wybierz pole')}</button>}</div>}
     </div>
     </div>
     {analysis&&<aside className="comparison-panel" aria-label={t("Wybór obrazów")}>
     {analysis&&<FieldExplorer key={analysis.search.id} analysis={analysis} currentId={fb.id} busy={!!busy} active={panel==='compare'&&step==='explore'&&workspaceTab==='compare'} pauseSignal={explorerPauseSignal} onApply={id=>applyObservationPair([analysis.frames[a].id,id],'custom',playbackAxis)} onState={(id,time)=>setExplorerTarget(previous=>previous&&previous.id===id&&previous.time===time?previous:{id,time})} onPlaying={setPlaying}/>}
    {expert&&<details className="manual-pair"><summary>{t('Ręczny dobór A/B')}</summary><ComparisonControls analysis={analysis} a={a} b={b} busy={!!busy} preset={pairPreset} shared={sharedDisplay} split={splitDisplay} personal={personalDisplay} onApply={ids=>applyObservationPair(ids)} onPreset={preset=>{pauseExplorer();void resetComparison(preset)}} onPause={pauseExplorer} onShared={setSharedDisplay} onSplit={setDisplaySplit} onPersonal={(slot,patch)=>{pauseExplorer();setPersonalDisplay(values=>values.map((value,index)=>index===slot?{...value,...patch}:value) as [DisplaySettings,DisplaySettings])}}/></details>}
      {sample&&<section className="point-readout" aria-label={t('Wskazana pozycja nieba')}><strong>{t('Wskazana pozycja')}</strong><dl><div><dt>RA · ICRS</dt><dd>{sample.ra.toFixed(6)}°</dd></div><div><dt>Dec · ICRS</dt><dd>{sample.dec.toFixed(6)}°</dd></div></dl></section>}
      <ComparisonDisplayControls analysis={analysis} a={a} b={b} busy={!!busy} preset={pairPreset} shared={sharedDisplay} split={splitDisplay} personal={personalDisplay} onApply={ids=>applyObservationPair(ids)} onPreset={preset=>{pauseExplorer();void resetComparison(preset)}} onPause={pauseExplorer} onShared={setSharedDisplay} onSplit={setDisplaySplit} onPersonal={(slot,patch)=>{pauseExplorer();setPersonalDisplay(values=>values.map((value,index)=>index===slot?{...value,...patch}:value) as [DisplaySettings,DisplaySettings])}}/>

     </aside>}
    </div>

    {analysis&&<details className="prepared-gallery" open><summary>{t('Przygotowane zdjęcia')} ({frames.length})</summary><FrameGallery showMissing={showMissing} analysis={analysis} a={a} b={b} seriesOnly={seriesOnly} series={series} onScope={only=>{setSeriesOnly(only);setPlaying(false)}} onSelect={index=>{pauseExplorer();setB(index);setPairPreset('custom');setSeriesOnly(false);setPlaying(false)}}/></details>}
    {analysis&&<details className="observation-checks"><summary>{t('Kontrola obserwacji i serii')} · {analysis.selection?.inspected??frames.length} {t('sprawdzonych')}</summary>
    {analysis&&<><SelectionReport analysis={analysis} activeIds={[fa.id,fb.id]}/><p className="comparison-question">{t(playbackAxis==='bands'?'Jak zmienia się wygląd między pasmami?':'Co zmieniło się między obserwacjami?')} <span>{t(playbackAxis==='bands'?'Porównaj długości fal i sprawdzaj rzeczywiste daty zdjęć.':'Obejrzyj serię, potem sprawdź przesunięcie albo jasność.')}</span></p><section className="series-status" aria-label={t("Przydatność serii")}><strong>{playbackAxis==='bands'?`${t('Pasma w odtwarzaniu:')} ${playback.length}.`:series.length>=2?`${t('Zdjęcia w porównywalnej serii:')} ${series.length}${sample?t(' — w zaznaczonym punkcie'):''}.`:frames.length===1?t('Dostępna jest jedna poprawna klatka. Animacja wymaga co najmniej dwóch.'):t('Brak serii o zbliżonych pasmach do oceny jasności. Możesz nadal przeglądać przesunięcia, sprawdzając geometrię i PSF.')}</strong><details><summary>{t("Dlaczego te zdjęcia?")}</summary><p>{sample?t('Sprawdzono ważność piksela i zbliżenie lokalnych pasm.'):analysis.selection?t('Sprawdzono lokalne pasma i pokrycie przy pozycji użytej do doboru w każdej dacie. Kliknięcie punktu zastępuje te kontrole danymi z wybranej stałej pozycji.'):t('Sprawdzono zbliżenie pasm w centrum i co najmniej 80% ważnego pokrycia każdej klatki. Kliknij punkt, aby sprawdzić pasma lokalnie.')}  {t("Wyrównanie pozycji nie wyrównuje PSF ani tła. Próg pasm jest heurystyką, bez gwarancji porównywalności naukowej.")}</p><label className="check-label"><input type="checkbox" checked={seriesOnly} onChange={e=>setSeriesOnly(e.target.checked)}/>  {t("Odtwarzaj tylko serię spełniającą te warunki")}</label>{series.length<2&&<p>{t("Możesz obejrzeć wszystkie klatki po wyłączeniu filtra. Aby oceniać zmiany, wybierz inne obserwacje.")}</p>}<div className="context-actions"><button disabled={!!busy} onClick={()=>{showField();setSearch(analysis.search)}}>{t("Wybierz inne obserwacje")}</button><button disabled={!!busy} onClick={()=>void searchField()}>{t("Sprawdź nowe obserwacje")}</button></div></details>{analysis.failures.length>0&&<div role="status"><p>{t("Nie udało się przygotować")} {analysis.failures.length}  {t("z")} {frames.length+analysis.failures.length}  {t("klatek. Udane wyniki zachowano.")}</p><button disabled={!!busy} onClick={()=>void prepare(true)}>{t("Ponów nieudane klatki")}</button><details><summary>{t("Przyczyny niepowodzenia")}</summary>{analysis.failures.map(f=><p key={f.observation}>{f.observation}: {t(f.error)}</p>)}</details></div>}</section></>}
    </details>}

    {analysis&&<details className="analysis-details"><summary>{t("Dane, eksport i skróty klawiaturowe")}</summary><p className="mono">ICRS {analysis.search.ra.toFixed(5)}°, {analysis.search.dec.toFixed(5)}° · {analysis.search.fov_arcmin}′ · {analysis.search.collection}</p><a href={apiUrl(`/api/analyses/${analysis.id}/export`)}>{t("Pobierz parametry analizy (JSON)")}</a><p>{t("Suwaki zmieniają datę i pasmo. X zamienia A/B w porównaniu. Na obrazie strzałki przesuwają punkt, Enter go wybiera.")}</p><ul>{analysis.limitations.map(s=><li key={s}>{t(s)}</li>)}</ul>{analysis.failures.map(f=><p key={f.observation}>{f.observation}: {t(f.error)}</p>)}</details>}
    </div>
    {step==='explore'&&workspaceTab==='sky'&&<SkyContext expert={expert} ra={ra} dec={dec} fov={fov} collection={collection} analysis={analysis} frameDate={fb?.date} onField={(r,d)=>{setFieldMethod('coordinates');setRa(r);setDec(d);setStep('field');setSearch(null);pauseExplorer();const url=new URL(location.href);url.search='';url.searchParams.set('ra',r);url.searchParams.set('dec',d);url.searchParams.set('fov',String(fov));url.searchParams.set('collection',collection);url.searchParams.set('lang',language);history.replaceState(null,'',url)}}/>}
    {analysis&&!analysis.provisional&&<div hidden={workspaceTab!=='measure'}><SpectralAnalysis analysis={analysis} point={samplePoint??point} a={a} b={b} hasPoint={!!samplePoint}/></div>}
    {analysis&&!analysis.provisional&&<div hidden={workspaceTab!=='irsa'}><IrsaWorkbench key={analysis.id} analysis={analysis} point={samplePoint??point} a={a} hasPoint={!!samplePoint} onSelect={(p,frameId)=>{const index=analysis.frames.findIndex(f=>f.id===frameId);if(index>=0){setA(index);if(index===b)setB(Math.max(0,analysis.frames.findIndex((_,i)=>i!==index)))}setPlaying(false);setMode('side');setSeriesOnly(false);setWorkspaceTab('compare');void sampleAt(p)}}/></div>}
   </section>
   </div>
   <footer className="app-footer"><span>{t("Dane: NASA / JPL-Caltech / IPAC · Niezależny prototyp")}</span><span>{t("Braki danych są oznaczone osobnym tłem")}</span></footer>
  </main>
 </div>;
}
