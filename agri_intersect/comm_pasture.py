import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import numpy as np
import os
import geopandas as gpd
import pandas as pd

countries_shapefile_path = os.path.join("inputs", "vectors", "natural_earth_vector.gpkg")
livestock_paths = {
    # "bvmeat" : "inputs/livestock/warped/bvmeat_proportion_grazing.tif",
    # "bvmilk" : "inputs/livestock/warped/bvmilk_proportion_grazing.tif",
    # "sgmeat" : "inputs/livestock/warped/sgmeat_proportion_grazing.tif",
    "bvmeat" : "inputs/livestock/GLW4/Cattle.tif",
    "bvmilk" : "inputs/livestock/GLW4/Cattle.tif",
    "sgmeat" : "inputs/livestock/GLW4/Sheep.tif",
    # "chickens"   : "inputs/livestock/GLW4/ch/5_Ch_2015_Da.tif",
    # "ducks"      : "inputs/livestock/GLW4/du/5_Dk_2015_Da.tif",
    # "pigs"       : "inputs/livestock/GLW4/pi/5_Pg_2015_Da.tif",
    }

def get_pixel_areas(dataset):
    # Calculate the area of each pixel in km2
    latitudes = np.linspace(dataset.bounds.bottom, 
                            dataset.bounds.top, 
                            dataset.height)
    R = 6371
    y0 = R * np.sin(np.deg2rad(dataset.res[0]))
    ydist = R * (np.sin(np.deg2rad(abs(latitudes))) \
                 - np.sin(np.deg2rad(abs(latitudes) - dataset.res[0])))
    # This assumes uniform longitude values
    return ydist * y0


shapefile = os.path.join("inputs", "vectors", "natural_earth_vector.gpkg")
countries = gpd.read_file(shapefile, layer = "ne_50m_admin_0_countries")

for ls, ls_path in livestock_paths.items():
    with rasterio.open(ls_path) as dataset:
        data = dataset.read(1)
        shape = dataset.shape
        transform = from_bounds(*dataset.bounds, dataset.width, dataset.height)
        pixel_areas_km2 = (np.full(shape = shape, fill_value=1).T * get_pixel_areas(dataset)).T
        dataset.close()
        dataset = None
    break

country_rasts = rasterize(
    ((geom, value) for geom, value in zip(countries.geometry, countries.index)),
    out_shape=shape,
    transform=transform,
    dtype=int,
    all_touched=True,
    fill=-99
)

df = pd.DataFrame(columns = ["Country_ISO", "livestock", "density_h_km2","pixel_area_km2"])
for country_id in range(countries.shape[0]):
    
    country_iso = countries.ISO_A3.loc[country_id]
    country_mask = country_rasts == country_id
    print(f"Processing {country_iso}, {round(country_id/countries.shape[0], 4)}...")
    for ls, ls_path in livestock_paths.items():
        with rasterio.open(ls_path) as dataset:
            data = dataset.read(1)
            shape = dataset.shape
            transform = from_bounds(*dataset.bounds, dataset.width, dataset.height)
            dataset.close()
            dataset = None
        
        masked_data = np.where(country_mask, data, 0)
        masked_pix = np.where(masked_data > 0, pixel_areas_km2, 0)
        dfx_dat = masked_data[masked_data > 0].flatten()
        pix_dat = masked_pix[masked_pix > 0].flatten()
        print(pix_dat.shape, dfx_dat.shape)
        dfx = pd.DataFrame({"Country_ISO":[country_iso]*len(dfx_dat),
                            "livestock":[ls]*len(dfx_dat),
                            "density_h_km2":dfx_dat,
                            "pixel_area_km2":pix_dat})
        df = pd.concat([df,dfx])

df.to_csv("livestock_densities.csv")
        
        
        