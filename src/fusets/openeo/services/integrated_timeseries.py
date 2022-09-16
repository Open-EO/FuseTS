import json
from importlib.resources import files
# Reads contents with UTF-8 encoding and returns str.
from openeo.api.process import Parameter
from openeo.processes import apply_dimension, run_udf


def generate_mogpr_udp():
    description = files('fusets.openeo.services').joinpath('mogpr.md').read_text(encoding='utf-8')

    input_cube = Parameter.raster_cube()

    process = apply_dimension(input_cube,process=lambda x:run_udf(x, udf="#mogpr", runtime="Python"),dimension="t")

    spec = {
        "id": "mogpr",
        "summary": "Integrates timeseries in data cube using multi-output gaussian process regression.",
        "description": description,
        "parameters": [
            input_cube.to_dict()
        ],
        "process_graph": process.flat_graph()
    }

    # write the UDP to a file
    with files('fusets.openeo.services').joinpath('mogpr.json').open(mode='w') as f:
        json.dump(spec, f, indent=4)

if __name__ == "__main__":
    generate_mogpr_udp()