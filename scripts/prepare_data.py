import json
from pathlib import Path
import rasterio
from core import sha
base=Path(__file__).resolve().parents[1]
manifest=json.load(open(base/'evidence/bridge-manifest.json')); result=[]
grid=None
for f in manifest['files']:
    p=base/'data'/f['canonical']
    if sha(p)!=f['sha256']: raise ValueError('checksum mismatch: '+str(p))
    with rasterio.open(p) as s:
        current=(str(s.crs),list(s.transform),s.width,s.height)
        if grid is not None and current!=grid:raise ValueError('unaligned data')
        grid=current
        result.append(dict(file=f['canonical'],sha256=sha(p),crs=str(s.crs),transform=list(s.transform),shape=list(s.shape),bands=s.count,descriptions=s.descriptions,valid_pixels=int((s.read_masks(1)>0).sum())))
(base/'evidence/data-inventory.json').write_text(json.dumps(result,indent=2))
print('All 3 rasters verified against team bridge pins; official portal identity not independently authenticated.')
