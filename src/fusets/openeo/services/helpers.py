import json
import os

import openeo
from importlib_resources import files


def get_openeo_connection():
    return openeo.connect("openeo.vito.be").authenticate_basic(os.getenv('OPENEO_USER'), os.getenv('OPENEO_PASSWORD'))


def read_description(service: str) -> str:
    return files('fusets.openeo.services').joinpath(f'descriptions/{service}.md').read_text(encoding='utf-8')


def write_service_info(id: str, summary: str, description: str, parameters: list, process_graph: any):
    output_file = files('fusets.openeo.services').joinpath(f'{id}.json')
    with output_file.open(mode='w') as f:
        json.dump({
            "id": id,
            "summary": summary,
            "description": description,
            "parameters": parameters,
            "process_graph": process_graph
        }, f, indent=4)
    return output_file


def publish_udp(id: str, summary: str, description: str, parameters: list, process_graph: any):
    connection = get_openeo_connection()
    connection.save_user_defined_process(user_defined_process_id=id, summary=summary, description=description,
                                         parameters=parameters, process_graph=process_graph, public=True)


def publish_service(id: str, summary: str, description: str, parameters: list, process_graph: any):
    # Write the content to the UDP folder
    write_service_info(id=id, summary=summary, description=description, parameters=parameters,
                       process_graph=process_graph)

    # Publish UDP
    publish_udp(id=id, summary=summary, description=description, parameters=parameters, process_graph=process_graph)
