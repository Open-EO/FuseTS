from datetime import datetime
from typing import Iterable, Sequence, Tuple

import numpy as np
import xarray
from scipy.signal import find_peaks
from xarray import DataArray

from fusets._xarray_utils import _extract_dates, _time_dimension


def peakvalley(
    array: DataArray,
    drop_thr: float = 0.15,
    rec_r: float = 1.0,
    slope_thr: float = -0.007,
) -> DataArray:
    """
    Algorithm for finding peak-valley patterns in the provided array.

    Args:
        array: input data array
        drop_thr: threshold value for the amplitude of the drop in the input feature
        rec_r: threshold value for the amplitude of the recovery, relative to the `drop_delta`
        slope_thr: threshold value for the slope where the peak should start

    Returns:
        data array with different values {1: peak, -1: valley, 0: between peak and valley, np.nan: other}
    """

    dates = np.array(_extract_dates(array))
    time_dimension = _time_dimension(array, None)

    def callback(timeseries):
        out, _ = peakvalley_f(dates, timeseries, drop_thr, rec_r, slope_thr)
        return out

    result = xarray.apply_ufunc(
        callback,
        array,
        input_core_dims=[[time_dimension]],
        output_core_dims=[[time_dimension]],
        vectorize=True,
    )

    result = result.rename("peak_valley_mask")
    return result


def peakvalley_f(
    x: Sequence[datetime],
    y: np.ndarray,
    drop_thr: float = 0.15,
    rec_r: float = 1.0,
    slope_thr: float = -0.007,
) -> np.ndarray:
    """
    Algorithm for finding peak-valley patterns in the provided array.

    Args:
        x: array of timestamps
        y: array of input feature values
        drop_thr: threshold value for the amplitude of the drop in the input feature
        rec_r: threshold value for the amplitude of the recovery, relative to the `drop_delta`
        slope_thr: threshold value for the slope where the peak should start

    Returns:
        array with different values {1: peak, -1: valley, 0: between peak and valley, np.nan: other}
    """

    drop_thr, rec_thr = drop_thr, drop_thr * rec_r
    result = np.full_like(y, np.nan)

    # find peaks and valleys in trend
    nan_mask = np.isnan(y)
    feature = y[~nan_mask]
    timestamps = x[~nan_mask]

    pk_ids = find_peaks(feature)[0]
    vl_ids = find_peaks(-feature)[0]
    if len(pk_ids) == 0 or len(vl_ids) == 0:
        return result, []

    # if first valley before peak, add initial peak
    if vl_ids[0] < pk_ids[0]:
        pk_ids = np.insert(pk_ids, 0, 0)

    # if last valley before last peak, add final valley
    if vl_ids[-1] < pk_ids[-1]:
        vl_ids = np.insert(vl_ids, len(pk_ids) - 1, len(feature) - 1)

    pairs = np.transpose([pk_ids, vl_ids])
    if len(pk_ids) == 0 or len(vl_ids) == 0:
        return result, []

    # merge fluctuations when dropping
    idx = 0
    new_pairs = [pairs[0]]
    while idx < len(pairs) - 1:
        idx += 1
        pk2, vl2 = pairs[idx]
        pk1, vl1 = new_pairs[-1]
        y11, y12, y21, y22 = feature[[pk1, vl1, pk2, vl2]]

        # merge with previous if second pair below threshold
        # and if second peak/valley below first peak/valley
        if (y21 - y12 < rec_thr) & (y22 < y12) & (y21 < y11):
            new_pairs[-1][1] = vl2
        else:
            new_pairs.append([pk2, vl2])
    pairs = np.array(new_pairs)

    # apply filter on merged
    mask = -np.diff(feature[pairs], axis=-1) > drop_thr
    pairs = pairs[mask.squeeze(-1)]

    # select eligible events
    new_pairs = []
    for p_id, (pk, vl) in enumerate(pairs):
        eligible = False
        assigned_peak = False  # flag to control if the peak has already been assigned
        skip_next = False

        # fix marker start
        for idx in range(vl - 1, pk - 1, -1):
            if skip_next:
                skip_next = False
                continue

            # if the difference is above the threshold and the peak has not yet been assigned
            if feature[idx] - feature[vl] > drop_thr and not assigned_peak:
                start = idx
                assigned_peak = True
                continue

            if assigned_peak:
                # calculate derivative between current NDVI and the next NDVI
                slope1 = _calculate_slope((idx + 1, idx), x, y)
                slope2 = _calculate_slope((idx + 1, idx - 1), x, y)
                if slope1 < slope_thr:
                    start = idx

                elif idx - 1 >= pk and slope2 < slope_thr:
                    start = idx - 1
                    skip_next = True
                else:
                    break

        # find marker end
        next_pk = pairs[p_id + 1][0] + 1 if p_id + 1 < len(pairs) else len(feature)
        for idx in range(vl, next_pk):
            if feature[idx] - feature[vl] > rec_thr:
                rec = idx
                eligible = True
                break
            if feature[idx] < feature[vl]:
                vl = idx

        if not eligible:
            continue

        new_pairs.append([start, vl])

    pairs = np.array(new_pairs)

    for pair in pairs:
        s, e = timestamps[pair]
        result[(x > s) & (x < e)] = 0
        result[(x == s)] = 1
        result[(x == e)] = -1

    return result, pairs


def _calculate_slope(
    indices: Tuple[int, int], x: Iterable[datetime], y: np.ndarray
) -> float:
    idx1, idx2 = indices
    return (y[idx1] - y[idx2]) / (x[idx1] - x[idx2]).days
