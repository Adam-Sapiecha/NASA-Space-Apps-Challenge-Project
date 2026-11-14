import test from 'node:test';
import assert from 'node:assert/strict';
import {observationCatalogue,bandChoices,pairForBand,defaultPair,spectralPair,temporalPairForObservation,playbackFrames,displayFromQuery,DEFAULT_DISPLAY} from '../src/comparison.ts';
import {recommendedAnalysis} from '../src/workflow.ts';

const row=(id,mjd,band='D1',wave=1)=>({id,mjd,band,date:'2026-01-01T00:00:00',em_min_um:wave,em_max_um:wave+.1,wavelength_um:wave,bandwidth_um:.04,coverage:1,masked_flags:[]});
const observations=[row('a',0),row('b',300),row('c',300,'D4',3),row('d',301,'D1',1),row('e',301,'D4',3)];
const analysis={id:'root',frames:observations.slice(0,2),failures:[],search:{observations},selection:{pair_ids:['a','b'],selected_ids:['a','b'],candidates:observations.slice(0,2)}};

test('all real archive observations remain selectable while only prepared frames are marked ready',()=>{
 const catalogue=observationCatalogue(analysis);
 assert.equal(catalogue.length,5);
 assert.deepEqual(catalogue.filter(row=>row.ready).map(row=>row.id),['a','b']);
 assert.equal(catalogue.find(row=>row.id==='c').wavelength_um,null);
});

test('shared-band proposals preserve exact dates where available and otherwise return actual nearest observations',()=>{
 const rows=observations.map(row=>({...row,ready:true}));
 const groups=bandChoices(rows);
 const d1=groups.find(group=>group.band==='D1');
 assert.deepEqual(pairForBand(d1,rows,['a','b']),['a','b']);
 const d4=groups.find(group=>group.band==='D4');
 assert.deepEqual(pairForBand(d4,rows,['a','b']),['c','e']);
 const chain=[row('x',0,'D1',1),row('y',1,'D1',1.015),row('z',2,'D1',1.03)].map(row=>({...row,ready:true}));
 assert.equal(bandChoices(chain).length,2);
});

test('switching to bands proposes different detectors close to the requested epoch',()=>{
 const rows=observations.map(row=>({...row,ready:true}));
 assert.deepEqual(spectralPair(rows,300),['b','c']);
 assert.equal(spectralPair(rows.filter(row=>row.band==='D1'),300),null);
});

test('motion preset stays in the selected local band instead of returning to an unrelated default',()=>{
 const expanded={...analysis,frames:observations};
 assert.deepEqual(temporalPairForObservation(expanded,'c'),['c','e']);
 assert.deepEqual(temporalPairForObservation(expanded,'b'),['a','d']);
 const validated={...expanded,selection:{...analysis.selection,candidates:analysis.selection.candidates.map(row=>({...row,aperture_valid:true}))}};
 assert.deepEqual(temporalPairForObservation(validated,'b'),['a','b']);
 assert.equal(temporalPairForObservation(analysis,'c'),null);
});

test('adding custom frames retains the recommended default without hiding the workspace pool',()=>{
 const expanded={...analysis,frames:observations,workspace:{recommended_pair_ids:['a','b'],recommended_ids:['a','b']}};
 assert.deepEqual(defaultPair(expanded),['a','b']);
 assert.equal(recommendedAnalysis(expanded),expanded);
});

test('time playback keeps matching wavelengths and recommended defaults; custom wavelength playback retains real dates',()=>{
 const expanded={...analysis,frames:observations};
 assert.deepEqual(playbackFrames(expanded,null,1,'time','auto'),[0,1]);
 assert.deepEqual(playbackFrames(expanded,null,1,'time','custom'),[0,1,3]);
 const indices=playbackFrames(expanded,null,2,'bands','bands');
 assert.ok(indices.every(index=>Math.abs(observations[index].mjd-300)<=1));
 assert.equal(indices.length,2);
 assert.equal(playbackFrames(expanded,null,2,'bands','custom').length,5);
});

test('independent display choices can be restored while the general defaults remain shared and uncoloured',()=>{
 assert.deepEqual(displayFromQuery(new URLSearchParams()),DEFAULT_DISPLAY);
 const query=new URLSearchParams('qualityA=valid&rangeA=faint&maskA=1&tintB=1&rangeB=full');
 assert.deepEqual(displayFromQuery(query,'A'),{quality:'valid',range:'faint',mask:true,tint:false});
 assert.deepEqual(displayFromQuery(query,'B'),{quality:'all',range:'full',mask:false,tint:true});
});
