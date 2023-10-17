import rasterio
import numpy as np

jung_path = "/maps/tsb42/bd_opp_cost/v2/raster_creation/inputs/JUNG/iucn_habitatclassification_composite_lvl2_ver004.tif"
output_path = "rasters/no_agri_/no_agri_93m.tif"

#crops, pasture, plantation
rm_list = [1401, 1402, 1403]
nodat_val = 0

with rasterio.open(jung_path) as raster:
    transform = raster.transform
    crs = raster.crs
    data = raster.read(1)
    data = np.where(np.isin(data, np.array(rm_list)), data, 0)
    raster.close()
    rasters = None

with rasterio.open(
    output_path, "w", driver="GTiff", height=data.shape[0],
    width=data.shape[1], 
    count=1,  # Number of bands
    dtype=data.dtype,
    crs=crs, transform=transform
) as dst:
    # Write the arrays to the bands
    dst.write(data, indexes=1)

