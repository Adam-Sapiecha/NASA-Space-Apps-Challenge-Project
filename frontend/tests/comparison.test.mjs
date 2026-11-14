import test from 'node:test';
import assert from 'node:assert/strict';
import {bestPair,prediction} from '../src/types.ts';

// Synthetic metadata for controlled unit tests; no NASA observations represented.
const frame=(mjd,wavelength,coverage=1)=>({mjd,wavelength_um:wavelength,bandwidth_um:.04,coverage});
test('chooses the longest comparable baseline, not simply first and last images',()=>{
 assert.deepEqual(bestPair([frame(0,1.2),frame(1,1.4),frame(100,1.21),frame(120,1.6)]),[0,2]);
});
test('does not silently substitute an incompatible spectral pair',()=>{
 assert.equal(bestPair([frame(0,1.2),frame(100,1.4)]),null);
});
test('does not choose poorly covered frames merely for a longer baseline',()=>{
 assert.deepEqual(bestPair([frame(0,1.2,.2),frame(1,1.2),frame(100,1.21)]),[1,2]);
});
test('simultaneous exposures do not form a temporal baseline',()=>{
 assert.equal(bestPair([frame(0,1.2),frame(0,1.21)]),null);
});
test('track interpolates by observation time rather than frame index',()=>{
 const anchors=[{x:.2,y:.1,mjd:10},{x:.6,y:.5,mjd:30}];
 const p=prediction(anchors,15);
 assert.ok(Math.abs(p.x-.3)<1e-10);
 assert.ok(Math.abs(p.y-.2)<1e-10);
 assert.equal(prediction([anchors[0],anchors[0]],15),null);
});
