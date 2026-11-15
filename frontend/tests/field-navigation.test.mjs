import test from 'node:test';
import assert from 'node:assert/strict';
import {observationDays,fieldTimeline,bandsOnDay,bandAtTime,skippedDays} from '../src/fieldNavigation.ts';
const row=(id,mjd,band='D1',wave=1,min=.75,max=1.2)=>({id,mjd,band,wavelength_um:wave,em_min_um:min,em_max_um:max,ready:false});

test('time includes both exposures of one UTC day, while the band control has one detector',()=>{
 const rows=[row('late',60000.6,'D6',4.61,4.4,5),row('early',60000.45,'D6',4.48,4.4,5)];
 assert.equal(observationDays(rows).length,1);
 assert.deepEqual(fieldTimeline(rows,'D6').map(row=>row.id),['early','late']);
 assert.equal(bandsOnDay(rows,60000.5).length,1);
});
test('time skips days without the selected detector and never invents missing exposures',()=>{
 const rows=[row('first',60000.4,'D6'),row('other-band',60001.4,'D3'),row('last',60002.4,'D6'),row('invalid',NaN,'D6')];
 assert.deepEqual(fieldTimeline(rows,'D6').map(row=>row.id),['first','last']);
 assert.equal(skippedDays(rows,'D6'),1);
 assert.equal(bandAtTime(rows,'D6',60001.4),null);
});
test('preparing wavelengths and readiness cannot move time steps, detector groups or day rows',()=>{
 const rows=[row('early',60000.1,'D3',null,1.63,2.43),row('late',60000.5,'D3',null,1.63,2.43),row('d6',60000.2,'D6',null,4.4,5)];
 const prepared=rows.map(row=>({...row,ready:true,wavelength_um:row.id==='early'?2.4:.8}));
 const ids=rows=>observationDays(rows)[0].rows.map(row=>row.id);
 assert.deepEqual(ids(prepared),ids(rows));
 assert.deepEqual(fieldTimeline(prepared,'D3').map(row=>row.id),fieldTimeline(rows,'D3').map(row=>row.id));
 assert.deepEqual(bandsOnDay(prepared,60000.1).map(group=>group.band),['D3','D6']);
});
test('switching bands selects the nearest actual time on that UTC day, without preferring cache state',()=>{
 const rows=[row('anchor',60000.4),{...row('far-ready',60000.8,'D3'),ready:true},row('near',60000.41,'D3'),row('other-day',60001.4,'D3')];
 assert.equal(bandAtTime(rows,'D3',60000.4).id,'near');
 assert.equal(bandAtTime(rows,'D5',60000.4),null);
});
test('repeated exposures remain available through time instead of duplicate detector choices',()=>{
 const rows=[row('a',60000.1),row('b',60000.2),row('c',60000.3,'D4',3,2.4,3.8)];
 const bands=bandsOnDay(rows,60000.1);
 assert.deepEqual(bands.map(group=>group.band),['D1','D4']);
 assert.equal(bands[0].rows.length,2);
 assert.equal(fieldTimeline(rows,'D1').length,2);
});
test('fast browsing omits downloads and keeps a pending chosen exposure at a stable position',()=>{
 const rows=[{...row('cached',60000.1),ready:true},row('pending',60000.2),row('other',60000.3)];
 assert.deepEqual(fieldTimeline(rows,'D1',true).map(row=>row.id),['cached']);
 const before=fieldTimeline(rows,'D1',true,'pending').map(row=>row.id);
 const after=fieldTimeline(rows.map(row=>({...row,ready:row.id!=='other'})),'D1',true,'pending').map(row=>row.id);
 assert.deepEqual(before,['cached','pending']);
 assert.deepEqual(after,before);
 assert.equal(fieldTimeline(rows,'D1').length,3);
});
test('fast band changes prefer a prepared exposure and still allow downloading a new band',()=>{
 const rows=[{...row('ready',60000.8,'D3'),ready:true},row('closer',60000.4,'D3')];
 assert.equal(bandAtTime(rows,'D3',60000.4,true).id,'ready');
 assert.equal(bandAtTime(rows,'D3',60000.4,false).id,'closer');
 assert.equal(bandAtTime([row('new-band',60000.5,'D6')],'D6',60000.5,true).id,'new-band');
});
