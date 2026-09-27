"""Auditable raster utilities and literal competition metric (100 m grid)."""
import hashlib
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, binary_dilation, uniform_filter, shift, maximum_filter

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while b := f.read(1024*1024): h.update(b)
    return h.hexdigest()

def validate(path, template):
    with rasterio.open(template) as t, rasterio.open(path) as p:
        for name in ['crs', 'transform', 'width', 'height']:
            if getattr(p, name) != getattr(t, name): raise ValueError('grid mismatch: '+name)
        if p.count != 1 or p.dtypes != ('float32',): raise ValueError('requires one float32 band')
        v = t.read_masks(1)>0
        a = p.read(1)
        if not np.array_equal(p.read_masks(1)>0, v): raise ValueError('mask mismatch')
        if not v.any(): raise ValueError('empty footprint')
        if not np.isfinite(a[v]).all() or (a[v]<0).any() or (a[v]>1).any():
            raise ValueError('Predicted values must be finite and in range [0, 1]')
        if not np.isnan(a[~v]).all(): raise ValueError('outside footprint must be NaN')
        return {'sha256':sha(path), 'valid_pixels':int(v.sum()), 'min':float(a[v].min()),'max':float(a[v].max())}

def write_prediction(path, values, template):
    with rasterio.open(template) as t:
        valid=t.read_masks(1)>0; profile=t.profile.copy()
    a=np.asarray(values,dtype='float32')
    if a.shape!=valid.shape or not np.isfinite(a[valid]).all() or (a[valid]<0).any() or (a[valid]>1).any():
        raise ValueError('invalid predictions; fix inference, do not silently clip')
    a=a.copy();a[~valid]=np.nan
    profile.update(count=1,dtype='float32',nodata=np.nan,compress='deflate')
    with rasterio.open(path,'w',**profile) as d:d.write(a,1)
    return validate(path,template)

def components(p, truth, region):
    if p.shape != truth.shape or p.shape != region.shape: raise ValueError('shape')
    if not np.isfinite(p).all() or (p<0).any() or (p>1).any(): raise ValueError('range')
    p=np.where(region,p,0);t=truth & region
    yy,xx=np.nonzero(t);credit=np.zeros(len(yy),dtype='float64')
    for dy in range(-2,3):
        for dx in range(-2,3):
            k=max(1-np.hypot(dy,dx)/3,0)
            y=yy+dy;x=xx+dx;v=(y>=0)&(x>=0)&(y<p.shape[0])&(x<p.shape[1])
            credit[v]=np.maximum(credit[v],p[y[v],x[v]]*k)
    tp=float(credit.sum());fn=float(len(yy)-tp)
    weight=np.minimum(distance_transform_edt(~t)/3,1) if t.any() else np.ones(t.shape)
    fp=float(np.sum(p*weight,dtype='float64'))
    return dict(tp=tp,fp=fp,fn=fn,dti=tp/(tp+.2*fp+.8*fn+1e-7))

def folds(truth, block=512):
    h,w=truth.shape;counts=[]
    for y in range(0,h,block):
        for x in range(0,w,block): counts.append((int(truth[y:y+block,x:x+block].sum()),y,x))
    out=np.zeros((h,w),dtype='uint8')
    for rank,(_,y,x) in enumerate(sorted(counts,key=lambda v:(-v[0],v[1],v[2]))):
        out[y:y+block,x:x+block]=rank%4
    return out

def training_mask(foldmap, fold, valid, collar=12):
    return valid & ~binary_dilation(foldmap==fold,iterations=collar)

def restoration(a, valid):
    """Mismatch reduction after tangential restoration, 4 boundary orientations.

    No wrapped edges. Unsupported 12-pixel boundary/missing-data neighborhoods
    yield NaN rather than false lineaments. No labels or global fitted scaling.
    """
    safe=maximum_filter((~valid).astype("uint8"),size=25,mode="constant",cval=1)==0
    a=np.where(valid,a,0).astype('float32')
    mean=uniform_filter(a,9);var=np.maximum(uniform_filter(a*a,9)-mean*mean,0)
    z=(a-mean)/np.sqrt(var+1e-6)
    results=[]
    for ny,nx in [(1,0),(0,1),(1,1),(1,-1)]:
        left=shift(z,(2*ny,2*nx),order=0,mode='constant',cval=0)
        right=shift(z,(-2*ny,-2*nx),order=0,mode='constant',cval=0)
        zero=uniform_filter((left-right)**2,5)
        best=zero.copy()
        for lag in [-4,-2,2,4]:
            moved=shift(right,(-nx*lag,ny*lag),order=0,mode='constant',cval=0)
            best=np.minimum(best,uniform_filter((left-moved)**2,5))
        score=np.maximum(zero-best,0)/(zero+1e-6);score[~safe]=np.nan
        results.append(score)
    return results
