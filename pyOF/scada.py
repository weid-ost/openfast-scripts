from pathlib import Path

import pandas as pd

from pyOF.utils import yaml_load


# TODO: Parallelise with multiprocessing library
def create_10min_ave():
    config_path = Path(__file__).parent
    config = yaml_load(config_path / "case_gen_config.yaml")

    work_dir = Path(config["case"]["case_dir"])
    outfiles = [str(path) for path in sorted(work_dir.glob("*/*.out"))]

    scada = []
    for outfile in outfiles:
        print(outfile)
        df = pd.read_csv(outfile, skiprows=6, sep="\t", header=[0, 1])
        df.columns = df.columns.map(lambda x: " ".join(map(str.strip, x)))

        df_transient = df.loc[df["Time (s)"] > 100.0].copy()
        df_transient["Time (s)"] = df_transient["Time (s)"] - 100.1

        df_transient["period"] = df_transient["Time (s)"] // 600.0

        df_agg = df_transient.groupby("period").agg(["mean", "std", "count"])

        df_agg.to_pickle(f"{outfile}.pkl")
        scada.append(df_agg)

    pd.concat(scada).to_pickle("SCADA.pkl")
