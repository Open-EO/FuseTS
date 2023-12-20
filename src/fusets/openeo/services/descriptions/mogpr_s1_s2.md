# Multi output gaussian process regression

## Description

Compute a temporal dense timeseries based on the fusion of Sentinel-1 (S1) and Sentinel-2 (S2) using MOGPR. 

## Parameters
| Name | Description | Type | Default |
|---|---|---|---------|
| polygon | Polygon representing the AOI on which to apply the data fusion | GeoJSON |         | 
| date | Date range for which to apply the data fusion | Array |         |
| s1_collection | S1 data collection to use for the fusion | Text | RVI     |
| s2_collection | S2 data collection to use for fusing the data | Text | NDVI       | 

### Supported collections

#### Sentinel-1

* RVI
* GRD
* GAMMA0
* COHERENCE (only Europe)

#### Sentinel-2

* NDVI
* FAPAR
* LAI
* FCOVER
* EVI
* CCC
* CWC


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
service = 'mogpr_s1_s2'
namespace = 'u:fusets'

mogpr = connection.datacube_from_process(service,
                                         namespace=f'https://openeo.vito.be/openeo/1.1/processes/{namespace}/{service}',
                                         polygon=spat_ext, date=temp_ext)

mogpr.execute_batch('./result_mogpr_s1_s2.nc', title=f'FuseTS - MOGPR S1 S2', job_options={
    'udf-dependency-archives': [
        'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
        'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
    ],
    'executor-memory': '8g'
})

```

## Limitations

The spatial extent is limited to a maximum size equal to a Sentinel-2 MGRS tile (100 km x 100 km).

## Configuration & Resource Usage
The executor memory defaults to 5 GB. You can increase the executor memory by specifying it as a job option, eg:

```python
job = cube.execute_batch(out_format="GTIFF", job_options={"executor-memory": "8g"})
```
