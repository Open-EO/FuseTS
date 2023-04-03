# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf

from src.fusets.openeo.services.helpers import read_description, publish_service


def generate_mogpr_udp():
    description = read_description('mogpr')

    input_cube = Parameter.raster_cube()
    process = apply_dimension(input_cube, process=lambda x: run_udf(x, udf="#mogpr", runtime="Python"), dimension="t")

    return publish_service(id="mogpr", summary="Integrates timeseries in data cube using multi-output gaussian "
                                               "process regression.", description=description, parameters=[
        input_cube.to_dict()
    ], process_graph=process.flat_graph())


if __name__ == "__main__":
    generate_mogpr_udp()
