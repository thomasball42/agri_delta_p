# -*- coding: utf-8 -*-
"""
Created on Wed May 17 15:51:13 2023

@authors: Thomas Ball, Ali Eyres

This is a modified version of global_code_residents.py that calculates delta p for a set of 
AOH csv files. Any resolution should work since it just uses x/y as identifiers.

This isn't tidied or commented properly
"""
import sys
import pandas as pd
import numpy as np
import argparse
import os
import warnings

quiet = False
overwrite = True

parser = argparse.ArgumentParser()
parser.add_argument('--current_path',
    type=str,required=True,dest="current_path",
    help="path to species current AOH hex")
parser.add_argument('--historic_path',
    type=str,required=True,dest="historic_path",
    help="path to species historic AOH hex")
parser.add_argument('--scenario_path',
    type=str,required=True,dest="scenario_path",
    help="path to species scenario AOH hex")
parser.add_argument('--output_path',
    type=str,required=True,dest="output_path",
    help="path to save output csv")
parser.add_argument('-ht', '--hist_table',
                    dest = "hist_table",
                    type = str)
args = vars(parser.parse_args())

if not overwrite and os.path.isfile(args['output_path']):
    quit(f"{args['output_path']} exists, set overwrite to False to ignore this.")

names = ["lon","lat","area"]   
try:
    current = pd.read_csv(args['current_path'],names=names)
    current = current.loc[current["area"] > 0]
    current_AOH = current['area'].sum()
except FileNotFoundError:
    if quiet:
        quit()
    else:
        quit(f"Current AOH file {args['current_path']} not found, aborting.")
try:
    scenario = pd.read_csv(args['scenario_path'],names=names)
    scenario = scenario.loc[scenario['area'] > 0]
except FileNotFoundError:
    if quiet:
        quit()
    else:
        quit(f"Scenario AOH file {args['scenario_path']} not found, aborting.")
if args["hist_table"] != None:
    """This only works with /maps/results/global_analysis/processed/PNV_AOH.csv"""
    hdf = pd.read_csv(args["hist_table"])
    taxid = os.path.split(args["current_path"])[-1].split("-")[-1].split(".")[0]
    seas = os.path.split(args["current_path"])[-1].split("-")[0].split(".")[-1].lower().strip(" ")
    historic_AOH = hdf[(hdf.id_no == int(taxid))&(hdf.season == " " + seas)].AOH.values[0]
else:
    try:
        historic = pd.read_csv(args['historic_path'],names=names)
        historic = historic.loc[historic['area'] >0]
        historic_AOH = historic['area'].sum()
    except FileNotFoundError:
        if quiet:
            quit()
        else:
            quit("Warning: missing csv for historic aoh - skipping species. This is probably due to artificial hab-preference.")

result = pd.merge(current, scenario, on =["lon","lat"], how='outer')
result['area_x'] = result['area_x'].fillna(0)
result['area_y'] = result['area_y'].fillna(0)

result.columns = ["lon", "lat", "aoh_current", "aoh_scenario"]

def global_p_calc(current_AOH,historic_AOH, exponent):
    sp_P = (current_AOH / historic_AOH)**exponent
    sp_P_fix = np.where(sp_P > 1, 1, sp_P)
    return sp_P_fix 

persistence = global_p_calc(current_AOH,historic_AOH,0.25)

result['new_aoh'] = current_AOH - result['aoh_current'] + result['aoh_scenario']
result['new_p'] = global_p_calc(result['new_aoh'], historic_AOH,0.25)
result['delta_p'] = result['new_p'] - persistence

result = result.loc[result["delta_p"] != 0]


if len(result) > 0:
    outfile = result[["lon","lat","delta_p"]]  
    print(f"Writing {args['output_path']}..")
    outfile.to_csv(args['output_path'], header=True,index=True)