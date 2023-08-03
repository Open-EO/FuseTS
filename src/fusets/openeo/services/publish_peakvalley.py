# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf

from fusets.openeo.peakvalley_udf import load_peakvalley_udf
from fusets.openeo.services.helpers import publish_service, read_description


def generate_peakvalley_udp():
    description = read_description('peakvalley')

    input_cube = Parameter.raster_cube()
    drop_param = Parameter.number(name='drop_thr',
                                  description='Threshold value for the amplitude of the drop in the input feature',
                                  default=.15)
    rec_param = Parameter.number(name='rec_r',
                                 description='Threshold value for the amplitude of the recovery, relative to the `drop_delta`',
                                 default=1.0)
    slope_param = Parameter.number(name='slope_thr',
                                   description='Threshold value for the slope where the peak should start',
                                   default=-0.007)

    context = {
        'drop_thr': {
            'from_parameter': 'drop_thr'
        },
        'rec_r': {
            'from_parameter': 'rec_r'
        },
        'slope_thr': {
            'from_parameter': 'slope_thr'
        },
    }
    process = apply_dimension(input_cube, process=lambda x: run_udf(x, udf=load_peakvalley_udf(), runtime="Python",
                                                                    context=context), dimension='t')

    return publish_service(id="peakvalley", summary="Detect peaks and valleys in a time series.",
                           description=description, parameters=[
            input_cube.to_dict(), drop_param.to_dict(), rec_param.to_dict(), slope_param.to_dict()
        ], process_graph=process)


if __name__ == "__main__":
    generate_peakvalley_udp()
