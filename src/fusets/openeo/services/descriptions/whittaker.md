# Whittaker

## Description

Whittaker represents a computationally efficient reconstruction method for smoothing and gap-filling of time series.
The main function takes as input two vectors of the same length: the y time series data (e.g. NDVI) and the
corresponding temporal vector (date format) x, comprised between the start and end dates of a satellite image
collection. Missing or null values as well as the cloud-masked values (i.e. NaN), are handled by introducing a
vector of 0-1 weights w, with wi = 0 for missing observations and wi=1 otherwise. Following, the Whittaker smoother
is applied to the time series profiles, computing therefore a daily smoothing interpolation.

Whittaker's fast processing speed was assessed through an initial performance testing by comparing different
time series fitting methods. Average runtime takes 0.0107 seconds to process a single NDVI temporal profile.

The smoother performance can be adjusted by tuning the lambda parameter, which penalizes the time series roughness:
the larger lambda the smoother the time series at the cost of the fit to the data getting worse. We found a lambda of
10000 adequate for obtaining more convenient results. A more detailed description of the algorithm can be
found in the original work of Eilers 2003.

## Usage

### Python

```python
import openeo

## Setup of parameters
spat_ext = {
    "type": "Polygon",
    "coordinates": [
        [
            [
                5.170012098271149,
                51.25062964728295
            ],
            [
                5.17085904378298,
                51.24882567194015
            ],
            [
                5.17857421368097,
                51.2468515482926
            ],
            [
                5.178972704726344,
                51.24982704376254
            ],
            [
                5.170012098271149,
                51.25062964728295
            ]
        ]
    ]
}
temp_ext = ["2022-01-01", "2022-12-31"]
smoothing_lambda = 10000

## Setup connection to openEO
connection = openeo.connect("openeo.vito.be").authenticate_oidc()
service = 'whittaker'
namespace = 'u:fusets'

## Create a base NDVI datacube that can be used as input for the service
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
base = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                  spatial_extent=spat_ext,
                                  temporal_extent=temp_ext,
                                  bands=["B04", "B08"])
base_cloudmasked = base.mask(cloud_mask)
base_ndvi = base_cloudmasked.ndvi(red="B04", nir="B08")

## Create a processing graph from the Whittaker process using an active openEO connection
whittaker = connection.datacube_from_process(service,
                                             namespace=f'https://openeo.vito.be/openeo/1.1/processes/{namespace}/{service}',
                                             data=base_ndvi, smoothing_lambda=smoothing_lambda)

## Calculate the average time series value for the given area of interest
whittaker = whittaker.aggregate_spatial(spat_ext, reducer='mean')

# Execute the service as a batch process
whittaker.execute_batch('./whittaker.json', title=f'FuseTS - Whittaker', job_options={
    'udf-dependency-archives': [
        'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
        'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
    ]})
```

