# Reads contents with UTF-8 encoding and returns str.
import openeo
import xarray
from openeo.api.process import Parameter
from openeo.metadata import CollectionMetadata, Band
from openeo.processes import apply_dimension, run_udf, reduce_dimension, apply_neighborhood, ProcessBuilder
from openeo.udf import execute_local_udf, XarrayDataCube

from fusets.analytics import phenology
from fusets.openeo.phenology_udf import load_phenology_udf, apply_datacube
from fusets.openeo.services.helpers import publish_service, read_description

phenology_bands = [
    "pos_values",
    "pos_times",
    "mos_values",
    "vos_values",
    "vos_times",
    "bse_values",
    "aos_values",
    "sos_values",
    "sos_times",
    "eos_values",
    "eos_times",
    "los_values",
    "roi_values",
    "rod_values",
    "lios_values",
    "sios_values",
    "liot_values",
    "siot_values"
]

def test_udf():
    connection = openeo.connect("openeo.vito.be").authenticate_oidc()
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
    temp_ext = ["2022-01-01","2022-12-31"]
    smoothing_lambda = 10000
    base = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                      spatial_extent=spat_ext,
                                      temporal_extent=temp_ext,
                                      bands=["B04","B08","SCL"])
    base_cloudmasked = base.process("mask_scl_dilation", data=base, scl_band_name="SCL")
    base_ndvi = base_cloudmasked.ndvi(red="B04", nir="B08")
    phenology = base_ndvi.apply_dimension(process=lambda x: run_udf(x, udf=load_phenology_udf(), runtime="Python"),
                                           dimension='t', target_dimension='phenology')
    # metadata = CollectionMetadata({})
    # metadata = metadata.add_dimension('bands', '', 'bands')
    # #    .rename_labels(dimension='var', target=phenology_bands)
    # phenology.metadata = metadata

    # phenology = phenology.rename_labels(dimension='bands', target=phenology_bands)

    # size = 125
    # phenology = base_ndvi.apply_neighborhood(process=lambda x: run_udf(x, udf=load_phenology_udf(), runtime="Python"),
    #                                           size=[
    #                                          {'dimension': 'x', 'value': size, 'unit': 'px'},
    #                                          {'dimension': 'y', 'value': size, 'unit': 'px'}
    #                                      ], overlap=[])
    phenology_job = phenology.execute_batch(out_format="netcdf", title=f'FuseTS - Phenology', job_options={
        'udf-dependency-archives': [
            'https://artifactory.vgt.vito.be:443/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
            'https://artifactory.vgt.vito.be:443/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
        ]
    })




    output_file = './phenology.nc'
    phenology_job.get_results().download_file(output_file)
    phenology_result_nc = xarray.load_dataset(output_file)
    print(phenology_result_nc)


def test_udf_locally():
    # data = xarray.load_dataset('./s2_field.nc')
    # data.NDVI.to_netcdf('./s2_field_ndvi.nc')

    phenology_udf = load_phenology_udf()
    result = execute_local_udf(phenology_udf, './s2_field_ndvi.nc', fmt='netcdf')
    result.get_datacube_list()[0].save_to_file('./result.nc')
    print(result)

def test_locally():
    data = xarray.load_dataset('./s2_field_ndvi.nc')
    result = apply_datacube(XarrayDataCube(data.to_array().rename({ 'variable': 'bands' })), context=None)
    result.array.to_netcdf('./result_local.nc')

def generate_phenology_process(cube):
    process = reduce_dimension(data=cube, reducer=lambda x: run_udf(x, udf=load_phenology_udf(), runtime="Python"),
                              dimension='t')

    # size = 125
    # process = apply_neighborhood(data=input_cube, process=lambda x: run_udf(x, udf=load_phenology_udf(), runtime="Python"),
    #                              size=[
    #                                  {'dimension': 'x', 'value': size, 'unit': 'px'},
    #                                  {'dimension': 'y', 'value': size, 'unit': 'px'}
    #                              ], overlap=[])
    return process


def generate_phenology_udp():
    description = read_description('phenology')



    input_cube = Parameter.raster_cube()
    process = generate_phenology_process(input_cube)

    return publish_service(id="phenology", summary='',
                           description=description, parameters=[
            input_cube.to_dict()
        ], process_graph=process.flat_graph())


if __name__ == "__main__":
    # generate_phenology_udp()
    test_udf()
    # test_udf_locally()
    # test_locally()




