import math
from datetime import timedelta, datetime

import numpy as np
import xarray
from vam.whittaker import ws2d
from xarray import DataArray

from fusets._xarray_utils import _extract_dates

"""


References

P. H. C. Eilers, V. Pesendorfer and R. Bonifacio, "Automatic smoothing of remote sensing data," 2017 9th International Workshop on the Analysis of Multitemporal Remote Sensing Images (MultiTemp), Brugge, 2017, pp. 1-3. doi: 10.1109/Multi-Temp.2017.8076705 URL: http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8076705&isnumber=8035194
"""

def whittaker(array:DataArray, smoothing_lambda=10000, time_dimension="t"):
    """
    Whittaker represents a computationally efficient reconstruction method for smoothing and gap-filling of time series.
    The main function takes as input two vectors of the same length: the y time series data (e.g. NDVI) and the
    corresponding temporal vector (date format) x, comprised between the start and end dates of a satellite image
    collection. Missing or null values as well as the cloud-masked values (i.e. NaN), are handled by introducing a
    vector of 0-1 weights w, with wi = 0 for missing observations and wi=1 otherwise. Following, the Whittaker smoother
    is applied to the time series profiles, computing therefore a daily smoothing interpolation.

    Whittaker's fast processing speed was assessed through an initial performance testing by comparing different
    time series fitting methods. Average runtime takes 0.0107 seconds to process a single NDVI temporal profile.

    The smoother performance can be adjusted by tuning the lambda parameter, which penalizes the time series roughness:
    the larger lambda the smoother the time series at the cost of the fit to the data getting worse. We found a
    lambda of 10000 adequate for obtaining more convenient results. A more detailed description of the algorithm can be
    found in the original work of Eilers 2003.

    @param array:
    @param smoothing_lambda:
    @param time_dimension:
    @return:
    """

    dates = _extract_dates(array)

    def callback(timeseries):
        z1_, xx, Zd, XXd = whittaker_f(dates, timeseries, smoothing_lambda, 1)
        indices = [XXd.index(date) for date in dates]

        result = list(Zd[i] for i in indices)
        return np.array(result)


    result = xarray.apply_ufunc(callback, array, input_core_dims=[[time_dimension]], output_core_dims=[[time_dimension]],vectorize=True)

    #make sure to preserve dimension order
    return result.transpose(*array.dims)




def whittaker_f(x, y, lmbd, d):
    """
    Whittaker represents a computationally efficient reconstruction method for smoothing and gap-filling of time series.
    The main function takes as input two vectors of the same length: the y time series data (e.g. NDVI) and the
    corresponding temporal vector (date format) x, comprised between the start and end dates of a satellite image
    collection. Missing or null values as well as the cloud-masked values (i.e. NaN), are handled by introducing a
    vector of 0-1 weights w, with wi = 0 for missing observations and wi=1 otherwise. Following, the Whittaker smoother
    is applied to the time series profiles, computing therefore a daily smoothing interpolation.

    Whittaker's fast processing speed was assessed through an initial performance testing by comparing different
    time series fitting methods. Average runtime takes 0.0107 seconds to process a single NDVI temporal profile.

    The smoother performance can be adjusted by tuning the lambda parameter, which penalizes the time series roughness:
    the larger lambda the smoother the time series at the cost of the fit to the data getting worse. We found a
    lambda of 10000 adequate for obtaining more convenient results. A more detailed description of the algorithm can be
    found in the original work of Eilers 2003.


    Args:
       x (ndarray) : # numpy ndarray of datetime objects
       y (ndarray) : # numpy ndarray of y values
       lmbd (double) : lambda value
       d (int) : period between returned values, as number of days

    Returns:
        Returns daily (default) and d spacing (d in days defined by the user) smoothed and gap-filled time series and the corresponding time date vector.
    """
    # minimum and maximum dates
    D1 = get_all_dates(x)
    D11 = D1[~np.isnan(y)]

    l = D1[-1] - D1[0]
    v = np.full(l + 1, -3000)
    v[D11] = 1

    t = np.full(l + 1, 0, dtype='float')
    t[D11] = y[~np.isnan(y)]

    # dates
    xx = [x[0] + timedelta(days=i) for i in range(l + 1)]  # try using pandas instead?

    # create weights
    w = np.array((v != -3000) * 1, dtype='double')

    # apply filter
    z_ = ws2d(t, lmbd, w)
    z1_ = np.array(z_)

    # return z1_,xx

    if isinstance(d, int):
        if d > 0 and d < z1_.size:
            n = z1_.size
            ind = [i * d for i in range(math.ceil(n / d))]
            Zd = z1_[ind]
            XXd = [xx[ii] for ii in ind]
        else:
            Zd = []
            XXd = []
            print("d must be positive and smaller than the total number of dates")
    else:
        Zd = []
        XXd = []
        print("d must be an integer")

    return z1_, xx, Zd, XXd


def get_all_dates(x):
    D = [ i.toordinal() for i in x]
    D1 = np.array(D) - D[0]
    return D1
