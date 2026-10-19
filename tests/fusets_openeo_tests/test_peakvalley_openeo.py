def test_peakvalley_openeo_udf(wetland_sentinel2_ndvi):
    from fusets import peakvalley

    result = peakvalley(wetland_sentinel2_ndvi)

    result.execute_batch(
        "peakvalley.nc",
        out_format="netCDF",
        title="Peak-Valley test",
        description="Testing fusets peak-valley",
        job_options={
            "udf-dependency-archives": [
                "https://auxdata.terrascope.be/openeo/FuseTS/fusets_venv.zip#tmp/venv",
                "https://auxdata.terrascope.be/openeo/FuseTS/fusets.zip#tmp/venv_static",
            ]
        },
    )
