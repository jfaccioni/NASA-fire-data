from __future__ import annotations

import os
from calendar import month_abbr
from contextlib import contextmanager
from typing import Dict, Generator, List, Optional, TYPE_CHECKING
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.fire_point import FirePoint
from src.settings import SETTINGS
from src.utils import ignore_pandas_warning

if TYPE_CHECKING:
    from io import TextIOWrapper


def main(input_dir: str, output_dir: str, percentile_filter: bool, percentile_column: str, cutoff_percentile: float,
         value_filter: bool, value_column: str, cutoff_value: float, analyse_column: str, top_row_number: int,
         distance_cutoff: float, temporal_cutoff: float, analyse_to_stdout: bool, analyse_to_log: bool,
         analyse_to_csv: bool, plot_data: bool, save_data: bool) -> None:
    """Main function of NASA fire data module.
    Parameters are read from the SETTINGS dictionary in the settings.py file"""
    # Loads input data
    print('loading all data...')
    dataset = load_dataset(input_dir=input_dir)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
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
        if any(cond is True for cond in [analyse_to_stdout, analyse_to_log, analyse_to_csv]):
            print(f'analysing top rows for dataset {name}...')
            analysis_loop(df=df, output_dir=output_dir, analyse_column=analyse_column, top_row_number=top_row_number,
                          distance_cutoff=distance_cutoff, temporal_cutoff=temporal_cutoff,
                          analyse_to_stdout=analyse_to_stdout, analyse_to_log=analyse_to_log,
                          analyse_to_csv=analyse_to_csv)
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


# noinspection PyTypeChecker
def analysis_loop(df: pd.DataFrame, output_dir: str, analyse_column: str, top_row_number: int, distance_cutoff: float,
                  temporal_cutoff: float, analyse_to_stdout: bool, analyse_to_log: bool, analyse_to_csv: bool) -> None:
    """Main analysis loop"""
    base_results_path = os.path.join(output_dir, 'results')
    if not os.path.exists(base_results_path):
        os.mkdir(base_results_path)
    log_path = os.path.join(base_results_path, 'log.txt')
    csv_path = os.path.join(base_results_path, 'firepoints.csv')
    with conditional_open(log_path, 'w', condition=analyse_to_log) as logfile, \
            conditional_open(csv_path, 'w', condition=analyse_to_csv) as csvfile:
        for top_point in yield_top_points(df=df, column_name=analyse_column, n=top_row_number):
            close_points = get_close_points(df=df, top_point=top_point, distance_cutoff=distance_cutoff,
                                            temporal_cutoff=temporal_cutoff)
            if analyse_to_stdout:
                to_stdout(top_point=top_point, close_points=close_points, distance_cutoff=distance_cutoff,
                          temporal_cutoff=temporal_cutoff)
            to_log(logfile=logfile, top_point=top_point, close_points=close_points, distance_cutoff=distance_cutoff,
                   temporal_cutoff=temporal_cutoff)
            to_csv(csvfile=csvfile, top_point=top_point, close_points=close_points)


@contextmanager
def conditional_open(filename: str, mode: str, condition: bool) -> Optional[TextIOWrapper]:
    """Context manager for returning an open file or a None value, depending on the condition argument"""
    if not condition:
        yield None
    resource = open(filename, mode)
    try:
        yield resource
    finally:
        resource.close()


def yield_top_points(df: pd.DataFrame, column_name: str, n: int) -> Generator[FirePoint, None, None]:
    """Yields the top k rows from data as FirePoint instances, regarding values in the column_name column"""
    top_df = df.sort_values(by=column_name).tail(n)
    for _, row in top_df.iterrows():
        yield FirePoint.from_dataset_row(row=row)


def get_close_points(df: pd.DataFrame, top_point: FirePoint, distance_cutoff: float,
                     temporal_cutoff: float) -> List[FirePoint]:
    """Analyses dataset k top values by finding points closest to it"""
    close_points = []
    for index, row in df.iterrows():  # TODO: this is very slow, since we have to iterate over the whole dataset
        candidate = FirePoint.from_dataset_row(row=row)
        if top_point.is_neighbor_of(candidate, time_delta=temporal_cutoff, distance_delta=distance_cutoff):
            close_points.append(candidate)
    return close_points


def to_stdout(top_point: FirePoint, close_points: List, distance_cutoff: float, temporal_cutoff: float) -> None:
    """Outputs information for FirePoint and its close points to standard output"""
    print(f'Top point: {top_point}')
    print(f'Points within distance={distance_cutoff} km, time={temporal_cutoff} days: {len(close_points)}')
    for point in close_points:
        print(point)
    print('\n')


def to_log(logfile: Optional[TextIOWrapper], top_point: FirePoint, close_points: List[FirePoint],
           distance_cutoff: float, temporal_cutoff: float) -> None:
    """Outputs information for FirePoint and its close points to log file.
    Returns early if the user chose not to do so"""
    if logfile is None:
        return
    logfile.write(f'Top point: {top_point}')
    logfile.write('\n')
    logfile.write(f'Points within distance={distance_cutoff} km, time={temporal_cutoff} days: {len(close_points)}')
    logfile.write('\n')
    for point in close_points:
        logfile.write(str(point))
        logfile.write('\n')
    logfile.write('\n')


def to_csv(csvfile: Optional[TextIOWrapper], top_point: FirePoint, close_points: List[FirePoint]) -> None:
    """Outputs information for FirePoint and its close points to csv file.
    Returns early if the user chose not to do so"""
    if csvfile is None:
        return
    csvfile.write(top_point.as_csv_row(is_top_point=True))
    csvfile.write('\n')
    for point in close_points:
        csvfile.write(point.as_csv_row(is_top_point=False))
        csvfile.write('\n')


def plot_dataset(df: pd.DataFrame, name: str) -> None:
    """Plots DataFrame values of longitude x latitude as a scatter plot"""
    sns.relplot(x='longitude', y='latitude', hue='year', data=df.sort_values(by='frp'))
    plt.title(name)


def save_dataset(df: pd.DataFrame, name: str, output_dir: str) -> None:
    """Saves DataFrame to a csv file in the specified output directory"""
    df.to_csv(os.path.join(output_dir, f'{name}.csv'), index=False)


if __name__ == '__main__':
    main(**SETTINGS)
