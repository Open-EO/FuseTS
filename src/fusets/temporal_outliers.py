from datetime import datetime
from typing import List, Sequence, Union

import numpy as np
import pandas as pd
import xarray
from xarray import DataArray

from fusets._xarray_utils import _extract_dates, _time_dimension


def temporal_outliers(
    array: DataArray, window: Union[int, str], threshold: float, variables: List[str] = None
) -> DataArray:
    """
    Algorithm for a z-score-based filtering of time series outliers

    Args:
        array: input data array
        window: pandas-based window-size, can be integer or string, e.g., '20D' for a 20 days window
        threshold: the threshold to be applied on the z-scores for filtering outlier (amount of st. dev.)
        variables: The list of variable names that should be affected, or None to use all variables

    Returns:
        data array with outliers filtered out and with the rolling mean of time series
    """

    dates = np.array(_extract_dates(array))
    time_dimension = _time_dimension(array, None)

    if variables is not None:
        array = array.drop_vars([var for var in list(array.data_vars) if var not in variables])

    def callback(timeseries):
        return temporal_outliers_f(dates, timeseries, window, threshold)

    result = xarray.apply_ufunc(
        callback,
        array,
        input_core_dims=[[time_dimension]],
        output_core_dims=[[time_dimension]],
        vectorize=True,
    )

    return result


def temporal_outliers_f(x: Sequence[datetime], y: np.ndarray, window: Union[int, str], threshold: float) -> np.ndarray:
    """
    Algorithm for a z-score-based filtering of time series outliers

    Args:
        x: array of timestamps
        y: array of input feature values
        window: pandas-based window-size, can be integer or string, e.g., '20D' for a 20 days window
        threshold: the threshold to be applied on the z-scores for filtering outlier (amount of st. dev.)

    Returns:
        array with outliers filtered out and replaced with the rolling mean of time series
    """

    timeseries = pd.Series(y, index=x)
    rolling = timeseries.rolling(window=window, center=True, closed="both")
    ts_mean = rolling.mean()
    ts_std = rolling.std(ddof=1)

    ts_zscore = timeseries.sub(ts_mean).div(ts_std)
    ts_mask = ts_zscore.between(-threshold, threshold)

    return timeseries.where(ts_mask, ts_mean).to_numpy(dtype="float32")
