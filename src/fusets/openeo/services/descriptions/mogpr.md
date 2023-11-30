# Multi output gaussian process regression

## Description

Compute an integrated timeseries based on multiple inputs.
For instance, combine Sentinel-2 NDVI with Sentinel-1 RVI into one integrated NDVI.

## Usage

Usage examples for the MOGPR process.

### Python

This code example highlights the usage of the MOGPR process in an OpenEO batch job.
The result of this batch job will consist of individual GeoTIFF files per date.
Generating multiple GeoTIFF files as output is only possible in a batch job.

```python
import openeo

## Setup of parameters
minx, miny, maxx, maxy = (15.179421073198585, 45.80924633589998, 15.185336903822831, 45.81302555710934)
spat_ext = dict(west=minx, east=maxx, north=maxy, south=miny, crs=4326)
temp_ext = ["2021-01-01", "2021-12-31"]

## Setup connection to openEO
connection = openeo.connect("openeo.vito.be").authenticate_oidc()
service = 'mogpr'
namespace = 'u:fusets'

## Creation of the base NDVI data cube upon which the mogpr is executed
s2 = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                spatial_extent=spat_ext,
                                temporal_extent=temp_ext,
                                bands=["B04", "B08", "SCL"])
s2 = s2.process("mask_scl_dilation", data=s2, scl_band_name="SCL")
base_ndvi = s2.ndvi(red="B04", nir="B08", target_band='NDVI').band('NDVI')

## Creation mogpr  data cube
mogpr = connection.datacube_from_process(service,
                                              namespace=f'https://openeo.vito.be/openeo/1.1/processes/{namespace}/{service}',
                                              data=base_ndvi)
## Calculate the average time series value for the given area of interest
mogpr = mogpr.aggregate_spatial(spat_ext, reducer='mean')

## Execute the service through an openEO batch job
mogpr_job = mogpr.execute_batch('./mogpr.json', out_format="json",
                                          title=f'FuseTS - MOGPR', job_options={
        'udf-dependency-archives': [
            'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
            'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
        ]
    })
```

## Limitations

The spatial extent is limited to a maximum size equal to a Sentinel-2 MGRS tile (100 km x 100 km).

## Configuration & Resource Usage

Run configurations for different ROI/TOI with memory requirements and estimated run durations.

### Synchronous calls

TODO: Replace with actual measurements!!!

| Spatial extent | Run duration |
|----------------|--------------|
| 100 m x 100 m  | 1 minute     |
| 500m x 500 m   | 1 minute     |
| 1 km x 1 km    | 1 minute     |
| 5 km x 5 km    | 2 minutes    |
| 10 km x 10 km  | 3 minutes    |
| 50 km x 50 km  | 9 minutes    |

The maximum duration of a synchronous run is 15 minutes.
For long running computations, you can use batch jobs.

### Batch jobs

TODO: Replace with actual measurements!!!

| Spatial extent  | Temporal extent | Executor memory | Run duration |
|-----------------|-----------------|-----------------|--------------|
| 100 m x 100 m   | 1 month         | default         | 7 minutes    |
| 500 m x 100 m   | 1 month         | default         | 7 minutes    |
| 1 km x 1 km     | 1 month         | default         | 7 minutes    |
| 5 km x 5 km     | 1 month         | default         | 10 minutes   |
| 10 km x 10 km   | 1 month         | default         | 11 minutes   |
| 50 km x 50 km   | 1 month         | 6 GB            | 20 minutes   |
| 100 km x 100 km | 1 month         | 7 GB            | 34 minutes   |
| 100m x 100 m    | 7 months        | default         | 10 minutes   |
| 500 m x 500 m   | 7 months        | default         | 10 minutes   |
| 1 km x 1 km     | 7 months        | default         | 14 minutes   |
| 5 km x 5 km     | 7 months        | default         | 14 minutes   |
| 10 km x 10 km   | 7 months        | default         | 19 minutes   |
| 50 km x 50 km   | 7 months        | 6 GB            | 45 minutes   |
| 100 km x 100 km | 7 months        | 8 GB            | 65 minutes   |

The executor memory defaults to 5 GB. You can increase the executor memory by specifying it as a job option, eg:

```python
job = cube.execute_batch(out_format="GTIFF", job_options={"executor-memory": "7g"})
```
