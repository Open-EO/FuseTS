# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf

from fusets.openeo import load_phenology_udf
from fusets.openeo.services.helpers import publish_service, read_description


def generate_phenology_udp():
    description = read_description('phenology')

    input_cube = Parameter.raster_cube()
    process = apply_dimension(input_cube, process=lambda x: run_udf(x, udf=load_phenology_udf(), runtime="Python"), dimension='t')

    return publish_service(id="phenology",
                           description=description, parameters=[
            input_cube.to_dict()
        ], process_graph=process.flat_graph())


if __name__ == "__main__":
    generate_phenology_udp()
