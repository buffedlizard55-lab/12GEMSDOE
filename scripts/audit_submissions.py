"""Compare local published artifacts, not authenticated upload receipts."""
import json,itertools
from pathlib import Path
import numpy as np
import rasterio
from core import sha
rows=[];arrays={};masks={};grids={}
for name in ['gems1','gems5','gems8']:
    p=Path('data')/(name+'.tif')
    with rasterio.open(p) as s:
        a=s.read(1);mask=s.read_masks(1)>0
        grid=(str(s.crs),list(s.transform),s.width,s.height)
        rows.append(dict(name=name,sha256=sha(p),bytes=p.stat().st_size,grid=grid,valid_pixels=int(mask.sum()),range=[float(a[mask].min()),float(a[mask].max())]))
        arrays[name]=a;masks[name]=mask;grids[name]=grid
pairs=[]
for x,y in itertools.combinations(arrays,2):
    same_grid=grids[x]==grids[y];same_mask=same_grid and np.array_equal(masks[x],masks[y])
    mask=masks[x]&masks[y]
    pairs.append(dict(a=x,b=y,same_grid=same_grid,same_mask=same_mask,pixel_equal=bool(same_mask and np.array_equal(arrays[x][mask],arrays[y][mask])),fraction_different=float(np.mean(arrays[x][mask]!=arrays[y][mask])) if same_grid else None))
Path('evidence/identity.json').write_text(json.dumps({'checked_utc':'2026-09-27','scope':'published artifacts, not upload receipts','files':rows,'pairs':pairs},indent=2))
print(json.dumps(pairs,indent=2))
