# Reads contents with UTF-8 encoding and returns str.
from typing import Union

import openeo
from openeo import DataCube
from openeo.api.process import Parameter
from openeo.processes import ProcessBuilder, apply_neighborhood

from fusets.openeo import load_mogpr_udf
from fusets.openeo.services.helpers import get_context_value, publish_service, read_description

NEIGHBORHOOD_SIZE = 32


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
    temp_ext = ["2023-01-01", "2023-03-31"]

    # Setup NDVI cube
    scl = connection.load_collection(
        "SENTINEL2_L2A", spatial_extent=spat_ext, temporal_extent=temp_ext, bands=["SCL"]
    )
    cloud_mask = scl.process(
        "to_scl_dilation_mask",
        data=scl,
        kernel1_size=17, kernel2_size=77,
        mask1_values=[2, 4, 5, 6, 7],
        mask2_values=[3, 8, 9, 10, 11],
        erosion_kernel_size=3)
    base_s2 = connection.load_collection(
        "SENTINEL2_L2A", spatial_extent=spat_ext, temporal_extent=temp_ext, bands=["B04", "B08"]
    )
    base_s2 = base_s2.mask(cloud_mask)
    base_s2 = base_s2.ndvi(red="B04", nir="B08", target_band="NDVI")
    base_s2 = base_s2.filter_bands(bands=["NDVI"])
    base_s2 = base_s2.mask_polygon(spat_ext)

    # Setup RVI cube
    base_s1 = connection.load_collection(
        "SENTINEL1_GRD", spatial_extent=spat_ext, temporal_extent=temp_ext, bands=["VH", "VV"]
    )

    VH = base_s1.band("VH")
    VV = base_s1.band("VV")
    base_s1 = (VH + VH) / (VV + VH)
    base_s1 = base_s1.add_dimension(name="bands", label="RVI", type="bands")

    # Merge input source
    merged_datacube = base_s2.merge(base_s1)

    # Execute MOGPR
    mogpr = connection.datacube_from_flat_graph(generate_mogpr_cube(merged_datacube, True, False).flat_graph())
    mogpr.execute_batch(
        "./result_mogpr.nc",
        title=f"FuseTS - MOGPR - Local",
        job_options={
            "udf-dependency-archives": [
                "https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_venv.zip#tmp/venv",
                "https://artifactory.vgt.vito.be:443/artifactory/auxdata-public/ai4food/fusets_mogpr_update.zip#tmp/venv_static",
            ],
            "executor-memory": "8g",
        },
    )


def generate_mogpr_cube(
    input_cube: Union[DataCube, ProcessBuilder, Parameter],
    include_uncertainties: Union[bool, Parameter],
    include_raw_inputs: Union[bool, Parameter],
):
    return apply_neighborhood(
        input_cube,
        lambda data: data.run_udf(
            udf=load_mogpr_udf(),
            runtime="Python",
            context={
                "include_uncertainties": get_context_value(include_uncertainties),
                "include_raw_inputs": get_context_value(include_raw_inputs),
            },
        ),
        size=[
            {"dimension": "x", "value": NEIGHBORHOOD_SIZE, "unit": "px"},
            {"dimension": "y", "value": NEIGHBORHOOD_SIZE, "unit": "px"},
        ],
        overlap=[],
    )


def generate_mogpr_udp():
    description = read_description("mogpr")

    input_cube = Parameter.raster_cube()

    include_uncertainties = Parameter.boolean(
        "include_uncertainties", "Flag to include the uncertainties in the output results", False
    )
    include_raw_inputs = Parameter.boolean(
        "include_raw_inputs",
        "Flag to include the raw input signals in the final result",
        False,
    )

    mogpr = generate_mogpr_cube(
        input_cube=input_cube, include_uncertainties=include_uncertainties, include_raw_inputs=include_raw_inputs
    )

    return publish_service(
        id="mogpr",
        summary="Integrates timeseries in data cube using multi-output gaussian " "process regression.",
        description=description,
        parameters=[input_cube.to_dict(), include_uncertainties.to_dict(), include_raw_inputs.to_dict()],
        process_graph=mogpr,
    )


if __name__ == "__main__":
    # execute_udf()
    generate_mogpr_udp()
