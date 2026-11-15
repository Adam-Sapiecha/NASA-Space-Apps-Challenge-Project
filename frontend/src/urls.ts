/** Keep API resources and static assets separate on Pages and prefixed hosts. */
export function createUrls(base='/',backend?:string){
 const path='/'+base.replace(/^\/+|\/+$/g,'');
 const root=path==='/'?'/':path+'/';
 const apiRoot=(backend??root).replace(/\/+$/,'');
 const external=(value:string)=>/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(value);
 const assetUrl=(value:string)=>external(value)||value.startsWith(root)?value:root+value.replace(/^\/+/,'');
 const apiUrl=(value:string)=>value==='/api'||value.startsWith('/api/')?apiRoot+value:assetUrl(value);
 const resources=<T>(value:T):T=>{
  if(typeof value==='string')return (value.startsWith('/api/')?apiUrl(value):value) as T;
  if(Array.isArray(value))return value.map(item=>resources(item)) as T;
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,resources(item)])) as T;
  return value;
 };
 return {assetUrl,apiUrl,resources};
}
const urls=createUrls(import.meta.env?.BASE_URL??'/',import.meta.env?.VITE_API_BASE_URL||undefined);
export const {assetUrl,apiUrl,resources}=urls;
