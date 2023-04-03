import sys
from pathlib import Path
from typing import Dict

from openeo.udf import XarrayDataCube

venv_path = 'tmp/venv_static'
if Path(venv_path).exists():
    sys.path.insert(0, 'tmp/venv_static')


def apply_datacube(cube: XarrayDataCube, context: Dict) -> XarrayDataCube:
    """
    Apply mogpr integration to a datacube.
    MOGPR requires a full timeseries for multiple bands, so it needs to be invoked in the context of an apply_neighborhood process.
    @param cube:
    @param context:
    @return:
    """

    from fusets.mogpr import MOGPRTransformer
    return XarrayDataCube(MOGPRTransformer().fit_transform(cube.get_array()))


def load_mogpr_udf() -> str:
    """
    Loads an openEO udf that applies mogpr.
    @return:
    """
    import os
    return Path(os.path.realpath(__file__)).read_text()
