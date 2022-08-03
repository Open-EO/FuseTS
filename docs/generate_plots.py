from pathlib import Path

import xarray,io, requests
import matplotlib.pyplot as plt
from fusets import whittaker

rye_ndvi = xarray.load_dataset(io.BytesIO(requests.get("https://artifactory.vgt.vito.be/testdata-public/fusets/rye_ndvi.nc",stream=True).content))

mean_ndvi = rye_ndvi['var'].mean(dim=('x','y'))
smooth100 = whittaker(mean_ndvi,smoothing_lambda=100)
smooth10000 = whittaker(mean_ndvi,smoothing_lambda=10000)

plt.figure(figsize= (16,6))
plt.plot(rye_ndvi.t, mean_ndvi, 'o', label='S2 NDVI')
plt.plot(rye_ndvi.t, smooth100, '-', label='Whittaker S2 NDVI lambda=100')
plt.plot(rye_ndvi.t, smooth10000, '-', label='Whittaker S2 NDVI lambda=10000')
plt.ylabel ('NDVI')
plt.grid(True)
plt.legend()

basedir = Path("source") / "images"
plt.savefig(basedir/"whittaker.svg",format="svg")





