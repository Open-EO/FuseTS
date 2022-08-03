import numpy as np

import xarray


from fusets._xarray_utils import _extract_dates, _time_dimension


def ccdc_change_detection(array: xarray.DataArray):
    """
    CCDC change detection.
    This implementation works on generic timeseries, not on raw Landsat data like the original version.
    Therefore, it assumes clear (cloud/shadow free) observations.

    `Zhe Zhu, Curtis E. Woodcock, Christopher Holden, Zhiqiang Yang, Generating synthetic Landsat images based on all available Landsat data: Predicting Landsat surface reflectance at any given time <https://doi.org/10.1016/j.rse.2015.02.009>`_

    :param: array:
    :return: the break days
    """

    import ccd.models as models

    def _filter_saturated(observations):
        """
        bool index for unsaturated obserervations between 0..10,000

        Useful for efficiently filtering noisy-data from arrays.

        Arguments:
            observations: spectra nd-array, assumed to be shaped as
                (6,n-moments) of unscaled data.

        Returns:
            1-d bool ndarray

        """
        unsaturated = ((0 < observations[0]) & (observations[0] < 10000))
        return unsaturated

    def _results_to_changemodel(fitted_models, start_day, end_day, break_day,
                                magnitudes, observation_count, change_probability,
                                curve_qa):
        """
        Helper method to consolidate results into a concise, self documenting data
        structure.

        This also converts any specific package types used during processing to
        standard python types to help with downstream processing.

        {start_day: int,
         end_day: int,
         break_day: int,
         observation_count: int,
         change_probability: float,
         curve_qa: int,
         blue:  {magnitude: float,
                 rmse: float,
                 coefficients: (float, float, ...),
                 intercept: float},
         etc...

        Returns:
            dict

        """
        spectral_models = []
        for ix, model in enumerate(fitted_models):
            spectral = {'rmse': float(model.rmse),
                        'coefficients': tuple(float(c) for c in
                                              model.fitted_model.coef_),
                        'intercept': float(model.fitted_model.intercept_),
                        'magnitude': float(magnitudes[ix])}
            spectral_models.append(spectral)

        return {'start_day': int(start_day),
                'end_day': int(end_day),
                'break_day': int(break_day),
                'observation_count': int(observation_count),
                'change_probability': float(change_probability),
                'curve_qa': int(curve_qa),
                'blue': spectral_models[0]
                }


    from ccd import app
    from ccd import procedures
    from ccd.models import lasso
    procedures.results_to_changemodel = _results_to_changemodel
    procedures.qa.filter_saturated = _filter_saturated

    time_dimension = _time_dimension(array, None)

    dates = _extract_dates(array)
    dates_np = np.array([d.toordinal() for d in dates])
    dates_np = dates_np - dates_np[0]


    def callback(timeseries):
        timeseries_valid = timeseries[~np.isnan(timeseries)]

        quality = np.ones(shape=(timeseries_valid.shape[0],))
        proc_params = app.get_default_params()
        thermal = np.full(shape=(timeseries_valid.shape[0],),fill_value=2731.5+10.0)#10 degrees kelvin, scaled
        proc_params.THERMAL_IDX=1 # index of thermal band, which we add ourselves
        proc_params.TMASK_BANDS=[0]#bands used for outlier detection
        proc_params.DETECTION_BANDS=[0]#index locations of the spectral bands that are used to determine stability

        results, processing_mask = procedures.standard_procedure(dates_np,np.array([timeseries_valid,thermal]),lasso.fitted_model,quality,None,proc_params)


        return np.array([r['break_day'] for r in results])

    result = xarray.apply_ufunc(callback, array, input_core_dims=[[time_dimension]],
                                output_core_dims=[["bands"]], vectorize=True)

    # make sure to preserve dimension order
    return result


def fit_harmonics_curve(array: xarray.DataArray, num_coefficients=6, time_dimension=None):
    """
    Fit a timeseries model based on fourier harmonics as proposed by CCDC.
    This method expects inputs in the [0,10000] range!

    `Zhe Zhu, Curtis E. Woodcock, Christopher Holden, Zhiqiang Yang, Generating synthetic Landsat images based on all available Landsat data: Predicting Landsat surface reflectance at any given time <https://doi.org/10.1016/j.rse.2015.02.009>`_

    :param array: DataArray containing timestamped observations in the range [0,10000]
    :param num_coefficients:
    :param time_dimension:
    :return:
    """

    from ccd.models import lasso
    from ccd.parameters import defaults

    time_dimension = _time_dimension(array, time_dimension)

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


