import openeo

connection = openeo.connect("openeo.vito.be").authenticate_oidc()

spat_ext = {
    "type": "Polygon",
    "coordinates": [
        [
            [
                5.170012098271149,
                51.25062964728295
            ],
            [
                5.17085904378298,
                51.24882567194015
            ],
            [
                5.17857421368097,
                51.2468515482926
            ],
            [
                5.178972704726344,
                51.24982704376254
            ],
            [
                5.170012098271149,
                51.25062964728295
            ]
        ]
    ]
}
temp_ext = ["2023-01-01","2023-01-31"]

smoothing_lambda = 100

base = connection.load_collection('SENTINEL2_L2A_SENTINELHUB',
                                  spatial_extent=spat_ext,
                                  temporal_extent=temp_ext,
                                  bands=["B04","B08","SCL"])
base_cloudmasked = base.process("mask_scl_dilation", data=base, scl_band_name="SCL")
base_ndvi = base_cloudmasked.ndvi(red="B04", nir="B08")

whittaker = connection.datacube_from_process('whittaker', namespace='https://openeo.vito.be/openeo/1.1/processes/u:bramjanssen', data=base_ndvi, smoothing_lambda=smoothing_lambda)

whittaker.download('result.json', format="json")
