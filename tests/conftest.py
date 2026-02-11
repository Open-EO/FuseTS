from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest
import xarray


@pytest.fixture
def connection():
    """Connection fixture to a backend of given version with some image collections."""
    import openeo

    return openeo.connect("openeo-dev.vito.be")


@pytest.fixture
def auth_connection(connection):
    """Connection fixture to a backend of given version with some image collections."""

    return connection.authenticate_oidc()


@pytest.fixture
def sinusoidal_timeseries():
    def generate_data(xs: np.array):
        """Generate test data from array of ints (day offsets)"""
        ts = [datetime(2022, 1, 1) + timedelta(days=int(x)) for x in xs]
        ys = np.cos(0.35 * xs)
        return ts, ys

    n = 32
    # Input: unevenly spaced timestamps and missing data
    xs = np.array([(x + x // 3) for x in range(n)], dtype="int")
    ts, ys = generate_data(xs)
    ys_with_nan = ys.copy()
    ys_with_nan[xs % 5 >= 2] = np.nan
    assert 0.25 < np.isnan(ys_with_nan).mean() < 0.75

    return xarray.DataArray(data=ys_with_nan, dims=["time"], coords=dict(time=ts))


@pytest.fixture
def harmonic_timeseries():
    intercept = 5000
    coef = [5, 600, 200]

    def generate_data(xs: np.array):
        """Generate test data from array of ints (day offsets)"""
        ts = [datetime(2016, 1, 1) + timedelta(days=int(5 * x)) for x in xs]
        days = 5 * xs
        ys = (
            intercept
            + coef[0] * days
            + coef[1] * np.cos(days * 1 * 2 * np.pi / 365.25)
            + coef[2] * np.sin(days * 1 * 2 * np.pi / 365.25)
        )
        return ts, ys

    n = 365
    # Input: unevenly spaced timestamps and missing data
    xs = np.array([x for x in range(n)], dtype="int")
    ts, ys = generate_data(xs)
    # ys_with_nan = ys.copy()
    # ys_with_nan[xs % 5 >= 2] = np.nan
    # assert 0.25 < np.isnan(ys_with_nan).mean() < 0.75

    return xarray.DataArray(data=ys, dims=["time"], coords=dict(time=ts))


@pytest.fixture
def outlier_timeseries():
    rng = np.random.default_rng(42)
    dates = pd.date_range("2019-01-01", "2019-12-31", periods=300)
    values = np.sin(np.linspace(0, 4 * np.pi, len(dates))) + rng.random(len(dates)) * 0.2
    values[rng.choice(range(len(dates)), 4).astype(int)] += rng.choice([-1, 1], 4) * 5

    return xarray.DataArray(data=values, dims=["time"], coords=dict(time=dates))


@pytest.fixture
def areas():
    return {
        "wetland": (22.490387, 53.328413, 22.573814, 53.372474),
        "agriculture_spain": (
            22.490387,
            53.328413,
            22.573814,
            53.372474,
        ),  # http://bboxfinder.com/#41.749159,-4.838362,53.372474,22.573814
        "malawi": (
            33.816830,
            -12.763348,
            33.827130,
            -12.758645,
        ),  # http://bboxfinder.com/#41.749159,-4.838362,53.372474,22.573814
    }


@pytest.fixture
def xarray_inputs(areas):
    from fusets.openeo import load_xarray

    return {
        area[0]: load_xarray("SENTINEL2_L2A", spatial_extent=area[1], temporal_extent=("2020-01-01", "2021-01-01"))
        for area in areas.items()
    }


@pytest.fixture
def wetland_sentinel2_ndvi(areas):
    import openeo

    openeo_connection = openeo.connect("openeo-dev.vito.be").authenticate_oidc()
    scl = openeo_connection.load_collection(
        "SENTINEL2_L2A", temporal_extent=("2020-01-01", "2021-01-01"), bands=["SCL"]
    ).filter_bbox(areas["wetland"])
    cloud_mask = scl.process(
        "to_scl_dilation_mask",
        data=scl,
        kernel1_size=17,
        kernel2_size=77,
        mask1_values=[2, 4, 5, 6, 7],
        mask2_values=[3, 8, 9, 10, 11],
        erosion_kernel_size=3,
    )
    data = openeo_connection.load_collection(
        "SENTINEL2_L2A", temporal_extent=("2020-01-01", "2021-01-01"), bands=["B08", "B04"]
    ).filter_bbox(areas["wetland"])
    data = data.mask(cloud_mask)

    return data.ndvi(nir="B08", red="B04")


def input_definitions(areas):
    return {
        "area": {},
        "temporal_extent": ("", ""),
        "collections": {"SENTINEL2_L2A": {"bands": ["B02", "B03"]}, "SENTINEL1_GRD": {"bands": ["VV", "VH"]}},
        "computed_variables": ["NDVI", "CropSAR-NDVI", "fAPAR"],
    }
