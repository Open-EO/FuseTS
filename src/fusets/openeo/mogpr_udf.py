import os
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Dict

from openeo.metadata import CollectionMetadata
from openeo.udf import XarrayDataCube, inspect


def load_venv():
    """
    Add the virtual environment to the system path if the folder `/tmp/venv_static` exists
    :return:
    """
    for venv_path in ["tmp/venv", "tmp/venv_static"]:
        if Path(venv_path).exists():
            sys.path.insert(0, venv_path)


def set_home(home):
    os.environ["HOME"] = home


def create_gpy_cfg():
    home = os.getenv("HOME")
    set_home("/tmp")
    user_file = Path.home() / ".config" / "GPy" / "user.cfg"
    if not user_file.exists():
        user_file.parent.mkdir(parents=True, exist_ok=True)
    return user_file, home


def write_gpy_cfg():
    user_file, home = create_gpy_cfg()
    config = ConfigParser()
    config["plotting"] = {"library": "none"}
    with open(user_file, "w") as cfg:
        config.write(cfg)
        cfg.close()
    return home


def apply_datacube(cube: XarrayDataCube, context: Dict) -> XarrayDataCube:
    """
    Apply mogpr integration to a datacube.
    MOGPR requires a full timeseries for multiple bands, so it needs to be invoked in the context of an apply_neighborhood process.
    @param cube:
    @param context:
    @return:
    """
    load_venv()
    home = write_gpy_cfg()

    from fusets.mogpr import mogpr

    variables = context.get("variables")
    time_dimension = context.get("time_dimension", "t")
    prediction_period = context.get("prediction_period", "5D")
    include_uncertainties = context.get("include_uncertainties", False)

    dims = cube.get_array().dims
    result = mogpr(
        cube.get_array().to_dataset(dim="bands"),
        variables=variables,
        time_dimension=time_dimension,
        prediction_period=prediction_period,
        include_uncertainties=include_uncertainties
    )
    result_dc = XarrayDataCube(result.to_array(dim="bands").transpose(*dims))
    set_home(home)
    return result_dc


def apply_metadata(metadata: CollectionMetadata, context: dict) -> CollectionMetadata:
    return metadata.rename_labels(
        dimension="bands",
        target=metadata.bands + [f"{x}_STD" for x in metadata.bands]
    )


def load_mogpr_udf() -> str:
    """
    Loads an openEO udf that applies mogpr.
    @return:
    """
    import os

    return Path(os.path.realpath(__file__)).read_text()
