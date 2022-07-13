from datetime import datetime

import numpy as np


def _extract_dates(array):
    time_coords = [c for c in array.coords.values() if c.dtype.type == np.datetime64]
    if len(time_coords) == 0:
        raise ValueError(
            "Whittaker expects an input with exactly one coordinate of type numpy.datetime64, which represents the time dimension, but found none.")
    if len(time_coords) > 1:
        raise ValueError(
            f"Whittaker expects an input with exactly one coordinate of type numpy.datetime64, which represents the time dimension, but found multiple: {time_coords}")
    dates = time_coords[0]
    assert dates.dtype.type == np.datetime64

    def topydate(t):
        return datetime.utcfromtimestamp((t - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's'))

    dates = list(dates.values)
    dates = [topydate(d) for d in dates]
    return dates