# Reads contents with UTF-8 encoding and returns str.
import openeo
from openeo.api.process import Parameter
from openeo.processes import apply_neighborhood, merge_cubes, if_, eq, process

from fusets.openeo import load_mogpr_udf
from fusets.openeo.services.dummies import DummyConnection
from fusets.openeo.services.helpers import read_description, publish_service, GEOJSON_SCHEMA, DATE_SCHEMA

NEIGHBORHOOD_SIZE = 32

S1_COLLECTIONS = ['RVI']
S2_COLLECTIONS = ['NDVI', 'FAPAR', 'LAI', 'FCOVER', 'CCC', 'CWC']


def test_udf():
    connection = openeo.connect("openeo.vito.be").authenticate_oidc()
    service = 'mogpr_s1_s2'
    namespace = 'u:bramjanssen'
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
    mogpr = connection.datacube_from_process(service,
                                             namespace=f'https://openeo.vito.be/openeo/1.1/processes/{namespace}/{service}',
                                             polygon=spat_ext, date=temp_ext)
    mogpr.execute_batch('./result_mogpr_s1_s2.nc', title=f'FuseTS - MOGPR S1 S2 - Local', job_options={
        'udf-dependency-archives': [
            'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv',
            'https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static'
        ],
        'executor-memory': '7g'
    })


#############################################################################################################
# Calculation of the supported data sets
#############################################################################################################

def _load_rvi(connection, polygon, date):
    base_s1 = connection.load_collection('SENTINEL1_GRD',
                                         spatial_extent=polygon,
                                         temporal_extent=date,
                                         bands=["VH", "VV"])

    VH = base_s1.band('VH')
    VV = base_s1.band('VV')
    rvi = (VH + VH) / (VV + VH)
    return rvi.add_dimension(name="bands", label="RVI", type="bands")


def _load_ndvi(connection, polygon, date):
    base_s2 = connection.load_collection('SENTINEL2_L2A',
                                         spatial_extent=polygon,
                                         temporal_extent=date,
                                         bands=["B04", "B08", "SCL"])
    base_s2 = base_s2.process("mask_scl_dilation", data=base_s2, scl_band_name="SCL")
    ndvi = base_s2.ndvi(red="B04", nir="B08", target_band='NDVI')
    ndvi = ndvi.filter_bands(bands=['NDVI'])
    return ndvi.mask_polygon(polygon)


def _load_biopar(polygon, date, biopar):
    biopar = process(
        process_id="BIOPAR",
        namespace="vito",
        date=date,
        polygon=polygon,
        biopar_type=biopar
    )
    return biopar.add_dimension(name="bands", label=biopar, type="bands")


#############################################################################################################
# OpenEO UDP implementation
#############################################################################################################
def load_s1_collection(connection, collection, polygon, date):
    collections = None
    for option in [
        {
            'label': 'rvi',
            'function': _load_rvi(connection=connection, polygon=polygon, date=date)

        },
    ]:
        collections = build_collection_graph(collection=collection,
                                             label=option['label'],
                                             callable=option['function'],
                                             reject=collections)
    return collections


def build_collection_graph(collection, label, callable, reject):
    return if_(eq(collection, label, case_sensitive=False), callable, reject)


def load_s2_collection(connection, collection, polygon, date):
    collections = None
    for option in [
        {
            'label': 'ndvi',
            'function': _load_ndvi(connection=connection, polygon=polygon, date=date)

        },
        {
            'label': 'fapar',
            'function': _load_biopar(polygon=polygon, date=date, biopar='FAPAR')
        },
        {
            'label': 'lai',
            'function': _load_biopar(polygon=polygon, date=date, biopar='LAI')
        },
        {
            'label': 'fcover',
            'function': _load_biopar(polygon=polygon, date=date, biopar='FCOVER')
        },
        {
            'label': 'ccc',
            'function': _load_biopar(polygon=polygon, date=date, biopar='CCC')
        },
        {
            'label': 'cwc',
            'function': _load_biopar(polygon=polygon, date=date, biopar='CWC')
        }
    ]:
        collections = build_collection_graph(collection=collection,
                                             label=option['label'],
                                             callable=option['function'],
                                             reject=collections)
    return collections

def generate_mogpr_s1_s2_udp(connection: openeo.Connection):
    description = read_description('mogpr')

    # Define the different parameters of the UDP
    polygon = Parameter(name='polygon', description='Polygon representing the AOI on which to apply the data fusion',
                        schema=GEOJSON_SCHEMA)
    date = Parameter(name='date', description='Date range for which to apply the data fusion', schema=DATE_SCHEMA)
    s1_collection = Parameter.string('s1_collection', 'S1 data to use', S1_COLLECTIONS[0], S1_COLLECTIONS)
    s2_collection = Parameter.string('s2_collection', 'S2 data to use', S2_COLLECTIONS[0], S2_COLLECTIONS)

    # Build the S1 and S2 input data cubes
    s1_input_cube = load_s1_collection(connection, s1_collection, polygon, date)
    s2_input_cube = load_s2_collection(connection, s2_collection, polygon, date)

    # Merge the inputs to a single datacube
    merged_cube = merge_cubes(s1_input_cube, s2_input_cube)

    # Apply the MOGPR UDF to the multi source datacube
    process = apply_neighborhood(s1_input_cube,
                                 lambda data: data.run_udf(udf=load_mogpr_udf(), runtime='Python', context=dict()),
                                 size=[
                                     {'dimension': 'x', 'value': NEIGHBORHOOD_SIZE, 'unit': 'px'},
                                     {'dimension': 'y', 'value': NEIGHBORHOOD_SIZE, 'unit': 'px'}
                                 ], overlap=[])

    return publish_service(id="mogpr_s1_s2", summary="Integrates timeseries in data cube using multi-output gaussian "
                                                     "process regression with a specific focus on fusing S1 and S2 data.",
                           description=description, parameters=[
            polygon.to_dict(),
            date.to_dict(),
            s1_collection.to_dict(),
            s2_collection.to_dict(),
        ], process_graph=process)


#############################################################################################################
# Main function
#############################################################################################################
if __name__ == "__main__":
    # Using the dummy connection as otherwise Datatype errors are generated when creating the input datacubes
    # where bands are selected.
    generate_mogpr_s1_s2_udp(connection=DummyConnection())
    test_udf()
