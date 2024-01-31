from datetime import datetime

import numpy as np
import pandas as pd


def _topydate(t):
    return datetime.utcfromtimestamp((t - np.datetime64("1970-01-01T00:00:00Z")) / np.timedelta64(1, "s"))


def _extract_dates(array):
    time_coords = [c for c in array.coords.values() if c.dtype.type == np.datetime64]
    if len(time_coords) == 0:
        raise ValueError(
            "Whittaker expects an input with exactly one coordinate of type numpy.datetime64, which represents the time dimension, but found none."
        )
    if len(time_coords) > 1:
        raise ValueError(
            f"Whittaker expects an input with exactly one coordinate of type numpy.datetime64, which represents the time dimension, but found multiple: {time_coords}"
        )
    dates = time_coords[0]
    assert dates.dtype.type == np.datetime64

    dates = list(dates.values)
    dates = [_topydate(d) for d in dates]
    return dates


def _time_dimension(array, time_dimension):
    time_coords = {c.name: c for c in array.coords.values() if c.dtype.type == np.datetime64}
    if len(time_coords) == 0:
        raise ValueError(f"Your input array does not have a time dimension {array}")
    if len(time_coords) > 1:
        if not (time_dimension in time_coords):
            raise ValueError(
                f"Specified time dimension {time_dimension} does not exist, available dimensions: f{time_coords.keys()}"
            )
    else:
        time_dimension = list(time_coords.keys())[0]
    return time_dimension


def _output_dates(prediction_period, start_date, end_date):
    period = pd.Timedelta(prediction_period)
    range = pd.date_range(start_date, end_date, freq=period)
    return [_topydate(d) for d in range.values]


def _suffix_variables(array, suffix):
    """
    Rename variables in a data array by appending the suffix to the variable names.
    """
    renamed_data_array = array.copy()
    renamed_variables = []
    for variable in renamed_data_array['variable'].values:
        renamed_variables.append(f"{variable}{suffix}")

    renamed_data_array['variables'] = np.array(renamed_variables)
    return renamed_data_array
