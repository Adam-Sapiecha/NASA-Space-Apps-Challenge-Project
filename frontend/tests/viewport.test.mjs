import test from 'node:test';
import assert from 'node:assert/strict';
import {panes,imageRect,imagePoint} from '../src/viewport.ts';

test('fit shows all four image edges on desktop and a narrow phone',()=>{
 for(const [w,h] of [[1000,500],[320,640],[800,300]]){
  for(const pane of panes(w,h,true)){
   const image=imageRect(pane,1,{x:10000,y:-10000});
   assert.ok(image.x>=pane.x&&image.y>=pane.y);
   assert.ok(image.x+image.width<=pane.x+pane.width+1e-8);
   assert.ok(image.y+image.height<=pane.y+pane.height+1e-8);
  }
 }
});
test('both complete images map to the same sky coordinate after zoom and pan',()=>{
 for(const [w,h] of [[1000,500],[320,640]]){
  const areas=panes(w,h,true),pan={x:25,y:-15};
  for(const area of areas){
   const rect=imageRect(area,2,pan);
   const point=imagePoint({x:rect.x+rect.width*.5,y:rect.y+rect.height*.5},areas,2,pan);
   assert.ok(Math.abs(point.x-.5)<1e-8&&Math.abs(point.y-.5)<1e-8);
  }
 }
});
test('the gap between photos cannot be mistaken for a source position',()=>{
 assert.equal(imagePoint({x:500,y:200},panes(1000,500,true),1,{x:0,y:0}),null);
 assert.equal(imagePoint({x:100,y:320},panes(320,640,true),1,{x:0,y:0}),null);
});
