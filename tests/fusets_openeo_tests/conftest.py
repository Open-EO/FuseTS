import json
import os

import geopandas as gpd
import pytest

from tests.helpers import RESOURCES


@pytest.fixture
def benchmark_features():
    aoi_dir = RESOURCES / "aois"
    geojson_files = [file for file in os.listdir(aoi_dir) if file.endswith(".geojson")]
    result = []
    for file in geojson_files:
        with open(aoi_dir / file, "r") as input:
            data = json.load(input)
            aois = data["features"]
            for feature in aois:
                feature["properties"] = {**feature["properties"], "jobname": file.split(".")[0]}
            result += aois
            input.close()
    return gpd.GeoDataFrame.from_features(result)
