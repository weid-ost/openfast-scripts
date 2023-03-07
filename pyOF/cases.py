import os

import matplotlib.pyplot as plt
import numpy as np
import pyFAST.case_generation.case_gen as case_gen
import pyFAST.case_generation.runner as runner
from scipy.stats import norm, qmc, weibull_min


def yaw_misalignment():
    """Example to run a set of OpenFAST simulations (parametric study)

    This script uses a reference directory (`ref_dir`) which contains a reference input file (.fst)
    1) The reference directory is copied to a working directory (`work_dir`).
    2) All the fast input files are generated in this directory based on a list of dictionaries (`PARAMS`).
    For each dictionary in this list:
       - The keys are "path" to a input parameter, e.g. `EDFile|RotSpeed`  or `FAST|TMax`.
         These should correspond to the variables used in the FAST inputs files.
       - The values are the values corresponding to this parameter
    For instance:
         PARAMS[0]['EDFile|RotSpeed']       = 5
         PARAMS[0]['InflowFile|HWindSpeed'] = 10

    3) The simulations are run, successively distributed on `nCores` CPUs.
    """
    # --- Parameters for this script
    FAST_EXE = "/home/florian/OpenFAST/install/bin/openfast"  # Command used in SLURM submission script
    base_dir = "/home/florian/Projects/openfast_aventa/OpenFAST/"

    # Folder where the fast input files are located (will be copied)
    ref_dir = os.path.join(base_dir, "ref_folder")

    # Main file in ref_dir, used as a template
    main_file = "runAventa.fst"

    # Output folder (will be created)
    work_dir = os.path.join(base_dir, "_Aventa_Yaw_Study_2/")

    # --- Defining the parametric study  (list of dictionnaries with keys as FAST parameters)
    base_dict = {}

    deg_incr = 30
    wind_dirs = np.arange(-30, 30 + deg_incr, deg_incr)
    params = []

    base_dict["InflowFile|WindVxiList"] = [0, 0]
    base_dict["InflowFile|WindVyiList"] = [0, 0]
    base_dict["InflowFile|WindVziList"] = [18.0, 16.0]

    for i, wind_dir in enumerate(wind_dirs):
        p = base_dict.copy()

        p["InflowFile|PropagationDir"] = wind_dir
        p["__name__"] = f"{i:03d}_wd{wind_dir:04.1f}"
        params.append(p)

    # --- Generating all files in a workdir
    fastfiles = case_gen.templateReplace(
        params,
        ref_dir,
        outputDir=work_dir,
        removeRefSubFiles=True,
        main_file=main_file,
        oneSimPerDir=False,
    )
    print(fastfiles)

    # # --- Running the simulations
    # runner.run_fastfiles(
    #     fastfiles, fastExe=FAST_EXE, parallel=True, showOutputs=False, nCores=2
    # )


def power_curve_lhc():
    # --- Parameters for this script
    # FAST_EXE = "/home/florian/OpenFAST/install/bin/openfast"  # Command used in SLURM submission script
    # base_dir = "/home/florian/Projects/openfast_aventa/OpenFAST/"

    # # Folder where the fast input files are located (will be copied)
    # ref_dir = os.path.join(base_dir, "ref_folder")

    # # Main file in ref_dir, used as a template
    # main_file = "runAventa.fst"

    # # Output folder (will be created)
    # work_dir = os.path.join(base_dir, "_Aventa_Yaw_Study_2/")

    # # --- Defining the parametric study  (list of dictionaries with keys as FAST parameters)
    # base_dict = {}

    sampler = qmc.Sobol(d=4, scramble=True, seed=20230307)
    sample = sampler.random_base2(7)

    a, k = 2 * 6.0 / np.sqrt(np.pi), 2.0

    bounds = weibull_min.cdf([2, 14], k, loc=0, scale=a)

    # Wind speed, yaw error, turbulence intensity, turbulence length scale
    l_bounds = [bounds[0], 0, 0, 0]
    u_bounds = [bounds[1], 1, 1, 1]

    sample = qmc.scale(sample, l_bounds, u_bounds)

    wind_speed = weibull_min.ppf(sample[:, 0], k, scale=a)
    yaw_error = norm.ppf(sample[:, 1], scale=2)
    turb_int = norm.ppf(sample[:, 2], loc=10, scale=2)
    turb_len_scale = norm.ppf(sample[:, 3], loc=0.2, scale=0.02)

    plt.hist(turb_int, bins=40)
    # plt.scatter(x, u)
    plt.savefig("test.png", dpi=300)

    # deg_incr = 30
    # wind_dirs = np.arange(-30, 30 + deg_incr, deg_incr)
    # params = []

    # base_dict["InflowFile|WindVxiList"] = [0, 0]
    # base_dict["InflowFile|WindVyiList"] = [0, 0]
    # base_dict["InflowFile|WindVziList"] = [18.0, 16.0]

    # for i, wind_dir in enumerate(wind_dirs):
    #     p = base_dict.copy()

    #     p["InflowFile|PropagationDir"] = wind_dir
    #     p["__name__"] = f"{i:03d}_wd{wind_dir:04.1f}"
    #     params.append(p)


if __name__ == "__main__":
    yaw_misalignment()
