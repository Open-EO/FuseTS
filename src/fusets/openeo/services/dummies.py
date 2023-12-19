from openeo.rest.datacube import DataCube


class DummyConnection:
    def load_collection(self, *args, **kwargs) -> DataCube:
        return DataCube.load_collection(*args, connection=self, fetch_metadata=False, **kwargs)
