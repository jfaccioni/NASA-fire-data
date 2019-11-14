import os
from calendar import month_abbr
from typing import Dict
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.fire_point import FirePoint
from src.settings import SETTINGS
from src.utils import ignore_pandas_warning


def main(input_dir: str, output_dir: str, percentile_filter: bool, percentile_column: str, cutoff_percentile: float,
         value_filter: bool, value_column: str, cutoff_value: float, analyse_top_frp: bool, plot_data: bool,
         save_data: bool) -> None:
    """Main function of NASA fire data module. Parameters are read from the dictionary in settings.py"""
    # Loads input data
    print('loading all data...')
    dataset = load_dataset(input_dir=input_dir)
    # Iterates over DataFrames and analyse each DataFrame individually
    for name, df in dataset.items():
        print(f'Adding date columns to dataset {name}...')
        add_dates(df=df)
        if value_filter is True:
            print(f'filtering dataset {name} by {value_column} > {cutoff_value} ...')
            df = filter_dataset_by_value(df=df, value_column=value_column, cutoff_value=cutoff_value)
        if percentile_filter is True:
            print(f'filtering dataset {name} by {percentile_column} > {cutoff_percentile} percentile...')
            df = filter_dataset_by_percentile(df=df, percentile_column=percentile_column,
                                              cutoff_percentile=cutoff_percentile)
        if analyse_top_frp is True:
            print(f'analysing top frp for dataset {name}...')
            analyse_dataset_frp(df=df)
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
    """Reads data from all csv files inside the input zip file and returns it as a concatenated pandas DataFrame.
    This is necessary because, for each instrument, there are archive csv files (more than 3 months ago) and
    near real time (nrt) files (data from less than 3 months ago, less confidence)."""
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


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_year_values(df: pd.DataFrame, date_col: str) -> None:
    """Adds year column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['year'] = df[date_col].apply(lambda x: int(x.split('-')[0]))


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_month_values(df: pd.DataFrame, date_col: str) -> None:
    """Adds month column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['month'] = df[date_col].apply(lambda x: int(x.split('-')[1]))


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_month_names(df: pd.DataFrame, date_col: str) -> None:
    """Adds month_name column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['month_name'] = df[date_col].apply(lambda x: month_abbr[int(x.split('-')[1])])


def filter_dataset_by_value(df: pd.DataFrame, value_column: str, cutoff_value: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column are above the value_cutoff"""
    return df.loc[df[value_column] > cutoff_value]


def filter_dataset_by_percentile(df: pd.DataFrame, percentile_column: str, cutoff_percentile: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column belong to the top percentile,
    based on the percentile argument"""
    cutoff_value = np.percentile(df[percentile_column], cutoff_percentile)
    return df.loc[df[percentile_column] > cutoff_value]


def analyse_dataset_frp(df: pd.DataFrame) -> None:
    """Analyses dataset top FRP points"""
    top_frp_df = df.sort_values(by='frp').tail(10)  # 10 highest FRP rows
    for index, row in top_frp_df.iterrows():
        close_points = []
        p = FirePoint.from_dataset_row(row=row)
        for i, r in df.iterrows():  # TODO: iterrows is too slow for this
            pp = FirePoint.from_dataset_row(row=r)
            if p.is_neighbor_of(pp, time_delta=30, distance_delta=10):
                close_points.append(pp)
        print(f'Top FRP point {p} has {len(close_points)} close points:')
        print(close_points)


def plot_dataset(df: pd.DataFrame, name: str) -> None:
    """Plots DataFrame values of longitude x latitude as a scatter plot"""
    sns.relplot(x='longitude', y='latitude', hue='year', data=df.sort_values(by='frp'))
    plt.title(name)


def save_dataset(df: pd.DataFrame, name: str, output_dir: str) -> None:
    """Saves DataFrame to a csv file in the specified output directory"""
    df.to_csv(os.path.join(output_dir, f'{name}.csv'), index=False)


if __name__ == '__main__':
    main(**SETTINGS)
