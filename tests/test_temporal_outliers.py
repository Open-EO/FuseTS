import numpy as np
from numpy.testing import assert_almost_equal

from fusets._xarray_utils import _extract_dates
from fusets.temporal_outliers import temporal_outliers_f


def test_temporal_outlier_filtering(outlier_timeseries):
    dates = np.array(_extract_dates(outlier_timeseries))
    vals = outlier_timeseries.values

    filtered_vals = temporal_outliers_f(dates, vals, window="20D", threshold=3)

    assert_almost_equal(filtered_vals.mean(), 0.09904716, decimal=6)
    assert_almost_equal(filtered_vals.std(), 0.71552783, decimal=6)
