"""Reviewed-label logistic model with group holdouts and JSON-only persistence.

No synthetic data are used to activate a scientific classifier. Scores are not
calibrated probabilities of discovery, source existence or instrument defects.
"""
import hashlib
import json

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.spatial import cKDTree
from scipy.stats import beta as beta_distribution

from backend import store

FEATURES = ['snr', 'reduced_chi2', 'elongation', 'valid_fraction', 'bad_fraction',
            'negative_residual_fraction', 'positive_residual_fraction', 'centroid_shift_arcsec']
VERSION = 'artifact-logistic-2'


def all_records(kind):
    with store.connect() as db:
        return [json.loads(r[0]) for r in db.execute('SELECT body FROM records WHERE kind=?', (kind,))]


def dataset():
    # Latest annotation wins only after explicit review; uncertain/blend retracts it.
    latest = {}
    for label in sorted(all_records('quality_label'), key=lambda r: (r['created_at'], r['id'])):
        latest[(label['source_id'], label['frame_id'])] = label
    examples = []
    for label in latest.values():
        if label['label'] not in ('source', 'artifact') or not store.get('label_review', label['id']):
            continue
        profile = store.get('artifact_features', label['source_id']+':'+label['frame_id'])
        if not profile or not profile.get('valid') or profile.get('method') != 'native-centroid-2' or not profile.get('obs_id') or any(not np.isfinite(profile.get(k, np.nan)) for k in FEATURES):
            continue
        examples.append(dict(label_id=label['id'], source_id=label['source_id'], analysis_id=label['analysis_id'],
                             frame_id=label['frame_id'], y=int(label['label'] == 'artifact'), profile=profile))
    return examples


def connected_groups(examples):
    parent = list(range(len(examples)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a, b):
        parent[root(a)] = root(b)
    seen = {}
    for i, example in enumerate(examples):
        for namespace, value in [('analysis', example['analysis_id']), ('source', example['source_id']),
                                 ('fits', example['profile'].get('source_sha256')),
                                 ('exposure', example['profile'].get('obs_id'))]:
            if value:
                key = (namespace, value)
                if key in seen: union(i, seen[key])
                seen[key] = i
    if examples:
        radians = np.deg2rad([[e['profile']['ra'], e['profile']['dec']] for e in examples])
        xyz = np.column_stack((np.cos(radians[:, 1])*np.cos(radians[:, 0]),
                               np.cos(radians[:, 1])*np.sin(radians[:, 0]), np.sin(radians[:, 1])))
        for a, b in cKDTree(xyz).query_pairs(2*np.sin(np.deg2rad(60/3600)/2)):
            union(a, b)
    # Stable component key from analysis identity, not labels or their timestamps.
    names = {}
    for i, example in enumerate(examples):
        names.setdefault(root(i), []).append(example['analysis_id'])
    return [min(names[root(i)]) for i in range(len(examples))]


def readiness(examples=None):
    examples = dataset() if examples is None else examples
    counts = {name: sum(e['y'] == value for e in examples) for name, value in [('source', 0), ('artifact', 1)]}
    groups = connected_groups(examples)
    active=store.get('artifact_active','current')
    model=store.get('artifact_model',active['model_id']) if active else None
    usable=bool(model and model.get('method')==VERSION and model.get('status')=='local_holdout_passed' and model.get('confidence_pass'))
    return dict(examples=len(examples), counts=counts, independent_groups=len(set(groups)),
                minimum_examples=60, minimum_per_class=20, minimum_groups=12,
                ready=len(examples) >= 60 and min(counts.values()) >= 20 and len(set(groups)) >= 12,
                active_model=active if usable else None,archived_model_ignored=bool(active and not usable),scientifically_validated=False)


def lower_bound(successes, trials):
    """One-sided exact 95% binomial bound; never evidence of group independence."""
    return float(beta_distribution.ppf(.05, successes, trials-successes+1)) if successes and trials else 0.


def group_confidence(y, predicted, groups):
    # Treat an entire group as successful only when every reviewed case of that
    # class is correct. Group correlations within a field cannot inflate n.
    results = {}
    for name, label in [('source_retention', 0), ('artifact_recall', 1)]:
        success = []
        for group in sorted(set(groups)):
            subset = (np.asarray(groups) == group) & (y == label)
            if np.any(subset):
                success.append(bool(np.all(predicted[subset] == label)))
        results[name] = dict(groups=len(success), successful_groups=sum(success),
                             lower_95=lower_bound(sum(success), len(success)))
    return results


def train():
    examples = dataset()
    state = readiness(examples)
    if not state['ready']:
        return dict(status='insufficient_reviewed_data', readiness=state,
                    reason='Potrzeba 60 zweryfikowanych ocen z cechami, po 20 każdej klasy i 12 niezależnych grup.')
    if len(examples) > 5000:
        raise ValueError('Limit lokalnego treningu: 5000 przykładów.')
    groups = connected_groups(examples)
    # Hash buckets keep assignments stable when independent new fields are added.
    def partition(group):
        bucket = int(hashlib.sha256(('artifact-holdout-1:'+group).encode()).hexdigest()[:8], 16) % 10
        return 'test' if bucket < 2 else 'validation' if bucket < 4 else 'train'
    split = np.array([partition(group) for group in groups])
    x = np.array([[e['profile'][k] for k in FEATURES] for e in examples])
    y = np.array([e['y'] for e in examples])
    for name in ('train', 'validation', 'test'):
        if any(np.sum((split == name) & (y == label)) < (10 if name == 'train' else 5) for label in (0, 1)):
            return dict(status='insufficient_holdout', readiness=state,
                        reason='Stały podział grup nie zawiera dostatecznej liczby obu klas. Dodaj niezależne pola.')
    train_mask = split == 'train'
    mean, scale = x[train_mask].mean(axis=0), x[train_mask].std(axis=0)
    scale[scale < 1e-8] = 1
    z = np.column_stack((np.ones(len(x)), np.clip((x-mean)/scale, -20, 20)))
    a, b = z[train_mask], y[train_mask]
    def loss(beta):
        logit = a@beta
        value = np.mean(np.logaddexp(0, logit)-b*logit)+.01*np.dot(beta[1:], beta[1:])
        gradient = a.T@(expit(logit)-b)/len(b)
        gradient[1:] += .02*beta[1:]
        return value, gradient
    fit = minimize(loss, np.zeros(z.shape[1]), jac=True, method='L-BFGS-B')
    if not fit.success:
        raise ValueError('Trening nie osiągnął zbieżności.')
    scores = expit(z@fit.x)
    val = split == 'validation'
    # Threshold chosen without looking at test labels.
    source_scores = scores[val & (y == 0)]
    threshold = float(np.max(source_scores) if len(source_scores) < 20 else np.quantile(source_scores, .95))
    def metrics(mask):
        predicted = scores[mask] > threshold
        truth = y[mask]
        return dict(source_retention=float(np.mean(~predicted[truth == 0])),
                    artifact_recall=float(np.mean(predicted[truth == 1])), examples=int(mask.sum()))
    validation, test = metrics(val), metrics(split == 'test')
    # Compare to an interpretable shape-rule score at the same validation budget.
    baseline_scores = np.maximum(x[:, FEATURES.index('reduced_chi2')]-3, 0)+np.maximum(x[:, FEATURES.index('elongation')]-2, 0)
    baseline_scores += 20*np.maximum(x[:, FEATURES.index('bad_fraction')]-.05, 0)
    baseline_threshold = float(np.max(baseline_scores[val & (y == 0)]))
    test_mask = split == 'test'
    baseline_flags = baseline_scores[test_mask] > baseline_threshold
    baseline_truth = y[test_mask]
    baseline = dict(source_retention=float(np.mean(~baseline_flags[baseline_truth == 0])),
                    artifact_recall=float(np.mean(baseline_flags[baseline_truth == 1])), threshold=baseline_threshold)
    improves_baseline = baseline['source_retention'] < .95 or test['artifact_recall'] >= baseline['artifact_recall']+.05
    confidence = group_confidence(y[test_mask], (scores[test_mask] > threshold).astype(int), np.asarray(groups)[test_mask])
    confidence_pass = confidence['source_retention']['lower_95'] >= .95 and confidence['artifact_recall']['lower_95'] >= .3
    accepted = validation['source_retention'] >= .9 and test['source_retention'] >= .95 and test['artifact_recall'] >= .3 and improves_baseline and confidence_pass
    fingerprint = hashlib.sha256(json.dumps(examples, sort_keys=True).encode()).hexdigest()
    key = hashlib.sha256((VERSION+fingerprint).encode()).hexdigest()
    result = dict(id=key, method=VERSION, status='local_holdout_passed' if accepted else 'experimental_rejected',
                  features=FEATURES, mean=mean.tolist(), scale=scale.tolist(), coefficients=fit.x.tolist(),
                  threshold=threshold, validation=validation, test=test, rule_baseline=baseline,
                  improves_baseline=improves_baseline, dataset_sha256=fingerprint,
                  group_confidence=confidence,confidence_pass=confidence_pass,scientifically_validated=False,
                  label_ids=[e['label_id'] for e in examples], groups=groups, split=split.tolist(),
                  activation_criteria=dict(source_retention=.95, artifact_recall=.3, minimum_recall_improvement=.05,
                                           one_sided_group_lower_95_retention=.95,one_sided_group_lower_95_recall=.3),
                  limitations=['Mały lokalny zbiór nie gwarantuje skuteczności na innych polach lub detektorach.',
                               'Oceny są ręczne, bez uwierzytelnienia recenzenta w tej lokalnej aplikacji.',
                               'Stały test jest zapisany; wielokrotne dostrajanie po jego obejrzeniu narusza niezależność.',
                               'Wynik modelu służy do przeglądu. Nie jest skalibrowanym prawdopodobieństwem.'])
    store.put('artifact_model', key, result)
    if accepted:
        store.put('artifact_active', 'current', dict(model_id=key, method=VERSION))
    return result


def predict(profile):
    active = store.get('artifact_active', 'current')
    if not active:
        return dict(status='no_validated_model', score=None)
    model = store.get('artifact_model', active['model_id'])
    if not model or model.get('method') != VERSION or model['status'] != 'local_holdout_passed' or not model.get('confidence_pass') or profile.get('method')!='native-centroid-2' or any(not np.isfinite(profile.get(k, np.nan)) for k in FEATURES):
        return dict(status='unavailable', score=None)
    values = np.array([profile[k] for k in FEATURES])
    z = np.r_[1., np.clip((values-np.array(model['mean']))/np.array(model['scale']), -20, 20)]
    score = float(expit(z@np.array(model['coefficients'])))
    return dict(status='review_artifact' if score > model['threshold'] else 'no_model_warning',
                score=score, threshold=model['threshold'], model_id=model['id'])


def assess_profile(profile):
    warnings = []
    if profile['snr'] < 5: warnings.append('Słabe dopasowane źródło.')
    if profile['reduced_chi2'] > 3: warnings.append('Kształt lub tło nie pasuje do modelu PSF.')
    if profile['elongation'] > 2: warnings.append('Wydłużony sygnał: źródło rozległe, sąsiedzi, ślad lub artefakt.')
    if profile['bad_fraction'] > .05: warnings.append('Ponad 5% wadliwych pikseli w otoczeniu.')
    if profile['negative_residual_fraction'] > .05 or profile['positive_residual_fraction'] > .05:
        warnings.append('Struktura w resztach dopasowania wymaga przeglądu.')
    return dict(rule_status='review' if warnings else 'no_rule_warning', warnings=warnings,
                model=predict(profile))
