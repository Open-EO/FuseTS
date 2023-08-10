# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf

from fusets.openeo import load_whittakker_udf
from fusets.openeo.services.helpers import publish_service, read_description


def generate_whittaker_udp():
    description = read_description('whittaker')

    input_cube = Parameter.raster_cube()
    lambda_param = Parameter.number(name='smoothing_lambda', default=10000,
                                    description='Lambda parameter to change the Whittaker smoothing')
    context = {
        'test': 10,
        'smoothing_lambda': {
            'from_parameter': 'smoothing_lambda'
        }
    }
    process = apply_dimension(input_cube, process=lambda x: run_udf(x, udf=load_whittakker_udf(), runtime="Python",
                                                                    context=context), dimension='t')

    return publish_service(id="whittaker", summary="Execute a computationally efficient reconstruction method for "
                                                   "smoothing and gap-filling of time series.",
                           description=description, parameters=[
            input_cube.to_dict(), lambda_param.to_dict()
        ], process_graph=process)


if __name__ == "__main__":
    generate_whittaker_udp()
