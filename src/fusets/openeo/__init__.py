from functools import reduce
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

def load_cubes(collections:dict,spatial_extent=None,temporal_extent=None,openeo_connection=None):
    """
    Create an openEO datacube based on a specification.

    @param collections:
    @param spatial_extent:
    @param temporal_extent:
    @param openeo_connection:
    @return:
    """
    if openeo_connection == None:
        openeo_connection = openeo.connect("openeo.cloud").authenticate_oidc()
    cubes = []
    if isinstance(collections,dict):
        def create_cube(collection,args):
            load_collections_kwargs = ["bands", "spatial_extent", "temporal_extent", "properties"]
            load_coll_args = {k: v for k, v in args.items() if k in load_collections_kwargs}
            other_args = {k: v for k, v in args.items() if k not in load_collections_kwargs}

            cube = openeo_connection.load_collection(collection, **load_coll_args)
            for k,v in other_args.items():
                cube = cube.process(k,data=cube, **v)
            return cube

        cubes = [create_cube(k,v) for k,v in collections.items()]
    elif isinstance(collections,str):
        cubes = [openeo_connection.load_collection(collections)]

    first_cube = cubes[0]
    merged = reduce(lambda r,l:r.merge_cubes(l.resample_cube_spatial(first_cube)),cubes)
    if(spatial_extent is not None):
        if(isinstance(spatial_extent,list)):
            merged = merged.filter_bbox(spatial_extent)
        else:
            merged = merged.filter_spatial(spatial_extent)
    if(temporal_extent is not None):
        merged = merged.filter_temporal(temporal_extent)
    return merged




def predict_ndvi(spatial_extent,temporal_extent,openeo_connection=None):
    """
    EXPERIMENTAL may be removed in final version
    Method to compute a predicted, cloud-free, NDVI from Sentinel-2 and Sentinel-1 inputs

    @param spatial_extent:
    @param temporal_extent:
    @param openeo_connection:
    @return:
    """
    if openeo_connection == None:
        openeo_connection = openeo.connect("openeo.cloud").authenticate_oidc()
    cube = openeo_connection.datacube_from_process(process_id="CropSAR_px",namespace="vito",geometry=spatial_extent,startdate=temporal_extent[0],enddate=temporal_extent[1],output_mask=True)


    return cube.add_dimension(name="bands", label="NDVI",type="bands")