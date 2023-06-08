import sys
from pathlib import Path
from typing import Dict

from openeo.udf import XarrayDataCube


def load_venv():
    """
    Add the virtual environment to the system path if the folder `/tmp/venv_static` exists
    :return:
    """
    for venv_path in ['tmp/venv_static', 'tmp/venv']:
        if Path(venv_path).exists():
            sys.path.insert(0, venv_path)


def apply_datacube(cube: XarrayDataCube, context: Dict) -> XarrayDataCube:
    """
    Apply phenology to a datacube
    @param cube:
    @param context:
    @return:
    """
    load_venv()

    from fusets.analytics import phenology
    data = cube.get_array()
    data = data.rename({'t': 'time'})
    phenology_result = phenology(data)
    return XarrayDataCube(phenology_result.to_array()))


def load_phenology_udf() -> str:
    """
    Loads an openEO udf that applies phenology service.
    @return:
    """
    import os
    return Path(os.path.realpath(__file__)).read_text()
