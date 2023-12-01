# Phenology

## Description

Computes phenology metrics based on the [Phenolopy](https://github.com/lewistrotter/PhenoloPy) implementation.
Phenolopy (phenology + python) is a python-based library for analysing satellite timeseries data.
Phenolopy has been designed to investigate the seasonality of satellite timeseries data and their relationship with
dynamic vegetation properties such as phenology and temporal growth patterns.
The temporal domain holds important information about short- and long-term changes within vegetation lifecycles.
Phenolopy can be applied to derive numerous phenometrics from satellite imagery.

![image.png](https://github.com/lewistrotter/Phenolopy/raw/main/documentation/images/pheno_explain.png?raw=trueg)

## Usage

### Python

```python
import openeo

## Setup of parameters
year = 2022
spat_ext = {
    "coordinates": [
        [
            [
                5.179169745059369,
                51.24984286550534
            ],
            [
                5.170016107999743,
                51.25052999567865
            ],
            [
                5.171081610725707,
                51.24861004739975
            ],
            [
                5.178604705735125,
                51.246720335821465
            ],
            [
                5.179169745059369,
                51.24984286550534
            ]
        ]
    ],
    "type": "Polygon"
}
temp_ext = [f"{year}-05-01", f"{year}-09-30"]

## Setup connection to openEO
connection = openeo.connect("openeo.vito.be").authenticate_oidc()
service = 'phenology'
namespace = 'u:fusets'

## Setup of the base NDVI data cube upon which to execute the phenology calculation. 
## To improve results, a smoothed data cube can be constructed.
s2 = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                spatial_extent=spat_ext,
                                temporal_extent=temp_ext,
                                bands=["B04", "B08", "SCL"])
s2 = s2.process("mask_scl_dilation", data=s2, scl_band_name="SCL")
s2 = s2.mask_polygon(spat_ext)
base_ndvi = s2.ndvi(red="B04", nir="B08")

phenology = connection.datacube_from_process(service,
                                             namespace=f'https://openeo.vito.be/openeo/1.1/processes/{namespace}/{service}',
                                             data=base_ndvi)

phenology_job = phenology.execute_batch('./phenology.nc', out_format="netcdf", title=f'FuseTS - Phenology',
                                        job_options={
                                            'udf-dependency-archives': [
                                                'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
                                                'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
                                            ]
                                        })
```
