from shapely.geometry import mapping, box

import openeo


def test_predict_ndvi_openeo_udp(areas,auth_connection):
    bbox = areas['wetland']
    from fusets.openeo import predict_ndvi
    cube = predict_ndvi(mapping(box(*bbox)),temporal_extent=("2020-01-01","2021-01-01"),openeo_connection=auth_connection)
    print(cube.metadata)
    cube.execute_batch("ndvi_gan_wetland.nc",title="FuseTS_test_predict_ndvi_openeo_udp")