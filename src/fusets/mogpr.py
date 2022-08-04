import itertools
from typing import List

import GPy
import numpy as np
import xarray
from xarray import DataArray,Dataset

from fusets._xarray_utils import _extract_dates


def mogpr(array:Dataset,variables:List[str]=None,  time_dimension="t"):
    """
    MOGPR (multi-output gaussia-process regression) integrates various timeseries into a single values. This allows to
    fill gaps based on other indicators that are correlated with each other.

    One example is combining an optical NDVI with a SAR based RVI to compute a gap-filled NDVI.

    Args:
        array: An input datacube having at least a temporal dimension over which the smoothing will be applied.
        variables: The list of variable names that should be included, or None to use all variables
        time_dimension: The name of the time dimension of this datacube. Only needs to be specified to resolve ambiguities.

    Returns: A gapfilled datacube.

    """

    dates = _extract_dates(array)

    dates_np = [d.toordinal() for d in dates]

    selected_values = [v.values for v in array.values() if variables is None or v.name in variables]

    out_mean, out_std, out_qflag, out_model = _MOGRP_GPY_retrieval(selected_values, [np.array(dates_np),np.array(dates_np)], master_ind=0, output_timevec=np.array(dates_np),
                                                                  nt=1)
    return out_mean



def _MOGRP_GPY_retrieval(data_in, time_in, master_ind, output_timevec, nt):
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
                K = GPy.kern.Matern32(1)
                LCM = GPy.util.multioutput.LCM(input_dim=1,
                                               num_outputs=noutputs,
                                               kernels_list=[K] * noutputs, W_rank=1)
                model = GPy.models.GPCoregionalizedRegression(Xtrain, Ytrain, kernel=LCM.copy())
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
                            out_mean[ind][:, None, x, y] = (Yp[:, None, 0] * Y_std_vec[ind] + Y_mean_vec[ind]) / nt
                            out_std[ind][:, None, x, y] = (Vp[:, None, 0] * Y_std_vec[ind]) / nt

                    else:
                        for ind in range(noutput_timeseries):
                            out_mean[ind][:, None, x, y] = out_mean[ind][:, None, x, y] + (Yp[:, None, 0] * Y_std_vec[ind] + Y_mean_vec[ind]) / nt
                            out_std[ind][:, None, x, y] = out_std[ind][:, None, x, y] + (Vp[:, None, 0] * Y_std_vec[ind]) / nt

                    del Yp, Vp

    return out_mean, out_std, out_qflag, out_model
