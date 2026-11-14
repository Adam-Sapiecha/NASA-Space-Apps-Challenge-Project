# Submission copy — NASA Space Apps 2026

Prepared 14 November 2026. **Draft for the team's review. No submission has been sent and no terms accepted.** Do not invent a project name, team identity, public URL, scientific discovery or user study. The descriptive headings below are not a project name.

## Fields the team must supply

- Project name: **[team decision]**.
- Team name and members: **[team-provided identities]**.
- Local event and any local pitching deadline: **[team confirmation]**.
- Public application URL: **[not deployed]**.
- Public demo URL: **[publish the English replay or ≤7-slide demo]**.
- Public code URL: **[team repository; none configured in this workspace]**.

## Current implementation update

The interface now opens in English with a Polish option and a simple, real-image demonstration of known comet 3I/ATLAS. Automatic preparation inspects local bands, flags, aperture coverage and background across detectors. A bounded recheck of 36 candidates per target found a valid D4 pair for Epsilon Indi B and a D6 pair for WISE 0855 separated by about 370 days. Barnard’s Star, RW Aurigae and R Draconis remain inconclusive for aperture photometry. These results do not confirm target identity, motion or variability. Latest evidence: `WDROZENIE_EN_I_DOBORU_OBSERWACJI.md` and `data/audit/five-targets-selection-final.json`.

## Short summary

Our web prototype helps people explore real SPHEREx images and examine apparent changes in the sky. Users enter coordinates, compare observation dates, explore available infrared wavelengths and save a reproducible evidence card. Local wavelengths, data gaps, quality flags and measurement limits remain visible, so a different-looking image is not automatically presented as a changing object.

## Detailed project description

SPHEREx observes the sky in many infrared bands. Comparing two images can reveal movement or changes in brightness, but changes in wavelength, coverage, background, source position or image quality can also change the appearance. Our team's existing concept connects accessible image exploration with checks on these alternative explanations.

The React/FastAPI application queries the NASA/IPAC Infrared Science Archive for actual SPHEREx products at user-entered RA and Dec. It downloads FITS cutouts, aligns images on a common celestial coordinate grid, applies a common display stretch and preserves missing data. A chronological series and A/B blinking support visual inspection. A separate wavelength player makes clear that stepping through wavelengths is not elapsed time and does not create a simultaneous 102-channel spectrum.

Users select a sky position or draw a two-position motion hypothesis. Exploratory photometry operates on native FITS pixels rather than display images. A diagnostic panel checks data availability, nearby wavelengths, dates, flags and potential contamination; it explicitly leaves PSF, source motion and systematic errors unresolved. A saved evidence card joins the user's assessment with the selected images, local wavelength metadata, source URLs, native FITS hashes and any linked measurement. The English HTML export embeds both previews for an outage, while JSON retains the full parameters and checks.

The extension improves the execution of the team's original idea. Image blinking, reprojection, aperture photometry and source extraction are established methods. We do not claim that these methods, the use of SI/AI or the existence of a new interface are themselves scientific inventions.

## NASA data and resources

The primary scientific inputs are **SPHEREx DR1 spectral-image FITS products served by IRSA**: IMAGE, VARIANCE, FLAGS and spectral WCS metadata. Native files retain their source identifiers and SHA-256 checksums. Display PNGs are derived from those products, and masked or unobserved pixels remain transparent. The application also accesses release-specific CWAVE/CBAND and pixel solid-angle calibration maps, supplied local ePSF models and the SPHEREx DR1 HiPS mosaic.

SPHEREx data are essential to the user's task, rather than a background illustration. Different dates and local wavelengths drive which comparisons are possible. The HiPS mosaic is labelled as a multi-date context product and is not used for photometry. MOST searches known Solar System objects; it is not a detector for an unknown Planet Nine. Gaia and AllWISE provide separate context, with their own epochs and limitations.

## What we actually tested

- Corrected two inaccurate target presets after querying catalogue identities: Epsilon Indi B and R Draconis. Presets now include proper-motion predictions around J2026.0, with their references and original coordinate epochs. This is not a full apparent-position solution.
- Repeated real SPHEREx queries for all five required fields at the corrected positions. Prepared **22 of 25 sampled cutouts** across the fields. Three downloads returned IRSA HTTP 503; these are preserved as failures. There are four valid exploratory apertures at predicted WISE 0855 positions and one browsing-compatible temporal pair. The other sampled apertures are rejected because of coverage, flags or unavailable clean background. **No target's motion or variability is confirmed.**
- Compared 30 actual native-image apertures with the independent Photutils 3.1.1 implementation. The largest flux difference was 0.108 mJy, below 0.465 of the local formal random error in this sample. Different sky-aperture approximations select some different boundary pixels. This checks numerical behaviour, not total-flux calibration or discovery significance.
- Ran backend regression tests, frontend tests and the production build. The final detailed counts and execution evidence are recorded in `AUDYT_NAPRAWY.md`.
- Exercised live HiPS, calibrated measurement, SEP extraction and MOST endpoints. The D6 check returned four valid calibrated rows; SEP returned four candidates; MOST returned 160 image intersections for 3I during 1–20 August 2025. Candidates/intersections are not confirmed detections.
- Tested actual image playback, keyboard point selection, diagnostic display, saving and reopening an evidence note, and map layer changes. See the audit for the checked responsive views and remaining limits.

## Limitations and next step

The application is a prototype. Similar wavelength labels do not establish equivalent response functions. Errors reported by exploratory photometry are random only; they omit full calibration and model uncertainty. Local ePSF results have not been validated against an actual matching IRSA Tractor export. Two clicks do not determine an orbit, and catalogue predictions do not establish source identification. The five-field audit is a bounded sample, not an assessment of all archive products.

No controlled usability study or improvement in discovery rate has been demonstrated. Public HTTPS hosting and a second-device acceptance check remain outstanding; the English static replay is a fallback, not a replacement for the live coordinate-search backend. The immediate next step is to deploy the prepared service with its persistent data seed and validate public links.

## SI / AI disclosure — team to verify

The original concept was supplied by the team: accessible exploration of real SPHEREx images, wavelength selection, time comparisons and investigation of apparent changes. OpenAI Codex assisted with code inspection, debugging, implementation of evidence export and a real-data English replay, validation scripts, catalogue checks and drafting documentation and submission text. SI/AI-generated suggestions were used to refine implementation of the existing concept, not to claim authorship of the team's original idea.

The team must review these contributions, make the final decisions and accurately describe any additional tools used outside this session. The sky images are actual NASA data, not AI-generated imagery. Synthetic fixtures appear only in labelled software tests. No generated astronomy observation or invented result is shown as data. This disclosure is not a certification by the assistant that the team's originality declaration is satisfied.

## Thirty-second video script

Use screen captures of the actual application or English replay. Add the team's real names and chosen project name; do not exceed 30 seconds. Approximate narration, to rehearse aloud:

> We are [team], working on Planet X and SPHEREx. Our tool turns NASA images into comparisons anyone can inspect. Enter coordinates, compare dates, then explore wavelengths separately. Before interpreting a change, check coverage, flags and measurement limits. Save an evidence card with the original observations and a reproducible result. We tested all five required fields. We do not claim a discovery: we help people ask a better next question.

| Time | Screen |
|---|---|
| 0–4 s | Team identity and chosen project name; challenge title |
| 4–11 s | Known comet 3I/ATLAS moves between two real SPHEREx images; visible UTC dates |
| 11–16 s | Separate wavelength player and its warning |
| 16–24 s | Selected point; one diagnostic and the evidence card |
| 24–30 s | Five-field result summary; real NASA data; clear unconfirmed status and public link |

The timing is a proposed edit, not a measured finished recording. A spoken language other than English requires English subtitles under the official guide. Do not include images, voices or likenesses of minors in the submitted demo.

## Alternative: seven-slide demo plan

Exactly seven slides including title and introductions. Keep text large, show actual observations and provide public links.

1. **[Chosen project name]** — team name, members, Planet X and SPHEREx; one-sentence purpose.
2. **A different image is not yet a discovery** — the same field at different dates/wavelengths; explain the interpretation problem.
3. **Coordinates → actual NASA images** — workbench screenshot with real dates, source identifiers and time playback.
4. **Separate time from wavelength** — wavelength player beside a clear time/wavelength distinction; no claim of complete simultaneous spectra.
5. **Inspect a hypothesis, keep the evidence** — selected point, explicit diagnostic limits and portable evidence card.
6. **Results, including failures** — 22/25 prepared cutouts, corrected catalogue fields, independent numerical check, no confirmed motion/variability; identify the limits.
7. **Try it and reproduce it** — verified public URLs after deployment; NASA data and tools, SI/AI disclosure, next step. Include team-approved credits.

## References

Official 2026 challenge, judging and submission guides were read in the prior same-day audit; their dated local snapshots were read during finalization. Direct web-tool reads of those pages again failed; the participant FAQ was read directly in the browser on 14 November 2026. Do not describe the failed fetches as successful verification. The guides specify five criteria, each 1–5, and an English submission with a video ≤30 seconds or a deck ≤7 slides. They give a 15 November 2026, 23:59 deadline in the local event's time zone; the team must also respect any earlier local presentation schedule.

- [Planet X and SPHEREx — 2026 challenge](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/).
- [Judging & Awards Guide](https://www.spaceappschallenge.org/resources/judging-awards-guide/).
- [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/).
- [Participant FAQs](https://www.spaceappschallenge.org/resources/participant-faqs/).
- [IRSA SPHEREx mission and data](https://irsa.ipac.caltech.edu/Missions/spherex.html).
- [SPHEREx data products and calibration documentation](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/).
- [IRSA cutout tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/) and [PSF tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/).
- [IRSA Spectrophotometry](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html) and [Source Discovery notebook](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/).
- [SIMBAD coordinate conventions](https://simbad.cds.unistra.fr/Pages/guide/ch15.htx); individual target references are retained in `backend/targets.json`.
- [Kirkpatrick et al. 2021 catalogue, J/ApJS/253/7](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJS/253/7), including the WISE 0855 reference position at MJD 57633.39.
- [Photutils aperture photometry](https://docs.astropy.org/projects/photutils/en/stable/api/photutils.aperture.aperture_photometry.html).
- [WiseView authorship — NASA](https://science.nasa.gov/people/dan-caselden/) and [Backyard Worlds — NASA](https://science.nasa.gov/citizen-science/backyard-worlds-planet-9/).
- Software: [Astropy](https://www.astropy.org/), [Astroquery](https://astroquery.readthedocs.io/), [Reproject](https://reproject.readthedocs.io/), [SEP](https://sep.readthedocs.io/), NumPy, SciPy, Pillow, FastAPI, React, Vite, TypeScript, SQLite, [Aladin Lite](https://github.com/cds-astro/aladin-lite), Lucide and locally bundled IBM Plex Sans. Versions are in lockfiles; local licences and visual-asset attribution are in `ASSET_SOURCES.md` and `frontend/public/licenses/`.

SPHEREx acknowledgement:

This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.
