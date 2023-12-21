from pyOF.cases import generate_power_curve_case
from pathlib import Path
from pyOF.utils import yaml_load, set_cfg

config_path = Path(__file__).parent
config = yaml_load(config_path / "case_gen_config.yaml")

set_cfg(config)


def test_generate_power_curve_case():
    generate_power_curve_case()
