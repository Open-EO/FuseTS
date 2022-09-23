"""
Builds `openEO user defined processes <https://api.openeo.org/#tag/User-Defined-Processes>`_ (UDP's) based on FuseTS functionality.

For each UDP, a json file containing the full process definition can be found in this module. These json files are generated
by code that is also part of this module. It is possible to manually write and maintain the jsons, but this is not advisable given
the complexity of some process graphs.

For the description of the processes, it is recommended to maintain markdown files that are supported by most editors. When
generating the json definitions, the markdown file content needs to be copied (programmatically).

This is a simple example:

.. code-block::
    :caption: Creating an openEO UDP

    import json
    from importlib.resources import files
    import openeo
    from openeo.api.process import Parameter
    from openeo.processes import apply_dimension, run_udf

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


"""