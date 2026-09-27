import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from core import components,folds,training_mask,restoration,write_prediction,validate

def test_metric_literal():
    rng=np.random.default_rng(10);p=rng.random((7,8));t=rng.random((7,8))>.8
    got=components(p,t,np.ones(t.shape,bool));gt=np.argwhere(t);tp=0;fp=0
    for g in gt:
        tp+=max(p[y,x]*max(1-np.linalg.norm(np.array([y,x])-g)/3,0) for y,x in np.ndindex(t.shape))
    for y,x in np.ndindex(t.shape):
        fp+=p[y,x]*(1-max(max(1-np.linalg.norm(np.array([y,x])-g)/3,0) for g in gt))
    assert got['tp']==pytest.approx(tp);assert got['fp']==pytest.approx(fp)
    assert got['fn']==pytest.approx(t.sum()-tp)

def test_metric_identity_empty_and_region():
    t=np.zeros((9,9),bool);t[4,4]=1;r=np.ones(t.shape,bool)
    assert components(t.astype(float),t,r)['dti']==pytest.approx(1)
    assert components(np.zeros(t.shape),t,r)['dti']==0
    r[:]=False
    assert components(np.ones(t.shape),t,r)['fp']==0
    with pytest.raises(ValueError):components(np.full(t.shape,2),t,r)

def test_spatial_collar():
    t=np.eye(80,dtype=bool);f=folds(t,block=20);v=np.ones_like(t)
    for k in range(4):
        train=training_mask(f,k,v,collar=12)
        from scipy.ndimage import distance_transform_edt
        assert (distance_transform_edt(f!=k)[train]>3).all()
        assert components((t&train).astype(float),t,v&(f==k))['tp']==0

def template(tmp_path):
    p=tmp_path/'template.tif';a=np.zeros((20,20),np.float32);a[0,:]=np.nan
    with rasterio.open(p,'w',driver='GTiff',height=20,width=20,count=1,dtype='float32',crs='EPSG:32611',transform=from_origin(200000,4500000,100,100),nodata=np.nan) as s:s.write(a,1)
    return p

def test_export_range_mask_and_grid(tmp_path):
    t=template(tmp_path);p=tmp_path/'candidate.tif';a=np.full((20,20),.3,np.float32)
    assert write_prediction(p,a,t)['valid_pixels']==380
    for bad in [-1,1.01,np.inf,np.nan]:
        a[5,5]=bad
        with pytest.raises(ValueError):write_prediction(p,a,t)
    with rasterio.open(p,'r+') as s:s.transform=from_origin(200100,4500000,100,100)
    with pytest.raises(ValueError,match='grid'):validate(p,t)

def test_restoration_constant_and_nodata():
    a=np.ones((80,80),np.float32);v=np.ones(a.shape,bool);v[40,40]=0
    for channel in restoration(a,v):
        assert np.nanmax(channel)==0
        assert np.isnan(channel[40,40]);assert np.isnan(channel[0,0])

def test_packaging_rejects_release_and_duplicate(tmp_path):
    from package_submission import package
    t=template(tmp_path);p=tmp_path/'p.npy';np.save(p,np.full((20,20),.4,np.float32))
    with pytest.raises(ValueError,match='Release blocked'):package(p,t,tmp_path,'test',True)
    result=package(p,t,tmp_path,'test');assert not result['submission_eligible']
    with pytest.raises(ValueError,match='duplicate'):package(p,t,tmp_path,'test')
    with pytest.raises(ValueError,match='duplicate'):package(p,t,tmp_path,'different-name')
    with pytest.raises(ValueError):package(p,t,tmp_path,'../../escape')

def test_restoration_detects_synthetic_displacement():
    yy,_=np.indices((100,100));a=(np.sin(yy*.4)+.4*np.cos(yy*.17)).astype('float32')
    displaced=a.copy();displaced[:,50:]=np.roll(a,4,axis=0)[:,50:]
    valid=np.ones(a.shape,bool)
    null=restoration(a,valid)[1];offset=restoration(displaced,valid)[1]
    assert np.nanmean(offset[20:80,49:51])>np.nanmean(null[20:80,49:51])+.2
