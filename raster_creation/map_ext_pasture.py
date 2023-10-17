import rasterio
from rasterio.windows import Window
import numpy as np
import os
import sys

pnv_path = "/maps/tsb42/bd_opp_cost/v2/raster_creation/rasters/jung_processed/pnv_lvl1_004_93m_400752_200376.tif"
cur_path = "/maps/tsb42/bd_opp_cost/v2/raster_creation/inputs/JUNG/iucn_habitatclassification_composite_lvl2_ver004.tif"

t_out_folder = "rasters/open_past_/past_exc_parts"

cattl_path = "rasters/open_past_/cattle_400752_200376.tif"

# where jungPNV is open habitat AND jungCurr is pasture OR stocking density < 0.1 / ha, 
# replace jungCurr with the open hab, everything else zeroes

open_ls = [200, # savannah
           300, # shrubland
           400, # grassland
           800] # desert

chunks = 16
num_d = 4

try:
    offs = int(sys.argv[1]) - 1
except IndexError:
    offs = 0

for c in range(int(chunks / num_d)):
    c = c + (num_d*offs)
    print(f"Processing chunk: {c}")
    with rasterio.open(pnv_path) as dataset:
        height, width = dataset.shape
        chunk_width = width / chunks
        chunk_height = height
        window = Window.from_slices((0, chunk_height), (c*chunk_width, (c+1)*chunk_width))
        transform = dataset.window_transform(window)
        crs = dataset.crs
        print(f"Reading {pnv_path}")
        pnv_ = dataset.read(1, window = window)
        dataset.close()
        dataset = None
    pnv_open_ls = np.where(np.isin(pnv_, np.array(open_ls)), pnv_, 0)
    del pnv_
    with rasterio.open(cur_path) as dataset:
        print(f"Reading {cur_path}")
        cur_ = dataset.read(1, window = window)
        dataset.close()
        dataset = None
    cur_past = np.where(cur_ == 1402, 1402, 0).astype(bool)
    del cur_
    with rasterio.open(cattl_path) as dataset:
        print(f"Reading {cattl_path}")
        cattl_ = dataset.read(1, window = window)
        cattl_[cattl_ < 0] = 0
        dataset.close()
        dataset = None
    cattl_ha = (cattl_ / 100) # to per hectare
    del cattl_
    cattl_ld = np.where(cattl_ha <= 0.5, True, False)
    del cattl_ha
    ext_past = np.where(cur_past & cattl_ld, pnv_open_ls, 0)
    del cattl_ld, pnv_open_ls

    print(np.count_nonzero(ext_past), np.count_nonzero(cur_past))

    chunk_file = os.path.join(t_out_folder, f'chunk_{c}.tif')
    with rasterio.open(
        chunk_file, "w", driver="GTiff", 
        height=ext_past.shape[0], width=ext_past.shape[1], 
        count=1,  # Number of bands
        dtype=ext_past.dtype,
        crs=crs, transform=transform,
        window = window,
        compress = "lzw"
    ) as dst:
        dst.write(ext_past, indexes=1)


