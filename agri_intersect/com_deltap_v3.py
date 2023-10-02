import numpy as np
from numpy import inf
import pandas as pd
import os
import sys

import rasterio
import geopandas as gpd
from rasterio.features import rasterize
from rasterio.transform import from_bounds

overwrite = False

data_raster = "inputs/deltap_all_species.tif"
crop_tgt_dir = "inputs/crops/har/"
anim_tgt_dir = "inputs"
gh_path = "inputs/gaez_hyde_10k.tif"

output_path = "outputs"
outfile = os.path.split(crop_tgt_dir)[-1].split(".")[0] + "country_opp_cost_v2" + ".csv"

livestock_paths = {"bvmeat" : "inputs/livestock/warped/bvmeat_proportion_grazing.tif",
                   "bvmilk" : "inputs/livestock/warped/bvmilk_proportion_grazing.tif",
                   "sgmeat" : "inputs/livestock/warped/sgmeat_proportion_grazing.tif",
                #    "bvmeat" : "inputs/livestock/GLW4/Cattle.tif",
                #    "bvmilk" : "inputs/livestock/GLW4/Cattle.tif",
                #    "sgmeat" : "inputs/livestock/GLW4/Sheep.tif",
                   "chickens"   : "inputs/livestock/GLW4/ch/5_Ch_2015_Da.tif",
                   "ducks"      : "inputs/livestock/GLW4/du/5_Dk_2015_Da.tif",
                   "pigs"       : "inputs/livestock/GLW4/pi/5_Pg_2015_Da.tif",
                   }

nperrs = np.seterr(all='ignore')

# load gh raster and process (sum crops + pasture)
gh = rasterio.open(gh_path)
gh_c = gh.read(1)
gh_p = gh.read(2)
c = np.ma.masked_array(gh_c, np.isnan(gh_c))
p = np.ma.masked_array(gh_p, np.isnan(gh_p))
gh_a = c + p

# load data raster (deltap)
dataset = rasterio.open(data_raster)
ds_values = dataset.read(1)

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
pixel_areas_km2 = get_pixel_areas(dataset)

def weighted_mean_err(countries, weight_vals, indata):
    arr_means, arr_errs = [],[]
    weight_vals[weight_vals < 0] = 0
    for country_id in range(countries.shape[0]):
        country_mask = country_rasts == country_id
        combi_mask = (weight_vals != 0) * country_mask
        wmasked = weight_vals * combi_mask.astype(int)
        if wmasked.sum() == 0:
            arr_means.append(np.nan)
            arr_errs.append(np.nan)
        else:
            wnorm = wmasked / wmasked.sum()
            dsmasked = indata * combi_mask.astype(int)
            # dsmasked = dsmasked / dsmasked.sum()
            weighted_arith_mean = (wnorm * dsmasked).sum() / wnorm.sum()
            arith_stderr = np.var(dsmasked) * np.sqrt((wnorm ** 2).sum())
            arr_means.append(weighted_arith_mean)
            arr_errs.append(arith_stderr)
    return arr_means, arr_errs

# ds value per km2
ds_values = np.divide(ds_values.T, pixel_areas_km2).T

# Load country boundaries shapefile
shapefile = os.path.join("inputs", "vectors", "natural_earth_vector.gpkg")
countries = gpd.read_file(shapefile, layer = "ne_50m_admin_0_countries")

# Rasterize country boundaries to match geotiff grid
transform = from_bounds(*dataset.bounds, dataset.width, dataset.height)
country_rasts = rasterize(
    ((geom, value) for geom, value in zip(countries.geometry, countries.index)),
    out_shape=(dataset.height, dataset.width),
    transform=transform,
    dtype=int,
    fill=0
)

# Create output df

if os.path.isfile(os.path.join(output_path, outfile)) and overwrite == False:
    df = pd.read_csv(os.path.join(output_path, outfile), index_col = 0)
else:
    df = pd.DataFrame()

# Find, load and operate upon crop rasters
f = []
for path, subdirs, files in os.walk(crop_tgt_dir):
        for name in files:
            f.append(os.path.join(path, name))
f = [x for x in f if ".tif" in x and "aux" not in x]
for ix, infile in enumerate(f):
    print(f"Processing {infile}, {round(ix/len(f), 4)}...")
    fname = os.path.split(infile)[-1]
    cname = fname.split("_")[0]

    if cname in df.columns and overwrite == False:
        pass
    else:
        # Load geotiff data
        geotiff_file = os.path.join(infile)
        crop_values = rasterio.open(geotiff_file).read(1)

        # Calculate mean value within each country
        mean_values, errs = weighted_mean_err(countries, crop_values, np.divide(ds_values, c))
        dfx = pd.DataFrame({'Country': countries['ISO_A3'], 'val': mean_values, 'err': errs})
        for row in dfx.iterrows():
            row = row[1]
            df.loc[row.Country, cname] = row.val
            df.loc[row.Country, f"{cname}_err"] = row.err

## pasture v2 with livestock dist masks
for lx, lskey in enumerate(livestock_paths.keys()):
    print(f"Processing {lskey}, {round(lx/len(livestock_paths.keys()), 4)}...")
    if lskey in df.columns and overwrite == False:
        pass
    else:
        ls_data = rasterio.open(livestock_paths[lskey]).read(1)
        means, errs = weighted_mean_err(countries, ls_data, np.divide(ds_values, gh_a))
        dfx = pd.DataFrame({'Country': countries['ISO_A3'], 'val': means, 'err': errs})
        for row in dfx.iterrows():
            row = row[1]
            df.loc[row.Country, lskey] = row.val
            df.loc[row.Country, f"{lskey}_err"] = row.err
        
# Do overall crops
# Calculate mean value within each country
means, errs = weighted_mean_err(countries, c, ds_values)
dfx = pd.DataFrame({'Country': countries['ISO_A3'], 'val': means, 'err': errs})
for row in dfx.iterrows():
    row = row[1]
    df.loc[row.Country, "crop"] = row.val
    df.loc[row.Country, f"crop_err"] = row.err
# Do overall pasture
means, errs = weighted_mean_err(countries, p, ds_values)
dfx = pd.DataFrame({'Country': countries['ISO_A3'], 'val': means, 'err': errs})
for row in dfx.iterrows():
    row = row[1]
    df.loc[row.Country, "past"] = row.val
    df.loc[row.Country, f"past_err"] = row.err
means, errs = weighted_mean_err(countries, gh_a, ds_values / gh_a)
dfx = pd.DataFrame({'Country': countries['ISO_A3'], 'val': means, 'err': errs})
for row in dfx.iterrows():
    row = row[1]
    df.loc[row.Country, "gh_all"] = row.val
    df.loc[row.Country, f"gh_all_err"] = row.err
# # Print the result table
print(f"Writing output :{os.path.join(output_path, outfile)}")
print(df)
df.to_csv(os.path.join(output_path, outfile))

