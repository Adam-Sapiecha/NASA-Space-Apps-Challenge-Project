import test from 'node:test';
import assert from 'node:assert/strict';
import {spectralFrames,proposeSpectral,spectralTemporalPair} from '../src/spectral.ts';

const frame=(id,mjd,wavelength)=>({id,mjd,wavelength_um:wavelength,bandwidth_um:.04,coverage:1});
test('spectral playback is wavelength ordered, retaining repeated channels and observation identity',()=>{
 const frames=[frame('red',1,4),frame('blue',3,1),frame('blue-repeat',2,1)];
 assert.deepEqual(spectralFrames(frames,null).map(r=>r.index),[2,1,0]);
});
test('source wavelengths supersede centre wavelengths and gaps are never filled from centre',()=>{
 const frames=[frame('a',0,1),frame('b',1,2),frame('c',2,3)];
 const sample={frames:[{id:'a',valid:false,wavelength_um:4,bandwidth_um:.1,flags:['BAD']},{id:'b',valid:true,wavelength_um:null}]};
 assert.deepEqual(spectralFrames(frames,sample),[{index:0,wavelength:4,bandwidth:.1,valid:false,flags:['BAD']}]);
});
test('invalid spectral metadata cannot become an invented channel',()=>{
 assert.deepEqual(spectralFrames([frame('a',0,NaN),frame('b',0,0),frame('c',0,-1)],null),[]);
});
test('spectral proposal covers detectors close in time, rather than taking a distant first row',()=>{
 const observations=[{id:'a-far',band:'D1',mjd:0},{id:'a',band:'D1',mjd:100},{id:'b',band:'D2',mjd:100.01},{id:'c',band:'D3',mjd:100.02}];
 assert.deepEqual(new Set(proposeSpectral(observations,3).map(r=>r.id)),new Set(['a','b','c']));
});
test('spectral proposal respects the analysis limit and keeps distinct products',()=>{
 const observations=Array.from({length:6},(_,d)=>Array.from({length:8},(_,i)=>({id:`${d}-${i}`,mjd:100+i/10,band:`D${d}`}))).flat();
 const result=proposeSpectral(observations);
 assert.equal(result.length,12);assert.equal(new Set(result.map(r=>r.id)).size,12);assert.equal(new Set(result.map(r=>r.band)).size,6);
 assert.deepEqual(proposeSpectral([]),[]);
});
test('time comparison remains anchored to the selected channel even outside the largest group',()=>{
 const frames=[frame('a',0,1),frame('b',1,1),frame('c',2,1),frame('red',0,4),frame('red-later',10,4.01)];
 assert.deepEqual(spectralTemporalPair(frames,null,3),[3,4]);
 assert.equal(spectralTemporalPair(frames,null,10),null);
});
test('time comparison refuses simultaneous, incompatible, or locally invalid observations',()=>{
 const frames=[frame('a',0,1),frame('b',0,1),frame('c',10,2)];
 assert.equal(spectralTemporalPair(frames,null,0),null);
 assert.equal(spectralTemporalPair(frames,{frames:[{id:'a',valid:false,wavelength_um:1,bandwidth_um:.04}]},0),null);
});
