import test from 'node:test';
import assert from 'node:assert/strict';
import {t,getLanguage,setLanguage,withLanguage,subscribeLanguage} from '../src/i18n.ts';
import {workspaceDefaults} from '../src/workspace.ts';

test('the first visit opens real comet motion in a simple English interface',()=>{
 assert.equal(getLanguage(),'en');
 assert.deepEqual(workspaceDefaults(new URLSearchParams()),{expert:false,motionOpen:true});
 assert.equal(t('Wyszukaj obrazy'),'Search images');
 assert.equal(t('Ta para nie pozwala ocenić zmienności.'),'This pair cannot establish variability.');
 assert.equal(t('Wyrównywanie obrazu 2/8'),'Aligning observation 2/8');
});
test('explicit fields, saved notes and advanced reports keep their entry points',()=>{
 for(const query of ['ra=12&dec=3','analysis=saved','motion=0','guided=1'])assert.equal(workspaceDefaults(new URLSearchParams(query)).motionOpen,false);
 assert.equal(workspaceDefaults(new URLSearchParams('analysis=saved&view=measure')).expert,true);
 assert.equal(workspaceDefaults(new URLSearchParams('analysis=saved&note=n')).expert,true);
 assert.equal(workspaceDefaults(new URLSearchParams('motion=1')).motionOpen,true);
});
test('language changes notify the app and survive links without changing scientific values',()=>{
 let notifications=0;const stop=subscribeLanguage(()=>notifications++);
 try{
  setLanguage('pl');assert.equal(t('Wyszukaj obrazy'),'Wyszukaj obrazy');
  assert.equal(t('Search images'),'Wyszukaj obrazy');
  assert.match(withLanguage('/?analysis=a&point=%7B%22x%22%3A0.5%7D'),/lang=pl/);
  assert.equal(new URL(withLanguage('/?ra=42.123&dec=-7.5'),'http://localhost').searchParams.get('ra'),'42.123');
  setLanguage('en');assert.equal(notifications,2);
 }finally{stop();setLanguage('en')}
});
