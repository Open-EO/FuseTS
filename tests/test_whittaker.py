import io
from datetime import datetime, timedelta

import numpy as np
import numpy.testing
import requests
import xarray

from fusets import whittaker
from fusets.whittaker import whittaker_f


def test_whittaker_f():
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

    # Smooth
    ys_smooth, ts_smooth, ys_smooth_sampled, ts_smooth_sampled = whittaker_f(x=ts, y=ys_with_nan, lmbd=1, d=4)

    xs_expected = np.arange(42)
    ts_expected, ys_expected = generate_data(xs_expected)
    assert ts_smooth == ts_expected
    assert np.isnan(ys_smooth).sum() == 0
    numpy.testing.assert_allclose(ys_smooth, ys_expected, atol=0.15)

    xs_expected = np.arange(42)[::4]
    ts_expected, ys_expected = generate_data(xs_expected)
    assert ts_smooth_sampled == ts_expected
    assert np.isnan(ys_smooth_sampled).sum() == 0
    numpy.testing.assert_allclose(ys_smooth_sampled, ys_expected, atol=0.15)


def test_whittaker_xarray(sinusoidal_timeseries):

    result = whittaker(sinusoidal_timeseries,smoothing_lambda=1,time_dimension="time")

    assert np.isnan(result).sum() == 0
    numpy.testing.assert_allclose(result[~sinusoidal_timeseries.isnull()], sinusoidal_timeseries.dropna(dim="time"), atol=0.15)



def test_whittaker_realdata():
    ds = xarray.load_dataset(io.BytesIO(requests.get("https://artifactory.vgt.vito.be/testdata-public/malawi_sentinel2.nc",stream=True).content))
    some_index = (ds.B04 - ds.B02) / (ds.B04 + ds.B02)
    print(some_index)
    smoothed_output = whittaker(some_index)
    out_set = xarray.Dataset({"index":smoothed_output.assign_attrs(grid_mapping="crs"),"crs":ds.crs},attrs=dict(Conventions="CF-1.8"))
    out_set.to_netcdf("malawi_smooth.nc")


