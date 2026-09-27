"""Publish measured screening evidence without unlocking the submission gate."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import t
p=Path('evidence/screening.json');r=json.loads(p.read_text())
if len(r.get('folds',[]))!=4 or 'means' not in r:raise ValueError('incomplete experiment')
d=np.array(r['paired_deltas']);se=d.std(ddof=1)/np.sqrt(len(d))
r['summary']={'paired_mean':float(d.mean()),'wins':int((d>0).sum()),'paired_t_interval_95_descriptive_only':[float(d.mean()-t.ppf(.975,3)*se),float(d.mean()+t.ppf(.975,3)*se)],'decision':'REJECT for submission: lower mean DTI than raw baseline, two of four fold wins, both learned arms below matched random-area control','caution':'Four spatial folds are not independent geological systems. Interval is descriptive, not proof of discovery. No private-label performance is known.'}
r['pooled']={}
for arm in r['means']:
    c={k:sum(row['arms'][arm][k] for row in r['folds']) for k in ['tp','fp','fn']}
    c['dti']=c['tp']/(c['tp']+.2*c['fp']+.8*c['fn']+1e-7);r['pooled'][arm]=c
p.write_text(json.dumps(r,indent=2)+'\n');Path('docs/screening.json').write_text(p.read_text())
print(json.dumps(r['summary'],indent=2))
