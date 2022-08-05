from datetime import datetime


def test_output_dates():
    from fusets._xarray_utils import _output_dates
    result_dates = _output_dates("P5D","2023-03-15","2024-02-29")
    print(result_dates)
    assert len(result_dates) == 71
    assert datetime(2023, 3, 15, 0, 0) == result_dates[0]
    assert datetime(2023, 3, 20, 0, 0) == result_dates[1]
    assert datetime(2024, 2, 28, 0, 0) == result_dates[70]

