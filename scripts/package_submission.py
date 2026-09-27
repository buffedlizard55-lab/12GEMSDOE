"""Research export only until a strongest-baseline release gate is implemented.

An explicit research artifact is safer than a renamed old submission. This command
never claims eligibility and rejects --release rather than trusting hand-written scores.
"""
import argparse,json
from pathlib import Path
import numpy as np
from core import write_prediction,sha

def package(prediction,template,out,slug,release=False):
    if release:raise ValueError('Release blocked: strongest-baseline holdout gate not established')
    if not slug or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in slug):raise ValueError('slug must use lowercase letters, digits, hyphens')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    arr=np.load(prediction,allow_pickle=False)
    import tempfile
    with tempfile.TemporaryDirectory(dir=out) as td:
        tmp=Path(td)/'candidate.tif';report=write_prediction(tmp,arr,template)
        digest=report['sha256'];name=f'12gems-{slug}-research-{digest[:12]}.tif';dest=out/name
        if dest.exists() or any(sha(p)==digest for p in out.glob('*.tif')):
            raise ValueError('duplicate artifact: '+name)
        tmp.replace(dest)
    manifest=dict(report,file=name,submission_eligible=False,note=f'12GEMS {slug}; research only; holdout release blocked; sha {digest[:12]}',template_sha256=sha(template),prediction_sha256=sha(prediction))
    dest.with_suffix('.json').write_text(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('prediction');a.add_argument('--template',default='data/sample_submission.tif');a.add_argument('--out',default='data/research-exports');a.add_argument('--name',required=True);a.add_argument('--release',action='store_true');args=a.parse_args()
    print(json.dumps(package(args.prediction,args.template,args.out,args.name,args.release),indent=2))
