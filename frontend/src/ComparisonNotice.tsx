import {Info,TriangleAlert} from 'lucide-react';
import {t} from './i18n';
import type {ComparisonNotice as Notice} from './viewerStatus';

export default function ComparisonNotice({notice,playing,displayComparison=false,intent='time'}:{notice:Notice;playing:boolean;displayComparison?:boolean;intent?:'time'|'bands'}){
 if(!notice)return null;
 if(notice.kind==='bands'&&intent==='bands')return null;
 const location=t(notice.location==='point'?'w zaznaczonym punkcie':notice.location==='target'?'przy pozycji celu':'w centrum pola');
 const message=notice.kind==='same'?t(displayComparison?'Ta sama obserwacja, różne ustawienia podglądu.':'A i B to ta sama klatka. Wybierz inną datę B, aby porównać obrazy.'):
  notice.kind==='missing'?t('W zaznaczonym punkcie brakuje ważnych danych A lub B.'):
  notice.kind==='unknown'?`${t('Brak danych o paśmie')} ${location}. ${t('Nie można sprawdzić zgodności pasm.')}`:
  `${t('Różne pasma')} ${location}. ${t('Zmiana wyglądu nie musi oznaczać zmiany źródła.')}`;
 const Icon=notice.kind==='same'?Info:TriangleAlert;
 return <div className={`comparison-notice ${notice.kind==='same'?'information':'caution'}`} role="status" aria-live={playing?'off':'polite'}><Icon size={15}/><span>{message}</span></div>;
}
