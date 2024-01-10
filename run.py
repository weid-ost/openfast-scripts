from pyOF.cases import (
    generate_power_curve_case,
    generate_turb_sim_bts,
    run_simulations,
)
from pyOF.scada import create_10min_ave

if __name__ == "__main__":
    generate_power_curve_case()
    generate_turb_sim_bts()
    run_simulations()
    create_10min_ave()
