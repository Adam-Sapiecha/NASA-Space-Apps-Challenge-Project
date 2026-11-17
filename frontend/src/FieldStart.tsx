import {ArrowRight} from 'lucide-react';
import {t} from './i18n';
import showcase from './showcase.json';
import motionShowcase from './motionShowcase.json';

export default function FieldStart({busy,onOpen,onOwn}:{busy:boolean;onOpen:(id:string)=>void;onOwn:()=>void}){
 const examples=[
  {id:showcase.analysis_id,title:'WISE 0855 · '+t('zmiany w czasie')},
  {id:showcase.spectral_analysis_id,title:'Barnard’s Star · '+t('różne pasma')},
  {id:motionShowcase.analysis_id,title:'3I/ATLAS · '+t('ruch komety')},
 ];
 return <section className="field-start" aria-labelledby="field-start-title">
  <header><h1 id="field-start-title">{t('Wybierz, od czego zacząć')}</h1><p>{t('Wybierz przykład lub własne pole nieba.')}</p></header>
  <div className="start-routes">
   <section aria-labelledby="ready-fields-title"><h2 id="ready-fields-title">{t('Gotowe dane')}</h2><p>{t('Zdjęcia są już pobrane.')}</p>
    <div className="ready-fields">{examples.map(example=><button disabled={busy} key={example.id} onClick={()=>onOpen(example.id)}><span><strong>{example.title}</strong></span><ArrowRight size={19} aria-hidden="true"/></button>)}</div>
   </section>
   <section aria-labelledby="own-field-title"><h2 id="own-field-title">{t('Wybierz fragment nieba')}</h2><p>{t('Współrzędne, obiekt lub mapa nieba.')}</p><p className="route-note">{t('Nowe obserwacje wymagają pobrania z IRSA.')}</p><button className="primary" disabled={busy} onClick={onOwn}>{t('Wybierz własne pole')}<ArrowRight size={17} aria-hidden="true"/></button></section>
  </div>
 </section>;
}
