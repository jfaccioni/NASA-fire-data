import geopandas

instrument = 'VIIRS'
INPUT_FILE = f'local/{instrument}.csv'


def geopandas_demo(input_file: str) -> None:
    """geopandas module demo"""
    df = geopandas.read_file(input_file)
    print(df)


if __name__ == '__main__':
    geopandas_demo(input_file=INPUT_FILE)
