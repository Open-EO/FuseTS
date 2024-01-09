def test_whittaker_openeo_udf(wetland_sentinel2_ndvi):
    from fusets import whittaker

    result = whittaker(wetland_sentinel2_ndvi, smoothing_lambda=100)

    result.execute_batch(
        "smoothed_wetland.nc",
        out_format="netCDF",
        title="Whittaker test",
        description="Testing fusets whitakker smoothing",
    )
