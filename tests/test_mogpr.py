import io


import numpy as np
import numpy.testing
import requests
import xarray

from fusets.mogpr import mogpr, MOGPRTransformer
from fusets.whittaker import  whittaker




ds = xarray.load_dataset(io.BytesIO(requests.get("https://artifactory.vgt.vito.be/testdata-public/fusets/b4_b8_vv_vh/rape.nc",stream=True).content))

ds['RVI'] = (ds.VH + ds.VH) / (ds.VV + ds.VH)
ds['NDVI'] = (ds.B08 - ds.B04) / (ds.B04 + ds.B08)
vars = ds[['NDVI', 'RVI']]

def test_mogpr_udf():
    """
    Simple test to help debug udf
    Returns:

    """

    from fusets.openeo.mogpr_udf import apply_datacube
    from openeo.udf import XarrayDataCube
    result = apply_datacube(XarrayDataCube(vars.to_array(dim="bands")),context={})
    print(result)
    assert result.array.dims == ("bands","t","y","x")
    assert result.array.shape == (2, 374, 19, 21)

def test_mogpr_train_model():
    t = MOGPRTransformer()
    t.fit(vars)
    out = t.transform(vars)

    print(out)
    print(out.NDVI.mean(dim=("x","y")))