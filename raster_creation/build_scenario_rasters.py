import yirgacheffe.layers
import numpy as np

no_agri_path = "rasters/no_agri_/no_agri_93m.tif"
gaez_hyde_path = "/maps/tsb42/bd_opp_cost/v2/raster_creation/rasters/gaez_hyde_/gaez_hyde_93m_400752_200376.tif"
jung_pnv_path = "/maps/tsb42/bd_opp_cost/v2/raster_creation/rasters/jung_processed/pnv_lvl1_004_93m_400752_200376.tif"
ext_past_path = "rasters/open_past_/pasture_exc_400752_200376.tif"

output_path_f_gh = "rasters/current_/noagri_fill_gh_400752_200376.tif"
output_path_f_pnv = "rasters/restored_/noagri_fill_pnv_400752_200376.tif"

raster_path_list_f_gh = [no_agri_path, ext_past_path, gaez_hyde_path, jung_pnv_path]
raster_path_list_f_pnv = [no_agri_path, ext_past_path, jung_pnv_path]

no_data_value = 0

def build_n_save(r_list, output_path):
    raster_list = [yirgacheffe.layers.Layer.layer_from_file(raster_path) for raster_path in r_list]
    result = yirgacheffe.layers.Layer.empty_raster_layer_like(raster_list[0], output_path)

    def add_to_stack(A, B):
        """Fills the gaps in A with B"""
        return np.where(A == no_data_value, B, A)

    for raster in raster_list:
        calc = result.numpy_apply(add_to_stack, raster)
        calc.save(result)

# build_n_save(raster_path_list_f_gh, output_path_f_gh)
build_n_save(raster_path_list_f_pnv, output_path_f_pnv)
