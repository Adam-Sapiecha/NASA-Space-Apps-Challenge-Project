export type WorkspaceTab='compare'|'sky'|'measure'|'irsa';
export type WorkspacePanel='motion'|'compare';
export type FieldStep='choose'|'field'|'explore';
export type FieldMethod='object'|'map'|'coordinates';
export function initialFieldMethod(query:URLSearchParams):FieldMethod{
 const picker=query.get('picker');
 if(picker==='map'||picker==='coordinates'||picker==='object')return picker;
 return query.get('ra')?.trim()||query.get('dec')?.trim()?'coordinates':'object';
}

export function fieldStep(query:URLSearchParams):FieldStep{
 if(['analysis','job','note','irsa','science'].some(key=>query.has(key)))return 'explore';
 if(query.has('ra')||query.has('dec'))return 'field';
 return 'choose';
}

export function displayMode(value:string|null):'side'|'series'{return value===null||value==='series'?'series':'side'}

export function workspacePanel(query:URLSearchParams):WorkspacePanel{
 const saved=query.get('panel');
 if(saved==='brightness'||saved==='prediction'||query.get('prediction')==='1'||query.get('guided')==='1')return 'compare';
 if(['motion','compare'].includes(saved??''))return saved as WorkspacePanel;
 return query.get('motion')==='1'?'motion':'compare';
}

export function workspaceDefaults(query:URLSearchParams){
 const explicitField=['analysis','job','ra','dec','note','view'].some(key=>query.has(key));
 return {
  expert:query.get('interface')==='advanced'||query.has('note')||['measure','irsa'].includes(query.get('view')??'')||query.has('irsa')||query.has('science'),
  motionOpen:query.get('motion')==='1'||(!explicitField&&query.get('motion')!=='0'&&query.get('guided')!=='1'),
 };
}

export function workspaceEntry(query:URLSearchParams,exampleId:string):{workbench:boolean;analysisId:string|null;tab:WorkspaceTab}{
 const workbench=true;
 const analysisId=query.get('analysis')??(workbench&&!query.has('job')&&!query.has('ra')&&!query.has('dec')?exampleId:null);
 const view=query.get('view');
 let tab:WorkspaceTab='compare';
 if(view&&['compare','sky','measure','irsa'].includes(view))tab=view as WorkspaceTab;
 if(view==='spectrum')tab='compare';
 // Reports saved before the navigation split used the shared measurement tab.
 if((!view||view==='measure')&&(query.has('irsa')||query.has('science')))tab='irsa';
 return {workbench,analysisId,tab};
}
