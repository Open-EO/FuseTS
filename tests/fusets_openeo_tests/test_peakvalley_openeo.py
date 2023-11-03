

def test_peakvalley_openeo_udf(wetland_sentinel2_ndvi):

    from fusets import peakvalley

    result = peakvalley(wetland_sentinel2_ndvi)

    result.execute_batch("peakvalley.nc",out_format="netCDF",title="Peak-Valley test",description="Testing fusets peak-valley")
