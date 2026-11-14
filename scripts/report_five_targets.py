"""Write the final five-target report from saved audit evidence, without queries."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astropy.time import Time
from backend import store


def main():
    audit=json.loads((store.ROOT/'audit/five-targets-final.json').read_text(encoding='utf-8'))
    flags=json.loads((store.ROOT/'audit/five-flags.json').read_text(encoding='utf-8'))
    lines=['# Wyniki pięciu wymaganych obiektów', '', 'Kontrola: 14 listopada 2026. Dane SPHEREx DR1; nowe zapytania i pola 6′ wokół katalogowych przewidywań J2026.0. '
           'Wybrano do ośmiu produktów D2 na pole i D6 dla WISE 0855, rozłożonych według czasu. '
           'W rzadkich lub skupionych terminach dobór dał mniej niż osiem ekspozycji. To próbka, nie pełny przegląd archiwum.', '',
           '**Wniosek: zweryfikowano katalogowe tożsamości i obrazy poprawionych pól. Nie potwierdzono identyfikacji wszystkich źródeł w SPHEREx, ruchu ani zmienności.**', '',
           'Wcześniejsze testy zawierały błędne centra Epsilon Indi B i R Draconis. Ich liczb i wyników nie należy traktować jako testów prawidłowych obiektów. '
           'Dotychczasowy Barnard’s Star był centrowany na starej pozycji, bez uwzględnienia dużego ruchu własnego.', '',
           '| Obiekt | Centrum pola J2026.0 (RA / Dec °) | Rekordy archiwum | Przygotowano / wybrano | Ważne apertury przy przewidywaniu | Pary o zbliżonych pasmach |',
           '|---|---|---:|---:|---:|---:|']
    for t in audit['targets']:
        p=t['target'];lines.append(f"| {p['name']} | {p['field_ra']:.7f} / {p['field_dec']:.7f} | {t['archive_rows']} | {t['prepared']} / {t['selected']} | {t['valid_predicted_apertures']} | {len(t['comparable_pairs'])} |")
    lines+=['', 'Ważna apertura nie jest potwierdzoną detekcją. Zgodność pasm to próg połowy węższej szerokości z WCS-WAVE; nie dowodzi zgodności pełnych odpowiedzi spektralnych. '
            'Pomiar w każdej ekspozycji wykonano przy osobnym katalogowym przewidywaniu, nie w starej stałej pozycji.', '', '## Tożsamości i wyniki szczegółowe', '']
    for t in audit['targets']:
        p=t['target'];m=store.get('analysis',t['analysis_id'])
        lines += [f"### {p['name']}", '', f"Katalog: **{p['catalogue_id']}**. [Źródło]({p['source']}), odniesienie `{p['reference']}`. "
                  f"Pozycja odniesienia ICRS {p['ra_deg']:.8f}°, {p['dec_deg']:.8f}°; epoka MJD {p['epoch_mjd']:.2f} "
                  f"(J{Time(p['epoch_mjd'],format='mjd').jyear:.4f}). Ruch własny μα* / μδ: {p['pmra_masyr']:.3f} / {p['pmdec_masyr']:.3f} mas/rok.", '',
                  f"Analiza: `{t['analysis_id']}` · [otwórz lokalnie](http://127.0.0.1:8000/?analysis={t['analysis_id']}). "
                  f"Detektor {t['selected_detector']}; daty przygotowanych produktów {m['frames'][0]['date']} — {m['frames'][-1]['date']} UTC.", '',
                  '| Data UTC | Przewidywane RA / Dec ° | Ważny pomiar | λ (µm) | Strumień apertury ± błąd losowy (mJy) | Ograniczenie |',
                  '|---|---|---|---|---|---|']
        for s in t['samples']:
            r=s['measurement'];q=s['prediction']
            wave=f"{r['wavelength_um']:.5f}" if r['valid'] else '—'
            flux=f"{r['flux_mjy']:.5g} ± {r['error_mjy']:.4g}" if r['valid'] else '—'
            reason=', '.join(r.get('flagged',[])) if r['valid'] else r.get('reason','Brak danych')
            lines.append(f"| {s['date']} | {q['ra']:.7f} / {q['dec']:.7f} | {'tak' if r['valid'] else 'nie'} | {wave} | {flux} | {reason} |")
        named=next(f for f in flags if f['name']==p['name'])
        bad=Counter(name for s in named['samples'] for name in s['flags_in_aperture'] if name!='SOURCE')
        sky=[f"{s['source_flagged_annulus_pixels']}/{s['annulus_pixels']}" for s in named['samples'] if s['annulus_pixels']]
        lines+=['', 'Kontrola natywnych flag przy przewidywanej pozycji: '+(', '.join(sorted(bad)) or 'brak dodatkowych flag w sprawdzonych aperturach')+'. '
                'Liczby pikseli SOURCE w pierścieniu tła: '+', '.join(sky)+'. SOURCE pozostaje dozwolone w aperturze celu, ale jest wykluczane z tła.', '']
        if t['comparable_pairs']:
            for pair in t['comparable_pairs']:
                lines.append(f"Zbliżona para przy osobnych przewidywaniach: `{pair['frame_ids'][0]}` / `{pair['frame_ids'][1]}`, {pair['days']:.3f} dni, λ {pair['wavelengths_um'][0]:.5f} / {pair['wavelengths_um'][1]:.5f} µm.")
        else:lines.append('Brak pary spełniającej jednocześnie przyjęte warunki apertury i lokalnego pasma w tej próbce. Nie oznacza to, że w całym archiwum taka para nie istnieje.')
        for failure in t['failures']:
            lines.append(f"Nieudane pobranie `{failure['observation']}`: {failure['error']}")
        lines+=['', '**Wynik astronomiczny: nierozstrzygnięty.** Katalogowa pozycja, pokrycie i flaga SOURCE nie są niezależnym potwierdzeniem tożsamości źródła. '
                'Nie raportujemy ruchu, zmienności ani prawdopodobieństwa odkrycia.', '']
    lines+=['## Kontrole i granice', '',
            '- SIMBAD ma jawne współrzędne odniesienia ICRS/J2000. WISE 0855 dodatkowo sprawdzono w pierwotnej tabeli Kirkpatrick 2021: RA 133.780984°, Dec −7.243932°, MJD 57633.39. Nie pomylono epoki pozycji z równonocą.',
            '- Propagacja Astropy uwzględnia ruch własny, bez paralaksy, ruchu orbitalnego i przyspieszenia perspektywicznego. To wystarcza do pola przeglądowego; nie do precyzyjnej astrometrii. Epsilon Indi B nie jest tu rozdzielany na dwa potwierdzone składniki.',
            '- WCS, jednostki MJy/sr, przezroczystość braków i źródłowe SHA są zachowane w manifestach; fotometria jest na natywnych IMAGE/VARIANCE/FLAGS. Błąd apertury jest losowy, bez pełnej systematyki.',
            '- Niezależna biblioteka Photutils 3.1.1: 30 porównań na tym samym rzeczywistym polu D6, także w czterech pozycjach kontrolnych poza celem. Maksymalna różnica 0,1076 mJy, mediana bezwzględnej różnicy 0,01580 mJy. Różnice brzegowych masek i tła pozostają jawne. Pól kontrolnych nie sklasyfikowano jako astrofizycznie puste ani stabilne.',
            '- Dla pojedynczej pary po wyłączeniu jednej ekspozycji pozostaje jeden termin: brak niezależnego potwierdzenia na odłożonej epoce o tym samym paśmie. Nie przedstawiono tego jako udanego testu odzysku.',
            '- Brak eksportu IRSA Tractor dopasowanego do tych samych ekspozycji. Lokalnego ePSF nie uznajemy za zewnętrznie zwalidowaną fotometrię.', '',
            '## Odtworzenie', '', '```powershell', '.\\.venv\\Scripts\\python.exe scripts/validate_five_targets.py',
            '.\\.venv\\Scripts\\python.exe scripts/independent_photometry_check.py',
            '.\\.venv\\Scripts\\python.exe scripts/report_five_targets.py', '```', '',
            'Pierwsze polecenie ponawia zapytania i tworzy nowe analizy. Nie usuwa cache. Photutils jest opcjonalnym narzędziem walidacji w `.cache/validation-libs`, a nie zależnością aplikacji produkcyjnej. '
            'Surowe dowody: `data/audit/five-targets-final.json`, `five-flags.json`, `independent-photutils.json`, `simbad-identities.json` i `wise0855-reference.tsv`. '
            'Snapshoty i FITS zawiera lokalny katalog danych; seed wdrożeniowy zachowuje potrzebne produkty. Liczby rekordów SIA oznaczają pokrycie pól, nie liczbę detekcji obiektów.', '']
    (ROOT/'WYNIKI_5_OBIEKTOW.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':main()
