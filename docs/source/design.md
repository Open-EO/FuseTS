# FuseTS design

Core FuseTS algorithms are based on the [Pangeo software stack](https://pangeo.io/architecture.html#software), to maximize
interoperability with other Python libraries. More specifically, XArray Data sets and arrays are used as input and output
types throughout the library.

FuseTS consist of multiple logical modules:

- Core timeseries integration
- Timeseries analysis
- OpenEO integration


## Data cubes

Conceptually, the FuseTS library mainly works on data cubes. The openEO standard provides [a good description](https://openeo.org/documentation/1.0/datacubes.html)
of this concept in our context. When running locally, FuseTS will use XArray to represent and work on such an in-memory data cube. 

The main data object used by this library is an [Xarray DataSet](https://docs.xarray.dev/en/latest/generated/xarray.Dataset.html).
This is a self-describing data structure that combines the raw array data with metadata that describes it. This section
further documents some of the conventions that are used when working with earth observation datasets.

For building these conventions, we rely on these sources:
- https://docs.openeo.cloud/federation/backends/collections.html#bands
- https://github.com/awesome-spectral-indices/awesome-spectral-indices#expressions

The 'bands' dimension in our EO data cubes is represented by variables in the XArray dataset. This allows us to
conveniently reference them by name. Certain algorithms may expect variables with a specific name to be available, or for
the variable name to be specified. Other algorithms simply process all of the variables in dataset in the same manner.

### Dimensions

In the earth observation domain, we can standardize on a few dimensions. The FuseTS library assumes that variables share
spatiotemporal dimensions. Multiple space or time dimensions are not supported unless otherwise noted.

| Name | Description                   | Units                                               |
|------|-------------------------------|-----------------------------------------------------|
| time | The temporal dimension        | Datetime objects as numpy.datetime64                |
| x    | East-West spatial dimension   | Units of spatial reference system (meters/degrees)  |
| y    | South-North spatial dimension | Units of spatial reference system (meters/degrees)  |

When a datacube has x and y dimensions, these are assumed to be evenly spaced. The time dimension can be irregular.
Instead of regular spatial dimensions, a cube axis can also have geometries as labels. In this case, the datacube is 
assumed to contain timeseries sampled at point locations or for instance aggregated over a geometry.

An algorithm may require a specific combination of dimensions and variables to be available. 







