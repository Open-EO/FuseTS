import sys
import time
from pathlib import Path
from typing import Dict

from openeo.udf import XarrayDataCube, inspect

start = time.time()


def log_time(message: str, previous=time.time()) -> float:
    """Create an output log for the batch job"""
    now = time.time()
    inspect(data=None, message=f"{message} ({previous - time.time()} seconds)")
    return now


def load_venv():
    """
    Add the virtual environment to the system path if the folder `/tmp/venv_static` exists
    :return:
    """
    for venv_path in ["tmp/venv_static", "tmp/venv"]:
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

    time = log_time("Initiated Whittaker environment")
    smoothing_lambda = context.get("smoothing_lambda", None)

    result = XarrayDataCube(whittaker(cube.get_array(), smoothing_lambda=smoothing_lambda))
    log_time("Calculated whittaker result", time)
    return result


def load_whittakker_udf() -> str:
    """
    Loads an openEO udf that applies whittaker smoothing.
    @return:
    """
    import os

    return Path(os.path.realpath(__file__)).read_text()
