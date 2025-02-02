import logging
from pathlib import Path

import geojson
import geopandas as gpd
import numpy as np
import openeo
import pandas as pd
import pytest
from openeo.extra.job_management import MultiBackendJobManager
from shapely.wkt import loads

from tests.helpers import read_test_json

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

job_options = {
    "executor-memory": "8g",
    "udf-dependency-archives": [
        "https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv",
        "https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static",
    ],
}


def start_job(data, context: dict, **kwargs) -> openeo.BatchJob:
    """
    Callback function for the openEO MultiBackendJobManager to start a new job.
    :param data: Dictionary containing the general information for launching the job
    :param context: Dictionary with additional job information
    :param kwargs:
    :return: OpenEO Batch Job
    """
    row = data["row"]
    connection = data["connection"]
    aoi = geojson.Feature(geometry=row["geometry"])

    if "params" in context and "skipData" in context["params"] and context["params"]["skipData"]:
        service_dc = connection.datacube_from_process(
            polygon=aoi,
            **context["jobinfo"],
        )
    else:
        scl = connection.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=aoi,
            temporal_extent=context["params"]["temp-ext"],
            bands=["SCL"],
        )
        cloud_mask = scl.process(
            "to_scl_dilation_mask",
            data=scl,
            kernel1_size=17, kernel2_size=77,
            mask1_values=[2, 4, 5, 6, 7],
            mask2_values=[3, 8, 9, 10, 11],
            erosion_kernel_size=3)
        base = connection.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=aoi,
            temporal_extent=context["params"]["temp-ext"],
            bands=["B04", "B08"],
        )
        base_cloudmasked = base.mask(cloud_mask)
        base_ndvi = base_cloudmasked.ndvi(red="B04", nir="B08")
        service_dc = connection.datacube_from_process(data=base_ndvi, **context["jobinfo"])

    return service_dc.create_job(
        title=f'FuseTS - Benchmark - {context["jobinfo"]["process_id"]} - {row["jobname"]}',
        job_options=job_options,
        format="netcdf",
    )


def get_job_cost(connection, jobId) -> float:
    """
    Retrieve the total cost of a job through openEO
    :param connection: OpenEO connection used to retrieve the job costs
    :param jobId: ID of the job for which to retrieve the cost
    :return: Floating number representing the total cost of the job in credits
    """
    job = connection.job(jobId).describe_job()
    return job["costs"] if "costs" in job else np.nan


def read_job_info(connection, path) -> pd.DataFrame:
    """
    Translate the job information CSV from openEO into a Dataframe for comparison with metrics. Additional
    information is added to the dataframe, such as the total cost per hectare.
    :param connection: OpenEO connection used to retrieve the job costs
    :param path: Path of the CSV file generated by openEO.
    :return: Dataframe containing the job information extended with additional information
    """
    job_data = pd.read_csv(path)
    geometry = [loads(poly) for poly in job_data["geometry"]]
    job_data = gpd.GeoDataFrame(job_data, geometry=geometry, crs=4326)
    job_data = job_data.to_crs(epsg=3857)
    for col in ["cpu", "memory", "duration", "sentinelhub"]:
        job_data[col] = job_data[col].str.extract("(\d+)").astype(float)

    job_data["area_hectares"] = job_data["geometry"].apply(lambda x: x.area / 10000)
    job_data["cost"] = job_data["id"].apply(lambda x: get_job_cost(connection, x))
    job_data["cost_ha"] = job_data["cost"] / job_data["area_hectares"]
    job_data["cpu_ha"] = job_data["cpu"] / job_data["area_hectares"]
    job_data["memory_ha"] = job_data["memory"] / job_data["area_hectares"]
    job_data["duration_ha"] = job_data["duration"] / job_data["area_hectares"]
    return job_data


def get_service_metrics(service) -> dict:
    """
    Read the base metrics for a specific service
    :param service: Name of the service for which to read the base metrics
    :return: Dictionary containing the base metrics for cost, cpu, duration, memory and sentinelhub
    """
    metrics = read_test_json("benchmarks/performance.json")
    return metrics[service]


def check_performance(service, jobs):
    """
    Read the performance metrics of a service and compare them to the results from the performance benchmark
    :param service: Name of the service for which to read the base metrics
    :param jobs:  Dataframe containing the job information of the performance test
    :return:
    """
    metrics = get_service_metrics(service)

    # Check performance benchmarks
    assert jobs["cpu_ha"].mean() == pytest.approx(metrics["cpu"], abs=metrics["cpu"] * 0.25)
    assert jobs["memory_ha"].mean() == pytest.approx(metrics["memory"], abs=metrics["memory"] * 0.25)
    assert jobs["duration_ha"].mean() == pytest.approx(metrics["duration"], abs=metrics["duration"] * 0.25)
    assert jobs["sentinelhub"].mean() == pytest.approx(metrics["sentinelhub"], abs=metrics["sentinelhub"] * 0.25)
    assert jobs["cost_ha"].mean() == pytest.approx(metrics["cost_ha"], abs=metrics["cost_ha"] * 0.25)


@pytest.mark.parametrize(
    "context",
    [
        (
            {
                "params": {
                    "temp-ext": ["2023-01-01", "2023-12-31"],
                },
                "jobinfo": {
                    "process_id": "whittaker",
                    "namespace": "https://openeo.vito.be/openeo/1.1/processes/u:fusets/whittaker",
                    "smoothing_lambda": 10000,
                },
            }
        ),
        (
            {
                "params": {
                    "temp-ext": ["2023-01-01", "2023-12-31"],
                },
                "jobinfo": {
                    "process_id": "mogpr",
                    "namespace": "https://openeo.vito.be/openeo/1.1/processes/u:fusets/mogpr",
                },
            }
        ),
        (
            {
                "params": {
                    "temp-ext": ["2023-01-01", "2023-12-31"],
                },
                "jobinfo": {
                    "process_id": "peakvalley",
                    "namespace": "https://openeo.vito.be/openeo/1.1/processes/u:fusets/peakvalley",
                },
            }
        ),
        (
            {
                "params": {
                    "temp-ext": ["2023-01-01", "2023-12-31"],
                },
                "jobinfo": {
                    "process_id": "phenology",
                    "namespace": "https://openeo.vito.be/openeo/1.1/processes/u:fusets/phenology",
                },
            }
        ),
        (
            {
                "params": {
                    "skipData": True,
                },
                "jobinfo": {
                    "process_id": "mogpr_s1_s2",
                    "namespace": "https://openeo.vito.be/openeo/1.1/processes/u:fusets/mogpr_s1_s2",
                    "date": ["2023-01-01", "2023-12-31"],
                },
            }
        ),
    ],
)
def test_benchmark_fusets_service(benchmark_features, context):
    """
    Execute a benchmark of the FuseTS services and compare them against base metrics.
    """
    output_file = Path(f"benchmark_fusets_{context['jobinfo']['process_id']}.csv")
    connection = openeo.connect("openeo.vito.be").authenticate_oidc()

    # Execute the jobs through the job manager
    manager = MultiBackendJobManager()
    manager.add_backend("vito", connection=connection, parallel_jobs=3)
    manager.run_jobs(
        df=benchmark_features,
        start_job=lambda **x: start_job(x, context=context),
        output_file=Path(f"benchmark_fusets_{context['jobinfo']['process_id']}.csv"),
    )

    # Evaluate the performance metrics
    job_data = read_job_info(connection, output_file)
    check_performance(context["jobinfo"]["process_id"], job_data)
