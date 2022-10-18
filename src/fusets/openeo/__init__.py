"""
This module contains the openEO variants of FuseTS core algorithms. These algorithms are integrated in openEO by using
user defined functions.

"""

from functools import reduce
from pathlib import Path

import xarray

from openeo.rest.datacube import DataCube
from .whittaker_udf import load_whittakker_udf
from .mogpr_udf import load_mogpr_udf
import openeo

def whittaker(datacube :DataCube, smoothing_lambda :float):
    """
    Whittaker represents a computationally efficient reconstruction method for smoothing and gap-filling of time series.
    The main function takes as input two vectors of the same length: the y time series data (e.g. NDVI) and the
    corresponding temporal vector (date format) x, comprised between the start and end dates of a satellite image
    collection. Missing or null values as well as the cloud-masked values (i.e. NaN), are handled by introducing a
    vector of 0-1 weights w, with wi = 0 for missing observations and wi=1 otherwise. Following, the Whittaker smoother
    is applied to the time series profiles, computing therefore a daily smoothing interpolation.

    Whittaker's fast processing speed was assessed through an initial performance testing by comparing different
    time series fitting methods. Average runtime takes 0.0107 seconds to process a single NDVI temporal profile.

    The smoother performance can be adjusted by tuning the lambda parameter, which penalizes the time series roughness:
    the larger lambda the smoother the time series at the cost of the fit to the data getting worse. We found a
    lambda of 10000 adequate for obtaining more convenient results. A more detailed description of the algorithm can be
    found in the original work of Eilers 2003.

    :param datacube:
    :param smoothing_lambda:
    :return:
    """

    return datacube.apply_dimension(code= load_whittakker_udf(),runtime="Python",context=dict(smoothing_lambda=smoothing_lambda))


def mogpr(datacube :DataCube):
    """

    Args:
        datacube: input datacube containing the bands to integrate

    Returns:

    """
    return datacube.apply_neighborhood(
        lambda data: data.run_udf(udf=load_mogpr_udf(), runtime='Python', context=dict()),
        size=[
            {'dimension': 'x', 'value': 1, 'unit': 'px'},
            {'dimension': 'y', 'value': 1, 'unit': 'px'}
        ]
    )


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

def load_cubes(collections:dict,spatial_extent=None,temporal_extent=None,openeo_connection=None) -> DataCube:
    """
    Create an openEO datacube based on a specification. Multiple collections can be specified and will be merged together into a single cube.
    The resulting cube will be sampled to the layout of the first collection in the list.

    :param collections:
    :param spatial_extent:
    :param temporal_extent:
    :param openeo_connection:
    :return:
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




def cropsar(spatial_extent, temporal_extent, openeo_connection=None):
    """
    EXPERIMENTAL may be removed in final version
    Method to compute a predicted, cloud-free, NDVI from Sentinel-2 and Sentinel-1 inputs. Depends on openEO service.

    :param spatial_extent:
    :param temporal_extent:
    :param openeo_connection:
    :return:
    """
    if openeo_connection == None:
        openeo_connection = openeo.connect("openeo.cloud").authenticate_oidc()
    cube = openeo_connection.datacube_from_process(process_id="CropSAR_px",namespace="vito",geometry=spatial_extent,startdate=temporal_extent[0],enddate=temporal_extent[1],output_mask=True)


    return cube.add_dimension(name="bands", label="NDVI",type="bands")