import rasterio
import numpy as np
import pandas as pd
import os

data_path = "../persistence_calc/"
output_csv = "outputs/global_agri_aoh.csv"
input_list = "file_index_aoh_results_5arc.csv" 
hist_csv = "/maps/results/global_analysis/processed/PNV_AOH.csv"
overwrite = False
quiet = True
z = 0.25

def main():

    input_df = pd.read_csv(input_list)
    hdf = pd.read_csv(hist_csv)

    sillygoofyrenamingfunction = lambda fname: fname.split(".")[0] + ".BREEDING-" + fname.split("-")[-1]

    # create or load output dataframe
    if os.path.isfile(output_csv) and not overwrite:
        outdf = pd.read_csv(output_csv)
    else:
        outdf = pd.DataFrame(columns = ["taxid","migrant","deltap"])
    rx = 0
    for r, row in input_df.iterrows():

        # define species vars (paths etc)
        curr_path = os.path.join(data_path, row["--current_path"])
        scen_path = os.path.join(data_path, row["--scenario_path"])
        taxid = os.path.split(curr_path)[-1].split("-")[-1].split(".")[0]
        seas = os.path.split(curr_path)[-1].split("-")[0].split(".")[-1].lower().strip(" ")

        try:
            hist_aoh = hdf[(hdf.id_no == int(taxid))&(hdf.season == " " + seas)].AOH.values[0]
            
            if hist_aoh == 0:
                if not quiet:
                    print(f"Skipping {taxid}, historic aoh is zero, likely due to artificial habitat preference...")
            
            else:
                if "NONBREEDING" in ".".join([curr_path,scen_path]):
                    migrant = True
                    nb_curr_path = curr_path
                    nb_scen_path = scen_path
                    curr_base,curr_fname = os.path.split(curr_path)
                    scen_base,scen_fname = os.path.split(scen_path)
                    br_curr_path = os.path.join(curr_base, sillygoofyrenamingfunction(curr_fname))
                    br_scen_path = os.path.join(scen_base, sillygoofyrenamingfunction(scen_fname))
                    nb_curr = rasterio.open(nb_curr_path).read(1).sum()
                    br_curr = rasterio.open(br_curr_path).read(1).sum()
                    nb_scen = rasterio.open(nb_scen_path).read(1).sum()
                    br_scen = rasterio.open(br_scen_path).read(1).sum()
                    p = lambda aoh: (aoh/hist_aoh) ** z
                    pnb_curr = p(nb_curr)
                    pnb_scen = p(nb_scen)
                    pbr_curr = p(br_curr)
                    pbr_scen = p(br_scen)
                    deltaP = np.sqrt(pnb_scen * pbr_scen) - np.sqrt(pbr_curr * pnb_curr)
                    outdf = pd.concat([outdf, 
                            pd.DataFrame({"taxid" : taxid,
                                        "migrant" : migrant,
                                        "deltap" : deltaP},
                                        index = [rx])])
                    rx += 1
                    
                elif "RESIDENT" in ".".join([curr_path,scen_path]):
                    migrant = False
                    curr = rasterio.open(curr_path).read(1).sum()
                    scen = rasterio.open(scen_path).read(1).sum()
                    p = lambda aoh: (aoh/hist_aoh) ** z
                    p_curr = p(curr)
                    p_scen = p(scen)
                    deltaP = p_scen - p_curr
                    outdf = pd.concat([outdf, 
                            pd.DataFrame({"taxid" : taxid,
                                        "migrant" : migrant,
                                        "deltap" : deltaP},
                                        index = [rx])])
                    rx += 1

        except IndexError:
            if not quiet:
                print(f"Skipping {taxid}, can't find a historic aoh in {hist_csv}...")

        print(" " * 40,end = "\r")
        print(f"Calculating deltaP; {round(r / len(input_df), 4)}",end = "\r")

    print(outdf)
    outdf.to_csv(output_csv)

if __name__ == "__main__":
    main()