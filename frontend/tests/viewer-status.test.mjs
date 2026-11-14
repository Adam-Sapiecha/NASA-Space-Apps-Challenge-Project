import test from 'node:test';
import assert from 'node:assert/strict';
import {comparisonNotice,pixelFlagSummary} from '../src/viewerStatus.ts';

const frames=[{id:'a',wavelength_um:1,bandwidth_um:.04,warned_fraction:.01},
 {id:'b',wavelength_um:2,bandwidth_um:.04,warned_fraction:.2}];

test('a series can replay its reference frame without a duplicate-image warning',()=>{
 assert.equal(comparisonNotice(frames,0,0,'series',null),null);
 assert.equal(comparisonNotice(frames,0,0,'side',null).kind,'same');
});

test('band notices use the target-local selection instead of unrelated field-centre bands',()=>{
 const selection={candidates:[{id:'a',wavelength_um:4.5,bandwidth_um:.04},{id:'b',wavelength_um:4.51,bandwidth_um:.04}]};
 assert.equal(comparisonNotice(frames,0,1,'side',null,selection),null);
 assert.deepEqual(comparisonNotice(frames,0,1,'side',null),{kind:'bands',location:'centre'});
 const sample={frames:[{id:'a',valid:true,wavelength_um:3,bandwidth_um:.04},{id:'b',valid:true,wavelength_um:4,bandwidth_um:.04}]};
 assert.deepEqual(comparisonNotice(frames,0,1,'side',sample,selection),{kind:'bands',location:'point'});
});

test('missing pixels and unknown wavelengths do not become claims of different bands',()=>{
 assert.equal(comparisonNotice(frames,0,1,'side',{frames:[]}).kind,'missing');
 const unknown=[frames[0],{...frames[1],wavelength_um:null}];
 assert.equal(comparisonNotice(unknown,0,1,'side',null).kind,'unknown');
 const local={frames:[{id:'a',valid:true,wavelength_um:1,bandwidth_um:.04},{id:'b',valid:true,wavelength_um:null,bandwidth_um:.04}]};
 assert.equal(comparisonNotice(frames,0,1,'side',local).kind,'unknown');
});

test('flag percentages follow only the displayed frames and retain a stable series label',()=>{
 assert.deepEqual(pixelFlagSummary(frames,0,1,'series'),[{index:1,label:'2',fraction:.2}]);
 assert.deepEqual(pixelFlagSummary(frames,0,0,'series'),[{index:0,label:'2',fraction:.01}]);
 assert.equal(pixelFlagSummary(frames,0,0,'side').length,1);
 assert.equal(pixelFlagSummary([{id:'x'}],0,0,'series')[0].fraction,null);
 assert.equal(pixelFlagSummary([{id:'x',warned_fraction:NaN}],0,0,'series')[0].fraction,null);
});
