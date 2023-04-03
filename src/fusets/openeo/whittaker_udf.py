import sys
from pathlib import Path
from typing import Dict

from openeo.udf import XarrayDataCube

venv_path = 'tmp/venv_static'
if Path(venv_path).exists():
    sys.path.insert(0, 'tmp/venv_static')

def apply_datacube(cube: XarrayDataCube, context: Dict) -> XarrayDataCube:
    """
    Apply whittaker smoothing to a datacube
    @param cube:
    @param context:
    @return:
    """

    from fusets.whittaker import whittaker
    smoothing_lambda = context.get("smoothing_lambda",None)
    return XarrayDataCube(whittaker(cube.get_array(),smoothing_lambda=smoothing_lambda))


def load_whittakker_udf() -> str:
    """
    Loads an openEO udf that applies whittaker smoothing.
    @return:
    """
    import os
    return Path(os.path.realpath(__file__)).read_text()
