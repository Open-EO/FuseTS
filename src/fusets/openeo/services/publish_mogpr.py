# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_neighborhood

from fusets.openeo import load_mogpr_udf
from fusets.openeo.services.helpers import read_description, publish_service


def generate_mogpr_udp():
    description = read_description('mogpr')

    input_cube = Parameter.raster_cube()
    size = 32
    process = apply_neighborhood(input_cube,
                                 lambda data: data.run_udf(udf=load_mogpr_udf(), runtime='Python', context=dict()),
                                 size=[
                                     {'dimension': 'x', 'value': size, 'unit': 'px'},
                                     {'dimension': 'y', 'value': size, 'unit': 'px'}
                                 ], overlap=[])

    return publish_service(id="mogpr", summary="Integrates timeseries in data cube using multi-output gaussian "
                                               "process regression.", description=description, parameters=[
        input_cube.to_dict()
    ], process_graph=process)


if __name__ == "__main__":
    generate_mogpr_udp()
