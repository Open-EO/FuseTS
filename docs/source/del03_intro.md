# Introduction

This design definition file describes the design of the [FuseTS library](https://github.com/Open-EO/FuseTS),
and the web services derived from it. This library is developed in the frame of the ESA AI4Food project, and provides algorithms for
integrated timeseries of EO data, as well as timeseries analytics methods.

This design definition file is generated directly from the open source project documentation, which ensures that all
descriptions of modules and functions in this document are completely synchronized with the current state of the software.
As such, this design description is also open source, and thus also serves as a good source of information for potential
users or contributors.

(sec_ai4food)=
# AI4Food Design

[The design](fig-ai4food-design) gives an overview of the components involved in AI4Food. The main component is the FuseTS Python
library. The algorithms in this library can either be run locally on XArray datastructures, or run on openEO.

Through the openEO support, it is possible to combine FuseTS functionality with openEO predefined functions into new openEO
'user-defined processes'. These user-defined processes combine with openEO's data access and processing capacity, resulting
in 'on-demand web services'. These web services are not entirely new web service instances, but simply high level processes exposed
through the openEO API.

:::{figure-md} fig-ai4food-design

<img src="images/AI4Food_highlevel.drawio.png" alt="AI4Food_design" class="bg-primary mb-1" width="500px">

high level design
:::

Next to core algorithms and on-demand services, we also foresee the possibility to have a plugin library, allowing to
easily integrate other algorithms that are maintained outside of the core FuseTS repository.