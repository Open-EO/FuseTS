import sys
from pathlib import Path
from typing import Dict

from openeo.udf import XarrayDataCube, inspect

phenology_bands = [
    "pos_values",
    "pos_times",
    "mos_values",
    "vos_values",
    "vos_times",
    "bse_values",
    "aos_values",
    "sos_values",
    "sos_times",
    "eos_values",
    "eos_times",
    "los_values",
    "roi_values",
    "rod_values",
    "lios_values",
    "sios_values",
    "liot_values",
    "siot_values"
]

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
    data = data.isel(bands=0)
    phenology_result = phenology(data)
    phenology_result = phenology_result.to_array(dim='bands')
    phenology_result = phenology_result.expand_dims(dim='t', axis=0).assign_coords(t=[data.time.values[0]])
    # phenology_result = phenology_result.transpose('t', 'bands', 'x', 'y')
    # raise Exception(phenology_result)
    inspect(data=phenology_result, message="Phenology result")
    return XarrayDataCube(phenology_result)


def load_phenology_udf() -> str:
    """
    Loads an openEO udf that applies phenology service.
    @return:
    """
    import os
    return Path(os.path.realpath(__file__)).read_text()
