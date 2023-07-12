# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf

from fusets.openeo.phenology_udf import load_phenology_udf
from fusets.openeo.services.helpers import publish_service, read_description


def generate_phenology_udp():
    description = read_description('phenology')

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

    input_cube = Parameter.raster_cube()
    size = 32
    process = apply_dimension(data=input_cube, process=lambda x: run_udf(x, udf=load_phenology_udf(), runtime="Python"),
                              dimension='t')

    # process = add_dimension(data=process, name='phenology', label=phenology_bands)

    return publish_service(id="phenology", summary='',
                           description=description, parameters=[
            input_cube.to_dict()
        ], process_graph=process.flat_graph())


if __name__ == "__main__":
    generate_phenology_udp()
