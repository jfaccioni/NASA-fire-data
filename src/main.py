import os
from calendar import month_abbr
from typing import Dict
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.utils import ignore_pandas_warning
from src.settings import SETTINGS

USE_SETTINGS = True


def main(input_dir: str = 'data', output_dir: str = 'output', apply_filter: bool = True, column_to_filter: str = 'frp',
         filter_percentile: float = 90, plot_data: bool = True, save_data: bool = True) -> None:
    """Main function of NASA fire data module"""
    # Loads input data
    print('loading all data...')
    dataset = load_dataset(input_dir=input_dir)
    # Iterates over DataFrames and analyse each DataFrame individually
    for name, df in dataset.items():
        print(f'organizing dataset {name}...')
        add_dates(df=df)
        if apply_filter is True:
            print(f'filtering dataset {name}...')
            df = filter_dataset(df=df, column_name=column_to_filter, percentile=filter_percentile)
        if plot_data is True:
            print(f'plotting dataset {name}...')
            plot_dataset(df=df, name=name)
        if save_data is True:
            print(f'saving dataset {name}...')
            save_dataset(df=df, name=name, output_dir=output_dir)
    # Shows resulting plots on the screen
    print('showing all data...')
    plt.show()


def load_dataset(input_dir: str) -> Dict[str, pd.DataFrame]:
    """Loads dataset from zip files. Returns a dictionary in the format {instrument name: pandas DataFrame}"""
    dataset = {}
    instrument_names = ('MODIS', 'VIIRS')
    zip_files = [os.path.join(input_dir, z) for z in os.listdir(input_dir) if z.endswith('.zip')]
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


def add_dates(df: pd.DataFrame) -> None:
    """Calls methods related to adding date columns to the DataFrame"""
    for func in (add_year_values, add_month_values, add_month_names):
        func(df=df, date_col='acq_date')


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


def filter_dataset(df: pd.DataFrame, column_name: str, percentile: float) -> pd.DataFrame:
    """Analyses dataset by calling analytical downstream functions"""
    return filter_above_percentile(df=df, column_name=column_name, percentile=percentile)


def filter_above_percentile(df: pd.DataFrame, column_name: str, percentile: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column belong to the top percentile,
    based on the percentile argument"""
    cutoff_value = np.percentile(df[column_name], percentile)
    return df.loc[df[column_name] > cutoff_value]


def plot_dataset(df: pd.DataFrame, name: str) -> None:
    """Plots DataFrame values of longitude x latitude as a scatter plot"""
    sns.relplot(x='longitude', y='latitude', hue='year', data=df.sort_values(by='frp'))
    plt.title(name)


def save_dataset(df: pd.DataFrame, name: str, output_dir: str) -> None:
    """Saves DataFrame to a csv file in the specified output directory"""
    df.to_csv(os.path.join(output_dir, f'{name}.csv'), index=False)


if __name__ == '__main__':
    if USE_SETTINGS:
        main(**SETTINGS)
    else:
        main()
