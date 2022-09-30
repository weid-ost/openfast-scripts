import numpy as np
import os
import pyFAST.case_generation.case_gen as case_gen
import pyFAST.case_generation.runner as runner


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
    work_dir = os.path.join(base_dir, "_Aventa_Yaw_Study/")

    # --- Defining the parametric study  (list of dictionnaries with keys as FAST parameters)
    base_dict = {}

    deg_incr = 30
    wind_dirs = np.arange(-30, 30 + deg_incr, deg_incr)
    params = []
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

    # --- Running the simulations
    runner.run_fastfiles(
        fastfiles, fastExe=FAST_EXE, parallel=True, showOutputs=False, nCores=2
    )


if __name__ == "__main__":
    yaw_misalignment()
