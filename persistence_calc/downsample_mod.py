from math import ceil, floor
import sys
import os

import numpy as np
from yirgacheffe.layers import RasterLayer, PixelScale

from osgeo import gdal

gdal.SetCacheMax(1024 * 1024 * 16)

overwrite = False
target_scale = PixelScale(0.083333333333333, -0.083333333333333)
quiet = False

try:
    source = RasterLayer.layer_from_file(sys.argv[1])
    target_name = sys.argv[2]  # pylint: disable=C0103
except IndexError:
    print(f"Usage: {sys.argv[0]} [SRC] [DEST]", file=sys.stderr)
    sys.exit(1)

if os.path.isfile(target_name) and overwrite == False:
    if quiet:
        qmsg = ""
    else:
        qmsg = f"Output file exists ({sys.argv[2]}), skipping.."
    quit(qmsg)

target = RasterLayer.empty_raster_layer(
    area=source.area,
    scale=target_scale,
    datatype=source.datatype,
    filename=target_name,
    projection=source.projection
)

pixels_per_x = source.window.xsize / target.window.xsize
pixels_per_y = source.window.ysize / target.window.ysize

for y in range(target.window.ysize):
    # read all the pixels that will overlap with this row from source
    low_y = floor(y * pixels_per_y)
    high_y = ceil((y+1) * pixels_per_y)

    band_height = high_y - low_y
    band = source.read_array(0, low_y, source.window.xsize, high_y - low_y)

    dest = np.zeros((1, target.window.xsize))
    
    for x in range(target.window.xsize):

        low_x = floor(x * pixels_per_x)
        high_x = ceil((x+1) * pixels_per_x)

        def calc_total(low_x, high_x):
            
            total = np.sum(band[1:band_height - 1, low_x+1:high_x - 1])

            # Work out the scaling factors for the sides
            first_y = float(low_y + 1) - (y * pixels_per_y)
            assert 0.0 <= first_y <= 1.0
            last_y = ((y + 1) * pixels_per_y) - float(high_y - 1)
            assert 0.0 <= last_y <= 1.0
            first_x = float(low_x + 1) - (x * pixels_per_x)
            assert 0.0 <= first_x <= 1.0
            try:
                last_x = ((x + 1) * pixels_per_x) - float(high_x - 1)
                assert 0.0 <= last_x <= 1.0
            except AssertionError:
                last_x = 1
                assert 0.0 <= last_x <= 1.0

            # major sides
            total += np.sum(band[1:band_height - 1, low_x:low_x+1]) * first_y
            total += np.sum(band[1:band_height - 1, high_x - 2:high_x - 1]) * last_y
            total += np.sum(band[0][low_x+1:high_x - 1]) * first_x
            total += np.sum(band[band_height - 1][low_x + 1:high_x - 1]) * last_x

            # corners
            total += band[0][low_x] * first_x * first_y
            total += band[band_height - 1][low_x] * first_x * last_y
            total += band[0][high_x - 1] * last_x * first_y
            total += band[band_height - 1][high_x - 1] * last_x * last_y
            return total
        
        try: 
            total = calc_total(low_x, high_x)
        except IndexError:
            total = calc_total(low_x, floor((x+1) * pixels_per_x))

        dest[0][x] = total

    target._dataset.GetRasterBand(1).WriteArray(dest, 0, y) # pylint: disable=W0212

before = source.sum()
after = target.sum()

print(f"before: {before}")
print(f"after:  {after}")
print(f"diff:  {((after - before)/before) * 100.0}") 
