"""
Thomas Ball, 7th Aug 2023
"""

import rasterio
import numpy as np
import sys
import os

gaez_path = "inputs/GLCSv11_02_5m.tif"
hyde_path = "inputs/grazing2017AD.asc"
disaggCutoff = 0.95
output_path = "rasters/gaez_hyde_/gaez_hyde_10k.tif"
pnv_path = ""

def pixel_areas(dataset):
    latitudes = np.linspace(dataset.bounds.bottom, dataset.bounds.top, dataset.height)
    R = 6371137 # metres
    y0 = R * np.sin(np.deg2rad(dataset.res[0]))
    ydist = R * (np.sin(np.deg2rad(abs(latitudes))) - np.sin(np.deg2rad(abs(latitudes) - dataset.res[0])))
    return ydist * y0

# load stuff and create pixelAreas
with rasterio.open(gaez_path) as dataset:
    transform = dataset.transform
    crs = dataset.crs
    gaez_ = dataset.read(1)
    dataset.close()
    dataset = None

with rasterio.open(hyde_path) as dataset:
    oneD_pixelAreasM2 = pixel_areas(dataset)
    hyde_ = dataset.read(1) # km2
    pixelAreasM2 = np.full(hyde_.shape, 0)
    pixelAreasM2[:,:] = oneD_pixelAreasM2.reshape((oneD_pixelAreasM2.shape[0], 1))
    dataset.close()
    dataset = None

# convert gaez and hyde to portion of pixel
hyde_ = hyde_ * (1000000) / pixelAreasM2 # to m2 then div by pixelArea
hyde_[hyde_ < 0] = 0 # no-data are -999; set these to zero 
gaez_ = gaez_ / 100 # percentage

# where gaez and hyde disagree (sum greater than disagg cutoff), scale down
totAgri = gaez_ + hyde_
# calculate ag-perc scalars
totAgri[gaez_ + hyde_ >= disaggCutoff] = disaggCutoff - (1/np.exp(2*totAgri[gaez_ + hyde_ >= disaggCutoff]))
# calcualte final vals
gaezRatio = np.divide(gaez_, gaez_ + hyde_, out = np.zeros_like(gaez_), where = gaez_ + hyde_ > 0)
gaezVals = totAgri * gaezRatio 
hydeRatio = np.divide(hyde_, gaez_ + hyde_, out = np.zeros_like(gaez_), where = gaez_ + hyde_ > 0)
hydeVals = totAgri * hydeRatio 

with rasterio.open(
    output_path, "w", driver="GTiff", height=gaezVals.shape[0],
    width=gaezVals.shape[1], 
    count=2,  # Number of bands
    dtype=gaezVals.dtype,
    crs=crs, transform=transform,
    tags = {"BandName":["crop", "past"]}
) as dst:
    # Write the arrays to the bands
    dst.write(gaezVals, indexes=1)
    dst.write(hydeVals, indexes=2)

