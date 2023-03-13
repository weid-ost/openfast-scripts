import os
from decimal import Decimal, getcontext
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyFAST.case_generation.case_gen as case_gen
import pyFAST.case_generation.runner as runner
from pyFAST.input_output import FASTInputFile
from scipy.stats import norm, qmc, weibull_min

from pyOF.utils import RedirectStdout, yaml_load


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

    # --- Running the simulations
    runner.run_fastfiles(
        fastfiles, fastExe=FAST_EXE, parallel=True, showOutputs=False, nCores=2
    )


def turb_sim_inflow(
    config: dict,
    fastfiles: list[str],
    wind_speeds: list[float],
    turb_ints: list[float],
) -> None:
    """Modify TurbSim parameters and write"""

    ref_file = (
        Path(config["case"]["ref_dir"]) / "Aventa/Wind/_TURBSIM_INPUTS.inp"
    )

    for fastfile, wind_speed, turb_int in zip(
        fastfiles, wind_speeds, turb_ints
    ):
        turb_file = get_turb_sim_input_path(fastfile=fastfile)

        fast_ref_input = FASTInputFile(ref_file)
        fast_ref_input["URef"] = wind_speed
        fast_ref_input["IECturbc"] = turb_int

        case_path = Path(fastfile)
        fast_ref_input.write(case_path.parent / "Aventa" / turb_file)


def simulation_input(config: dict) -> list[float]:
    inputs = config["case"]["inputs"]

    sampler = qmc.Sobol(d=3, scramble=True, seed=inputs["seed"])

    n_inputs = int(np.round(np.log2(inputs["n_inputs"])))
    sample = sampler.random_base2(n_inputs)

    a = 2 * inputs["wind"]["weibull"]["A"] / np.sqrt(np.pi)
    k = inputs["wind"]["weibull"]["k"]

    bounds = weibull_min.cdf(
        [inputs["turbine"]["cut_in"], inputs["turbine"]["cut_out"]],
        k,
        loc=0,
        scale=a,
    )

    # Wind speed, yaw error and turbulence intensity
    l_bounds = [bounds[0], 0, 0]
    u_bounds = [bounds[1], 1, 1]

    sample = qmc.scale(sample, l_bounds, u_bounds)

    wind_speed = weibull_min.ppf(sample[:, 0], k, scale=a)
    yaw_error = norm.ppf(sample[:, 1], scale=inputs["wind"]["yaw_error"]["sd"])
    turb_int = norm.ppf(
        sample[:, 2],
        loc=inputs["wind"]["turb_int_ref"]["mean"],
        scale=inputs["wind"]["turb_int_ref"]["sd"],
    )

    return wind_speed, yaw_error, turb_int


def generate_power_curve_case():
    config_path = Path(__file__).parent
    config = yaml_load(config_path / "case_gen_config.yaml")

    # Folder where the fast input files are located (will be copied)
    ref_dir = config["case"]["ref_dir"]

    # Main file in ref_dir, used as a template
    main_file = config["case"]["main_file"]

    # # Output folder (will be created)
    work_dir = config["case"]["case_dir"]

    wind_speeds, yaw_errors, turb_ints = simulation_input(config)

    plot_distributions(wind_speeds, yaw_errors, turb_ints)

    # # --- Defining the parametric study  (list of dictionaries with keys as FAST parameters)
    base_dict = {}

    params = []

    getcontext().prec = 4

    for wind_speed, yaw_error, turb_int in zip(
        wind_speeds, yaw_errors, turb_ints
    ):
        p = base_dict.copy()

        p[
            "InflowFile|Filename"
        ] = f"Wind/_TURBSIM_INPUTS_{wind_speed:.1f}_{turb_int:.1f}.bts"
        p["InflowFile|m/s"] = Decimal(wind_speed) * 1
        p["InflowFile|PropagationDir"] = Decimal(yaw_error) * 1
        p[
            "__name__"
        ] = f"ws-{wind_speed:.1f}_wd-{yaw_error:.1f}_ti-{turb_int:.1f}"
        params.append(p)

    with open("fastfiles.log", "w") as f, RedirectStdout(f):
        # --- Generating all files in a workdir
        fastfiles = case_gen.templateReplace(
            params,
            ref_dir,
            outputDir=work_dir,
            removeRefSubFiles=True,
            main_file=main_file,
            oneSimPerDir=True,
        )

        turb_sim_inflow(config, fastfiles, wind_speeds, turb_ints)


def generate_turb_sim_bts():
    config_path = Path(__file__).parent
    config = yaml_load(config_path / "case_gen_config.yaml")

    # # Output folder (will be created)
    work_dir = Path(config["case"]["case_dir"])

    turbsim_exe = config["case"]["turbsim_exe"]

    fastfiles = sorted(work_dir.glob("*/*.fst"))

    with open("turb_sim.log", "w") as f, RedirectStdout(f):
        for fastfile in fastfiles:
            turb_file_name = get_turb_sim_input_path(fastfile)

            case_path = Path(fastfile).parent
            turb_file_path = str(case_path / "Aventa" / turb_file_name)

            runner.run_cmd(
                turb_file_path,
                turbsim_exe,
                wait=True,
                showOutputs=True,
                showCommand=True,
            )


def run_simulations():
    pass


def get_turb_sim_input_path(fastfile: list[str | Path]) -> str | Path:
    fast_input_path = Path(fastfile)
    fast_input = FASTInputFile(fast_input_path)

    inflow_file_path = str(
        fast_input_path.parent / fast_input["InflowFile"].strip('"')
    )
    inflow_file = FASTInputFile(inflow_file_path)

    return f"{Path(inflow_file['Filename_BTS']).with_suffix('')}.inp"


def plot_distributions(
    wind_speed: list[float], yaw_error: list[float], turb_int: list[float]
) -> None:
    _, axes = plt.subplots(3, 1, figsize=(10, 10))
    axes[0].hist(wind_speed)
    axes[1].hist(yaw_error)
    axes[2].hist(turb_int)
    plt.savefig("plots/distributions.png", dpi=300)
