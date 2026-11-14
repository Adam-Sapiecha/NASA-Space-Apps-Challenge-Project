import test from 'node:test';
import assert from 'node:assert/strict';
import {workspaceEntry} from '../src/workspace.ts';

test('the homepage opens the complete workbench and prepared data; guide is opt-in',()=>{
 assert.deepEqual(workspaceEntry(new URLSearchParams(),'prepared'),{workbench:true,analysisId:'prepared',tab:'compare'});
 assert.deepEqual(workspaceEntry(new URLSearchParams('guided=1'),'prepared'),{workbench:false,analysisId:null,tab:'compare'});
});
test('custom coordinates and explicit analyses are never replaced by the example',()=>{
 assert.equal(workspaceEntry(new URLSearchParams('ra=12&dec=3'),'prepared').analysisId,null);
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine'),'prepared').analysisId,'mine');
});
test('saved notes and old IRSA links still open their results after tools are separated',()=>{
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&note=n'),'prepared').tab,'result');
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&view=measure&irsa=r'),'prepared').tab,'irsa');
 assert.equal(workspaceEntry(new URLSearchParams('analysis=mine&view=result&irsa=r'),'prepared').tab,'result');
 for(const view of ['compare','sky','spectrum','measure','irsa','result'])assert.equal(workspaceEntry(new URLSearchParams({view}),'prepared').tab,view);
});
