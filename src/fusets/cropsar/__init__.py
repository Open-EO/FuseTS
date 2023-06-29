#
# Copyright (c) 2021-2023 VITO NV; Sinergise d.o.o.; University of Valencia, Spain;
#
# This file is licenced under “CC BY-NC-SA 4.0” – see `licenses/CC BY-NC-SA 4.0.md`
#


import sys
from openeo.udf import XarrayDataCube
from typing import Dict, Optional, List, Tuple, Union
import functools
import xarray
import numpy
import pandas
import threading
from pathlib import Path
from abc import ABC, abstractmethod


WINDOW_SIZE = 128
GAN_WINDOW_HALF = "80D"
ACQUISITION_STEPS = "5D"
GAN_STEPS = "5D"
GAN_SAMPLES = 32  # this is 2*gan_window_half/gan_steps + 1

NDVI = 'ndvi'
S2id = 'S2ndvi'
VHid = 'VH'
VVid = 'VV'
orbitdirections = ["ASCENDING", "DESCENDING"]

_threadlocal = threading.local()


class ModelWrapper(ABC):
    def __init__(
            self,
            window_size: int,
            samples: int,
            steps: str,
            model_path: str = None
    ):
        self.window_size = window_size
        self.samples = samples
        self.steps = steps
        self.model_path = Path(model_path) if model_path is not None else model_path

    @property
    @abstractmethod
    def s1_bands(self):
        pass

    @abstractmethod
    def prepare_s1(self, inarr: xarray.DataArray) -> xarray.DataArray:
        """
        Prepare the input data stack for the expected Sentinel-1 channels.

        :param inarr: entire input data stack, including both Sentinel-1 and Sentinel-2
        :return: modified data stack, including both Sentinel-1 and Sentinel-2
        """
        pass


    @abstractmethod
    def predict(
            self,
            s1: xarray.DataArray,
            s2: xarray.DataArray,
            prediction_buffer: xarray.DataArray,
            acquisition_dates: pandas.DatetimeIndex,
            inpaint_only: bool,
            output_mask: bool,
            drop_dates: list,
            nrt_mode: bool
    ):
        """
        Compute the CropSAR_px time series.

        :param s1: Sentinel-1 VV, VH input data
        :param s2: Sentinel-2 NDVI input data
        :param prediction_buffer: prediction result buffer
        :param acquisition_dates: acquisition date index for output
        """
        pass

    def get_s2_mask(
            self,
            s2: xarray.DataArray,
            acquisition_dates: pandas.DatetimeIndex,
            drop_dates: list
    ) -> Tuple[xarray.DataArray, xarray.DataArray]:
        """
        Get the Sentinel-2 mask for the provided input data and list of dropped dates.
        mask categories:
            0: no data
            1: data
            2: manually masked
            3: no prediction because all NaN input data

        :param s2: Sentinel-2 data
        :param acquisition_dates: acquisition dates
        :param drop_dates: list of dropped dates
        :returns: tuple of Sentinel-2 data and mask
        """
        s2_mask = (~numpy.isnan(s2)).astype(int)
        if drop_dates is not None:
            # add to mask
            s2_mask_inf = numpy.isinf(s2).astype(int)
            s2_mask += s2_mask_inf

            # put NaN for manually masked values before feeding data into the network
            s2 = xarray.where(s2 == numpy.inf, numpy.NaN, s2)

        return s2, s2_mask


class GANWrapper(ModelWrapper):
    s1_bands = [VVid, VHid]

    def __init__(self, window_size: int, samples: int, steps: str, model_path: str = None):
        super().__init__(
            window_size=window_size,
            samples=samples,
            steps=steps,
            model_path=model_path
        )
        self.scaler = Scaler()

    @functools.lru_cache()
    def get_model(self):
        return load_generator_model(self.model_path)

    def prepare_s1(self, inarr: xarray.DataArray) -> xarray.DataArray:
        if not all(band in inarr.bands for band in self.s1_bands):
            # combine ascending and descending Sentinel-1 data
            for band in self.s1_bands:
                inarr = xarray.concat([
                    inarr,
                    inarr.sel(
                        bands=f"{band}_{orbitdirections[0]}"
                    ).combine_first(
                        inarr.sel(bands=f"{band}_{orbitdirections[1]}")
                    ).expand_dims({"bands": [band]}, axis=1)], dim="bands")
                inarr = inarr.drop_sel(bands=[f"{band}_{orbitdirection}" for orbitdirection in orbitdirections])
        return inarr

    def predict(self, s1, s2, prediction_buffer, acquisition_dates, inpaint_only, output_mask, drop_dates, nrt_mode):
        # compute windows
        xsize, ysize = s2.x.shape[0], s2.y.shape[0]
        windowlist = [
            ((ix, ix + self.window_size), (iy, iy + self.window_size))
            for ix in range(0, s2.x.shape[0], self.window_size)
            for iy in range(0, ysize, self.window_size)
        ]

        for window in windowlist:
            window_slice = {
                'x': slice(window[0][0], window[0][1]),
                'y': slice(window[1][0], window[1][1]),
            }

            for date in acquisition_dates:
                time_slice = slice(
                    date - pandas.to_timedelta(self.steps) * self.samples / 2,
                    date + pandas.to_timedelta(self.steps) *
                    self.samples / 2 if not nrt_mode else date
                )
                result = self.predict_stack(
                    s1=s1.isel(window_slice).sel(t=time_slice),
                    s2=s2.isel(window_slice).sel(t=time_slice),
                    inpaint_only=inpaint_only,
                    output_mask=output_mask,
                    drop_dates=drop_dates
                ).astype(numpy.float32)
                prediction_buffer.loc[window_slice].loc[{'t': date}] = result

    def predict_stack(
            self,
            s1,
            s2,
            inpaint_only: bool = True,
            output_mask: bool = False,
            nodata: float = 0.,
            drop_dates: Optional[List] = None
    ):
        if _force_even_tsteps():
            if len(s1.t) % 2 == 1:
                s1 = s1[:-1]
                s2 = s2[:-1]

        s1 = s1.expand_dims(dim=['batch', 'channel'], axis=[0, -1])
        s2 = s2.expand_dims(dim=['batch', 'channel'], axis=[0, -1])

        s1_vh = s1.sel(bands=VHid)
        s1_vv = s1.sel(bands=VVid)
        # Get the center acquisition to inpaint
        s2_ndvi_center = s2.values[:, self.samples //
                                      2, ...].reshape((self.window_size, self.window_size)).copy()

        # Get a mask and the center NDVI
        # mask categories
        #   0: no data
        #   1: data
        #   2: manually masked
        #   3: no prediction because all NaN input data
        s2_mask_category = (~numpy.isnan(s2_ndvi_center)).astype(int)

        if drop_dates is not None:
            # add to mask
            s2_mask_inf = numpy.isinf(s2_ndvi_center).astype(int)
            s2_mask_category += s2_mask_inf
            # put NaN for manually masked values before feeding into the network
            s2 = xarray.where(s2 == numpy.inf, numpy.NaN, s2)
            s2_ndvi_center[s2_ndvi_center == numpy.inf] = numpy.NaN

        # simplify categories to binary mask
        s2_mask = (s2_mask_category == 1).astype(int)

        # Scale Sentinel-1
        s1_vv = self.scaler.minmaxscaler(s1_vv, VVid)
        s1_vh = self.scaler.minmaxscaler(s1_vh, VHid)

        # Concatenate Sentinel-1 data
        s1_backscatter = xarray.concat((s1_vv, s1_vh), dim='channel')

        # Scale NDVI
        s2_ndvi = self.scaler.minmaxscaler(s2, NDVI)

        # Remove any nan values
        # Passing in numpy arrays because reduces RAM usage
        # (newer tensorflows copy out from xarray into a numpy array)
        # and backwards compatibility goes further back in time
        s2_ndvi = s2_ndvi.fillna(nodata).values
        s1_backscatter = s1_backscatter.fillna(nodata).values

        # Run neural network
        predictions = self.get_model().predict((s1_backscatter, s2_ndvi))

        # Unscale
        predictions = self.scaler.minmaxunscaler(predictions, NDVI)
        pred_reshaped = predictions.reshape(
            (self.window_size, self.window_size))

        if inpaint_only:
            # Only predict masked regions
            # We want to avoid crisp borders
            # so first dilate the inverted mask
            s2_mask_nan = s2_mask.astype(float)
            s2_mask_inv_dilated = _dilate_mask(1 - s2_mask)

            # Put mask values to NaN
            s2_mask_nan[s2_mask_nan == 0] = numpy.nan
            s2_mask_inv_dilated[s2_mask_inv_dilated == 0] = numpy.nan

            # Stack original and predicted pixels
            # masked pixels become NaN
            stacked = numpy.stack(
                [s2_mask_nan * s2_ndvi_center,
                 s2_mask_inv_dilated * pred_reshaped],
                axis=-1)

            # By taking a nanmean, we take the mean
            # of the original and predicted values
            # in overlap regions of mask borders
            completed = numpy.nanmean(stacked, axis=-1)

            # completed = s2_mask * s2_ndvi_center + \
            #     (1 - s2_mask) * pred_reshaped
        else:
            # Return prediction for all pixels
            completed = pred_reshaped

        if output_mask:
            return numpy.stack([completed, s2_mask_category])
        else:
            return completed


class AttentionUnetWrapper(ModelWrapper):
    # s1_bands = [f"{VHid}_ASCENDING", f"{VHid}_DESCENDING", f"{VVid}_ASCENDING", f"{VVid}_DESCENDING"]
    s1_bands = [VHid, VVid]

    def predict(self, s1: xarray.DataArray, s2: xarray.DataArray, prediction_buffer: xarray.DataArray,
                acquisition_dates: pandas.DatetimeIndex, inpaint_only: bool, output_mask: bool, drop_dates: list,
                nrt_mode: bool):
        s1 = s1.rename({"bands": "channel"})
        s2 = s2.expand_dims(dim=['channel'], axis=[1])

        s2, mask = self.get_s2_mask(s2, acquisition_dates=acquisition_dates, drop_dates=drop_dates)
        if output_mask:
            prediction_buffer.loc[{'bands': 'mask'}] = mask.squeeze(axis=1)[s2.t.isin(acquisition_dates)]

        if nrt_mode:
            self.predict_nrt(s1=s1, s2=s2, prediction_buffer=prediction_buffer, acquisition_dates=acquisition_dates)
        else:
            from vito_cropsar.inference.predict_arbitrary_shape import main as predict_arbitrary_shape
            result = predict_arbitrary_shape(
                s2=s2.values,
                s1=s1.values,
                model=self.get_model()
            )
            prediction_buffer.loc[{'bands': 'NDVI'}] = result.squeeze(axis=1)[s2.t.isin(acquisition_dates)]

    def predict_nrt(
            self,
            s1: xarray.DataArray,
            s2: xarray.DataArray,
            prediction_buffer: xarray.DataArray,
            acquisition_dates: pandas.DatetimeIndex
    ):
        """
        Predict in NRT mode by looping over acquisition dates and placing them at the right-most position of the
        temporal interval for prediction.

        Very inefficient in comparison to the normal prediction, which predicts multiple acquisition dates at the
        same time. Only to be used for validation purposes!

        :param s1: Sentinel-1 input data
        :param s2: Sentinel-2 input data
        :param prediction_buffer: prediction result buffer
        :param acquisition_dates: acquisition dates
        """
        model = self.get_model()
        for date in acquisition_dates:
            # slice window with acquisition date on the right
            tslice = pandas.date_range(end=date, periods=GAN_SAMPLES, freq=date.freq)
            pred = model(s1=s1.reindex(t=tslice).values, s2=s2.reindex(t=tslice).values)
            prediction_buffer.loc[{'bands': 'NDVI', 't': date}] = pred.squeeze(axis=1)[-1]

    def prepare_s1(self, inarr: xarray.DataArray) -> xarray.DataArray:
        # take ASCENDING or DESCENDING, whichever has the most acquisitions
        if not all(band in inarr.bands for band in self.s1_bands):
            s1_0_bands = inarr.sel(bands=[f"{self.s1_bands[0]}_{orbitdirection}" for orbitdirection in orbitdirections])
            best_direction = s1_0_bands.isel(
                bands=s1_0_bands.count(dim=("x", "y", "t")).argmax()
            ).bands.values.item().split("_")[-1]

            for orbitdirection in orbitdirections:
                if orbitdirection == best_direction:
                    # rename to band without direction
                    for band in self.s1_bands:
                        inarr = xarray.concat(
                            [
                                inarr,
                                inarr.sel(
                                    bands=f"{band}_{orbitdirection}",
                                    drop=True
                                ).expand_dims({"bands": [band]}, axis=1)
                            ],
                            dim="bands"
                        )
                # remove band
                inarr = inarr.drop_sel(bands=[f"{band}_{orbitdirection}" for band in self.s1_bands])
        return inarr

    @functools.lru_cache()
    def get_model(self):
        # extra_deps = "/data/users/Public/caertss/CropSAR/wheels/unzipped/"
        # sys.path.append(extra_deps)
        if "naive" in str(self.model_path):
            from vito_cropsar.models import InpaintingNaive
            model = InpaintingNaive.load(self.model_path)
        elif "resunet3d" in str(self.model_path):
            from vito_cropsar.models import InpaintingResUNet3d
            model = InpaintingResUNet3d.load(self.model_path)
        elif "cnn_transformer" in str(self.model_path):
            from vito_cropsar.models import InpaintingCnnTransformer
            model = InpaintingCnnTransformer.load(self.model_path)
        else:
            raise Exception("Cannot find model type to load")

        return model

    def _generate_mask(self):
        pass


def load_generator_model(path: Optional[Union[Path, str]] = None):
    from cropsar_px.models.tensorflow.model import CropsarPixelModel

    # Keras/tensorflow models are not guaranteed to be threadsafe,
    # but by loading and storing the model once per thread we should
    # be able to safely eliminate loading at model predict time
    generator_model = getattr(_threadlocal, 'generator_model', None)
    if generator_model is None:
        generator_model = CropsarPixelModel(modelinputs={'S1': 2, 'S2': 1},
                                            windowsize=32,
                                            tslength=32).generator

        if path is None:
            try:
                import importlib.resources as pkg_resources
            except ImportError:
                import importlib_resources as pkg_resources

            with pkg_resources.path('cropsar_px.resources', 'cropsar_px_generator.h5') as path:
                generator_model.load_weights(path)
        else:
            generator_model.load_weights(path)

        # Store per thread
        _threadlocal.generator_model = generator_model

    return generator_model


@functools.lru_cache(maxsize=25)
def load_datafusion_model():
    return load_generator_model()


class Scaler:
    def minmaxscaler(self, data, source):
        ranges = {}
        ranges[NDVI] = [-0.08, 1]
        ranges[VVid] = [-20, -2]
        ranges[VHid] = [-33, -8]
        # Scale between -1 and 1
        datarescaled = 2 * \
                       (data - ranges[source][0]) / \
                       (ranges[source][1] - ranges[source][0]) - 1
        return datarescaled

    def minmaxunscaler(self, data, source):
        ranges = {}
        ranges[NDVI] = [-0.08, 1]
        ranges[VVid] = [-20, -2]
        ranges[VHid] = [-33, -8]
        # Unscale
        dataunscaled = 0.5 * \
                       (data + 1) * (ranges[source][1] -
                                     ranges[source][0]) + ranges[source][0]
        return dataunscaled


def multitemporal_mask(ndvicube):

    print('Running multitemporal masking ...')
    from cropsar_px.utils.masking import flaglocalminima

    timestamps = list(ndvicube.t.values)

    daily_daterange = pandas.date_range(
        timestamps[0],
        timestamps[-1] + pandas.Timedelta(days=1),
        freq='D').floor('D')
    ndvi_daily = ndvicube.reindex(t=daily_daterange,
                                  method='bfill', tolerance='1D')

    # ndvi_daily.values[:,50,25]

    # Run multitemporal dip detection
    # Need to do it in slices, to avoid memory issues
    step = 256
    for idx in numpy.r_[:ndvi_daily.values.shape[1]:step]:
        for idy in numpy.r_[:ndvi_daily.values.shape[2]:step]:

            ndvi_daily.values[
            :, idx:idx+step, idy:idy+step] = flaglocalminima(
                ndvi_daily.values[:, idx:idx+step, idy:idy+step],
                maxdip=0.01,
                maxdif=0.1,
                maxgap=60,
                maxpasses=5)

    # Subset on the original timestamps
    ndvi_cleaned = ndvi_daily.sel(t=timestamps,
                                  method='ffill',
                                  tolerance='1D')

    return ndvi_cleaned


def process(
        inarr: xarray.DataArray,
        startdate: str,
        enddate: str,
        output: str,
        gan_window_half: str = GAN_WINDOW_HALF,
        acquisition_steps: str = ACQUISITION_STEPS,
        gan_window_size: int = WINDOW_SIZE,
        gan_steps: str = GAN_STEPS,
        gan_samples: int = GAN_SAMPLES,
        model_path: str = None,
        inpaint_only: bool = True,
        output_mask: bool = False,
        nrt_mode: bool = False,
        drop_dates: Optional[list] = None,
        version: int = 2,
        path_extras: Optional[List[str]] = None,
        dump_inputs: Optional[str] = None
) -> xarray.DataArray:
    """
    Apply the CropSAR_px algorithm to the provided input data.

    :param inarr: input data (Sentinel-1 + Sentinel-2)
    :param startdate: requested start date
    :param enddate: requested end date
    :param gan_window_half: half GAN temporal window size
    :param acquisition_steps: acquisition interval in the output
    :param gan_window_size: GAN window size
    :param gan_steps: GAN steps
    :param gan_samples: number of GAN samples, this is 2*gan_window_half/gan_steps + 1
    :param model_path: path to custom GAN model file
    :param inpaint_only: keep actual NDVI acquisitions, only predict areas where there is no data
    :param output_mask: output the Sentinel-2 mask: 0 = no data, 1 = data
    :param nrt_mode: only use prior data for prediction
    :param drop_dates: drop Sentinel-2 acquisitions for provided dates
    :param version: version of the prediction model to use
    :param path_extras: dependencies to be added to the path
    :param dump_inputs: directory path to dump input stack
    """
    if path_extras is not None:
        sys.path = path_extras + sys.path

    if drop_dates is not None:
        # Drop Sentinel-2 acquisitions
        drop_dates = list(map(pandas.to_datetime, drop_dates))
        inarr.loc[dict(
            bands=S2id, t=[d for d in drop_dates if d in inarr.t])] = numpy.NaN

    # Run multitemporal mask
    inarr.loc[dict(bands=S2id)] = multitemporal_mask(inarr.sel(bands=S2id))

    input_date_index = pandas.date_range(
        pandas.to_datetime(startdate) - pandas.to_timedelta(gan_window_half),
        pandas.to_datetime(enddate) + pandas.to_timedelta(gan_window_half),
        freq=acquisition_steps
    )

    # compute acquisition dates for output
    acquisition_dates = pandas.date_range(
        pandas.to_datetime(startdate),
        pandas.to_datetime(enddate),
        freq=acquisition_steps
    )

    model_wrapper: ModelWrapper
    if version == 1:
        model_wrapper = GANWrapper(
            window_size=gan_window_size,
            samples=gan_samples,
            steps=gan_steps,
            model_path=model_path
        )
    elif version == 2:
        model_wrapper = AttentionUnetWrapper(
            window_size=gan_window_size,
            samples=gan_samples,
            steps=gan_steps,
            model_path=model_path
        )
    else:
        raise Exception(f"Version {version} is not supported.")

    inarr = model_wrapper.prepare_s1(inarr)

    if drop_dates is not None:
        # put manually masked values to infinity, so we can track it when resampling
        inarr.loc[dict(
            bands=S2id, t=[d for d in drop_dates if d in inarr.t])] = numpy.inf

    # Process Sentinel-1
    S1 = _process_s1(inarr.sel(bands=model_wrapper.s1_bands),
                     input_date_index, gan_steps)

    # Process Sentinel-2
    S2 = _process_s2(inarr.sel(bands=S2id), input_date_index, gan_steps)

    # check if we have enough data to do a prediction
    if numpy.isnan(S1).all() or numpy.isnan(S2).all():
        # don't do a prediction, because it will be based on no input data
        out = numpy.empty((inarr.x.shape[0], inarr.y.shape[0]))
        out[:] = numpy.NaN

        # expand bands dimension
        out = numpy.expand_dims(out, axis=0)

        if output_mask:
            mask = numpy.empty((inarr.x.shape[0], inarr.y.shape[0]))
            mask[:] = 3
            # out = numpy.stack([out, mask])
            out = numpy.insert(out, [1], mask, axis=0)

        # expand time dimension
        out = numpy.stack((out,) * len(acquisition_dates))

        return xarray.DataArray(
            out,
            dims=inarr.dims,
            coords={'bands': ["NDVI", "mask"] if output_mask else [
                "NDVI"], 't': acquisition_dates}
        )

    # result buffer
    xsize, ysize = inarr.x.shape[0], inarr.y.shape[0]
    bands = ["NDVI", "mask"] if output_mask else ["NDVI"]
    shape = [len(acquisition_dates), len(bands), 1, 1]
    shape[inarr.dims.index('x')] = xsize
    shape[inarr.dims.index('y')] = ysize
    predictions = xarray.DataArray(
        numpy.full(shape, numpy.nan, dtype=numpy.float32),
        dims=inarr.dims,
        coords={'bands': bands, 't': acquisition_dates}
    )

    if dump_inputs is not None:
        dump_inputs = Path(dump_inputs)
        dump_inputs.mkdir(parents=True, exist_ok=True)
        import tempfile
        dump_file = tempfile.NamedTemporaryFile(delete=False, dir=dump_inputs, suffix=".tif")

        import rioxarray  # needed for rio accessor

        # S2.transpose('t', 'y', 'x').rio.to_raster('/home/stijn/Downloads/test.tif')
        _tmp = S2.copy()
        # conversion for dates as band names
        _tmp['t'] = _tmp['t'].dt.strftime("%Y-%m-%d")
        _tmp.to_dataset(dim='t').transpose('y', 'x').rio.to_raster(dump_file.name)

    model_wrapper.predict(
        s1=S1,
        s2=S2,
        prediction_buffer=predictions,
        acquisition_dates=acquisition_dates,
        inpaint_only=inpaint_only,
        output_mask=output_mask,
        drop_dates=drop_dates,
        nrt_mode=nrt_mode
    )

    return predictions


def _process_s2(s2data: xarray.DataArray, output_index, gan_steps):
    '''Sentinel-2:
    - Make a resample object to 5-day resolution
    - Take the best image out of each group
    - Finally do the reindexing to the requested 5-day
        index and make sure we propagate values no more
        than 5 days (should there still be NaNs (?))
    '''
    def _take_best(group: xarray.DataArray):
        best_image = group.isel(t=group.notnull().sum(
            dim=[dim for dim in s2data.dims if dim != 't']).argmax())
        return best_image

    s2data_resampled = s2data.resample(
        t=gan_steps
    ).map(
        _take_best
    ).reindex(
        {'t': output_index}, method='ffill', tolerance=gan_steps
    )

    return s2data_resampled


def _process_s1(s1data: xarray.DataArray, output_index, gan_steps):
    '''Sentinel-1:
    - First transform to power values
    - then apply multitemporal speckle filter
    - then resample to every 5-days and average the obs
        in each window
    - next interpolate any missing values using linear
        interpolation
    - next do the reindexing to the requested 5-day index
        and make sure we propagate the values no more than
        5 days (should there still be NaNs (?))
    - finally re-introduce the decibels
    '''
    from cropsar_px.utils.speckle import multitemporal_speckle

    # To power values
    s1data = numpy.power(10, s1data / 10.)

    # Apply multitemporal speckle filter
    s1data.values = multitemporal_speckle(s1data.values)

    # Resample
    s1data_resampled = s1data.resample(
        t=gan_steps
    ).mean(
        skipna=True
    ).interpolate_na(
        dim='t', method='linear'
    ).reindex(
        {'t': output_index}, method='ffill', tolerance=gan_steps
    )

    # To dB
    s1data_resampled_db = 10 * numpy.log10(s1data_resampled)

    return s1data_resampled_db


def _force_even_tsteps():
    if GAN_SAMPLES % 2 == 0:
        return True
    else:
        return False


def _dilate_mask(mask, dilate_r=5):
    from skimage.morphology import selem, binary_dilation

    dilate_disk = selem.disk(dilate_r)
    dilated_mask = binary_dilation(mask, dilate_disk)

    return dilated_mask.astype(float)


def apply_datacube(cube: XarrayDataCube, context: Dict) -> XarrayDataCube:
    # extract xarray
    inarr = cube.get_array()
    # get predictions
    predictions = process(inarr, **context)
    # wrap predictions in an OpenEO datacube
    return XarrayDataCube(predictions)


def load_cropsar_px_udf() -> str:
    import os
    with open(os.path.realpath(__file__), 'r+') as f:
        return f.read()