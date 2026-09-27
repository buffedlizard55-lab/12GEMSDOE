"""Frozen spatial 4-fold screening comparing Raw 19 bands against Candidate Geological Hypotheses.

Hypothesis 1 (Candidate 23): Concealed Basement Step & Gravity Gradient Curvature
Hypothesis 1+2+3 (Candidate 25): Multi-Physics Structural Coupling (Basement Step + Tilt Angle + Strain Dilation)

Spatially blocked 512-px folds, 12-px collar exclusion, fixed seed 12027.
"""
import json, os, time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier
from core import folds, training_mask, components, sha

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

with rasterio.open('data/sample_submission.tif') as s:
    valid = s.read_masks(1) > 0
    shape = s.shape

with rasterio.open('data/labels.tif') as s:
    truth = (s.read(1, masked=True).filled(0) > 0) & valid

mempath = ROOT / 'data/candidate-screen-features.npy'
cube = np.lib.format.open_memmap(str(mempath), mode='r')
flat = cube.reshape(-1, 25)

fmap = folds(truth)
np.save('data/foldmap.npy', fmap)

report = {
    'protocol': 'docs/hypotheses.md',
    'status': 'preregistered_spatial_holdout_screen',
    'foldmap_sha256': sha('data/foldmap.npy'),
    'feature_cube_shape': list(cube.shape),
    'arms_evaluated': {
        'raw19': 'Baseline: 19 raw GeoDAWN and INGENIOUS bands',
        'h1_basement_step23': 'Hypothesis 1: Raw 19 + Depth to basement gradient magnitude, basement Laplacian curvature, gravity horizontal gradient derivative, conductivity boundary',
        'multiphysics25': 'Hypotheses 1+2+3: Candidate 23 + Magnetic tilt angle horizontal derivative + Transtensional shear-dilation index',
        'random06': 'Matched random 6% area control'
    },
    'folds': []
}

t_all = time.time()
for fold in range(4):
    start = time.time()
    train = training_mask(fmap, fold, valid)
    region = valid & (fmap == fold)
    assert not (train & region).any()
    
    rng = np.random.default_rng(12027 + fold)
    pos = np.flatnonzero(train & truth)
    neg = np.flatnonzero(train & ~truth)
    neg = rng.choice(neg, min(100000, len(neg)), replace=False)
    idx = np.concatenate([pos, neg])
    y = truth.ravel()[idx]
    weights = np.where(y, 0.5/len(pos), 0.5/len(neg)) * len(idx)
    
    testidx = np.flatnonzero(region)
    row = {
        'fold': fold,
        'train_positive': int(len(pos)),
        'train_negative': int(len(neg)),
        'score_pixels': int(len(testidx)),
        'score_positive': int((truth & region).sum()),
        'arms': {}
    }
    
    k = int(0.06 * len(testidx))
    
    for name, n_feat in [('raw19', 19), ('h1_basement_step23', 23), ('multiphysics25', 25)]:
        clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=15, early_stopping=False, random_state=12027)
        clf.fit(flat[idx, :n_feat], y, sample_weight=weights)
        prob = np.empty(len(testidx), dtype='float32')
        for start_i in range(0, len(testidx), 100000):
            ids = testidx[start_i:start_i+100000]
            prob[start_i:start_i+len(ids)] = clf.predict_proba(flat[ids, :n_feat])[:, 1]
            
        selected = np.lexsort((testidx, -prob))[:k]
        pred = np.zeros(shape, dtype='float32')
        pred.ravel()[testidx[selected]] = 1.0
        row['arms'][name] = components(pred, truth, region)
        
    # Random 6% control
    pred_rand = np.zeros(shape, dtype='float32')
    pred_rand.ravel()[rng.choice(testidx, k, replace=False)] = 1.0
    row['arms']['random06'] = components(pred_rand, truth, region)
    
    row['seconds'] = round(time.time() - start, 2)
    report['folds'].append(row)
    print(f"Fold {fold} complete in {row['seconds']}s: raw19={row['arms']['raw19']['dti']:.5f}, h1={row['arms']['h1_basement_step23']['dti']:.5f}, multiphysics25={row['arms']['multiphysics25']['dti']:.5f}", flush=True)

report['means'] = {
    arm: float(np.mean([r['arms'][arm]['dti'] for r in report['folds']]))
    for arm in ['raw19', 'h1_basement_step23', 'multiphysics25', 'random06']
}
report['paired_deltas_h1_vs_raw19'] = [
    float(r['arms']['h1_basement_step23']['dti'] - r['arms']['raw19']['dti']) for r in report['folds']
]
report['paired_deltas_multiphysics25_vs_raw19'] = [
    float(r['arms']['multiphysics25']['dti'] - r['arms']['raw19']['dti']) for r in report['folds']
]

report['total_seconds'] = round(time.time() - t_all, 2)
Path('evidence/screening.json').write_text(json.dumps(report, indent=2))
Path('docs/screening.json').write_text(json.dumps(report, indent=2))
print("Final summary:", json.dumps(report['means'], indent=2), flush=True)
