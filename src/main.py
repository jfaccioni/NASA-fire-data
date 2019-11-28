from __future__ import annotations

import os
from calendar import month_abbr
from functools import lru_cache
from typing import Dict, Generator, List, Optional, TYPE_CHECKING, Tuple
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.fire_point import FirePoint
from src.settings import SETTINGS
from src.utils import conditional_open, ignore_pandas_warning

if TYPE_CHECKING:
    from io import TextIOWrapper


def main(input_dir: str, output_dir: str, percentile_filter: bool, percentile_column: str, cutoff_percentile: float,
         value_filter: bool, filter_type: str, value_column: str, cutoff_value: float, analyse_column: str,
         top_row_number: int, distance_cutoff: float, temporal_cutoff: float, analyse_to_stdout: bool,
         analyse_to_log: bool, log_name: Optional[str], analyse_to_csv: bool, csv_name: Optional[str], plot_data: bool,
         save_data: bool) -> None:
    """Main function of NASA fire data module.
    Parameters are read from the SETTINGS dictionary in the settings.py file"""
    filter_func = {
        'equal': filter_dataset_by_equal_value,
        'below': filter_dataset_by_value_below,
        'above': filter_dataset_by_value_above
    }[filter_type]
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
            print(f'filtering dataset {name} by {value_column} {filter_type} {cutoff_value} ...')
            df = filter_func(df=df, value_column=value_column, cutoff_value=cutoff_value)
        if percentile_filter is True:
            print(f'filtering dataset {name} by {percentile_column} > {cutoff_percentile} percentile...')
            df = filter_dataset_by_percentile(df=df, percentile_column=percentile_column,
                                              cutoff_percentile=cutoff_percentile)
        if any(cond is True for cond in [analyse_to_stdout, analyse_to_log, analyse_to_csv]):
            print(f'analysing top rows for dataset {name}...')
            analysis_loop(df=df, output_dir=output_dir, analyse_column=analyse_column, top_row_number=top_row_number,
                          distance_cutoff=distance_cutoff, temporal_cutoff=temporal_cutoff,
                          analyse_to_stdout=analyse_to_stdout, analyse_to_log=analyse_to_log, log_name=log_name,
                          analyse_to_csv=analyse_to_csv, csv_name=csv_name)
        if plot_data is True:
            print(f'plotting dataset {name}...')
            plot_dataset(df=df, name=name)
        if save_data is True:
            print(f'saving dataset {name}...')
            save_dataset(df=df, name=name, output_dir=output_dir)
    # Shows resulting plots on the screen
    print('showing all data...')
    plt.show()


@lru_cache(maxsize=32)
def load_dataset(input_dir: str) -> Dict[str, pd.DataFrame]:
    """Loads dataset from zip files. Returns a dictionary in the format {instrument name: pandas DataFrame}"""
    dataset = {}
    instrument_names = ('MODIS', 'VIIRS')
    zip_files = [os.path.join(input_dir, z) for z in os.listdir(input_dir) if z.endswith('.zip')]
    for instrument_name, zip_file in zip(instrument_names, zip_files):
        with ZipFile(zip_file) as zip_input:
            dataset[instrument_name] = load_csvs_from_zip_file(zip_file=zip_input)
    return dataset


@lru_cache(maxsize=32)
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


def filter_dataset_by_equal_value(df: pd.DataFrame, value_column: str, cutoff_value: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column are equal to the value_cutoff"""
    return df.loc[df[value_column] == cutoff_value]


def filter_dataset_by_value_below(df: pd.DataFrame, value_column: str, cutoff_value: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column are below the value_cutoff"""
    return df.loc[df[value_column] < cutoff_value]


def filter_dataset_by_value_above(df: pd.DataFrame, value_column: str, cutoff_value: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column are above the value_cutoff"""
    return df.loc[df[value_column] > cutoff_value]


def filter_dataset_by_percentile(df: pd.DataFrame, percentile_column: str, cutoff_percentile: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column belong to the top percentile,
    based on the percentile argument"""
    cutoff_value = np.percentile(df[percentile_column], cutoff_percentile)
    return df.loc[df[percentile_column] > cutoff_value]


# noinspection PyTypeChecker
def analysis_loop(df: pd.DataFrame, output_dir: str, analyse_column: str, top_row_number: int, distance_cutoff: float,
                  temporal_cutoff: float, analyse_to_stdout: bool, analyse_to_log: bool, log_name: Optional[str],
                  analyse_to_csv: bool, csv_name: Optional[str]) -> None:
    """Main analysis loop"""
    base_results_path = os.path.join(output_dir, 'batch_results')  # TODO: remove this once batch is finished
    if not os.path.exists(base_results_path):
        os.mkdir(base_results_path)
    if log_name is None:
        log_name = 'log.txt'
    if csv_name is None:
        csv_name = 'firepoints.csv'
    log_path = os.path.join(base_results_path, log_name)
    csv_path = os.path.join(base_results_path, csv_name)
    with conditional_open(log_path, 'w', condition=analyse_to_log) as logfile, \
            conditional_open(csv_path, 'w', condition=analyse_to_csv) as csvfile:
        if csvfile is not None:
            add_header(csvfile=csvfile)
        for index, top_point in yield_top_points(df=df, column_name=analyse_column, n=top_row_number):
            group_id = int(index) + 1
            close_points = get_close_points(df=df, top_point=top_point, distance_cutoff=distance_cutoff,
                                            temporal_cutoff=temporal_cutoff)
            if analyse_to_stdout:
                to_stdout(top_point=top_point, close_points=close_points, distance_cutoff=distance_cutoff,
                          temporal_cutoff=temporal_cutoff, group_id=group_id)
            to_log(logfile=logfile, top_point=top_point, close_points=close_points, distance_cutoff=distance_cutoff,
                   temporal_cutoff=temporal_cutoff, group_id=group_id)
            to_csv(csvfile=csvfile, top_point=top_point, close_points=close_points, group_id=group_id)


def add_header(csvfile: TextIOWrapper) -> None:
    """Adds the first line (table header) to the output csv file"""
    csvfile.write('frp,day,time,latitude,longitude,instrument,is_top_point,group_id\n')


def yield_top_points(df: pd.DataFrame, column_name: str, n: int) -> Generator[Tuple[int, FirePoint], None, None]:
    """Yields the top k rows from data as FirePoint instances, regarding values in the column_name column"""
    top_df = df.sort_values(by=column_name).tail(n)
    for index, row in top_df.iterrows():
        yield index, FirePoint.from_dataset_row(row=row)


def get_close_points(df: pd.DataFrame, top_point: FirePoint, distance_cutoff: float,
                     temporal_cutoff: float) -> List[FirePoint]:
    """Analyses dataset k top values by finding points closest to it"""
    close_points = []
    for index, row in df.iterrows():  # TODO: this is very slow, since we have to iterate over the whole dataset
        candidate = FirePoint.from_dataset_row(row=row)
        if top_point.is_neighbor_of(candidate, time_delta=temporal_cutoff, distance_delta=distance_cutoff):
            close_points.append(candidate)
    return close_points


def to_stdout(top_point: FirePoint, close_points: List, distance_cutoff: float, temporal_cutoff: float,
              group_id: int) -> None:
    """Outputs information for FirePoint and its close points to standard output"""
    print(f'Top point: {top_point}')
    print(f'group_id: {group_id}')
    print(f'{len(close_points)} points within distance={distance_cutoff} km, time= +-{temporal_cutoff} days:')
    for point in close_points:
        print(point)
    print('\n')


def to_log(logfile: Optional[TextIOWrapper], top_point: FirePoint, close_points: List[FirePoint],
           distance_cutoff: float, temporal_cutoff: float, group_id: int) -> None:
    """Outputs information for FirePoint and its close points to log file.
    Returns early if the user chose not to do so"""
    if logfile is None:
        return
    logfile.write(f'Top point: {top_point}')
    logfile.write('\n')
    logfile.write(f'group_id: {group_id}')
    logfile.write('\n')
    logfile.write(f'{len(close_points)} points within distance={distance_cutoff} km, time= +-{temporal_cutoff} days:')
    logfile.write('\n')
    for point in close_points:
        logfile.write(str(point))
        logfile.write('\n')
    logfile.write('\n')


def to_csv(csvfile: Optional[TextIOWrapper], top_point: FirePoint, close_points: List[FirePoint],
           group_id: int) -> None:
    """Outputs information for FirePoint and its close points to csv file.
    Returns early if the user chose not to do so"""
    if csvfile is None:
        return
    csvfile.write(top_point.as_csv_row(is_top_point=True, group_id=group_id))
    csvfile.write('\n')
    for point in close_points:
        csvfile.write(point.as_csv_row(is_top_point=False, group_id=group_id))
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
