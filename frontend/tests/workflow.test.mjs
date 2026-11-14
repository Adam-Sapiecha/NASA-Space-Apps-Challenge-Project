import test from 'node:test';
import assert from 'node:assert/strict';
import {proposeSeries,comparisonSeries,closeBands,nextFrame,validPoint} from '../src/workflow.ts';

const observation=(id,mjd,band='D1')=>({id,mjd,band});
const frame=(id,mjd,wavelength,coverage=1)=>({...observation(id,mjd),coverage,wavelength_um:wavelength,bandwidth_um:.04});
test('proposal chooses distinct times, rather than privileging D2 or simultaneous images',()=>{
 const observations=[observation('a',0),observation('b',5),observation('c',10),observation('d',0,'D2'),observation('e',0,'D2'),observation('f',0,'D2'),observation('g',0,'D2')];
 assert.deepEqual(proposeSeries(observations).map(o=>o.id),['a','b','c']);
 assert.deepEqual(proposeSeries([]),[]);
});
test('proposal spans sparse time coverage despite a dense cluster of early images',()=>{
 const observations=[...Array.from({length:90},(_,i)=>observation(String(i),i/100)),observation('middle',50),observation('end',100)];
 const result=proposeSeries(observations,3);
 assert.deepEqual(result.map(o=>o.id),['0','middle','end']);
});
test('series requires mutual spectral compatibility, not a chain of overlapping neighbours',()=>{
 const frames=[frame('a',0,1),frame('b',10,1.015),frame('c',20,1.03)];
 const result=comparisonSeries(frames);
 assert.equal(result.length,2);
 assert.ok(closeBands(frames[result[0]],frames[result[1]]));
});
test('local checks replace centre checks and reject invalid or missing local pixels',()=>{
 const frames=[frame('a',0,1),frame('b',10,1),frame('c',20,1,.5)];
 const sample={frames:[{id:'a',valid:false,wavelength_um:1,bandwidth_um:.04},{id:'b',valid:true,wavelength_um:2,bandwidth_um:.04},{id:'c',valid:true,wavelength_um:2.01,bandwidth_um:.04}]};
 assert.deepEqual(comparisonSeries(frames),[0,1]);
 assert.deepEqual(comparisonSeries(frames,sample),[1,2]);
 assert.deepEqual(comparisonSeries(frames,{frames:[]}),[]);
});
test('no temporal series is fabricated from simultaneous or invalid metadata',()=>{
 assert.deepEqual(comparisonSeries([frame('a',0,1),frame('b',0,1)]),[]);
 assert.equal(closeBands({wavelength_um:null,bandwidth_um:.04},{wavelength_um:1,bandwidth_um:.04}),false);
 assert.equal(closeBands({wavelength_um:1,bandwidth_um:0},{wavelength_um:1,bandwidth_um:.04}),false);
});
test('playback steps only through allowed frames and handles absent current frame',()=>{
 assert.equal(nextFrame(2,[0,2,5]),5);
 assert.equal(nextFrame(0,[0,2,5],-1),5);
 assert.equal(nextFrame(1,[0,2,5]),0);
 assert.equal(nextFrame(1,[]),1);
});
test('shared points require finite, bounded coordinates',()=>{
 assert.equal(validPoint({x:.2,y:.5}),true);
 for(const p of [null,{}, {x:NaN,y:0},{x:0,y:2},{x:'0',y:0}])assert.equal(validPoint(p),false);
});

test('validated local target coverage permits playback despite incomplete field edges',()=>{
 const frames=[frame('a',0,1,.4),frame('b',100,2,.5)];
 const selection={candidates:[{id:'a',central_valid:true,local_coverage:1,wavelength_um:4.5,bandwidth_um:.04},
  {id:'b',central_valid:true,local_coverage:1,wavelength_um:4.51,bandwidth_um:.04}]};
 assert.deepEqual(comparisonSeries(frames),[]);
 assert.deepEqual(comparisonSeries(frames,null,selection),[0,1]);
 // Clicking a point replaces the catalogue-position checks, including failures.
 assert.deepEqual(comparisonSeries(frames,{frames:[]},selection),[]);
 selection.candidates[1].central_valid=false;
 assert.deepEqual(comparisonSeries(frames,null,selection),[]);
});
