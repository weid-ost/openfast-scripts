import netCDF4 as nc


class Dataset:
    def __init__(self, path):
        self.nc_file = nc.Dataset(path)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        print("Close nc_file")
        self.nc_file.close()

    def set_var(self, name, value):
        print(f"Set var {name} with value {value}")


if __name__ == "__main__":

    with Dataset("Twr29_16-Sep-2020_cor.nc") as data:
        data.set_var("wind_speed", 12.0)

    print(data.nc_file)
