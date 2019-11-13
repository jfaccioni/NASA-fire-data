import os
from calendar import month_abbr
from typing import Dict
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.utils import ignore_pandas_warning


def main(data_dir: str = 'data') -> None:
    """Main function of NASA fire data module"""
    print('loading dataset...')
    dataset = load_dataset(data_dir=data_dir)
    print('analysing dataset...')
    analyse_dataset(dataset=dataset)
    print('plotting dataset...')
    plt.show()


def load_dataset(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Loads dataset from zip files. Returns a dictionary in the format {instrument name: pandas DataFrame}"""
    dataset = {}
    instrument_names = ('MODIS', 'VIIRS')
    zip_files = [os.path.join(data_dir, z) for z in os.listdir(data_dir) if z.endswith('.zip')]
    for instrument_name, zip_file in zip(instrument_names, zip_files):
        with ZipFile(zip_file) as zip_input:
            dataset[instrument_name] = load_csvs_from_zip_file(zip_file=zip_input)
    return dataset


def load_csvs_from_zip_file(zip_file: ZipFile) -> pd.DataFrame:
    """Reads data from all csv files inside the input zip file and returns it as a concatenated pandas DataFrame"""
    data = []
    csv_files = [c for c in zip_file.namelist() if c.endswith('.csv')]
    for csv_file in csv_files:
        with zip_file.open(csv_file) as csv_input:
            df = pd.read_csv(csv_input)
        data.append(df)
    return pd.concat(data, sort=False, ignore_index=True)


def analyse_dataset(dataset: Dict[str, pd.DataFrame]) -> None:
    """Analyses dataset by calling analytical downstream functions"""
    for name, data in dataset.items():
        data = filter_above_percentile(df=data, column_name='frp', percentile=99.9)
        for func in (add_year_values, add_month_values, add_month_names):
            func(df=data, date_col='acq_date')
        sns.relplot(x='longitude', y='latitude', hue='year', data=data.sort_values(by='frp'))
        plt.title(name)


def filter_above_percentile(df: pd.DataFrame, column_name: str, percentile: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column belong to the top percentile,
    based on the percentile argument"""
    cutoff_value = np.percentile(df[column_name], percentile)
    return df.loc[df[column_name] > cutoff_value]


@ignore_pandas_warning
def add_year_values(df: pd.DataFrame, date_col: str) -> None:
    """Adds year column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['year'] = df[date_col].apply(lambda x: int(x.split('-')[0]))


@ignore_pandas_warning
def add_month_values(df: pd.DataFrame, date_col: str) -> None:
    """Adds month column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['month'] = df[date_col].apply(lambda x: int(x.split('-')[1]))


@ignore_pandas_warning
def add_month_names(df: pd.DataFrame, date_col: str) -> None:
    """Adds month_name column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['month_name'] = df[date_col].apply(lambda x: month_abbr[int(x.split('-')[1])])


if __name__ == '__main__':
    main()
