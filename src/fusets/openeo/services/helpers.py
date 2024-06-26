import json
import os
from typing import Any, Union

import openeo
from openeo.api.process import Parameter

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files
from openeo.processes import ProcessBuilder
from openeo.rest.udp import build_process_dict


def get_openeo_connection():
    return openeo.connect("openeo.vito.be").authenticate_basic(os.getenv("OPENEO_USER"), os.getenv("OPENEO_PASSWORD"))


def read_description(service: str) -> str:
    return files("fusets.openeo.services").joinpath(f"descriptions/{service}.md").read_text(encoding="utf-8")


def write_service_info(id: str, summary: str, description: str, parameters: list, process_graph: ProcessBuilder):
    output_file = files("fusets.openeo.services").joinpath(f"{id}.json")
    spec = build_process_dict(
        process_id=id, description=description, summary=summary, process_graph=process_graph, parameters=parameters
    )
    with output_file.open(mode="w") as f:
        json.dump(spec, f, indent=4)
    return output_file


def publish_service(id: str, summary: str, description: str, parameters: list, process_graph: ProcessBuilder):
    # Write the content to the UDP folder
    write_service_info(
        id=id, summary=summary, description=description, parameters=parameters, process_graph=process_graph
    )

    # Publish UDP
    connection = get_openeo_connection()
    connection.save_user_defined_process(
        user_defined_process_id=id,
        summary=summary,
        description=description,
        parameters=parameters,
        process_graph=process_graph,
        public=True,
    )


DATE_SCHEMA = {
    "type": "array",
    "subtype": "temporal-interval",
    "minItems": 2,
    "maxItems": 2,
    "items": {
        "anyOf": [
            {"type": "string", "format": "date-time", "subtype": "date-time"},
            {"type": "string", "format": "date", "subtype": "date"},
            {"type": "string", "subtype": "year", "minLength": 4, "maxLength": 4, "pattern": "^\\d{4}$"},
            {"type": "null"},
        ]
    },
    "examples": [["2015-01-01T00:00:00Z", "2016-01-01T00:00:00Z"], ["2015-01-01", "2016-01-01"]],
}

GEOJSON_SCHEMA = {"type": "object", "subtype": "geojson"}


def get_context_value(p: Union[Parameter, Any]) -> Union[dict, Any]:
    return {"from_parameter": p.name} if isinstance(p, Parameter) else p
