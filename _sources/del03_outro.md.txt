# On-demand Services Design

In AI4Food WP5, functionality of the FuseTS library will be exposed as higher-level
services on top of the openEO platform. This enables the use of FuseTS 'as a service', without
requiring users to install the library or even have Python (or programmnig) knowledge.
It also gives users access to a version that is kept up to date by the platform.

The selection of functionality to expose needs to be made when there is a more clear view
on the accuracy, performance and relevancy of various methods. It is advisable to choose
5 to 10 services that are offered with sufficient quality rather than trying to expose
and maintain a high volume of services at a lower quality level.

Some examples of potential services to expose:

- Sentinel-2 based integrated biophysical parameters (`fAPAR`, `fCover`, `NDVI`)
- A phenometrics service based on integrated parameters
- A peak-valley detection service based on integrated parameters

These services can be parametrized, for instance to work on different sensor inputs, or
biophysical parameters. It should be noted however that this also increases the number of
options to validate, which can be a time consuming task. Exposing an unvalidated parameter is
possible, but then requires very clear warnings in the service documentation, which are unfortunately
often ignored or forgotten by users of the service.

## OpenEO User-defined Processes

The main concept to expose services is by using [openEO UDPs](https://api.openeo.org/#tag/User-Defined-Processes). Because this library is open source,
we can expose a catalog of UDP's as public links in the Github repository. This gives any backend
or tool access to the definitions of the UDP. It should only be noted that a backend also either
needs to install the FuseTS library and its dependencies in the UDF runtime environment, or
provide a way to load these dynamically.

The creation of this public catalog can be done via the [Python API](https://open-eo.github.io/openeo-python-client/udp.html). More details and
an example can be found in the API documentation of this library.

Once a UDP is defined, and uploaded, the openEO web editor can be used to visualize it. This can serve
as a very basic interface for the on demand service. With some UI work to generic openEO components, this
experience can still be improved.

The Python API can also be used to invoke the service, without requiring a local installation of the
FuseTS library:

```{eval-rst}
.. code-block::
   :caption: Executing on demand service using the Python API
   
    cube = connection.datacube_from_process(
        "MOGPR",
        namespace="FuseTS",
    )
    cube.execute_batch(out_format="GTIFF")
```


It is important to mention one limitation: an openEO user-defined process always consists of a single process
graph, that generates the complete result in one invocation. The number of services that can be built in this
way is growing with the capabilities of openEO and the backend implementations, but sometimes there are still
workflows that require multiple openEO invocations, are more complex preprocessing of inputs.

To work around this limitation, we refer to the Euro Data Cube functionality that allows exposing arbitrary
[Python code as a service](https://eurodatacube.com/documentation/offer_algorithms_for_on_demand_data_generation).

This approach is very complementary to the openEO user-defined processes. Having both options available ensures
that we can expose any on-demand service.


## Discoverable Services in EOplaza

The UDP catalog on Github, or published in a given openEO backend, is not easy to discover by users.
To achieve that, we will additionally publish these services on the EOplaza marketplace.
The EOplaza is integrated with EGI Checkin, making it accessible for existing openEO users.

[This](https://portal.terrascope.be/catalogue/app-details/23) is an example phenology service, based on  a proprietary library.


The services are published on a marketplace to make them discoverable by users, and to document them.
Good documentation is important for operational services, and describes functionality, usage limitations,
expected accuracy, usage, and a cost estimate.

Another side-effect of publishing the services is the inclusion of a remuneration model that allows a 'value-added'
cost to be associated with the use of a service.

The Terrascope marketplace uses ‘maturity levels’ to classify services. This allows users to also share
services that are not yet operational. Services can define an ‘added value’ cost, but only if they achieve
a sufficiently high maturity level.

For mature services, we require automated testing. This typically needs to be set up by the service publisher. For services maintained by VITO, a continuous integration system verifies the functioning of the service whenever changes are made. We should be able to reuse this framework for the on-demand services in AI4FOOD project.


# Planned functionality & next steps

This section describes the modules and functionality that did not yet make it into this milestone, but is still planned
for inclusion in the library. This planning is open for discussion.

- Extend unit and integration tests
- Benchmarks tests
- Performance improvments for the core integration algorithms.
- Refactor all algorithms to work with the estimators framework (extend BaseEstimator)
- [Multi temporal outlier filter](https://github.com/Open-EO/FuseTS/issues/61)
- [Documentation for working with original Sentinel-2 products](https://github.com/Open-EO/FuseTS/issues/59)

