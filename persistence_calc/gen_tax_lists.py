"""assumes experiments in config.json are set up correctly"""

import subprocess
import os
import argparse

python_path = "/maps/tsb42/bd_opp_cost/v3/persistence_calc/env/bin/python3.10"
vt316 = "persistence-calculator/vt316generator.py"
aohcalc = "persistence-calculator/aohcalc.py"
spList = "--list canonical_spList.csv"

parser = argparse.ArgumentParser(description="Runs vt314generator.py and places results in structured folders")
parser.add_argument(
        '--classes',
        type=str,
        help="Comma sep, no spaces, options are 'mammals','reptiles','amphibians','bow', for example: 'mammals,reptiles'.",
        required=True,
        dest="classes"
    )
parser.add_argument(
        '--hmaps',
        type=str,
        help="Comma sep, no spaces, options are 'pnv_curr','gh_curr', 'hist'",
        required=True,
        dest="hmaps"
    )
parser.add_argument(
        '--outputf',
        type=str,
        help="",
        required=True,
        dest="outputf"
    )
parser.add_argument(
        '--suffix',
        type=str,
        help="",
        required=True,
        dest="suffix"
    )

args = vars(parser.parse_args())
c = args['classes']
c = c.split(",")

cdict = {"mammals"      :"MAMMALIA",
         "reptiles"     :"REPTILIA",
         "amphibians"   :"AMPHIBIA",
         "bow"          :"AVES"
        }

hmaps = args['hmaps']
hmaps = hmaps.split(",")

outputf = args['outputf']
suff = args['suffix']

# for dc in c:
#     for h in hmaps:
#         exp_name = f"{dc}_{h}{suff}"
#         print(exp_name)
#         epath = os.path.join(outputf,exp_name)
#         print(epath)
#         if os.path.isdir(os.path.join(epath,"aoh_rasters")) == False:
#             os.makedirs(os.path.join(epath, "aoh_rasters"), exist_ok=True)
#         experiment = f"--experiment {exp_name}"
#         epochs = f"--epochs {exp_name}"
#         output = f"--output {os.path.join(epath, 'taxa.csv')}"
#         class_str = f"--class {cdict[dc]}"
#         pstr = f"{python_path} {vt316} {experiment} {spList} {epochs} {output} {class_str}"
#         print(pstr)
#         process = subprocess.Popen(pstr, shell=True, stdout=subprocess.PIPE)
#         process.wait()

for dc in c:
    for h in hmaps:
        exp_name = f"{dc}_{h}{suff}"
        epath = os.path.join(outputf,exp_name)
        taxa = os.path.join(epath, 'taxa_test.csv')
        geotiffs = f"--geotiffs {os.path.join(epath,'aoh_rasters')}"
        o = f"-o {os.path.join(epath,'aoh.csv')}"
        pstr = f"littlejohn -j 30 -c {taxa} {o} {python_path} {aohcalc} {geotiffs} --config config.json"
        print(pstr)
        # process = subprocess.Popen(pstr, shell = True) 
        # process.wait()