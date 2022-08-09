import numpy as np
from fusets.peakvalley import peakvalley_f
from numpy.testing import assert_array_equal


def test_fit_simple_harmonics_exact(harmonic_timeseries):
    _, pairs = peakvalley_f(harmonic_timeseries, drop_thr=200, rec_r=1.0, slope_thr=0)
    test_values = np.array([[9, 35], [82, 108], [155, 181], [228, 254], [301, 327]])
    assert_array_equal(pairs, test_values)
