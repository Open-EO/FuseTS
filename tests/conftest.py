from datetime import datetime, timedelta

import numpy as np
import pytest
import xarray


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

    return xarray.DataArray(data=ys_with_nan,
                     dims=["time"],
                     coords=dict(time=ts))