# Peak Valley

## Overview

Identify the highest and lowest points in the data and gain a better understanding of the underlying patterns and
trends.

## Usage

### Python

```python
import openeo

## Setup of parameters
minx, miny, maxx, maxy = (15.179421073198585, 45.80924633589998, 15.185336903822831, 45.81302555710934)
spat_ext = dict(west=minx, east=maxx, north=maxy, south=miny, crs=4326)
temp_ext = ["2021-01-01", "2021-12-31"]

## Setup connection to openEO
connection = openeo.connect("openeo.vito.be").authenticate_oidc()
service = 'peakvalley'
namespace = 'u:fusets'

## Creation of the base NDVI data cube upon which the peak valley detection is executed
scl = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                spatial_extent=spat_ext,
                                temporal_extent=temp_ext,
                                bands=["SCL"])
cloud_mask = scl.process(
    "to_scl_dilation_mask",
    data=scl,
    kernel1_size=17, kernel2_size=77,
    mask1_values=[2, 4, 5, 6, 7],
    mask2_values=[3, 8, 9, 10, 11],
    erosion_kernel_size=3)
s2 = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                spatial_extent=spat_ext,
                                temporal_extent=temp_ext,
                                bands=["B04", "B08"])
s2 = s2.mask(cloud_mask)
base_ndvi = s2.ndvi(red="B04", nir="B08", target_band='NDVI').band('NDVI')

## Creation peak valley detection data cube
peakvalley = connection.datacube_from_process(service,
                                              namespace=f'https://openeo.vito.be/openeo/1.1/processes/{namespace}/{service}',
                                              data=base_ndvi)

## Execute the service through an openEO batch job
peakvalley_job = peakvalley.execute_batch('./peakvalley.nc', out_format="netcdf",
                                          title=f'FuseTS - Peak Valley Detection', job_options={
        'udf-dependency-archives': [
            'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
            'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
        ]
    })
```
