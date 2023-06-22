import math
from array import array
from datetime import timedelta
from typing import Union

import numpy as np
import xarray
from vam.whittaker import ws2d, ws2doptv
from xarray import DataArray

from fusets._xarray_utils import _extract_dates, _time_dimension, _output_dates

import importlib.util

from fusets.base import BaseEstimator

_openeo_exists = importlib.util.find_spec("openeo") is not None
if _openeo_exists:
    from openeo import DataCube


"""


References

P. H. C. Eilers, V. Pesendorfer and R. Bonifacio, "Automatic smoothing of remote sensing data," 2017 9th International Workshop on the Analysis of Multitemporal Remote Sensing Images (MultiTemp), Brugge, 2017, pp. 1-3. doi: 10.1109/Multi-Temp.2017.8076705 URL: http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=8076705&isnumber=8035194
"""


class WhittakerTransformer(BaseEstimator):
    """
    A transformer that applies whittaker smoothing to an irregular timeseries.

    """

    def fit_transform(self, X:Union[DataArray,DataCube], y:Union[DataArray,DataCube]=None, **fit_params):
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

        .. image:: images/whittaker_rye.svg
          :width: 800
          :alt: Comparing smoothing parameter

        Args:
            array: An input datacube having at least a temporal dimension over which the smoothing will be applied.
            smoothing_lambda: The smoothing factor.
            time_dimension: The name of the time dimension of this datacube. Only needs to be specified to resolve ambiguities.
            prediction_period: The duration specified as ISO-8601, e.g. P5D: 5-daily, P1M: monthly. First date of the time dimension is used as starting point.

        Returns: A smoothed datacube

        """

        smoothing = fit_params.get("smoothing_lambda", 10000)
        if _openeo_exists and isinstance(array, DataCube):
            from .openeo import whittaker as whittaker_openeo
            return whittaker_openeo(array, smoothing)

        return whittaker(X, smoothing, fit_params.get("time_dimension", "t"), fit_params.get("prediction_period", None))


def whittaker(array:Union[DataArray,DataCube], smoothing_lambda=10000, time_dimension="t", prediction_period=None) -> Union[DataArray,DataCube]:
    """
    Convenience method for whittaker. See :meth:`fusets.whittaker.WhittakerTransformer.fit_transform` for more detailed documentation.

    Args:
        array: An input datacube having at least a temporal dimension over which the smoothing will be applied.
        smoothing_lambda: The smoothing factor.
        time_dimension: The name of the time dimension of this datacube. Only needs to be specified to resolve ambiguities.
        prediction_period: The duration specified as ISO-8601, e.g. P5D: 5-daily, P1M: monthly. First date of the time dimension is used as starting point.

    Returns: A smoothed datacube

    """
    if _openeo_exists and isinstance(array,DataCube):
        from .openeo import whittaker as whittaker_openeo
        return whittaker_openeo(array,smoothing_lambda)


    dates = _extract_dates(array)
    time_dimension = _time_dimension(array, time_dimension)

    output_dates = dates
    output_time_dimension = time_dimension

    if prediction_period is not None:
        output_dates = _output_dates(prediction_period, dates[0], dates[-1])
        output_time_dimension = "t_new"

    def callback(timeseries):
        _, _, Zd, XXd = whittaker_f(dates, timeseries, smoothing_lambda, 1)
        dates_mask = np.in1d(XXd, output_dates)
        return Zd[dates_mask]

    result = xarray.apply_ufunc(callback, array, input_core_dims=[[time_dimension]], output_core_dims=[[output_time_dimension]],vectorize=True)

    result[output_time_dimension] = output_dates
    result = result.rename({output_time_dimension: time_dimension})

    # make sure to preserve dimension order
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
    if isinstance(lmbd,list):
        # the whitakker library also allows to choose a lambda value from a list. Note that values in this list need to be log10(lambda) (or so it seems)
        z_,the_lambda = ws2doptv(t, w=w,llas=array('d',lmbd))
    else:
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
