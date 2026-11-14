import test from 'node:test';
import assert from 'node:assert/strict';
import {guidedVerdict} from '../src/guidedResult.ts';

test('a large formal difference must never be presented as confirmed variability',()=>{
 assert.equal(guidedVerdict({status:'requires_validation',metrics:{delta_mjy:1000,random_error_mjy:.001},checks:[]}), 'unconfirmed');
});
test('blocked comparisons cannot display a brightness conclusion even with numeric metrics',()=>{
 assert.equal(guidedVerdict({status:'blocked',metrics:{delta_mjy:1,random_error_mjy:.1},checks:[]}), 'unavailable');
});
test('missing or invalid measurements never become a successful result',()=>{
 for(const metrics of [null,{delta_mjy:NaN,random_error_mjy:1},{delta_mjy:1,random_error_mjy:0}])assert.equal(guidedVerdict({status:'requires_validation',metrics,checks:[]}), 'unavailable');
});
