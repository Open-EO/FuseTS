# Whittaker

## Description

Whittaker represents a computationally efficient reconstruction method for smoothing and gap-filling of time series.
The main function takes as input two vectors of the same length: the y time series data (e.g. NDVI) and the
corresponding temporal vector (date format) x, comprised between the start and end dates of a satellite image
collection. Missing or null values as well as the cloud-masked values (i.e. NaN), are handled by introducing a
vector of 0-1 weights w, with wi = 0 for missing observations and wi=1 otherwise. Following, the Whittaker smoother
is applied to the time series profiles, computing therefore a daily smoothing interpolation.

Whittaker's fast processing speed was assessed through an initial performance testing by comparing different
time series fitting methods. Average runtime takes 0.0107 seconds to process a single NDVI temporal profile.

The smoother performance can be adjusted by tuning the lambda parameter, which penalizes the time series roughness:
the larger lambda the smoother the time series at the cost of the fit to the data getting worse. We found a lambda of
10000 adequate for obtaining more convenient results. A more detailed description of the algorithm can be
found in the original work of Eilers 2003.



