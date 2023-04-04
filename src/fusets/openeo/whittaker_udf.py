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
    Apply whittaker smoothing to a datacube
    @param cube:
    @param context:
    @return:
    """
    load_venv()

    from fusets.whittaker import whittaker
    smoothing_lambda = context.get("smoothing_lambda", None)
    return XarrayDataCube(whittaker(cube.get_array(), smoothing_lambda=smoothing_lambda))


def load_whittakker_udf() -> str:
    """
    Loads an openEO udf that applies whittaker smoothing.
    @return:
    """
    import os
    return Path(os.path.realpath(__file__)).read_text()
