# Reads contents with UTF-8 encoding and returns str.
import openeo
from openeo.api.process import Parameter
from openeo.processes import eq, gt, if_, merge_cubes, process

from fusets.openeo.services.dummies import DummyConnection
from fusets.openeo.services.helpers import DATE_SCHEMA, GEOJSON_SCHEMA, publish_service, read_description
from fusets.openeo.services.publish_mogpr import generate_mogpr_cube
from fusets.openeo.services.publish_whittaker import WHITTAKER_DEFAULT_SMOOTHING, generate_whittaker_cube

NEIGHBORHOOD_SIZE = 32

S1_COLLECTIONS = ["RVI ASC", "RVI DESC", "GRD ASC", "GRD DESC", "GAMMA0", "COHERENCE"]
S2_COLLECTIONS = ["NDVI", "FAPAR", "LAI", "FCOVER", "EVI", "CCC", "CWC"]


def execute_udf():
    connection = openeo.connect("openeo.vito.be").authenticate_oidc()
    spat_ext = {
        "type": "Polygon",
        "coordinates": [
            [
                [5.170012098271149, 51.25062964728295],
                [5.17085904378298, 51.24882567194015],
                [5.17857421368097, 51.2468515482926],
                [5.178972704726344, 51.24982704376254],
                [5.170012098271149, 51.25062964728295],
            ]
        ],
    }
    temp_ext = ["2023-01-01", "2023-02-28"]
    mogpr = connection.datacube_from_flat_graph(
        generate_cube(
            connection=connection,
            s1_collection="RVI DESC",
            s1_smoothing_lambda=WHITTAKER_DEFAULT_SMOOTHING,
            s2_collection="NDVI",
            polygon=spat_ext,
            date=temp_ext,
            include_uncertainties=True,
            include_raw_inputs=True,
        ).flat_graph()
    )
    mogpr.execute_batch(
        "./result_mogpr_s1_s2_outputs_smoothed.nc",
        title=f"FuseTS - MOGPR S1 S2 - Local - Outputs - DESC",
        job_options={
            "udf-dependency-archives": [
                "https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv",
                "https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets.zip#tmp/venv_static",
            ],
            "executor-memory": "8g",
        },
    )


#######################################################################################################################
# Calculation of the supported data sets
#######################################################################################################################


#######################################################################################################################
#   S1 collection implementation
#######################################################################################################################
def _load_s1_grd_bands(connection, polygon, date, bands, orbit_direction):
    """
    Create an S1 datacube containing a selected set of bands from the SENTINEL1_GRD data collection.
    :param connection: openEO connection
    :param polygon: Area of interest
    :param date: Time of interest
    :param bands: Bands to load
    :param orbit_direction: Orbit direction to use
    :return:
    """
    s1_grd = connection.load_collection(
        "SENTINEL1_GRD",
        spatial_extent=polygon,
        temporal_extent=date,
        bands=bands,
        properties={
            "sat:orbit_state": lambda orbit_state: orbit_state == orbit_direction,
            "resolution": lambda x: eq(x, "HIGH"),
            "sar:instrument_mode": lambda x: eq(x, "IW"),
        },
    )
    return s1_grd.mask_polygon(polygon)


def _load_rvi(connection, polygon, date, orbit_direction):
    """
    Create an RVI datacube based on the S1 VV and VH bands.
    :param connection: openEO connection
    :param polygon: Area of interest
    :param date: Time of interest
    :param orbit_direction: Orbit direction to use
    :return:
    """
    base_s1 = _load_s1_grd_bands(connection, polygon, date, ["VV", "VH"], orbit_direction)

    VH = base_s1.band("VH")
    VV = base_s1.band("VV")
    rvi = (VH + VH) / (VV + VH)
    return rvi.add_dimension(name="bands", label="RVI", type="bands")


def _load_gamma0(connection, polygon, date):
    """
    Create a GAMMA0 datacube using the SENTINEL1_GAMMA0_SENTINELHUB collection in combination with the
    sar_backscatter process
    :param connection: openEO connection
    :param polygon: Area of interest
    :param date: Time of interest
    :return:
    """
    s1_gamma0 = connection.load_collection(
        "SENTINEL1_GAMMA0_SENTINELHUB",
        spatial_extent=polygon,
        temporal_extent=date,
        bands=["VH", "VV"],
        properties={"polarization": lambda od: eq(od, "DV")},
    ).sar_backscatter()
    return s1_gamma0.mask_polygon(polygon)


def _load_coherence(connection, polygon, date):
    """
    Create a S1 SLC Coherence datacube based on the existing TERRASCOPE_S1_SLC_COHERENCE data collection.
    :param connection: openEO connection
    :param polygon: Area of interest
    :param date: Time of interest
    :return:
    """
    s1_coh = connection.load_collection(
        "TERRASCOPE_S1_SLC_COHERENCE_V1",
        spatial_extent=polygon,
        temporal_extent=date,
    )
    return s1_coh.mask_polygon(polygon)


#######################################################################################################################
#   S2 collection implementation
#######################################################################################################################


def _load_ndvi(connection, polygon, date):
    """
    Create an NDVI datacube based on the SENTINEL2_L2A data collection.
    :param connection: openEO connection
    :param polygon: Area of interest
    :param date:
    :return:
    """
    scl = connection.load_collection(
        "SENTINEL2_L2A", spatial_extent=polygon, temporal_extent=date, bands=["SCL"]
    )
    cloud_mask = scl.process(
        "to_scl_dilation_mask",
        data=scl,
        kernel1_size=17, kernel2_size=77,
        mask1_values=[2, 4, 5, 6, 7],
        mask2_values=[3, 8, 9, 10, 11],
        erosion_kernel_size=3)
    base_s2 = connection.load_collection(
        "SENTINEL2_L2A", spatial_extent=polygon, temporal_extent=date, bands=["B04", "B08"]
    )
    base_s2 = base_s2.mask(cloud_mask)
    ndvi = base_s2.ndvi(red="B04", nir="B08", target_band="NDVI")
    ndvi = ndvi.filter_bands(bands=["NDVI"])
    return ndvi.mask_polygon(polygon)


def _load_biopar(polygon, date, biopar):
    """
    Create a BIOPAR datacube. This is done by using the existing BIOPAR service:
    https://portal.terrascope.be/catalogue/app-details/21

    :param polygon: Area of interest
    :param date: Time of interest
    :param biopar: BIOPAR type (see documentation of service on portal)
    :return:
    """
    base_biopar = process(process_id="BIOPAR", namespace="vito", date=date, polygon=polygon, biopar_type=biopar)
    return base_biopar.mask_polygon(polygon)


def _load_evi(connection, polygon, date):
    """
    Create an EVI datacube. More information is available at https://en.wikipedia.org/wiki/Enhanced_vegetation_index
    :param connection: openEO connection
    :param polygon: Area of interest
    :param date: Time of interest
    :return:
    """
    scl = connection.load_collection(
        collection_id="SENTINEL2_L2A",
        spatial_extent=polygon,
        temporal_extent=date,
        bands=["SCL"],
    )
    cloud_mask = scl.process(
        "to_scl_dilation_mask",
        data=scl,
        kernel1_size=17, kernel2_size=77,
        mask1_values=[2, 4, 5, 6, 7],
        mask2_values=[3, 8, 9, 10, 11],
        erosion_kernel_size=3)
    base_s2 = connection.load_collection(
        collection_id="SENTINEL2_L2A",
        spatial_extent=polygon,
        temporal_extent=date,
        bands=["B02", "B04", "B08"],
    )
    base_s2 = base_s2.mask(cloud_mask)

    B02 = base_s2.band("B04")
    B04 = base_s2.band("B04")
    B08 = base_s2.band("B08")

    evi = (2.5 * (B08 - B04)) / ((B08 + 6.0 * B04 - 7.5 * B02) + 1.0)
    evi = evi.mask_polygon(mask=polygon)
    return evi.add_dimension(name="bands", label="EVI", type="bands")


#######################################################################################################################
# OpenEO UDP implementation
#######################################################################################################################
def _build_collection_graph(collection, label, callable, reject):
    """
    Helper function that will construct an if-else structure using the if_ openEO process. If the value of the
    collection parameter matches with the given label, the callable is executed. If not the reject function is
    executed.

    :param collection: openEO collection parameter
    :param label: String representing the text with which the collection should match
    :param callable: Function that is executed when the collection matches the label
    :param reject: Function that is executed when the collection does not match the label
    :return:
    """
    return if_(eq(collection, label, case_sensitive=False), callable, reject)


def load_s1_collection(connection, collection, smoothing_lambda, polygon, date):
    """
    Create a S1 input data cube based on the collection selected by the user. This achieved by building an
    if-else structure through the different openEO processes, making sure that the correct datacube is selected
    when executing the UDP.

    :param connection: openEO connection
    :param collection: One of the supported collection (S1_COLLECTIONS)
    :param smoothing_lambda: Number that indicate the lambda to use in the Whittaker smoothing process
    :param polygon: Area of interest
    :param date:  Time of interest
    :return:
    """
    collections = None
    for option in [
        {
            "label": "grd desc",
            "function": _load_s1_grd_bands(
                connection=connection, polygon=polygon, date=date, bands=["VV", "VH"], orbit_direction="DESCENDING"
            ),
        },
        {
            "label": "grd asc",
            "function": _load_s1_grd_bands(
                connection=connection, polygon=polygon, date=date, bands=["VV", "VH"], orbit_direction="ASCENDING"
            ),
        },
        {
            "label": "rvi desc",
            "function": _load_rvi(connection=connection, polygon=polygon, date=date, orbit_direction="DESCENDING"),
        },
        {
            "label": "rvi asc",
            "function": _load_rvi(connection=connection, polygon=polygon, date=date, orbit_direction="ASCENDING"),
        },
        {"label": "gamma0", "function": _load_gamma0(connection=connection, polygon=polygon, date=date)},
        {"label": "coherence", "function": _load_coherence(connection=connection, polygon=polygon, date=date)},
    ]:
        collections = _build_collection_graph(
            collection=collection, label=option["label"], callable=option["function"], reject=collections
        )

    smoothed = if_(
        gt(0, smoothing_lambda),
        generate_whittaker_cube(input_cube=collections, smoothing_lambda=smoothing_lambda),
        collections,
    )
    return smoothed


def load_s2_collection(connection, collection, polygon, date):
    """
    Create a S2 input data cube based on the collection selected by the user. This achieved by building an
    if-else structure through the different openEO processes, making sure that the correct datacube is selected
    when executing the UDP.

    :param connection: openEO connection
    :param collection: One of the supported collection (S2_COLLECTIONS)
    :param polygon: Area of interest
    :param date:  Time of interest
    :return:
    """
    collections = None
    for option in [
        {"label": "ndvi", "function": _load_ndvi(connection=connection, polygon=polygon, date=date)},
        {"label": "fapar", "function": _load_biopar(polygon=polygon, date=date, biopar="FAPAR")},
        {"label": "lai", "function": _load_biopar(polygon=polygon, date=date, biopar="LAI")},
        {"label": "fcover", "function": _load_biopar(polygon=polygon, date=date, biopar="FCOVER")},
        {"label": "evi", "function": _load_evi(connection=connection, polygon=polygon, date=date)},
        {"label": "ccc", "function": _load_biopar(polygon=polygon, date=date, biopar="CCC")},
        {"label": "cwc", "function": _load_biopar(polygon=polygon, date=date, biopar="CWC")},
    ]:
        collections = _build_collection_graph(
            collection=collection, label=option["label"], callable=option["function"], reject=collections
        )
    return collections


def generate_cube(
    connection,
    s1_collection,
    s1_smoothing_lambda,
    s2_collection,
    polygon,
    date,
    include_uncertainties,
    include_raw_inputs,
):
    # Build the S1 and S2 input data cubes
    s1_input_cube = load_s1_collection(connection, s1_collection, s1_smoothing_lambda, polygon, date)
    s2_input_cube = load_s2_collection(connection, s2_collection, polygon, date)

    # Merge the inputs to a single datacube
    input_cube = merge_cubes(s1_input_cube, s2_input_cube)

    # Apply the MOGPR UDF to the multi source datacube
    return generate_mogpr_cube(input_cube, include_uncertainties, include_raw_inputs)


def generate_mogpr_s1_s2_udp(connection):
    """
    Build the MOGPR S1 S2 UPD and publish the result.

    :param connection: openEO connection
    :return:
    """
    description = read_description("mogpr_s1_s2")

    # Define the different parameters of the UDP
    polygon = Parameter(
        name="polygon",
        description="Polygon representing the AOI on which to apply the data fusion",
        schema=GEOJSON_SCHEMA,
    )
    date = Parameter(name="date", description="Date range for which to apply the data fusion", schema=DATE_SCHEMA)
    s1_collection = Parameter.string(
        "s1_collection", "S1 data collection to use for fusing the data", S1_COLLECTIONS[0], S1_COLLECTIONS
    )
    s2_collection = Parameter.string(
        "s2_collection", "S2 data collection to use for fusing the data", S2_COLLECTIONS[0], S2_COLLECTIONS
    )
    s1_smoothing_lambda = Parameter.number(
        "s1_smoothing_lambda",
        "Smoothing factor (Whittaker) to smooth the S1 data (0 = no smoothing)",
        WHITTAKER_DEFAULT_SMOOTHING,
    )

    include_uncertainties = Parameter.boolean(
        "include_uncertainties",
        "Flag to include the uncertainties, expressed as the standard deviation in the final result",
        False,
    )

    include_raw_inputs = Parameter.boolean(
        "include_raw_inputs",
        "Flag to include the raw input signals in the final result",
        False,
    )

    process = generate_cube(
        connection=connection,
        s1_collection=s1_collection,
        s2_collection=s2_collection,
        polygon=polygon,
        date=date,
        s1_smoothing_lambda=s1_smoothing_lambda,
        include_uncertainties=include_uncertainties,
        include_raw_inputs=include_raw_inputs,
    )
    return publish_service(
        id="mogpr_s1_s2",
        summary="Integrates timeseries in data cube using multi-output gaussian "
        "process regression with a specific focus on fusing S1 and S2 data.",
        description=description,
        parameters=[
            polygon.to_dict(),
            date.to_dict(),
            s1_collection.to_dict(),
            s1_smoothing_lambda.to_dict(),
            s2_collection.to_dict(),
            include_uncertainties.to_dict(),
            include_raw_inputs.to_dict(),
        ],
        process_graph=process,
    )


#######################################################################################################################
# Main function
#######################################################################################################################
if __name__ == "__main__":
    # Using the dummy connection as otherwise Datatype errors are generated when creating the input datacubes
    # where bands are selected.
    generate_mogpr_s1_s2_udp(connection=DummyConnection())
    # execute_udf()
