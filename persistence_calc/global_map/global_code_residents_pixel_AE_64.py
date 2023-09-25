# -*- coding: utf-8 -*-
"""
Created on Wed May 17 15:51:13 2023

@authors: Thomas Ball, Ali Eyres

This is a modified version of global_code_residents.py that calculates delta p for a set of 
Rasters. Any resolution should work since it just uses x/y as identifiers.

# AE modified from TB's Code for CSVs
# Not sure if it works... 

This isn't tidied or commented properly
"""
import sys
import pandas as pd
import numpy as np
import argparse
import os
import warnings

from osgeo import gdal
from yirgacheffe.layers import RasterLayer, ConstantLayer


quiet = True
overwrite = True
exponent = 0.25 

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
   
try:
    current32 = RasterLayer.layer_from_file(args['current_path'])
    current = RasterLayer.empty_raster_layer_like(current32, datatype=gdal.GDT_Float64)
    current32.save(current) # think of save as 'save into' - this saves current32 into current

    current_AOH = current.sum() 
except FileNotFoundError:
    if quiet:
        quit()
    else:
        quit("Current AOH file {args['current_path']} not found, aborting.")
try:
    scenario32 = RasterLayer.layer_from_file(args['scenario_path'])
    scenario = RasterLayer.empty_raster_layer_like(scenario32, datatype=gdal.GDT_Float64)
    scenario32.save(scenario)

except FileNotFoundError:
    if quiet:
        quit()
    else:
        quit("Scenario AOH file {args['scenario_path']} not found, aborting.")
if args["hist_table"] != None:
    """ This only works with /maps/results/global_analysis/processed/PNV_AOH.csv"""
    hdf = pd.read_csv(args["hist_table"])
    taxid = os.path.split(args["current_path"])[-1].split("-")[-1].split(".")[0]
    seas = os.path.split(args["current_path"])[-1].split("-")[0].split(".")[-1].lower().strip(" ")
    historic_AOH = hdf[(hdf.id_no == int(taxid))&(hdf.season == " " + seas)].AOH.values[0]
else:
    try:
        historic32 = RasterLayer.layer_from_file(args['historic_path'])
        historic = RasterLayer.empty_raster_layer_like(historic32, datatype=gdal.GDT_Float64)
        historic32.save(historic)

        historic_AOH = historic.sum()
    except FileNotFoundError:
        if quiet:
            quit()
        else:
            quit("Warning: missing csv for historic aoh - skipping species. This is probably due to artificial hab-preference.")


def global_p_calc(current_AOH,historic_AOH, exponent):
    sp_P = (current_AOH / historic_AOH)**exponent
    sp_P_fix = np.where(sp_P > 1, 1, sp_P)
    return sp_P_fix 

persistence = global_p_calc(current_AOH,historic_AOH,exponent)
print(persistence)

seas = os.path.split(args["current_path"])[-1].split("-")[0].split(".")[-1].lower().strip(" ")
if "RESIDENT" in seas:
    # New section added in: Calculating for rasters rather than csv's
    const_layer = ConstantLayer(current_AOH) # MAKE A LAYER WITH THE SAME PROPERTIES AS CURRENT AOH RASTER BUT FILLED WITH THE CURRENT AOH 
    calc_1 = (const_layer - current) + scenario # FIRST CALCULATION : NEW AOH 
    new_AOH = RasterLayer.empty_raster_layer_like(current)
    calc_1.save(new_AOH)

    calc_2 = ((new_AOH / historic_AOH) ** exponent) #SECOND CALCULATION: NEW PERSISTENCE
    calc_2 = calc_2.numpy_apply(lambda chunk: np.where(chunk > 1, 1, chunk))
    new_p = RasterLayer.empty_raster_layer_like(new_AOH)
    calc_2.save(new_p)
    # calc_2.sum()
    # calc_2.save(new_p, and_sum=True)

    calc_3 = calc_2 - ConstantLayer(persistence) # CALCULATION 3 : DELTA P
    delta_p = RasterLayer.empty_raster_layer_like(new_p, filename=args['output_path'])
    calc_3.save(delta_p)

if "NONBREEDING" in seas:

    current_nb = current
    historic_AOH_nb = historic_AOH
    scenario_nb = scenario

    def sillygoofyrenamingfunction(fname):
        return fname.split(".")[0] + ".BREEDING-" + fname.split("-")[-1]

    curr_base,curr_fname = os.path.split(args["current_path"])
    br_curr_path = os.path.join(curr_base, sillygoofyrenamingfunction(curr_fname))
    if args["hist_table"] != None:
        """ This only works with /maps/results/global_analysis/processed/PNV_AOH.csv"""
        hdf = pd.read_csv(args["hist_table"])
        taxid = os.path.split(args["current_path"])[-1].split("-")[-1].split(".")[0]
        seas = "BREEDING"
        b_hist = hdf[(hdf.id_no == int(taxid))&(hdf.season == " " + seas)].AOH.values[0]
    else:
        hist_base,hist_fname = os.path.split(args["historic_path"])
        br_hist_path = os.path.join(hist_base, sillygoofyrenamingfunction(hist_fname))
        historic32_br = RasterLayer.layer_from_file(br_hist_path)
        historic_br = RasterLayer.empty_raster_layer_like(historic32_br, datatype=gdal.GDT_Float64)
        historic32_br.save(historic_br)
        historic_AOH_br = historic_br.sum()

    scen_base,scen_fname = os.path.split(args["scenario_path"])
    br_scen_path = os.path.join(scen_base, sillygoofyrenamingfunction(scen_fname))

    scenario32_br = RasterLayer.layer_from_file(br_scen_path)
    scenario_br = RasterLayer.empty_raster_layer_like(scenario32_br, datatype=gdal.GDT_Float64)
    scenario32_br.save(scenario_br)
    current32_br = RasterLayer.layer_from_file(br_scen_path)
    current_br = RasterLayer.empty_raster_layer_like(current32_br, datatype=gdal.GDT_Float64)
    current32_br.save(current_br)

    # a) Calculate the AOH for for the scenario
    # result['new_aoh_br'] = current_AOH_br - result['aoh_current_br'] + result['aoh_scenario_br']
    # result['new_aoh_non'] = current_AOH_non - result['aoh_current_non'] + result['aoh_scenario_non']
    # # b) Calculate the new P 
    # result['new_p_br'] = global_p_calc(result['new_aoh_br'], historic_AOH_br,z)
    # result['new_p_non'] = global_p_calc(result['new_aoh_non'], historic_AOH_non,z)
    # result['new_P'] = (result['new_p_br']**0.5) * (result['new_p_non']**0.5)
    # # c) calculate delta P 
    # result['delta_p'] = result['new_P'] - persistence
    # result = result.loc[result["delta_p"] !=0]

    #breeding
    current_AOH_br = ConstantLayer(current_br.sum())  
    calc_new_aoh_br = current_AOH_br - current_br + scenario_br
    #nonbreeding
    current_AOH_nb = ConstantLayer(current_nb.sum()) 
    calc_new_aoh_nb = current_AOH_nb - current_nb + scenario_nb
    
    calc_newpbr = ((calc_new_aoh_br / historic_br) ** exponent) 
    calc_newpbr = calc_newpbr.numpy_apply(lambda chunk: np.where(chunk > 1, 1, chunk))
    
    calc_newpnb = ((calc_new_aoh_nb / historic_nb) ** exponent) 
    calc_newpnb = calc_newpnb.numpy_apply(lambda chunk: np.where(chunk > 1, 1, chunk))

    calc_new_p = (calc_newpbr ** 0.5) * (calc_newpnb ** 0.5)

    old_p = (((current_AOH_nb / historic_AOH_nb)**exponent)**0.5) * (((current_AOH_br / historic_AOH_br)**exponent)**0.5)

    calc_delta_p = calc_new_p - ConstantLayer(old_p)
    delta_p = RasterLayer.empty_raster_layer_like(calc_new_p, filename=args['output_path'])
    #the raster will get saved as 'nonbreeding' but know it's the combined seasonality..
    calc_delta_p.save(delta_p)