from pathlib import Path

import numpy as np
import xarray,io, requests
import matplotlib.pyplot as plt
from fusets import whittaker

rye_ndvi = xarray.load_dataset(io.BytesIO(requests.get("https://artifactory.vgt.vito.be/testdata-public/fusets/rye_ndvi.nc",stream=True).content))
rye_ndvi_gan = xarray.load_dataset("/home/driesj/python/FuseTS/tests/validation/Rye-ndvi-gan.nc")
mean_ndvi = rye_ndvi['var'].mean(dim=('x','y'))

rye_ndvi_mogpr = xarray.load_dataset("/home/driesj/python/FuseTS/tests/mogpr_rye.nc")

middle_x = rye_ndvi.x.shape[0] //2
middle_y = rye_ndvi.y.shape[0] //2

rye_ndvi_gan = rye_ndvi_gan.where(rye_ndvi_gan.NDVI != 255)
mean_ndvi_gan = rye_ndvi_gan.isel(x=middle_x,y=middle_y).NDVI.astype(np.float) /250.0 - 0.08
mean_ndvi_mogpr = rye_ndvi_mogpr.NDVI.isel(x=middle_x,y=middle_y)

smooth100 = whittaker(mean_ndvi,smoothing_lambda=100)
smooth10000 = whittaker(mean_ndvi,smoothing_lambda=10000)
smooth_optim = whittaker(mean_ndvi,smoothing_lambda=[3.0,3.8])

plt.figure(figsize= (16,6))
plt.plot(rye_ndvi.t, mean_ndvi, 'o', label='S2 NDVI')
plt.plot(rye_ndvi.t, smooth100, '-', label='Whittaker S2 NDVI lambda=100')
plt.plot(rye_ndvi.t, smooth10000, '-', label='Whittaker S2 NDVI lambda=10000')
plt.plot(rye_ndvi.t, smooth_optim, '-', label='Whittaker S2 NDVI lambda optimized')
plt.ylabel ('NDVI')
plt.grid(True)
plt.legend()

basedir = Path("source") / "images"
plt.savefig(basedir/"whittaker.svg",format="svg")
plt.savefig(basedir/"whittaker.png",format="png")


smooth10000_pixel = whittaker(rye_ndvi['var'],smoothing_lambda=1000).isel(x=middle_x,y=middle_y)

plt.figure(figsize= (16,6))
date_range = slice('2017-01-01', '2020-01-01')
plt.plot(rye_ndvi.sel(t =date_range).t, rye_ndvi['var'].isel(x=middle_x, y=middle_y).sel(t =date_range), 'o', label='S2 NDVI')
plt.plot(rye_ndvi.sel(t =date_range).t, smooth10000_pixel.sel(t =date_range), '-', label='Whittaker S2 NDVI lambda=10000')
plt.plot(mean_ndvi_gan.sel(t =date_range).t, mean_ndvi_gan.sel(t =date_range), '-', label='Sentinel 1/2 Integrated NDVI (GAN)')
plt.plot(mean_ndvi_mogpr.sel(t =date_range).t, mean_ndvi_mogpr.sel(t =date_range), '-', label='Sentinel 1/2 Integrated NDVI (MOGPR)')
plt.ylabel ('NDVI')
plt.grid(True)
plt.legend()
plt.savefig(basedir/"integrated_ndvi.svg",format="svg")
plt.savefig(basedir/"integrated_ndvi.png",format="png")



