import openeo
from fusets.openeo import load_cubes


def test_merging(auth_connection):

    bbox = (5.039291, 51.166858, 5.243225, 51.319455)
    data = auth_connection.load_collection("SENTINEL2_L2A",bands=["B02","B03","B04"])
    data = data.process("mask_scl_dilation", data=data)
    data_S1_asc = auth_connection.load_collection("SENTINEL1_GRD").resample_cube_spatial(data)
    cube = data.merge_cubes(data_S1_asc).filter_bbox(bbox=bbox)


    spec = {
        "collections": {
            "SENTINEL2_L2A": {"bands":["B02","B03","B04"],"mask_scl_dilation":{}},
            "SENTINEL1_GRD": {}
        },
        "spatial_extent": [5.039291,51.166858,5.243225,51.319455]
    }
    cube2 = load_cubes(**spec, openeo_connection=auth_connection)
    assert cube.graph == cube2.graph

