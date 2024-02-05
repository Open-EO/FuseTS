# Reads contents with UTF-8 encoding and returns str.
from typing import Union

from openeo import DataCube
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf, ProcessBuilder

from fusets.openeo import load_whittakker_udf
from fusets.openeo.services.helpers import publish_service, read_description, get_context_value

WHITTAKER_DEFAULT_SMOOTHING = 10000


def generate_whittaker_cube(
        input_cube: Union[DataCube, ProcessBuilder, Parameter],
        smoothing_lambda: Union[float, Parameter]
):
    context = {"smoothing_lambda": get_context_value(smoothing_lambda)}
    return apply_dimension(
        input_cube,
        process=lambda x: run_udf(x, udf=load_whittakker_udf(), runtime="Python", context=context),
        dimension="t",
    )


def generate_whittaker_udp():
    description = read_description("whittaker")

    input_cube = Parameter.raster_cube()
    lambda_param = Parameter.number(
        name="smoothing_lambda", default=WHITTAKER_DEFAULT_SMOOTHING,
        description="Lambda parameter to change the Whittaker smoothing"
    )

    process = generate_whittaker_cube(
        input_cube=input_cube,
        smoothing_lambda=lambda_param
    )

    return publish_service(
        id="whittaker",
        summary="Execute a computationally efficient reconstruction method for "
                "smoothing and gap-filling of time series.",
        description=description,
        parameters=[input_cube.to_dict(), lambda_param.to_dict()],
        process_graph=process,
    )


if __name__ == "__main__":
    generate_whittaker_udp()
