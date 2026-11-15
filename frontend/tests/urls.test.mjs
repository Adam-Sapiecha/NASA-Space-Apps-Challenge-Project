import test from 'node:test';
import assert from 'node:assert/strict';
import {createUrls} from '../src/urls.ts';

test('local, prefixed server and Pages deployments keep their own asset roots',()=>{
 assert.equal(createUrls().apiUrl('/api/search'),'/api/search');
 const server=createUrls('/spherex/');
 assert.equal(server.assetUrl('/motion-demo/1.png'),'/spherex/motion-demo/1.png');
 assert.equal(server.apiUrl('/api/health'),'/spherex/api/health');
 assert.equal(server.assetUrl('/spherex/demo/'),'/spherex/demo/');
 const pages=createUrls('/NASA-Space-Apps-Challenge-Project/','https://server.example:8443/spherex/');
 assert.equal(pages.assetUrl('/?analysis=a'),'/NASA-Space-Apps-Challenge-Project/?analysis=a');
 assert.equal(pages.apiUrl('/api/analyses/a'), 'https://server.example:8443/spherex/api/analyses/a');
 assert.equal(pages.assetUrl('https://irsa.ipac.caltech.edu/source'),'https://irsa.ipac.caltech.edu/source');
});
test('API resource rewriting retains IDs, scientific values and external archive provenance',()=>{
 const pages=createUrls('/project/','https://server.example/app');
 const data={id:'a',frames:[{image:'/api/analyses/a/frames/b.png',wave:4.5,url:'https://irsa.ipac.caltech.edu/native.fits'}],point:null};
 const result=pages.resources(data);
 assert.equal(result.frames[0].image,'https://server.example/app/api/analyses/a/frames/b.png');
 assert.equal(result.frames[0].wave,4.5);
 assert.equal(result.frames[0].url,data.frames[0].url);
 assert.equal(result.id,'a');
 assert.equal(result.point,null);
 assert.equal(data.frames[0].image,'/api/analyses/a/frames/b.png');
 assert.deepEqual(pages.resources(result),result);
});
