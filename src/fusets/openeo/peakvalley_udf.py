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

    from fusets import peakvalley

    drop_thr = context.get('drop_thr', 0.15)
    rec_r = context.get('rec_r', 1.0)
    slope_thr = context.get('slope_thr', -0.007)

    result = peakvalley(cube.get_array(), drop_thr=drop_thr, rec_r=rec_r, slope_thr=slope_thr)
    return XarrayDataCube(result)


def load_peakvalley_udf() -> str:
    """
    Loads an openEO udf that applies peak valley detection service.
    @return:
    """
    import os
    return Path(os.path.realpath(__file__)).read_text()
