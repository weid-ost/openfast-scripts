import sys
from pathlib import Path
from typing import TextIO
import numpy as np
from scipy.stats import circmean
import yaml

from dynaconf import Dynaconf

from . import __config_filepath__

cfg = Dynaconf(
    envvar_prefix="PYOF_SCRIPTS",
    settings_files=[
        __config_filepath__,
    ],
)


def get_default_cfg():
    return cfg


def set_cfg(new_cfg: dict):
    global cfg
    cfg = get_default_cfg()
    cfg.update(new_cfg)


def yaml_load(file_path: str | Path) -> dict:
    """Load YAMl file

    Parameters
    ----------
    file_path:
        Path to YAML file.

    Returns
    -------
    data:
        A dict containing the loaded key-value pairs from the YAML file.

    """
    with open(file_path, encoding="utf8") as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        data = yaml.load(file, Loader=yaml.FullLoader)
        if data is None:
            data = {}
    return data


class RedirectStdout:
    def __init__(self, new_output: TextIO):
        self.new_output = new_output
        self.save_stdout = sys.stdout

    def __enter__(self):
        sys.stdout = self.new_output

    def __exit__(self, *args, **kwargs):
        sys.stdout = self.save_stdout


def circmean_deg(x):
    x_rad = x / 180.0 * np.pi
    return circmean(x_rad) / np.pi * 180.0
