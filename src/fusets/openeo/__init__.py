from pathlib import Path

import xarray

from openeo.rest.datacube import DataCube
from .whittaker_udf import load_whittakker_udf
import openeo

def whittaker(datacube :DataCube, smoothing_lambda :float):
    """

    @param datacube:
    @param smoothing_lambda:
    @return:
    """

    return datacube.apply_dimension(code= load_whittakker_udf(),runtime="Python",context=dict(smoothing_lambda=smoothing_lambda))

def load_xarray(collection_id,spatial_extent,temporal_extent,properties=None,openeo_connection=None):
    if openeo_connection == None:
        openeo_connection = openeo.connect("openeo.cloud").authenticate_oidc()
    print(spatial_extent)
    data = openeo_connection.load_collection(collection_id,temporal_extent=temporal_extent,bands=["B02","B03","B04","SCL"]).filter_bbox(spatial_extent)
    data = data.process("mask_scl_dilation", data=data, scl_band_name="SCL")
    job = data.execute_batch(out_format="netCDF")
    results = job.get_results()
    base_path = Path(job.job_id)
    base_path.mkdir(exist_ok=True)
    results.download_files(target=base_path)
    netcdfs = [a for a in results.get_assets() if "netcdf" in a.metadata.get("type","").lower()]
    if(len(netcdfs)>0):
        path = base_path / netcdfs[0].name
        return xarray.load_dataset(path)
