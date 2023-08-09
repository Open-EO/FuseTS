# Reads contents with UTF-8 encoding and returns str.
import openeo
from openeo.api.process import Parameter
from openeo.processes import apply_neighborhood
from openeo.udf import execute_local_udf

from fusets.openeo import load_mogpr_udf
from fusets.openeo.services.helpers import read_description, publish_service

NEIGHBORHOOD_SIZE = 32


def test_udf():
    connection = openeo.connect("openeo-dev.vito.be").authenticate_oidc()
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
    temp_ext = ["2022-05-01", "2022-07-30"]
    base = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                      spatial_extent=spat_ext,
                                      temporal_extent=temp_ext,
                                      bands=["B04", "B08", "SCL"])
    base_cloudmasked = base.process("mask_scl_dilation", data=base, scl_band_name="SCL")
    base_ndvi = base_cloudmasked.ndvi(red="B04", nir="B08")

    mogpr = base_ndvi.apply_neighborhood(
        lambda data: data.run_udf(udf=load_mogpr_udf(), runtime='Python', context=dict()),
        size=[
            {'dimension': 'x', 'value': NEIGHBORHOOD_SIZE, 'unit': 'px'},
            {'dimension': 'y', 'value': NEIGHBORHOOD_SIZE, 'unit': 'px'}
        ], overlap=[])
    mogpr.execute_batch('./result_mogpr.nc', title=f'FuseTS - MOGPR - Local', job_options={
        'udf-dependency-archives': [
            'https://artifactory.vgt.vito.be:443/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
            'https://artifactory.vgt.vito.be:443/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
        ],
        'executor-memory': '7g'
    })


def test_udf_locally():
    """
    Test the UDF locally using NetCDF files.
    :return:
    """
    mogpr_udf = load_mogpr_udf()
    result = execute_local_udf(mogpr_udf, './s2_field_ndvi.nc', fmt='netcdf')
    result.get_datacube_list()[0].save_to_file('./result_mogpr_local.nc')
    print(result)


def generate_mogpr_udp():
    description = read_description('mogpr')

    input_cube = Parameter.raster_cube()

    process = apply_neighborhood(input_cube,
                                 lambda data: data.run_udf(udf=load_mogpr_udf(), runtime='Python', context=dict()),
                                 size=[
                                     {'dimension': 'x', 'value': NEIGHBORHOOD_SIZE, 'unit': 'px'},
                                     {'dimension': 'y', 'value': NEIGHBORHOOD_SIZE, 'unit': 'px'}
                                 ], overlap=[])

    return publish_service(id="mogpr", summary="Integrates timeseries in data cube using multi-output gaussian "
                                               "process regression.", description=description, parameters=[
        input_cube.to_dict()
    ], process_graph=process)


if __name__ == "__main__":
    # test_udf_locally()
    # test_udf()
    generate_mogpr_udp()
