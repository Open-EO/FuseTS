import io

import pytest
import requests
import xarray

from fusets.mogpr import MOGPRTransformer


@pytest.fixture()
def data() -> xarray.Dataset:
    bytes_data = requests.get("https://artifactory.vgt.vito.be/testdata-public/fusets/b4_b8_vv_vh/rape.nc", stream=True)
    ds = xarray.load_dataset(io.BytesIO(bytes_data.content))
    ds = ds.isel(t=ds.t.dt.year.isin([2019, 2020]), x=slice(9, 11), y=slice(9, 11))

    ds["RVI"] = (ds.VH + ds.VH) / (ds.VV + ds.VH)
    ds["NDVI"] = (ds.B08 - ds.B04) / (ds.B04 + ds.B08)
    return ds[["NDVI", "RVI"]]


def test_mogpr_udf(data):
    from openeo.udf import XarrayDataCube

    from fusets.openeo.mogpr_udf import apply_datacube

    result = apply_datacube(XarrayDataCube(data.to_array(dim="bands")), context={})
    assert result.array.dims == ("bands", "t", "y", "x")
    assert result.array.shape == (2, 146, 2, 2)


def test_mogpr_train_model(data):
    t = MOGPRTransformer()
    t.fit(data)
    out = t.transform(data)

    assert tuple(out.coords) == ("t", "y", "x")
    assert out.NDVI.shape == (146, 2, 2)
