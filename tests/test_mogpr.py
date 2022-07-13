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
    smoothed_output = mogpr(some_index)
    out_set = xarray.Dataset({"index":smoothed_output.assign_attrs(grid_mapping="crs"),"crs":ds.crs},attrs=dict(Conventions="CF-1.8"))
    out_set.to_netcdf("malawi_smooth.nc")


