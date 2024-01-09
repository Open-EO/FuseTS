import io

import pytest
import requests
import xarray
from numpy.testing import assert_allclose

from fusets.ccdc import ccdc_change_detection, fit_harmonics_curve
from fusets.whittaker import whittaker


def test_fit_harmonics():
    ds = xarray.load_dataset(
        io.BytesIO(
            requests.get(
                "https://artifactory.vgt.vito.be/artifactory/testdata-public/malawi_sentinel2.nc", stream=True
            ).content
        )
    )
    some_index = (ds.B04 - ds.B02) / (ds.B04 + ds.B02)
    print(some_index)
    smoothed_output = whittaker(some_index)

    # fitting harmonics doesn't support nan
    coefficients = fit_harmonics_curve(10000 * smoothed_output)
    print(coefficients)

    # out_set = xarray.Dataset({"index":smoothed_output.assign_attrs(grid_mapping="crs"),"crs":ds.crs},attrs=dict(Conventions="CF-1.8"))
    # out_set.to_netcdf("malawi_smooth.nc")


def test_fit_simple_harmonics_exact(harmonic_timeseries):
    coefficients = fit_harmonics_curve(harmonic_timeseries, num_coefficients=4)
    assert_allclose(coefficients, [5000, 5, 600, 200], atol=3)


@pytest.mark.skip(reason="See https://github.com/Open-EO/FuseTS/issues/84#issuecomment-1600702434")
def test_ccdc_change_detection(harmonic_timeseries):
    breaks = ccdc_change_detection(harmonic_timeseries)
    print(breaks)
