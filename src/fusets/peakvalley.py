from typing import Iterable, Tuple

import numpy as np
import pandas as pd
import xarray
from scipy.signal import find_peaks

from fusets._xarray_utils import _extract_dates


def peakvalley_f(
    array: xarray.DataArray,
    drop_thr: float = 0.15,
    rec_r: float = 1.0,
    slope_thr: float = 0.2,
) -> np.ndarray:
    """
    Algorithm for finding peak-valley patterns in the provided array.

    @param array: DataArray containing timestamped observations
    @param drop_thr: threshold value for the amplitude of the drop in the input feature
    @param rec_r: threshold value for the amplitude of the recovery, relative to the `drop_delta`
    @param slope_thr: threshold value for the slope where the peak should start
    @return: array with different values:
                *  1: peak
                * -1: valley
                *  0: between peak and valley
                * np.nan: values outside of found peak-valley patterns
    """

    nan_mask = np.isnan(array).values
    x = np.array(_extract_dates(array))[~nan_mask]
    y = array[~nan_mask].values

    rec_thr = drop_thr * rec_r

    pk_ids = find_peaks(y)[0]
    vl_ids = find_peaks(-y)[0]
    if len(pk_ids) == 0 or len(vl_ids) == 0:
        return None

    # if first valley before peak, add initial peak
    if vl_ids[0] < pk_ids[0]:
        pk_ids = np.insert(pk_ids, 0, 0)

    # if last valley before last peak, add final valley
    if vl_ids[-1] < pk_ids[-1]:
        vl_ids = np.insert(vl_ids, len(pk_ids) - 1, len(y) - 1)

    pairs = np.transpose([pk_ids, vl_ids])
    if len(pk_ids) == 0 or len(vl_ids) == 0:
        return None

    pairs = _merge_dropping_fluctuations(pairs, y, rec_thr)
    pairs = _filter_fluctuations(pairs, y, drop_thr)
    pairs = _backtrace_till_slope(pairs, x, y, drop_thr, slope_thr)
    pairs = _filter_recovery_point(pairs, y, rec_thr)

    out = np.full_like(y, np.nan)
    for pk, vl in pairs:
        out[pk] = 1
        out[vl] = -1
        out[pk + 1 : vl] = 0

    return out, pairs


def _merge_dropping_fluctuations(pairs: np.ndarray, y: np.ndarray, rec_thr: float):
    # merge fluctuations when dropping
    idx = 0
    new_pairs = [pairs[0]]
    while idx < len(pairs) - 1:
        idx += 1
        pk2, vl2 = pairs[idx]
        pk1, vl1 = new_pairs[-1]
        y11, y12, y21, y22 = y[[pk1, vl1, pk2, vl2]]

        # merge with previous if second pair below threshold
        # and if second peak/valley below first peak/valley
        if (y21 - y12 < rec_thr) & (y22 < y12) & (y21 < y11):
            new_pairs[-1][1] = vl2
        else:
            new_pairs.append([pk2, vl2])
    return np.array(new_pairs)


def _filter_fluctuations(pairs: np.ndarray, y: np.ndarray, drop_thr: float):
    mask = -np.diff(y[pairs], axis=-1) > drop_thr
    pairs = pairs[mask.squeeze(-1)]
    return pairs


def _backtrace_till_slope(
    pairs: np.ndarray, x: np.ndarray, y: np.ndarray, drop_thr: float, slope_thr: float
):
    new_pairs = []
    for pk, vl in pairs:
        assigned_peak = False
        skip_next = False

        start = pk
        for idx in range(vl - 1, pk - 1, -1):
            if skip_next:
                skip_next = False
                continue

            # if the difference is above the threshold and the peak has not yet been assigned
            if y[idx] - y[vl] > drop_thr and not assigned_peak:
                start = idx
                assigned_peak = True
                continue

            if assigned_peak:
                # calculate derivative between current NDVI and the next NDVI
                if _calculate_slope((idx + 1, idx), x, y) < slope_thr:
                    start = idx
                elif (
                    idx - 1 >= pk
                    and _calculate_slope((idx + 1, idx - 1), x, y) < slope_thr
                ):
                    start = idx - 1
                    skip_next = True
                else:
                    break
        new_pairs.append([start, vl])
    return np.array(new_pairs)


def _filter_recovery_point(pairs: np.ndarray, y: np.ndarray, rec_thr: float):
    new_pairs = []
    for pair_id, (pk, vl) in enumerate(pairs):
        eligible = False
        next_pk = pairs[pair_id + 1][0] + 1 if pair_id + 1 < len(pairs) else len(y)
        for idx in range(vl, next_pk):
            if y[idx] - y[vl] > rec_thr:
                eligible = True
                break
            if y[idx] < y[vl]:
                vl = idx

        if eligible:
            new_pairs.append([pk, vl])
    return np.array(new_pairs)


def _calculate_slope(
    indices: Tuple[int, int], x: Iterable[pd.datetime], y: np.ndarray
) -> float:
    idx1, idx2 = indices
    return (y[idx1] - y[idx2]) / (x[idx1] - x[idx2]).days
