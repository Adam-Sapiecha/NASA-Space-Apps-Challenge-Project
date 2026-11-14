"""Explain pairwise aperture differences without claiming variability detection."""
import math


def diagnose(measurement, a, b):
    if a == b:
        raise ValueError('Wybierz dwie różne ekspozycje A i B.')
    lookup = {r['id']: r for r in measurement['rows']}
    if a not in lookup or b not in lookup:
        raise ValueError('Obie ekspozycje muszą należeć do zapisanego pomiaru.')
    pair = [lookup[a], lookup[b]]
    checks = []

    def check(name, status, detail, action):
        checks.append(dict(name=name, status=status, detail=detail, action=action))

    required = ('flux_mjy', 'error_mjy', 'wavelength_um', 'bandwidth_um', 'mjd')
    usable = all(r.get('valid') and all(isinstance(r.get(k), (int, float)) and math.isfinite(r[k])
                 for k in required) and r['error_mjy'] > 0 and r['bandwidth_um'] > 0 for r in pair)
    check('Dostępność pomiarów', 'checked' if usable else 'blocked',
          'Obie apertury mają ważne pomiary i błędy losowe.' if usable else
          ' / '.join(f"{label}: {r.get('reason') or 'Brak ważnych wartości lub niepewności.'}"
                     for label, r in zip(('A', 'B'), pair) if not r.get('valid')) or 'Niepoprawne wartości pomiaru.',
          'Jeśli brakuje danych, wybierz inne ekspozycje lub punkt dalej od brzegu obrazu.')
    metrics = None
    if usable:
        x, y = pair
        separation = abs(x['wavelength_um']-y['wavelength_um'])
        tolerance = min(x['bandwidth_um'], y['bandwidth_um'])/2
        compatible = separation <= tolerance
        check('Lokalne pasma', 'caution' if compatible else 'blocked',
              f"A: {x['wavelength_um']:.5f} μm; B: {y['wavelength_um']:.5f} μm. "
              f'Różnica {separation:.5f} μm; próg przeglądowy {tolerance:.5f} μm. '
              'Spełnienie progu nie gwarantuje identycznej odpowiedzi spektralnej.',
              'Porównaj dodatkowe epoki o bliższych pasmach; kolor źródła może imitować zmienność.')
        days = abs(x['mjd']-y['mjd'])
        check('Różne terminy', 'checked' if days > 0 else 'blocked',
              f'Odstęp A–B: {days:.5f} dni.', 'Wybierz obserwacje z różnych terminów.')
        warnings = [f"{label}: {', '.join(r.get('flagged', []))}" for label, r in zip(('A', 'B'), pair) if r.get('flagged')]
        check('Flagi apertury', 'caution' if warnings else 'checked',
              '; '.join(warnings) or 'Brak zgłoszonych flag w aperturach. To nie dowodzi braku artefaktów.',
              'Obejrzyj maskę jakości i znaczenie flag; część flag opisuje źródła, a nie błędy.')
        neighbor = any(r.get('neighbor_warning') for r in pair)
        check('Otoczenie źródła', 'caution' if neighbor else 'checked',
              'Jasne piksele w pierścieniu tła mogą zaburzać pomiar.' if neighbor else
              'Test pierścienia tła nie zgłosił jasnego sąsiada; izolacja źródła nie jest potwierdzona.',
              'Obejrzyj sąsiednie źródła i powtórz pomiar z innym promieniem apertury.')
        metrics = dict(delta_mjy=x['flux_mjy']-y['flux_mjy'],
                       random_error_mjy=math.hypot(x['error_mjy'], y['error_mjy']),
                       flux_a_mjy=x['flux_mjy'], flux_b_mjy=y['flux_mjy'], days=days)
        color_examples = [(p,100*((y['wavelength_um']/x['wavelength_um'])**p-1)) for p in (-2,0,2,10)]
        check('Wrażliwość na kolor', 'unknown',
              'Modelowe Fν ∝ λ^p: przewidywana różnica B/A '+', '.join(f'p={p}: {value:+.3f}%' for p,value in color_examples)+
              '. Przykłady gładkich widm, nie korekcja koloru obiektu ani pełna odpowiedź filtrów.',
              'Oddziel wpływ pasma od czasu; nie interpretuj różnicy bez kontroli modelu widma.')
    if measurement.get('method') not in (None,'native-aperture-area-3'):
        check('Wersja pomiaru','caution','Zachowany wynik pochodzi z wcześniejszej metody fotometrii.',
              'Wykonaj nowy pomiar z mapą powierzchni pikseli. Archiwalny wynik pozostaje zachowany.')
    backgrounds = all(all(isinstance(r.get(k), (int, float)) and math.isfinite(r[k])
                          for k in ('background', 'background_scatter')) for r in pair)
    check('Tło', 'unknown',
          (f"Średnie tło A/B: {pair[0]['background']:.5g} / {pair[1]['background']:.5g}; "
           f"rozrzut: {pair[0]['background_scatter']:.5g} / {pair[1]['background_scatter']:.5g} "
           '(w jednostce powierzchniowej natywnego FITS). ' if backgrounds else '') +
          'Odjęto lokalne średnie tło, ale nie zweryfikowano jego struktury ani modelu ZODI.',
          'Sprawdź gradienty i pierścień tła; sama różnica średnich nie dowodzi artefaktu.')
    check('PSF i pozycja', 'unknown',
          'Brak dopasowania PSF i korekty apertury. Pomiar dotyczy tej samej pozycji ICRS, '
          'więc ruch źródła i błędy wyrównania mogą zmienić strumień w aperturze.',
          'Sprawdź centrowanie, ruch i kształt źródła; potwierdzenie wymaga fotometrii z kontrolą PSF.')
    blocked = any(c['status'] == 'blocked' for c in checks)
    return dict(method='aperture-pair-diagnostics-1', measurement_id=measurement['id'],
                analysis_id=measurement['analysis_id'], frame_ids=[a, b],
                point=measurement.get('point'), ra=measurement.get('ra'), dec=measurement.get('dec'),
                radius_arcsec=measurement['radius_arcsec'],
                status='blocked' if blocked else 'requires_validation',
                summary='Ta para nie pozwala ocenić zmienności.' if blocked else
                'Różnica wymaga weryfikacji. Nie potwierdzono rzeczywistej zmiany źródła.',
                metrics=metrics, checks=checks,
                limitations=['Różnica A−B dotyczy strumieni apertury po odjęciu lokalnego tła.',
                             'Błąd różnicy zakłada niezależne błędy losowe ekspozycji. Nie obejmuje systematyki, PSF ani korelacji.',
                             'Brak prawdopodobieństwa odkrycia i testu istotności zmienności. WCS-WAVE służy tu do przeglądu.'])
