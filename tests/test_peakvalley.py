import numpy as np
from fusets._xarray_utils import _extract_dates
from fusets.peakvalley import peakvalley_f
from numpy.testing import assert_array_equal


def test_peak_valley_detection(harmonic_timeseries):
    dates = np.array(_extract_dates(harmonic_timeseries))
    vals = harmonic_timeseries.values
    _, pairs = peakvalley_f(dates, vals, drop_thr=200, rec_r=1.0, slope_thr=0)
    test_values = np.array([[9, 35], [82, 108], [155, 181], [228, 254], [301, 327]])
    assert_array_equal(pairs, test_values)
