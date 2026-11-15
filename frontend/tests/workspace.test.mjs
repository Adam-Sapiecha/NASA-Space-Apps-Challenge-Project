import test from 'node:test';
import assert from 'node:assert/strict';
import {workspaceEntry,workspacePanel,displayMode,fieldStep,initialFieldMethod} from '../src/workspace.ts';

test('field steps start with a choice, restore custom fields and bypass setup for saved work',()=>{
 for(const query of ['', 'lang=pl', 'panel=compare', 'interface=advanced'])assert.equal(fieldStep(new URLSearchParams(query)),'choose');
 for(const query of ['ra=12&dec=3','ra=&dec=','dec=-7'])assert.equal(fieldStep(new URLSearchParams(query)),'field');
 for(const query of ['analysis=saved','job=running&ra=12','analysis=saved&view=measure','note=n','irsa=r','science=s'])assert.equal(fieldStep(new URLSearchParams(query)),'explore');
});

test('the shared shell opens field exploration while preserving explicit tools and saved task links',()=>{
 assert.equal(workspacePanel(new URLSearchParams()),'compare');
 assert.equal(workspacePanel(new URLSearchParams('panel=brightness')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('analysis=mine')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('ra=12&dec=3')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('job=running')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('guided=1')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('prediction=1')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('analysis=mine&panel=prediction')),'compare');
 assert.equal(workspacePanel(new URLSearchParams('analysis=mine&panel=motion')),'motion');
 assert.equal(workspacePanel(new URLSearchParams('panel=unknown&analysis=mine')),'compare');
});

test('the removed brightness guide redirects to the workbench with prepared data',()=>{
 assert.deepEqual(workspaceEntry(new URLSearchParams(),'prepared'),{workbench:true,analysisId:'prepared',tab:'compare'});
 assert.deepEqual(workspaceEntry(new URLSearchParams('guided=1'),'prepared'),{workbench:true,analysisId:'prepared',tab:'compare'});
});
test('custom coordinates and explicit analyses are never replaced by the example',()=>{
 assert.equal(workspaceEntry(new URLSearchParams('ra=12&dec=3'),'prepared').analysisId,null);
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine'),'prepared').analysisId,'mine');
 assert.equal(workspaceEntry(new URLSearchParams('job=running'),'prepared').analysisId,null);
});
test('saved notes and old IRSA links still open their results after tools are separated',()=>{
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&note=n'),'prepared').tab,'compare');
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&view=measure&irsa=r'),'prepared').tab,'irsa');
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&view=result&irsa=r'),'prepared').tab,'compare');
 for(const view of ['compare','sky','measure','irsa'])assert.equal(workspaceEntry(new URLSearchParams({view}),'prepared').tab,view);
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&view=spectrum'),'prepared').tab,'compare');
});

test('removed viewer modes cannot be reactivated by saved links',()=>{
 for(const value of ['lens','blink','route','spectral','garbage'])assert.equal(displayMode(value),'side');
 assert.equal(displayMode('series'),'series');
 assert.equal(displayMode(null),'series');
});

test('field input methods default to the object list and restore explicit coordinates or map selection',()=>{
 assert.equal(initialFieldMethod(new URLSearchParams()),'object');
 assert.equal(initialFieldMethod(new URLSearchParams('ra=&dec=')),'object');
 assert.equal(initialFieldMethod(new URLSearchParams('ra=0&dec=0')),'coordinates');
 assert.equal(initialFieldMethod(new URLSearchParams('ra=12&dec=3&picker=map')),'map');
 assert.equal(initialFieldMethod(new URLSearchParams('picker=invalid')),'object');
});
