import io


import numpy as np
import numpy.testing
import requests
import xarray

from fusets.mogpr import mogpr, MOGPRTransformer
from fusets.whittaker import  whittaker



def test_mogpr_train_model():
    ds = xarray.load_dataset(io.BytesIO(requests.get("https://artifactory.vgt.vito.be/testdata-public/fusets/b4_b8_vv_vh/rye.nc",stream=True).content))

    ds['RVI'] = (ds.VH + ds.VH) / (ds.VV + ds.VH)
    ds['NDVI'] = (ds.B08 - ds.B04) / (ds.B04 + ds.B08)
    vars = ds[['NDVI', 'RVI']]


    t = MOGPRTransformer()
    t.fit(vars)
    out = t.transform(vars)

    print(out)
    print(out.NDVI.mean(dim=("x","y")))