from zipfile import ZipFile
import os
from typing import Dict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def main(data_dir: str = 'data') -> None:
    """Main function of NASA fire data module"""
    dataset = load_dataset(data_dir=data_dir)
    print(dataset)


def load_dataset(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Loads dataset from zip files. Returns a dictionary in the format {instrument name: pandas DataFrame}"""
    dataset = {}
    instrument_names = ('MODIS', 'VIIRS')
    zip_files = [z for z in os.listdir(data_dir) if z.endswith('.zip')]
    for instrument_name, zip_file in zip(instrument_names, zip_files):
        with ZipFile(zip_file) as zip_input:
            data = []
            csv_files = [c for c in zip_input.namelist() if c.endswith('.csv')]
            for csv_file in csv_files:
                with zip_input.open(csv_file) as csv_input:
                    df = pd.read_csv(csv_input)
                data.append(df)
            dataset[instrument_name] = pd.concat(data, sort=False, ignore_index=True)
    return dataset


if __name__ == '__main__':
    main()
