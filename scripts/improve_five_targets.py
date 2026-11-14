"""Evaluate target-local selection without replacing earlier audit evidence."""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from astropy import log
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from backend import archive, science, store
from backend.measurements import measure
from backend.observation_selection import select_observations, inspect_observation, choose
from backend.targets import TARGETS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--fresh', action='store_true')
    parser.add_argument('--reuse-candidates', help='Recheck the exact candidate IDs from an earlier report.')
    parser.add_argument('--candidates', type=int, default=36, choices=range(12, 49))
    parser.add_argument('--target', choices=[t['id'] for t in TARGETS])
    parser.add_argument('--output', default='data/audit/five-targets-selection-v1.json')
    args = parser.parse_args()
    prior = json.loads(Path(args.reuse_candidates).read_text(encoding='utf-8')) if args.reuse_candidates else None
    log.setLevel('ERROR')
    old = json.loads((store.ROOT/'audit/five-targets-final.json').read_text(encoding='utf-8'))
    report = dict(checked_at=datetime.now(timezone.utc).isoformat(), offline=args.offline,
                  method='target-local-selection-1', targets=[])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    for target in TARGETS:
        if args.target and target['id'] != args.target:
            continue
        previous = next(t for t in old['targets'] if t['target']['id'] == target['id'])
        source = store.get('analysis', previous['analysis_id'])['search']
        if args.fresh:
            source = dict(archive.search(str(target['field_ra']), str(target['field_dec']), 6, 'spherex_dr1'), id=uuid.uuid4().hex)
            store.put('search', source['id'], source)
        print(target['name'], flush=True)
        row = dict(target_id=target['id'], name=target['name'], source_retrieved_at=source.get('retrieved_at'),
                   old_prepared=previous['prepared'], old_valid_apertures=previous['valid_predicted_apertures'])
        try:
            if prior:
                original = next(t for t in prior['targets'] if t['target_id'] == target['id'])['selection']
                lookup = {o['id']: o for o in source['observations']}
                candidates = []
                for saved in original['candidates']:
                    checked = inspect_observation(lookup[saved['id']], source, target, original['radius_arcsec'], offline=args.offline)
                    if saved.get('reason', '').startswith('HTTPStatusError'):
                        checked['original_download_error'] = saved['reason']
                    candidates.append(checked)
                selection = dict(original, checked_at=datetime.now(timezone.utc).isoformat(),
                                 candidates=candidates, **choose(candidates))
            else:
                selection = select_observations(source, target['id'], args.candidates, offline=args.offline,
                    progress=lambda done,total,message: print(f'  {message}', flush=True))
            row['selection'] = selection
            if args.prepare and selection['selected_ids']:
                id = uuid.uuid4().hex
                science.build_analysis(id, source, selection['selected_ids'], selection=selection)
                store.put('selection', id, dict(id=id, **selection))
                manifest = store.get('analysis', id)
                if manifest is None:
                    raise ValueError(store.get('job', id)['message'])
                row.update(analysis_id=id, prepared=len(manifest['frames']), failures=manifest['failures'], measurements=[])
                for f in manifest['frames']:
                    info = next(r for r in selection['candidates'] if r['id'] == f['id'])
                    if not info['aperture_valid']:
                        row['measurements'].append(dict(id=f['id'], date=f['date'], mjd=f['mjd'], valid=False,
                                                        reason=info.get('reason', 'Native aperture checks failed.')))
                        continue
                    sky = info['prediction']
                    px, py = WCS(manifest['wcs']).world_to_pixel(SkyCoord(sky['ra'], sky['dec'], unit='deg'))
                    n = manifest['pixels']
                    x, y = float((px+.5)/n), float(1-(py+.5)/n)
                    measured = measure(manifest, x, y, selection['radius_arcsec'])
                    row['measurements'].append(next(r for r in measured['rows'] if r['id'] == f['id']))
                row['valid_apertures'] = sum(r['valid'] for r in row['measurements'])
            print(json.dumps(dict(target=target['id'], status=selection['status'],
                  inspected=selection['inspected'], local_apertures=sum(r['aperture_valid'] for r in selection['candidates']),
                  selected=len(selection['selected_ids']), baseline_days=selection.get('baseline_days'),
                  prepared=row.get('prepared'), valid_apertures=row.get('valid_apertures'))), flush=True)
        except Exception as exc:
            row['error'] = f'{type(exc).__name__}: {exc}'
            print(row['error'], flush=True)
        report['targets'].append(row)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    print(output, flush=True)


if __name__ == '__main__':
    main()
