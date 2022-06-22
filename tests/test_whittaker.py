from datetime import datetime, timedelta

import numpy as np
import numpy.testing

from fusets.whittaker import whittaker_f, whittaker


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
    result = whittaker(sinusoidal_timeseries,smoothing_lambda=10000,time_dimension="time")

    print(result)
    assert np.isnan(result).sum() == 0
    #numpy.testing.assert_allclose(result, sinusoidal_timeseries, atol=0.15)



