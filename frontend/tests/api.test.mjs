import test from 'node:test';
import assert from 'node:assert/strict';
import {api} from '../src/types.ts';

test('archive proxy HTML 503 has a useful retry message instead of a JSON parser error',async()=>{
 const saved=globalThis.fetch;
 try{globalThis.fetch=async()=>new Response('<html>Service unavailable</html>',{status:503});await assert.rejects(api('/api/search'),/HTTP 503/)}finally{globalThis.fetch=saved}
});
test('structured validation errors remain available, and network loss is actionable',async()=>{
 const saved=globalThis.fetch;
 try{
  globalThis.fetch=async()=>Response.json({detail:'Invalid coordinates'},{status:422});await assert.rejects(api('/api/search'),/Invalid coordinates/);
  globalThis.fetch=async()=>{throw new TypeError('Failed to fetch')};await assert.rejects(api('/api/search'),/Cannot connect to the server/);
 }finally{globalThis.fetch=saved}
});
