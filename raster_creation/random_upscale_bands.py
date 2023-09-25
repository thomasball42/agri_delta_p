# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 10:41:50 2023

@author: tom
"""

try:
    import gdal
except ImportError:
    from osgeo import gdal
import numpy as np
import random
import subprocess
import shutil
import sys
import os

im_path = "rasters/gaez_hyde_/gaez_hyde_10k.tif"
working_path = "rasters/gaez_hyde_"
output_path = "rasters/gaez_hyde_"
target_res_im_path = "inputs/JUNG/iucn_habitatclassification_composite_lvl2_ver004.tif"


def progressStr(perc, tot_len):
    char = "#"
    progress = int(perc * 100 * (tot_len / 100))
    bar = char * progress
    blank = " " * (tot_len - progress)
    return f'[{bar+blank}] {round(perc * 100, 4)}%'

im = gdal.Open(im_path)
imX = im.RasterXSize
imY = im.RasterYSize
bandNames = [im.GetRasterBand(band + 1).GetDescription() \
             for band in range(im.RasterCount)]
imGeoTrans = im.GetGeoTransform()

tgt = gdal.Open(target_res_im_path)
targetGeoTrans = tgt.GetGeoTransform()

tRatio = round(imGeoTrans[1] / targetGeoTrans[1])

destX = imX * tRatio
destY = imY * tRatio
emptyName = os.path.join(working_path, os.path.split(im_path)[-1].split(".")[0] + str(tRatio) + "_empty")

driver = gdal.GetDriverByName('GTiff')
dst_ds = driver.Create(f"{emptyName}.tif", destX, destY, 1, gdal.GDT_Int32)
dst_ds.SetGeoTransform(targetGeoTrans)
dst_ds.SetProjection(im.GetProjection())
dst_ds.GetRasterBand(1).Fill(0)
dst_ds = None
outputBandVals = [1401, 1402] # : [crops, pasture]
destination = gdal.Open(f"{emptyName}.tif", gdal.GA_Update)
outBand = destination.GetRasterBand(1)
for y in range(imY):
    for x in range(imX):
        bandVals = im.ReadAsArray(x, y, 1, 1)
        # np.nan > 0 returns False, abusing this for now
        pixCountVals = [int(x * tRatio ** 2) if x > 0 else 0 for x in bandVals]
        newVals = [0] * (tRatio * tRatio)
        b = 0
        for bandInt, pixCount in enumerate(pixCountVals):
            for i in range(pixCount):
                if len(outputBandVals) > 0:
                    bName = outputBandVals[bandInt]
                else:
                    bName = bandInt+1
                newVals[b+i] = bName
            b += pixCount
        random.shuffle(newVals)
        newVals = np.array(newVals)
        newVals = newVals.reshape(tRatio, tRatio)
        outBand.WriteArray(newVals, x*tRatio, y*tRatio)
        perc = (y*imX + x) / (imX*imY)
        strOut = f'{progressStr(perc, 50)}\r'
        sys.stdout.write(strOut)
outBand.SetNoDataValue(0)
outBand = None
destination.SetGeoTransform(targetGeoTrans)
destination = None  
shutil.copyfile(f"{emptyName}.tif", os.path.join(output_path, f"{tRatio}X_{os.path.split(im_path)[-1].split(".")[0]}.tif"))
