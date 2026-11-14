"""Real-data audit of five fields. No source identification or detection claims."""
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.archive import search
from backend.measurements import measure
from backend.science import build_analysis
from backend import store
from backend.targets import TARGETS as CATALOGUE_TARGETS

TARGETS = [(t['name'],str(t['field_ra']),str(t['field_dec'])) for t in CATALOGUE_TARGETS]


def main():
    (store.ROOT/'audit').mkdir(parents=True, exist_ok=True)
    report = []
    for name, ra, dec in TARGETS:
        print(f'Checking {name}', flush=True)
        row = dict(name=name, checked_at=datetime.now(timezone.utc).isoformat())
        try:
            source = search(ra, dec, 4, 'spherex_dr1')
            source['id'] = uuid.uuid4().hex
            store.put('search', source['id'], source)
            row['archive_rows'] = source['archive_rows']
            candidates = [o for o in source['observations'] if o['band']=='SPHEREx-D2']
            if len(candidates) < 2:
                raise ValueError('Brak dwóch ekspozycji D2.')
            id = uuid.uuid4().hex
            build_analysis(id, source, [candidates[0]['id'], candidates[-1]['id']])
            analysis = store.get('analysis', id)
            if not analysis:
                raise ValueError(store.get('job', id)['message'])
            measurement = measure(analysis, .5, .5, 12.4)
            a, b = analysis['frames']
            sample = [r for r in measurement['rows'] if r['valid']]
            row.update(analysis_id=id, measurement_id=measurement['id'],
                       baseline_days=abs(a['mjd']-b['mjd']),
                       coverage=[f['coverage'] for f in analysis['frames']],
                       wavelengths_um=[r['wavelength_um'] for r in sample],
                       valid_apertures=len(sample),
                       comparable_at_center=(len(sample)==2 and abs(sample[0]['wavelength_um']-sample[1]['wavelength_um']) <= min(r['bandwidth_um'] for r in sample)/2),
                       result='Sprawdzono obrazy pola i aperturę w pozycji startowej; nie zidentyfikowano źródła ani nie potwierdzono ruchu/zmienności.')
        except Exception as exc:
            row.update(error=f'{type(exc).__name__}: {exc}', result='Brak rozstrzygającego porównania.')
        report.append(row)
        (store.ROOT/'audit'/'plan-v4.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(json.dumps(row, ensure_ascii=True), flush=True)
    lines = ['# Walidacja pól według planu 4.0', '',
             'Rzeczywiste zapytania IRSA DR1, pola 4′, pierwsza i ostatnia dostępna ekspozycja D2. '+
             'To kontrola pipeline, lokalnego pasma i pokrycia, bez identyfikacji źródeł. Centra pól to katalogowe przewidywania J2026.0; pomiar w centrum nie śledzi źródła. '+
             'Apertura 12,4″ w centrum pola nie musi obejmować wskazanego obiektu. Wybór skrajnych dat nie gwarantuje zgodnych pasm.', '',
             '| Pole | Rekordy SIA | Baza dni | Ważne apertury | Zbliżone pasma w centrum | Wynik |',
             '|---|---:|---:|---:|---|---|']
    for row in report:
        lines.append(f"| {row['name']} | {row.get('archive_rows','—')} | {row.get('baseline_days',0):.2f} | {row.get('valid_apertures','—')} | {row.get('comparable_at_center','—')} | {row.get('error', row['result']).replace(chr(10),' ')} |")
    lines += ['', '## Odtworzenie', '', 'Szczegóły zapytań, identyfikatory analiz i pomiarów: `data/audit/plan-v4.json`. '+
              'Analizę można otworzyć jako `/?analysis=ID`. Manifest analizy zawiera identyfikatory i SHA-256 źródłowych FITS. '+
              'Pomiary: `/api/measurements/ID`. Pliki cache pozostają na tym samym serwerze.', '',
              '## Nierozstrzygnięte', '', 'Brak niezależnej identyfikacji i astrometrii, modelu ruchu, kalibracji PSF/apertury i badania skuteczności. '+
              'Nie potwierdzamy detekcji pięciu obiektów, wykrycia ruchu ani zmiany jasności. '+
              'Asystent nie proponuje wag przed walidacją na niezależnych obserwacjach.']
    Path('WALIDACJA_PLANU_V4.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__=='__main__':
    main()
