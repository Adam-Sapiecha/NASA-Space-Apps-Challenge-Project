import {ArrowRight} from 'lucide-react';
import {t} from './i18n';
import showcase from './showcase.json';
import motionShowcase from './motionShowcase.json';

export default function FieldStart({busy,onOpen,onOwn}:{busy:boolean;onOpen:(id:string)=>void;onOwn:()=>void}){
 const examples=[
  {id:showcase.analysis_id,title:'WISE 0855 · '+t('zmiany w czasie'),description:t('Zapisane obserwacje jednego pola z różnych dat.')},
  {id:showcase.spectral_analysis_id,title:'Barnard’s Star · '+t('różne pasma'),description:t('Zapisany zestaw do oglądania pola w różnych długościach fali.')},
  {id:motionShowcase.analysis_id,title:'3I/ATLAS · '+t('ruch komety'),description:t('Dwie rzeczywiste obserwacje znanej komety.')},
 ];
 return <section className="field-start" aria-labelledby="field-start-title">
  <header><h1 id="field-start-title">{t('Wybierz, od czego zacząć')}</h1><p>{t('Otwórz gotowy przykład albo wybierz własny fragment nieba. Potem przeglądaj jego daty i pasma w jednym widoku.')}</p></header>
  <div className="start-routes">
   <section aria-labelledby="ready-fields-title"><span className="route-label">{t('Gotowe dane')}</span><h2 id="ready-fields-title">{t('Preset / gotowy test')}</h2><p>{t('Początkowe zdjęcia są już pobrane. Wybierz przykład i przejdź do analizy.')}</p>
    <div className="ready-fields">{examples.map(example=><button disabled={busy} key={example.id} onClick={()=>onOpen(example.id)}><span><strong>{example.title}</strong><small>{example.description}</small></span><ArrowRight size={19} aria-hidden="true"/></button>)}</div>
   </section>
   <section aria-labelledby="own-field-title"><span className="route-label">{t('Własne pole')}</span><h2 id="own-field-title">{t('Wybierz fragment nieba')}</h2><p>{t('Podaj współrzędne, wybierz okolicę obiektu z listy lub wskaż środek na mapie. Ustal rozmiar pola i wyszukaj obserwacje.')}</p><p className="route-note">{t('Nowe zdjęcia wymagają pobrania z archiwum. Postęp zobaczysz przed otwarciem podglądu.')}</p><button className="primary" disabled={busy} onClick={onOwn}>{t('Wybierz własne pole')}<ArrowRight size={17} aria-hidden="true"/></button></section>
  </div>
 </section>;
}
