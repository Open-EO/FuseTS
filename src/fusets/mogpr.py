'''
The methodology is based on the great work of Luca Pipia´s (et al) paper
Link: https://doi.org/10.1016/j.rse.2019.111452
'''

import importlib
import itertools
from datetime import datetime
from typing import List, Union

import numpy as np
import pandas as pd
import xarray
from xarray import Dataset

from fusets._xarray_utils import _extract_dates, _time_dimension
from fusets.base import BaseEstimator

_openeo_exists = importlib.util.find_spec("openeo") is not None
if _openeo_exists:
    from openeo import DataCube


class MOGPRTransformer(BaseEstimator):
    """
    
    MOGPR (multi-output gaussia-process regression) integrates various timeseries and delivers the same amount of reconstructed timeseries. This allows to
    fill gaps based on other indicators that are correlated with each other.
    
    """

    def __init__(self) -> None:
        self.model = None

    def fit(self, X, y=None, **fit_params):
        ds = X
        for pos_x in range(4):  # len(ds.coords['x'].values)
            for pos_y in range(4):  # len(ds.coords['y'].values)

                master_ind = 0
                nt = 1
                day_step = 15

                time = []
                data = []
                time_str = []
                var_names = []

                for d in ds:
                    y = ds[d][:, pos_y, pos_x].values
                    x = ds[d]['t'].values

                    time_vec_num = np.asarray([pd.Timestamp(_).to_pydatetime().toordinal() for _ in x],
                                              dtype=np.float64)
                    time.append(time_vec_num)
                    data.append(y)
                    var_names.append(d)

                time_vec_min = np.min(list(pd.core.common.flatten(time)))
                time_vec_max = np.max(list(pd.core.common.flatten(time)))
                output_timevec = np.array(range(int(time_vec_min), int(time_vec_max), 5), dtype=np.float64)
                output_time = [datetime.fromordinal(int(_)) for _ in output_timevec]

                out_mean, out_std, out_qflag, out_model = mogpr_1D(data[:], time[:], master_ind, output_timevec, nt)
                if out_model is not None:
                    print(out_model)
                    self.model = out_model
                    return

    def transform(self, X):
        array = X
        ds = array
        variables = None
        time_dimension = 't'

        output = []

        for pos_x in range(len(ds.coords['x'].values)):
            for pos_y in range(len(ds.coords['y'].values)):

                master_ind = 0
                nt = 1
                day_step = 15

                time = []
                data = []
                time_str = []
                var_names = []

                for d in ds:
                    y = ds[d][:, pos_y, pos_x].values
                    x = ds[d]['t'].values

                    time_vec_num = np.asarray([pd.Timestamp(_).to_pydatetime().toordinal() for _ in x],
                                              dtype=np.float64)
                    time.append(time_vec_num)
                    data.append(y)
                    var_names.append(d)

                time_vec_min = np.min(list(pd.core.common.flatten(time)))
                time_vec_max = np.max(list(pd.core.common.flatten(time)))
                output_timevec = np.array(range(int(time_vec_min), int(time_vec_max), 5), dtype=np.float64)
                output_time = [datetime.fromordinal(int(_)) for _ in output_timevec]

                out_mean, out_std, out_qflag, out_model = mogpr_1D(data[:], time[:], master_ind, output_timevec, nt,
                                                                   trained_model=self.model)

                output.append(out_mean)
        array_x_y_ds_t = np.array(output).reshape((len(ds.coords['x'].values), len(ds.coords['y'].values), len(ds), -1))
        array_ds_t_x_y = np.moveaxis(np.moveaxis(array_x_y_ds_t, 0, -1), 0, -1)

        # TODO rudimentary dataset construction, needs to be better

        vars = {}
        c = 0
        for var in ds:
            vars[var] = (('t', 'x', 'y'), array_ds_t_x_y[c])
            c = c + 1

        out_ds = xarray.Dataset(data_vars=vars, coords=dict(
            x=ds.x,
            y=ds.y,
            t=output_time,

        ))
        return out_ds

    def fit_transform(self, X: Union[Dataset, DataCube], y=None, **fit_params):
        if _openeo_exists and isinstance(X, DataCube):
            from .openeo import mogpr as mogpr_openeo
            return mogpr_openeo(X)

        return mogpr(X)


def mogpr(array: Dataset, variables: List[str] = None, time_dimension="t") -> xarray.Dataset:
    """
    MOGPR (multi-output gaussian-process regression) integrates various timeseries into a single values. This allows to
    fill gaps based on other indicators that are correlated with each other.

    One example is combining an optical NDVI with a SAR based RVI to compute a gap-filled NDVI.

    Args:
        array: An input datacube having at least a temporal dimension over which the smoothing will be applied.
        variables: The list of variable names that should be included, or None to use all variables
        time_dimension: The name of the time dimension of this datacube. Only needs to be specified to resolve ambiguities.

    Returns: A gapfilled datacube.

    """

    dates = _extract_dates(array)
    time_dimension = _time_dimension(array, time_dimension)
    output_time_dimension = 't_new'

    dates_np = [d.toordinal() for d in dates]

    if isinstance(array, xarray.Dataset):
        selected_values = [v.values for v in array.values() if variables is None or v.name in variables]
    else:
        selected_values = [array]

    tstep = 5
    time_vec_min = np.min(dates_np)
    time_vec_max = np.max(dates_np)
    output_timevec = np.array(range(int(time_vec_min), int(time_vec_max), tstep), dtype=np.float64)
    output_time = [datetime.fromordinal(int(_)) for _ in output_timevec]

    if len(output_time) == 0:
        raise Exception('The result does not contain any output times, please select a larger range')

    def callback(timeseries):
        out_mean, out_std, out_qflag, out_model = mogpr_1D(timeseries, list([np.array(dates_np) for i in timeseries]),
                                                           0, output_timevec=output_timevec, nt=1, trained_model=None)
        result = np.array(out_mean)
        return result

    # setting vectorize to true is convenient, but has performance similar to for loop
    result = xarray.apply_ufunc(callback, array.to_array(dim="variable"),
                                input_core_dims=[["variable", time_dimension]],
                                output_core_dims=[["variable", output_time_dimension]], vectorize=True)

    result = result.assign_coords({output_time_dimension: output_time})
    result = result.rename({output_time_dimension: time_dimension, "variable": "bands"})

    return result.to_dataset(dim="bands")


def _MOGPR_GPY_retrieval(data_in, time_in, master_ind, output_timevec, nt):
    """
    Function performing the multioutput gaussian-process regression at pixel level for gapfilling purposes

    Args:
        data_in (array): 3D (2DSpace, Time) array containing data to be processed
        time_in (array): vector containing the dates of each layer in the time dimension
        master_ind (int): Index identifying the Master output
        output_timevec (array) :vector containing the dates on which output must be estimated
        nt [int]: # of time the GP training must be performed (def=1)
    Returns:
        a tuple
        (out_mean, out_std, out_qflag, out_model) where:

        - out_mean (array): 3D (2DSpace, Time) mean value of the prediction at pixel level
        - out_std (array): 3D (2DSpace, Time) standard deviation  of the prediction at pixel level
        - out_qflag (array): 2D map of Quality Flag for any numerical error in the model determination
        - out_model (list): Matrix-like structure containing the model information at pixel level
    """
    from GPy.kern import Matern32
    from GPy.util.multioutput import LCM
    from GPy.models import GPCoregionalizedRegression

    noutput_timeseries = len(data_in)

    x_size = data_in[0].shape[1]
    y_size = data_in[0].shape[2]
    imout_sz = (output_timevec.shape[0], x_size, y_size)

    Xtest = output_timevec.reshape(output_timevec.shape[0], 1)
    out_qflag = np.ones((x_size, y_size), dtype=bool)
    out_mean = []
    out_std = []
    out_model = [[0] * y_size for _ in range(x_size)]

    for _ in range(noutput_timeseries):
        out_mean.append(np.full(imout_sz, np.nan))
        out_std.append(np.full(imout_sz, np.nan))

    for x, y in itertools.product(range(x_size), range(y_size)):

        X_vec = []
        Y_vec = []
        Y_mean_vec = []
        Y_std_vec = []

        for ind in range(noutput_timeseries):
            X_tmp = time_in[ind]
            Y_tmp = data_in[ind][:, x, y]
            X_tmp = X_tmp[~np.isnan(Y_tmp), np.newaxis]
            Y_tmp = Y_tmp[~np.isnan(Y_tmp), np.newaxis]
            X_vec.append(X_tmp)
            Y_vec.append(Y_tmp)
            del X_tmp, Y_tmp

        if np.size(Y_vec[master_ind]) > 0:

            # Data Normalization
            for ind in range(noutput_timeseries):
                Y_mean_vec.append(np.mean(Y_vec[ind]))
                Y_std_vec.append(np.std(Y_vec[ind]))
                Y_vec[ind] = (Y_vec[ind] - Y_mean_vec[ind]) / Y_std_vec[ind]

            # Multi-output train and test sets
            Xtrain = X_vec
            Ytrain = Y_vec

            nsamples, npixels = Xtest.shape
            noutputs = len(Ytrain)

            for i_test in range(nt):
                Yp = np.zeros((nsamples, noutputs))
                Vp = np.zeros((nsamples, noutputs))
                K = Matern32(1)
                LCM = LCM(input_dim=1,
                          num_outputs=noutputs,
                          kernels_list=[K] * noutputs, W_rank=1)
                model = GPCoregionalizedRegression(Xtrain, Ytrain, kernel=LCM.copy())
                if not np.isnan(Ytrain[1]).all():

                    try:
                        # if trained_model is None:
                        model.optimize()
                        list_tmp = [model.param_array]

                        for _ in range(noutput_timeseries):
                            list_tmp.append(eval('model.sum.ICM' + str(_) + '.B.B'))
                        out_model[x][y] = list_tmp


                    except:
                        out_qflag[x, y] = False
                        continue

                    for out in range(noutputs):
                        newX = Xtest.copy()

                        newX = np.hstack([newX, out * np.ones((newX.shape[0], 1))])
                        noise_dict = {'output_index': newX[:, -1:].astype(int)}
                        Yp[:, None, out], Vp[:, None, out] = model.predict(newX, Y_metadata=noise_dict)

                    if i_test == 0:

                        for ind in range(noutput_timeseries):
                            out_mean[ind][:, None, x, y] = (Yp[:, None, ind] * Y_std_vec[ind] + Y_mean_vec[ind]) / nt
                            out_std[ind][:, None, x, y] = (Vp[:, None, ind] * Y_std_vec[ind]) / nt

                    else:
                        for ind in range(noutput_timeseries):
                            out_mean[ind][:, None, x, y] = out_mean[ind][:, None, x, y] + (
                                    Yp[:, None, ind] * Y_std_vec[ind] + Y_mean_vec[ind]) / nt
                            out_std[ind][:, None, x, y] = out_std[ind][:, None, x, y] + (
                                    Vp[:, None, ind] * Y_std_vec[ind]) / nt

                    del Yp, Vp

    return out_mean, out_std, out_qflag, out_model


def mogpr_1D(data_in, time_in, master_ind, output_timevec, nt, trained_model=None):
    """
    Function performing the multioutput gaussian-process regression at pixel level for gapfilling purposes
    
    Args:
        data_in (list): List of numpy 1D arrays containing data to be processed
        time_in (list): List of numpy 1D arrays containing the (ordinal)dates of each variable in the time dimension
        master_ind (int): Index identifying the Master output
        output_timevec (array) : Vector containing the dates on which output must be estimated
        nt [int]: # of times the GP training must be performed (def=1)
    Returns:
        a tuple
        (out_mean, out_std, out_qflag, out_model) where:
        - out_mean_list (array): List of numpy 1D arrays containing mean value of the prediction at pixel level
        - out_std_list (array): List of numpy 1D arrays containing standard deviation of the prediction at pixel level
        - out_qflag (bool): Quality Flag for any numerical error in the model determination
        - out_model (Object): Gaussian Process model for heteroscedastic multioutput regression
    """
    from GPy.kern import Matern32
    from GPy.util.multioutput import LCM
    from GPy.models import GPCoregionalizedRegression

    # Number of outputs
    noutputs = len(data_in)
    # Number of output samples
    outputs_len = output_timevec.shape[0]

    out_mean = []
    out_std = []
    out_model = []

    X_vec = []
    Y_vec = []
    Y_mean_vec = []
    Y_std_vec = []

    out_qflag = True

    # Variable is initialized to take into account possibility of no valid pixels present
    for ind in range(noutputs):
        out_mean.append(np.full(outputs_len, np.nan))
        out_std.append(np.full(outputs_len, np.nan))

        X_tmp = time_in[ind]
        Y_tmp = data_in[ind]
        X_tmp = X_tmp[~np.isnan(Y_tmp), np.newaxis]
        Y_tmp = Y_tmp[~np.isnan(Y_tmp), np.newaxis]
        X_vec.append(X_tmp)
        Y_vec.append(Y_tmp)
        del X_tmp, Y_tmp

        # Data Normalization        
        Y_mean_vec.append(np.mean(Y_vec[ind]))
        Y_std_vec.append(np.std(Y_vec[ind]))
        Y_vec[ind] = (Y_vec[ind] - Y_mean_vec[ind]) / Y_std_vec[ind]

    if np.size(Y_vec[master_ind]) > 0:
        # Multi-output train and test sets
        Xtrain = X_vec
        Ytrain = Y_vec

        Yp = np.zeros((outputs_len, noutputs))
        Vp = np.zeros((outputs_len, noutputs))

        for i_test in range(nt):
            try:
                # Kernel
                K = Matern32(input_dim=1)
                # Linear Coregionalization
                LCM = LCM(input_dim=1, num_outputs=noutputs, kernels_list=[K] * noutputs, W_rank=1)
                if trained_model is None:
                    # Linear coregionalization                    
                    out_model = GPCoregionalizedRegression(Xtrain, Ytrain, kernel=LCM.copy())
                    out_model.optimize()
                else:
                    # Extract hyperparams
                    l = trained_model['.*ICM.*lengthscale'][0]
                    v = trained_model['.*ICM.*var'][0]
                    k = trained_model['.*ICM.*B.kappa'].values
                    w = trained_model['.*ICM.*B.W'].values

                    out_model = GPCoregionalizedRegression(Xtrain, Ytrain, kernel=LCM.copy())

                    # Fix hyperparams
                    out_model['.*ICM.*len'].constrain_fixed(l)
                    out_model['.*ICM.*var'].constrain_fixed(v)
                    out_model['.*ICM.*B.kappa'].constrain_fixed(k)
                    out_model['.*ICM.*B.W'].constrain_fixed(w)

                    out_model.optimize()

            except:
                out_qflag = False
                continue

            for out in range(noutputs):
                newX = output_timevec[:, np.newaxis]
                newX = np.hstack([newX, out * np.ones((newX.shape[0], 1))])

                noise_dict = {'output_index': newX[:, -1:].astype(int)}
                # Prediction
                Yp[:, None, out], Vp[:, None, out] = out_model.predict(newX, Y_metadata=noise_dict)

                if i_test == 0:
                    out_mean[out][:, None] = (Yp[:, None, out] * Y_std_vec[out] + Y_mean_vec[out]) / nt
                    out_std[out][:, None] = (Vp[:, None, out] * Y_std_vec[out]) / nt
                else:
                    out_mean[out][:, None] = out_mean[out][:, None] + (
                            Yp[:, None, out] * Y_std_vec[out] + Y_mean_vec[out]) / nt
                    out_std[out][:, None] = out_std[out][:, None] + (Vp[:, None, out] * Y_std_vec[out]) / nt

            del Yp, Vp

    # Flatten the series    
    out_mean_list = []
    out_std_list = []

    for ind in range(noutputs):
        out_mean_list.append(out_mean[ind].ravel())
        out_std_list.append(out_std[ind].ravel())

    return out_mean_list, out_std_list, out_qflag, out_model
