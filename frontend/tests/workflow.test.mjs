import test from 'node:test';
import assert from 'node:assert/strict';
import {proposeSeries,comparisonSeries,closeBands,nextFrame,validPoint,recommendedAnalysis} from '../src/workflow.ts';

const observation=(id,mjd,band='D1')=>({id,mjd,band});
const frame=(id,mjd,wavelength,coverage=1)=>({...observation(id,mjd),coverage,wavelength_um:wavelength,bandwidth_um:.04});

test('saved full galleries reopen the recommended frames and retain measurement warnings',()=>{
 const frames=Array.from({length:36},(_,i)=>frame(String(i),i,i<2?1:i));
 const saved={frames,failures:[{observation:'35',error:'archive failure'}],selection:{selected_ids:['0','1'],pair_ids:['0','1'],status:'image_pair_only'}};
 const result=recommendedAnalysis(saved);
 assert.deepEqual(result.frames.map(f=>f.id),['0','1']);
 assert.equal(saved.frames.length,36);
 assert.equal(result.selection.status,'image_pair_only');
 assert.equal(result.failures.length,0);
 const manual={frames,failures:[]};
 assert.equal(recommendedAnalysis(manual),manual);
});

test('full 48-frame galleries find the best series without exponential subset search',()=>{
 const frames=Array.from({length:48},(_,i)=>frame(String(i),Math.floor(i/2),1));
 const result=comparisonSeries(frames);
 assert.equal(result.length,24);
 assert.equal(new Set(result.map(i=>frames[i].mjd)).size,24);
});

test('wavelength-extreme search agrees with exhaustive search for varied widths and repeated dates',()=>{
 let seed=19;
 const random=()=>((seed=(seed*1664525+1013904223)>>>0)/2**32);
 for(let run=0;run<80;run++){
  const frames=Array.from({length:9},(_,i)=>({...frame(String(i),Math.floor(random()*6),1+random()*.1),bandwidth_um:.01+random()*.16}));
  let count=0,span=-1;
  for(let mask=1;mask<1<<frames.length;mask++){
   const chosen=frames.filter((_,i)=>mask>>i&1);
   if(chosen.length<2||!chosen.every((a,i)=>chosen.slice(i+1).every(b=>a.mjd!==b.mjd&&closeBands(a,b))))continue;
   const gap=Math.max(...chosen.map(f=>f.mjd))-Math.min(...chosen.map(f=>f.mjd));
   if(chosen.length>count||chosen.length===count&&gap>span){count=chosen.length;span=gap}
  }
  const result=comparisonSeries(frames);
  assert.equal(result.length,count);
  if(result.length)assert.equal(frames[result.at(-1)].mjd-frames[result[0]].mjd,span);
 }
});
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
