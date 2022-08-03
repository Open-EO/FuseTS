import io


import numpy as np
import numpy.testing
import requests
import xarray

from fusets.mogpr import mogpr
from fusets.whittaker import  whittaker



def test_mogpr_realdata():
    ds = xarray.load_dataset(io.BytesIO(requests.get("https://artifactory.vgt.vito.be/testdata-public/malawi_sentinel2.nc",stream=True).content))
    some_index = (ds.B04 - ds.B02) / (ds.B04 + ds.B02)
    print(some_index)
    smoothed_output = mogpr(some_index[:, [5, 5]])
    print(smoothed_output)


