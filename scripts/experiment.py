"""Frozen screening only. Does not release submissions or tune on test folds."""
import json, os, time
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','2')
import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier
from core import folds, training_mask, restoration, components, sha
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
with rasterio.open('data/sample_submission.tif') as s: valid=s.read_masks(1)>0; shape=s.shape
with rasterio.open('data/labels.tif') as s: truth=(s.read(1,masked=True).filled(0)>0)&valid
cube=np.lib.format.open_memmap('data/screen-features.npy',mode='w+',dtype='float32',shape=(*shape,27))
with rasterio.open('data/training_features.tif') as s:
    for band in range(1,20):
        a=s.read(band,masked=True).filled(np.nan);cube[:,:,band-1]=a
    for j,band in enumerate([2,1]):
        a=cube[:,:,band-1].copy();mask=valid&np.isfinite(a)
        for k,channel in enumerate(restoration(a,mask)):cube[:,:,19+4*j+k]=channel
cube.flush(); flat=cube.reshape(-1,27);fmap=folds(truth)
np.save('data/foldmap.npy',fmap)
report={'protocol':'docs/hypotheses.md','status':'screening_only_not_submission_eligible', 'foldmap_sha256':sha('data/foldmap.npy'), 'source_sha256':{str(p):sha(p) for p in [Path('scripts/experiment.py'),Path('scripts/core.py'),Path('docs/hypotheses.md')]},'folds':[]}
for fold in range(4):
    start=time.time();train=training_mask(fmap,fold,valid);region=valid&(fmap==fold)
    assert not (train&region).any()
    rng=np.random.default_rng(12027+fold)
    pos=np.flatnonzero(train&truth);neg=np.flatnonzero(train&~truth)
    neg=rng.choice(neg,min(100000,len(neg)),replace=False);idx=np.concatenate([pos,neg]);y=truth.ravel()[idx]
    weights=np.where(y,.5/len(pos),.5/len(neg))*len(idx)
    testidx=np.flatnonzero(region);row={'fold':fold,'train_positive':len(pos),'train_negative':len(neg),'score_pixels':len(testidx),'score_positive':int((truth&region).sum()),'arms':{}}
    for name,n in [('raw19',19),('restoration27',27)]:
        model=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,early_stopping=False,random_state=12027)
        model.fit(flat[idx,:n],y,sample_weight=weights)
        prob=np.empty(len(testidx),dtype='float32')
        for start_i in range(0,len(testidx),100000):
            ids=testidx[start_i:start_i+100000];prob[start_i:start_i+len(ids)]=model.predict_proba(flat[ids,:n])[:,1]
        # Exact fixed area budget; deterministic tie-breaking by flat index.
        k=int(.06*len(testidx));selected=np.lexsort((testidx,-prob))[:k]
        pred=np.zeros(shape,dtype='float32');pred.ravel()[testidx[selected]]=1
        row['arms'][name]=components(pred,truth,region)
    pred=np.zeros(shape,dtype='float32');pred.ravel()[rng.choice(testidx,int(.06*len(testidx)),replace=False)]=1
    row['arms']['random06']=components(pred,truth,region)
    row['seconds']=time.time()-start;report['folds'].append(row)
    print(json.dumps(row),flush=True)
    Path('evidence/screening.json').write_text(json.dumps(report,indent=2))
report['means']={arm:float(np.mean([r['arms'][arm]['dti'] for r in report['folds']])) for arm in ['raw19','restoration27','random06']}
report['paired_deltas']=[r['arms']['restoration27']['dti']-r['arms']['raw19']['dti'] for r in report['folds']]
report['release_allowed']=False
report['release_reason']='Current strongest sibling baseline not reproduced under identical protocol; screening is not a release gate.'
Path('evidence/screening.json').write_text(json.dumps(report,indent=2));print(report['means'],flush=True)
