from decimal import Decimal, getcontext
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import openfast_toolbox.case_generation.case_gen as case_gen
import openfast_toolbox.case_generation.runner as runner
from openfast_toolbox.io import FASTInputFile
from scipy.stats import norm, qmc, weibull_min

from pyOF.utils import RedirectStdout, get_default_cfg


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
    config = get_default_cfg()
    # Folder where the fast input files are located (will be copied)
    ref_dir = config["case"]["ref_dir"]

    # Main file in ref_dir, used as a template
    main_file = config["case"]["main_file"]

    # # Output folder (will be created)
    work_dir = config["case"]["case_dir"]

    wind_speeds, yaw_errors, turb_ints = simulation_input(config)

    plot_distributions(wind_speeds, yaw_errors, turb_ints, bins=20)

    # # --- Defining the parametric study  (list of dictionaries with keys as FAST parameters)
    base_dict = {}

    params = []

    getcontext().prec = 4

    for wind_speed, yaw_error, turb_int in zip(
        wind_speeds, yaw_errors, turb_ints
    ):
        p = base_dict.copy()

        p[
            "InflowFile|Filename_BTS"
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
    config = get_default_cfg()

    # Output folder (will be created)
    work_dir = Path(config["case"]["case_dir"])

    turbsim_exe = config["case"]["turbsim_exe"]

    fastfiles = sorted(work_dir.glob("*/*.fst"))
    turb_file_paths = []

    with open("turb_sim.log", "w") as f, RedirectStdout(f):
        for fastfile in fastfiles:
            turb_file_name = get_turb_sim_input_path(fastfile)

            case_path = Path(fastfile).parent
            turb_file_paths.append(str(case_path / "Aventa" / turb_file_name))

    runner.run_cmds(
        turb_file_paths,
        turbsim_exe,
        showOutputs=True,
        showCommand=True,
    )


def run_simulations():
    config = get_default_cfg()
    fast_exe = config["case"]["fast_exe"]

    work_dir = Path(config["case"]["case_dir"])
    fastfiles = [str(path) for path in sorted(work_dir.glob("*/*.fst"))]

    runner.run_fastfiles(
        fastfiles, fastExe=fast_exe, parallel=True, showOutputs=True
    )


def get_turb_sim_input_path(fastfile: list[str | Path]) -> str | Path:
    fast_input_path = Path(fastfile)
    fast_input = FASTInputFile(fast_input_path)

    inflow_file_path = str(
        fast_input_path.parent / fast_input["InflowFile"].strip('"')
    )
    inflow_file = FASTInputFile(inflow_file_path)

    return f"{Path(inflow_file['Filename_BTS']).with_suffix('')}.inp"


def plot_distributions(
    wind_speed: list[float],
    yaw_error: list[float],
    turb_int: list[float],
    bins: int | str | list = None,
) -> None:
    _, axes = plt.subplots(3, 1, figsize=(10, 10), sharey=True)
    axes[0].hist(wind_speed, bins=bins)
    axes[1].hist(yaw_error, bins=bins)
    axes[2].hist(turb_int, bins=bins)

    axes[0].set_xlabel("Wind speed [m/s]")
    axes[1].set_xlabel("Yaw misalignment [deg]")
    axes[2].set_xlabel("Turbulence intensity [%]")

    axes[0].set_ylabel("Frequency")
    axes[1].set_ylabel("Frequency")
    axes[2].set_ylabel("Frequency")

    plt.tight_layout()

    plt.savefig("plots/distributions.png", dpi=300)


if __name__ == "__main__":
    print(FASTInputFile)
