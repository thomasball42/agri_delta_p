import argparse
import pandas as pd
import numpy as np
import os 

gcr_list = "file_index"

parser = argparse.ArgumentParser()
parser.add_argument('--target_dir',
                    type=str,
                    help="Folder containing csvs to sum",
                    required=True,
                    dest="target_dir")
parser.add_argument('--csv_out',
                    type=str,
                    help="Output csv for summed vals",
                    required=True,
                    dest="csv_out")
parser.add_argument('--sum_col', type=str,
                    help="The name of the columns (usually 'delta_p')", required=True,
                    dest="sum_col")
parser.add_argument('-i', '--ignore',
                    help = "Ignores any files with this in their path",
                    dest = "ignore",
                    type = str)

args = vars(parser.parse_args())
target_dir = args["target_dir"]
csv_out = args["csv_out"]
sum_col = args["sum_col"]
ignore = args["ignore"]

if args["ignore"] != None:
    ignore = ignore.split(",") + [gcr_list]
else:
    ignore = [gcr_list]

f = []
for path, subdirs, files in os.walk(args["target_dir"]):
    for name in files:
        f.append(os.path.join(path, name))
f = [file for file in f if ".csv" in file]
for ign in ignore:
    f = [file for file in f if ign not in file]

files = f

point_sums = {}
n = 0
for f, file in enumerate(files):

    dat = pd.read_csv(file, index_col = 0)
    
    if "lat" not in dat.columns:
        dat = pd.read_csv(file)
        dat.columns = ["lat", "lon", sum_col]

    summed = dat.groupby(["lat", "lon"])[sum_col].sum()

    if dat.lat.max() > 90 or dat.lat.min() < -90:
        print(f"skipping {file}, invalid lats (this shouldn't happen)..")
    elif len(dat.lon.unique()) <= 1 and len(dat.lat.unique()) > 10:
        print(f"skipping {file} (corr lon)")
        print(dat)
        quit()
    else:
        for point, value in summed.items():
            if point in point_sums:
                point_sums[point] += value
            else:
                point_sums[point] = value
        n += 1
    print("                                ",end = "\r")
    print(f"{round(f / len(files), 4)}; {n}",end = "\r")

summed_data = [{'lat': point[0], 'lon': point[1], 'delta_p_sum': value} for point, value in point_sums.items()]
df = pd.DataFrame(summed_data)
df.to_csv(csv_out, index=False, float_format='%.16f')