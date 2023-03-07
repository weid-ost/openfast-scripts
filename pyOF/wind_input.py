import numpy as np
import pandas as pd


def uniform_wind():
    """
    Create uniform wind file used as input for InflowWind when using WindType = 2

    TODO: Create config file in order to set the parameters. Allow for multiple output.
    """
    dt = 0.001
    Tdat = np.arange(0, 100 + dt, dt)

    size = len(Tdat)

    Delta = np.zeros(size)
    VZ = np.zeros(size)
    HLinShr = np.zeros(size)
    VLinShr = np.zeros(size)
    VGust = np.zeros(size)

    freq = 0.05
    amplitude = 0.5
    ws_mean = 7.0

    Vh_ref = np.sin(Tdat * freq * np.pi * 2) * amplitude + ws_mean
    Vshr = np.ones(size) * 0.143

    # Predefined column order for uniform wind inflow file.
    # DO NOT CHANGE ORDER! Read in within InflowWind is based on order as opposed to column names.
    data = {
        "Tdat": Tdat,
        "Vh_ref": Vh_ref,
        "Delta": Delta,
        "VZ": VZ,
        "HLinShr": HLinShr,
        "Vshr": Vshr,
        "VLinShr": VLinShr,
        "VGust": VGust,
    }
    df = pd.DataFrame(data)

    df.to_csv(
        f"Sinus_ws{ws_mean}_a{amplitude}_f{freq}.csv", index=False, header=None
    )


if __name__ == "__main__":
    uniform_wind()
    # pass
