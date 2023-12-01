import io
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import requests
import xarray
from matplotlib.dates import DateFormatter

from fusets import whittaker

area = "rye"

rye_raw = xarray.load_dataset(
    io.BytesIO(
        requests.get(
            f"https://artifactory.vgt.vito.be/artifactory/testdata-public/fusets/b4_b8_vv_vh/{area}.nc", stream=True
        ).content
    )
)
rye_ndvi = (rye_raw.B08 - rye_raw.B04) / (rye_raw.B08 + rye_raw.B04)
rye_ndvi_gan = xarray.load_dataset(f"/home/driesj/python/FuseTS/tests/validation/{area}-ndvi-gan.nc")
mean_ndvi = rye_ndvi.mean(dim=("x", "y"))


ds = rye_raw
ds["RVI"] = (ds.VH + ds.VH) / (ds.VV + ds.VH)


rye_ndvi_mogpr = xarray.load_dataset(f"/home/driesj/python/FuseTS/tests/mogpr_{area}_full.nc")

middle_x = rye_ndvi.x.shape[0] // 2
middle_y = rye_ndvi.y.shape[0] // 2
middle_x_data = float(rye_ndvi.x[middle_x])
middle_y_data = float(rye_ndvi.y[middle_y])

rye_ndvi_gan = rye_ndvi_gan.where(rye_ndvi_gan.NDVI != 255)
mean_ndvi_gan = rye_ndvi_gan.isel(x=middle_x, y=middle_y).NDVI.astype(np.float) / 250.0 - 0.08

if rye_ndvi_mogpr is not None:
    mean_ndvi_mogpr = rye_ndvi_mogpr.NDVI.isel(x=0, y=0)
else:
    mean_ndvi_mogpr = None

basedir = Path("source") / "images"


def hide_axis_labels():
    ax = plt.gca()
    ax.axes.xaxis.set_ticklabels([])
    ax.axes.yaxis.set_ticklabels([])


def plot_whittaker(mean_ndvi):
    smooth100 = whittaker(mean_ndvi, smoothing_lambda=100)
    smooth10000 = whittaker(mean_ndvi, smoothing_lambda=10000)
    smooth_optim = whittaker(mean_ndvi, smoothing_lambda=[3.0, 3.8])

    date_range = slice("2017-01-01", "2021-01-01")
    plt.figure(figsize=(16, 6))
    plt.plot(rye_ndvi.t.sel(t=date_range), mean_ndvi.sel(t=date_range), "o", label="S2 NDVI")
    plt.plot(rye_ndvi.t.sel(t=date_range), smooth100.sel(t=date_range), "-", label="Whittaker S2 NDVI lambda=100")
    plt.plot(rye_ndvi.t.sel(t=date_range), smooth10000.sel(t=date_range), "-", label="Whittaker S2 NDVI lambda=10000")
    plt.plot(
        rye_ndvi.t.sel(t=date_range), smooth_optim.sel(t=date_range), "-", label="Whittaker S2 NDVI lambda optimized"
    )
    plt.ylabel("NDVI")
    plt.grid(True)
    plt.legend()

    plt.savefig(basedir / f"whittaker_{area}.svg", format="svg")
    plt.savefig(basedir / f"whittaker_{area}.png", format="png")


plot_whittaker(mean_ndvi)


def plot_comparison():
    smooth10000_pixel = whittaker(rye_ndvi, smoothing_lambda=1000).isel(x=middle_x, y=middle_y)

    plt.figure(figsize=(16, 6))
    date_range = slice("2017-01-01", "2020-01-01")
    plt.plot(
        rye_ndvi.sel(t=date_range).t, rye_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range), "o", label="S2 NDVI"
    )
    plt.plot(
        rye_ndvi.sel(t=date_range).t, smooth10000_pixel.sel(t=date_range), "-", label="Whittaker S2 NDVI lambda=10000"
    )
    plt.plot(
        mean_ndvi_gan.sel(t=date_range).t,
        mean_ndvi_gan.sel(t=date_range),
        "-",
        label="Sentinel 1/2 Integrated NDVI (GAN)",
    )
    if mean_ndvi_mogpr is not None:
        plt.plot(
            mean_ndvi_mogpr.sel(t=date_range).t,
            mean_ndvi_mogpr.sel(t=date_range),
            "-",
            label="Sentinel 1/2 Integrated NDVI (MOGPR)",
        )
    plt.ylabel("NDVI")
    plt.grid(True)
    plt.legend()
    plt.savefig(basedir / f"integrated_ndvi_{area}.svg", format="svg")
    plt.savefig(basedir / f"integrated_ndvi_{area}.png", format="png")


# plot_comparison()


def plot_comparison_zoom():
    smooth100_pixel = whittaker(rye_ndvi, smoothing_lambda=100).isel(x=middle_x, y=middle_y)
    smooth10000_pixel = whittaker(rye_ndvi, smoothing_lambda=1000).isel(x=middle_x, y=middle_y)

    plt.figure(figsize=(16, 6))
    date_range = slice("2018-04-01", "2018-07-01")
    plt.plot(
        rye_ndvi.sel(t=date_range).t, rye_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range), "o", label="S2 NDVI"
    )
    plt.plot(
        rye_ndvi.sel(t=date_range).t, smooth10000_pixel.sel(t=date_range), "-", label="Whittaker S2 NDVI lambda=1000"
    )
    plt.plot(rye_ndvi.sel(t=date_range).t, smooth100_pixel.sel(t=date_range), "-", label="Whittaker S2 NDVI lambda=100")
    plt.plot(
        mean_ndvi_gan.sel(t=date_range).t,
        mean_ndvi_gan.sel(t=date_range),
        "-",
        label="Sentinel 1/2 Integrated NDVI (GAN)",
    )

    plt.ylabel("NDVI")
    plt.grid(True)
    plt.legend()

    plt.savefig(basedir / f"integrated_ndvi_{area}_detail.png", format="png")


# plot_comparison_zoom()


def plot_artifacts():
    import xarray

    large_ds = xarray.open_dataset("/home/driesj/python/FuseTS/tests/validation/rape-ndvi-gan-large.nc")
    ((large_ds.NDVI / 250.0) - 0.08).isel(t=[2, 23, 33], x=slice(400, 600), y=slice(400, 600)).plot(
        vmin=0, vmax=1.0, cmap="RdYlGn", col="t", col_wrap=3
    )
    hide_axis_labels()
    # plt.savefig(basedir / f"gan_artifacts_{area}.svg", format="svg")
    plt.savefig(basedir / f"gan_artifacts_{area}.png", format="png")


# plot_artifacts()


def plot_ndvi_rise():
    import xarray

    large_ds = xarray.open_dataset("/home/driesj/python/FuseTS/tests/validation/rape-ndvi-gan-large.nc")
    ((large_ds.NDVI / 250.0) - 0.08).isel(t=[49, 50, 51], x=slice(200, 700), y=slice(200, 700)).plot(
        vmin=0, vmax=1.0, cmap="RdYlGn", col="t", col_wrap=3
    )
    hide_axis_labels()
    ax = plt.gca()
    ax.annotate(
        "Rye",
        xy=(middle_x_data, middle_y_data),
        xycoords="data",
        xytext=(0.8, 0.95),
        textcoords="axes fraction",
        arrowprops=dict(facecolor="black", shrink=0.05),
        horizontalalignment="right",
        verticalalignment="top",
    )

    # plt.savefig(basedir / f"gan_detail_{area}.svg", format="svg")
    plt.savefig(basedir / f"gan_detail_{area}.png", format="png")


# plot_ndvi_rise()


def plot_rye_dip():
    """
    Rye field has an interesting dip in ndvi in 2018 season
    Returns:

    """
    ((rye_ndvi)).dropna(dim="t", how="all").isel(t=slice(33, 39)).plot(
        vmin=0, vmax=1.0, cmap="RdYlGn", col="t", col_wrap=3
    )
    hide_axis_labels()
    plt.savefig(basedir / f"rye_dip.svg", format="svg")
    plt.savefig(basedir / f"rye_dip.png", format="png")


def plot_pipeline():
    rye_unmasked = xarray.load_dataset("/home/driesj/python/FuseTS/tests/validation/Rye_sentinel2_raw.nc")
    rye_unmasked_ndvi = (rye_unmasked.B08 - rye_unmasked.B04) / (rye_unmasked.B08 + rye_unmasked.B04)

    date_range = slice("2017-09-01", "2018-09-01")
    ymin = 0.0
    ymax = 0.9
    plt.figure()
    size = (3, 2)
    fig, ax = plt.subplots(figsize=size)
    ax.set_ylim([ymin, ymax])
    plt.plot(
        rye_ndvi.sel(t=date_range).t, rye_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range), "o", label="Masked NDVI"
    )
    plt.plot(
        rye_unmasked_ndvi.sel(t=date_range).t,
        rye_unmasked_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range),
        "-",
        label="Unmasked NDVI",
        linewidth="2",
    )

    date_form = DateFormatter("%m-%d")
    ax.xaxis.set_major_formatter(date_form)
    hide_axis_labels()

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.savefig(basedir / f"unmasked.svg", format="svg")
    plt.savefig(basedir / f"unmasked.png", format="png")

    plt.figure()
    fig, ax = plt.subplots(figsize=size)
    ax.set_ylim([ymin, ymax])
    ndvi_series = rye_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range).dropna(dim="t")
    plt.plot(ndvi_series.t, ndvi_series, "-", label="Masked NDVI", linewidth="2")
    plt.plot(
        rye_unmasked_ndvi.sel(t=date_range).t,
        rye_unmasked_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range),
        "o",
        label="Unmasked NDVI",
    )
    ax.xaxis.set_major_formatter(date_form)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    hide_axis_labels()
    plt.savefig(basedir / f"masked.svg", format="svg")
    plt.savefig(basedir / f"masked.png", format="png")

    smooth100 = whittaker(rye_ndvi, smoothing_lambda=100)
    plt.figure()
    fig, ax = plt.subplots(figsize=size)
    ax.set_ylim([ymin, ymax])
    plt.plot(
        rye_ndvi.sel(t=date_range).t, rye_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range), "o", label="Masked NDVI"
    )
    plt.plot(
        smooth100.sel(t=date_range).t,
        smooth100.isel(x=middle_x, y=middle_y).sel(t=date_range),
        "-",
        label="smooth NDVI",
        linewidth="2",
    )

    ax.xaxis.set_major_formatter(date_form)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    hide_axis_labels()
    plt.savefig(basedir / f"smooth.svg", format="svg")
    plt.savefig(basedir / f"smooth.png", format="png")

    plt.figure()
    fig, ax = plt.subplots(figsize=size)
    ax.set_ylim([ymin, ymax])
    plt.plot(
        rye_ndvi.sel(t=date_range).t, rye_ndvi.isel(x=middle_x, y=middle_y).sel(t=date_range), "o", label="Masked NDVI"
    )
    plt.plot(ds["RVI"].sel(t=date_range).t, ds["RVI"].isel(x=middle_x, y=middle_y).sel(t=date_range), ".", label="RVI")
    plt.plot(
        rye_ndvi_mogpr.NDVI.sel(t=date_range).t,
        rye_ndvi_mogpr.NDVI.isel(x=middle_x, y=middle_y).sel(t=date_range),
        "-",
        label="Fused NDVI",
        linewidth="2",
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    hide_axis_labels()
    plt.savefig(basedir / f"fusion.svg", format="svg")
    plt.savefig(basedir / f"fusion.png", format="png")

    plt.figure()

    fig, ax = plt.subplots(figsize=size)
    ax.set_ylim([ymin, ymax])
    plt.plot(
        rye_ndvi_mogpr.NDVI.sel(t=date_range).t,
        rye_ndvi_mogpr.NDVI.isel(x=middle_x, y=middle_y).sel(t=date_range),
        "-",
        label="Fused NDVI",
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    hide_axis_labels()
    plt.savefig(basedir / f"analytics.svg", format="svg")
    plt.savefig(basedir / f"analytics.png", format="png")


# plot_pipeline()
