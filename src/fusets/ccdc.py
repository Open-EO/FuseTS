import numpy as np
from ccd.models import lasso
from ccd.parameters import defaults
import xarray

from fusets._xarray_utils import _extract_dates


def fit_harmonics_curve(array: xarray.DataArray, num_coefficients=6, time_dimension=None):
    """
    Fit a timeseries model based on fourier harmonics as proposed by CCDC.
    This method expects inputs in the [0,10000] range!

    `Zhe Zhu, Curtis E. Woodcock, Christopher Holden, Zhiqiang Yang, Generating synthetic Landsat images based on all available Landsat data: Predicting Landsat surface reflectance at any given time <https://doi.org/10.1016/j.rse.2015.02.009>`_


    @param array: DataArray containing timestamped observations in the range [0,10000]
    @return:
    """

    time_coords = {c.name:c for c in array.coords.values() if c.dtype.type == np.datetime64}
    if len(time_coords) == 0:
        raise ValueError(f"Your input array does not have a time dimension {array}" )
    if len(time_coords) > 1:
        if not (time_dimension in time_coords):
            raise ValueError(f"Specified time dimension {time_dimension} does not exist, available dimensions: f{time_coords.keys()}")
    else:
        time_dimension = list(time_coords.keys())[0]



    dates = _extract_dates(array)
    dates_np = np.array([d.toordinal() for d in dates])
    dates_np = dates_np - dates_np[0]

    def callback(timeseries):
        timeseries_valid = timeseries[~np.isnan(timeseries)]
        models = lasso.fitted_model(dates_np, timeseries_valid, defaults['LASSO_MAX_ITER'], defaults['AVG_DAYS_YR'], num_coefficients)

        coeffs = [models.fitted_model.intercept_,*models.fitted_model.coef_[0:num_coefficients-1]]
        return np.array(coeffs)

    result = xarray.apply_ufunc(callback, array, input_core_dims=[[time_dimension]],
                                output_core_dims=[["bands"]], vectorize=True)

    # make sure to preserve dimension order
    return result
