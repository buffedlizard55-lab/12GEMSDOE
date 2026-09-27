"""Retrieve read-only, pinned team artifacts; never submits predictions."""
import json,subprocess
from pathlib import Path
from core import sha
root=Path(__file__).resolve().parents[1];(root/'data').mkdir(exist_ok=True)
for row in json.loads((root/'evidence/history-sources.json').read_text()):
    dest=root/'data'/row['filename']
    with dest.open('wb') as f:
        subprocess.run(['gh','api',f"repos/buffedlizard55-lab/{row['repo']}/contents/{row['path']}?ref={row['revision']}",'-H','Accept: application/vnd.github.raw+json'],stdout=f,check=True)
    if sha(dest)!=row['sha256']:raise ValueError('history identity changed: '+str(dest))
    print('verified',row['filename'])
