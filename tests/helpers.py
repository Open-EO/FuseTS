import json
from pathlib import Path

RESOURCES = Path(__file__).parent / 'resources'


def read_test_json(name, ):
    with open(f'{RESOURCES}/{name}', 'r') as file:
        return json.load(file)
