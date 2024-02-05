from pathlib import Path

from openeo.metadata import CollectionMetadata


def apply_metadata(metadata: CollectionMetadata, context: dict) -> CollectionMetadata:
    raise Exception(metadata)
    extra_bands = [Band(f"{x}_STD", None, None) for x in metadata.bands]
    for band in extra_bands:
        metadata = metadata.append_band(band)
    return metadata


def load_mogpr_bands_udf() -> str:
    """
    Loads an openEO udf that applies mogpr.
    @return:
    """
    import os

    return Path(os.path.realpath(__file__)).read_text()
