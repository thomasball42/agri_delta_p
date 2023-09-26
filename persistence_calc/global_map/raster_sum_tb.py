import os
import rasterio
import sys
import numpy as np

target_dir = sys.argv[1]
output_path = sys.argv[2]

left = -180
right = 180
top = 90
bottom = -90
width = 4320
height = 2160

arr = np.zeros(shape=(height,width))
bounds = rasterio.coords.BoundingBox(left=left,right=right,top=top,bottom=bottom)
transform = rasterio.transform.from_bounds(*bounds, width, height)

f = []
for path, subdirs, files in os.walk(target_dir):
    for name in files:
        f.append(os.path.join(path, name))
f = [file for file in f if ".tif" in file]
f = [file for file in f if "RESIDENT" in file]


for fx, file in enumerate(f):
    rast = rasterio.open(file)
    crs = rast.crs
    window = rasterio.windows.from_bounds(*bounds, transform=rast.transform)
    dat = rast.read(1, window = window, boundless = True)
    dat[dat < 0] = 0
    arr = arr + dat
    dat = None
    print(" " * 40,end = "\r")
    print(f"Summing rasters; {round(fx / len(f), 4)}",end = "\r")

with rasterio.open(
    output_path, "w", driver="GTiff", height=height,
    width=width, 
    count=1,  # Number of bands
    dtype=np.float32,
    crs=crs, transform=transform,
) as dst:
    # Write the arrays to the bands
    dst.write(arr, indexes=1)
