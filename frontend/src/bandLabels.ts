// These names describe positions in SPHEREx's infrared range, not visible colours.
import {getLanguage} from './i18n.ts';
export function bandLabel(wavelength:number,language:'pl'|'en'=getLanguage()){
 const index=wavelength<1.1?0:wavelength<1.8?1:wavelength<2.8?2:wavelength<4?3:4;
 return (language==='pl'
  ?['Najkrótsze fale podczerwieni','Krótsze fale podczerwieni','Środkowa część zakresu','Dłuższe fale podczerwieni','Najdłuższe fale w tym widoku']
  :['Shortest infrared wavelengths','Shorter infrared wavelengths','Middle of the range','Longer infrared wavelengths','Longest wavelengths in this view'])[index];
}
