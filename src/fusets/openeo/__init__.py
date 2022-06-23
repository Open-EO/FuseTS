
from openeo.rest.datacube import DataCube
from whittaker_udf import load_whittakker_udf

def whittaker(datacube :DataCube, smoothing_lambda :float):
    """

    @param datacube:
    @param smoothing_lambda:
    @return:
    """

    return datacube.apply_dimension(code= load_whittakker_udf(),context=dict(smoothing_lambda=smoothing_lambda))