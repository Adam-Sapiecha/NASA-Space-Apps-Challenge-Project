export type XY={x:number;y:number};
export type Rect={x:number;y:number;width:number;height:number};
export function panes(width:number,height:number,sideBySide:boolean):Rect[]{
 const w=Math.max(1,width),h=Math.max(1,height),gap=8;
 if(!sideBySide)return [{x:0,y:0,width:w,height:h}];
 return w<480?[{x:0,y:0,width:w,height:(h-gap)/2},{x:0,y:(h+gap)/2,width:w,height:(h-gap)/2}]:
  [{x:0,y:0,width:(w-gap)/2,height:h},{x:(w+gap)/2,y:0,width:(w-gap)/2,height:h}];
}
export function imageRect(pane:Rect,zoom:number,pan:XY):Rect{
 const fit=Math.min(pane.width,pane.height),side=fit*zoom;
 const limitX=Math.max(0,(side-pane.width)/2),limitY=Math.max(0,(side-pane.height)/2);
 return {x:pane.x+(pane.width-side)/2+Math.max(-limitX,Math.min(limitX,pan.x)),
  y:pane.y+(pane.height-side)/2+Math.max(-limitY,Math.min(limitY,pan.y)),width:side,height:side};
}
export function imagePoint(point:XY,areas:Rect[],zoom:number,pan:XY):XY|null{
 const pane=areas.find(r=>point.x>=r.x&&point.x<=r.x+r.width&&point.y>=r.y&&point.y<=r.y+r.height);
 if(!pane)return null;
 const rect=imageRect(pane,zoom,pan),x=(point.x-rect.x)/rect.width,y=(point.y-rect.y)/rect.height;
 return x>=0&&x<=1&&y>=0&&y<=1?{x,y}:null;
}
