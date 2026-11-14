export type WorkspaceTab='compare'|'sky'|'measure'|'spectrum'|'irsa'|'result';

export function workspaceDefaults(query:URLSearchParams){
 const explicitField=['analysis','ra','dec','note','view'].some(key=>query.has(key));
 return {
  expert:query.get('interface')==='advanced'||query.has('note')||['measure','irsa'].includes(query.get('view')??'')||query.has('irsa')||query.has('science'),
  motionOpen:query.get('motion')==='1'||(!explicitField&&query.get('motion')!=='0'&&query.get('guided')!=='1'),
 };
}

export function workspaceEntry(query:URLSearchParams,exampleId:string):{workbench:boolean;analysisId:string|null;tab:WorkspaceTab}{
 const workbench=query.get('guided')!=='1'||query.get('interface')==='advanced'||query.has('analysis')||query.has('ra')||query.has('dec');
 const analysisId=query.get('analysis')??(workbench&&!query.has('ra')&&!query.has('dec')?exampleId:null);
 const view=query.get('view');
 let tab:WorkspaceTab='compare';
 if(view&&['compare','sky','measure','spectrum','irsa','result'].includes(view))tab=view as WorkspaceTab;
 // Reports saved before the navigation split used the shared measurement tab.
 if((!view||view==='measure')&&(query.has('irsa')||query.has('science')))tab='irsa';
 if(query.has('note')&&!view)tab='result';
 return {workbench,analysisId,tab};
}
