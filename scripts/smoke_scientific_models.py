"""Live, bounded smoke checks; does not train on synthetic data or claim detections."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import store
from backend.artifact_model import readiness
from backend.native_diagnostics import profile_series
from backend.object_context import context
from backend.trajectory import ephemeris


def main():
    result = dict(created_at=datetime.now(timezone.utc).isoformat(), checks={})
    demo = store.ROOT/'spectral_demo.json'
    if demo.exists():
        key = json.loads(demo.read_text(encoding='utf-8'))['id']
        manifest = store.get('analysis', key)
        if manifest:
            try:
                profile = profile_series(manifest, .5, .5)
                result['checks']['native_fits'] = dict(status='completed', analysis_id=key,
                    valid_fits=sum(r['valid'] for r in profile['rows']), rows=profile['rows'])
            except Exception as exc:
                result['checks']['native_fits'] = dict(status='failed', reason=str(exc))
            try:
                value = context(manifest, .5, .5, manifest['frames'][0]['id'], 30)
                result['checks']['catalogs'] = dict(status='completed',
                    catalogs=[dict(catalog=c['catalog'], candidates=len(c['candidates'])) for c in value['catalogs']],
                    failures=value['failures'])
            except Exception as exc:
                result['checks']['catalogs'] = dict(status='failed', reason=str(exc))
    try:
        value = ephemeris('Ceres', [61358., 61359.])
        result['checks']['horizons'] = dict(status='completed', resolved_name=value['resolved_name'],
                                          observer=value['observer'], predictions=value['predictions'])
    except Exception as exc:
        result['checks']['horizons'] = dict(status='failed', reason=str(exc))
    result['checks']['artifact_data'] = readiness()
    output = store.ROOT/'smoke_scientific_models.json'
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({key: value.get('status', 'readiness') for key, value in result['checks'].items()}))
    print(str(output))


if __name__ == '__main__':
    main()
