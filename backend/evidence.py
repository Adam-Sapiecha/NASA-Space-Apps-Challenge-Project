"""Portable evidence for a saved human hypothesis, without new inference."""
import base64
import html
from pathlib import Path

import numpy as np
from astropy.wcs import WCS

from backend import store
from backend.change_diagnostics import diagnose
from backend.coordinates import point_sky, point_sample, frame_point


def evidence(note, manifest, measurement=None):
    frames = {f['id']: f for f in manifest['frames']}
    point = note.get('point')
    sources = []
    for id in note['frame_ids']:
        frame = frames[id]
        selected = frame_point(note, frame)
        source = {k: frame.get(k) for k in ('id', 'obs_id', 'date', 'mjd', 'band', 'collection',
                                           'url', 'sha256', 'unit', 'processing_version',
                                           'wavelength_um', 'bandwidth_um', 'coverage', 'masked_flags')}
        source['wavelength_location'] = 'field centre'
        source['point'] = selected
        if selected:
            with np.load(store.ROOT/'analyses'/manifest['id']/f'{id}.npz') as data:
                local = point_sample(manifest, selected, data)
                source.update({key: local[key] for key in ('wavelength_um', 'bandwidth_um', 'pixel')})
                source['valid_at_point'] = local['valid']
                source['flags_at_point'] = [name for name, bit in frame['flag_definitions'].items()
                                            if local['flags_word'] & (1<<bit)]
            coord = point_sky(manifest, selected)
            source['sky'] = dict(ra=float(coord.ra.deg), dec=float(coord.dec.deg), frame='ICRS')
            source['wavelength_location'] = 'marker position (interpolated WCS-WAVE browsing approximation); quality flags: containing output pixel'
        elif note.get('mode') == 'route':
            source.update(wavelength_um=None, bandwidth_um=None, wavelength_location='route position unavailable')
        sources.append(source)
    diagnostics = None
    if measurement and len(set(note['frame_ids'])) == 2:
        diagnostics = diagnose(measurement, *note['frame_ids'])
    anchor_times = {a['mjd'] for a in note.get('anchors', [])}
    held_out = [dict(frame_id=id, date=frames[id]['date'], assessment=assessment,
                     different_epoch_from_anchors=frames[id]['mjd'] not in anchor_times,
                     independent_epoch=None, independence='not_established_by_date')
                for id, assessment in note.get('route_checks', {}).items()]
    sky = None
    if point and note.get('mode') != 'route':
        coord = point_sky(manifest, point)
        sky = dict(ra=float(coord.ra.deg), dec=float(coord.dec.deg), frame='ICRS')
    return dict(schema_version=2, kind='human-hypothesis-evidence', note_id=note['id'],
                analysis_id=manifest['id'], created_at=note['created_at'],
                pipeline_version=manifest.get('pipeline_version'),
                hypothesis=dict(kind=note['kind'], text=note['text'], authorship='User-supplied assessment'),
                view={k: note.get(k) for k in ('point', 'anchors', 'mode', 'quality', 'range_mode', 'series_only')},
                sky=sky, search=manifest['search'], sources=sources,
                processing=manifest.get('processing'), display=manifest['display'],
                measurement=measurement, diagnostics=diagnostics, held_out_checks=held_out,
                measurement_position=(dict(point=measurement.get('point'),ra=measurement.get('ra'),dec=measurement.get('dec'),
                                           method=measurement.get('method'),kind='fixed_aperture_position') if measurement else None),
                conclusion='Unconfirmed hypothesis. No automatic detection, orbit, variability significance or discovery probability.',
                limitations=['Two clicks define a hypothesis, not an orbit or astrometric fit.',
                             'Held-out assessments are human judgements, not independent automated detections.',
                             'Similar wavelengths do not prove equal spectral response; WCS-WAVE is for browsing.',
                             'Photometry errors are random only; PSF, source motion, neighbours and systematics require validation.',
                             'Embedded images use the analysis quality mask and original common stretch, not the current display preview.'],
                acknowledgement=manifest.get('acknowledgement'))


def evidence_html(report):
    esc = lambda value: html.escape(str(value))
    sources = report['sources']
    panels = []
    for label, source in zip(('A', 'B'), sources):
        path = store.ROOT/'analyses'/report['analysis_id']/f"{source['id']}.png"
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        wave = source['wavelength_um']
        wave = f'{wave:.5f}' if wave is not None else 'unavailable'
        point = source.get('point')
        marker = (f'<span class="marker" aria-label="Selected sky position" style="left:{point["x"]*100:.5f}%;top:{point["y"]*100:.5f}%">⊕</span>' if point else '')
        panels.append(f'<figure><div class="image"><img alt="SPHEREx observation {label}, north up, east left" src="data:image/png;base64,{encoded}">{marker}</div>'
                      f'<figcaption><b>{label}: {esc(source["date"])} UTC</b><br>{wave} µm · {esc(source["band"])} · '
                      f'{esc(source["wavelength_location"])}</figcaption></figure>')
    checks = report['held_out_checks']
    diagnostic = report['diagnostics']
    verdict = 'No linked aperture diagnostic. No brightness conclusion.'
    if diagnostic:
        verdict = ('Comparison blocked by data, wavelength or epoch checks.' if diagnostic['status']=='blocked'
                   else 'Further validation required. Variability is unconfirmed.')
    metric = ''
    if diagnostic and diagnostic['metrics']:
        m = diagnostic['metrics']
        metric = f'<p>Aperture A−B: <b>{m["delta_mjy"]:.5g} ± {m["random_error_mjy"]:.5g} mJy</b> (random error only); {m["days"]:.3f} days. Not a significance test.</p>'
        position=report.get('measurement_position')
        if position and position.get('ra') is not None and position.get('dec') is not None:
            metric += f'<p>Photometry uses a fixed aperture at ICRS {position["ra"]:.7f}°, {position["dec"]:.7f}°. Method: {esc(position.get("method") or "archival")}.</p>'
            if report['view'].get('mode')=='route':
                metric += '<p>Route markers describe a separate motion hypothesis.</p>'
    sky = report.get('sky')
    location = (f'ICRS {sky["ra"]:.7f}°, {sky["dec"]:.7f}° · fixed sky position'
                if sky and report['view'].get('mode')!='route' else 'User-drawn motion hypothesis; markers show the selected anchors, not measured detections.')
    source_rows = ''.join(f'<tr><td>{esc(s["obs_id"])}</td><td>{esc(s["unit"])}</td>'
                          f'<td><a href="{esc(s["url"])}">IRSA FITS source</a><br><code>{esc(s["sha256"])}</code></td></tr>' for s in sources)
    held = ''.join(f'<li>{esc(c["date"])} UTC: {esc(c["assessment"])} (human assessment)</li>' for c in checks)
    limitations = ''.join(f'<li>{esc(s)}</li>' for s in report['limitations'])
    title = 'SPHEREx observation evidence'
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>body{{font:16px/1.55 system-ui,sans-serif;max-width:1050px;margin:auto;padding:24px;color:#202d32;background:#f8f8f4}}h1{{font-size:28px}}.images{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}figure{{margin:0}}.image{{position:relative}}.marker{{position:absolute;transform:translate(-50%,-50%);font:30px/1 monospace;color:#ffd17e;text-shadow:0 0 3px black}}img{{display:block;width:100%;image-rendering:pixelated;background:repeating-linear-gradient(135deg,#0b1520 0 5px,#25313c 5px 6px)}}figcaption{{padding:8px 0}}.verdict{{border-left:4px solid #856112;padding:12px;background:#fff3d4}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;border-bottom:1px solid #bbb;padding:10px;vertical-align:top}}code{{overflow-wrap:anywhere}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}@media(max-width:600px){{.images{{grid-template-columns:1fr}}td,th{{padding:5px;font-size:13px}}}}@media print{{body{{padding:0}}}}</style>
<h1>{title}</h1><p>Real NASA observations · saved human hypothesis · unconfirmed</p>
<p>Note <code>{esc(report['note_id'])}</code> · Analysis <code>{esc(report['analysis_id'])}</code></p>
<h2>Question and human assessment</h2><p>{esc(report['hypothesis']['kind'])}</p><pre>{esc(report['hypothesis']['text'])}</pre>
<p>{location}</p>
<div class="images">{''.join(panels)}</div><p>Common WCS and brightness scale. North ↑, east ←. Hatching means missing or quality-masked data, never zero flux.</p>
<p class="verdict">{verdict} {esc(report['conclusion'])}</p>
{metric}
<h2>Checks on other epochs</h2><ul>{held or '<li>No held-out epoch assessed.</li>'}</ul>
<h2>Provenance</h2><table><tr><th>Observation</th><th>Surface brightness</th><th>Source and native FITS SHA-256</th></tr>{source_rows}</table>
<p>Pipeline {esc(report['pipeline_version'])}. Processing: {esc(report['processing'])}.</p>
<h2>Limits</h2><ul>{limitations}</ul><p>{esc(report.get('acknowledgement') or 'Data: NASA / JPL-Caltech / IPAC.')}</p>
<p>This portable file embeds both preview images. IRSA source links require a network connection. Export the accompanying JSON for measurements, parameters and full checks.</p></html>'''
