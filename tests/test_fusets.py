import fusets


def test_init():
    # dummy test
    assert fusets.__version__
    assert not hasattr(fusets, "mogpr")
    assert not hasattr(fusets, "MOGPRTransformer")
