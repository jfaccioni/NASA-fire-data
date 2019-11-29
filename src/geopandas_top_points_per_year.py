from __future__ import annotations

import os
from calendar import month_abbr
from functools import lru_cache
from typing import Generator, TYPE_CHECKING, Union
from zipfile import ZipFile
import datetime
import numpy as np
import geopandas
import matplotlib.pyplot as plt
import pandas as pd

from src.utils import ignore_pandas_warning

if TYPE_CHECKING:
    from io import TextIOWrapper
    from geopandas import GeoDataFrame

SETTINGS = {
    # I/O SETTINGS
    'input_dir': 'data',     # where the zip files are located
    'output_dir': 'output/geopandas_top_points',  # where to save output (if any)
    # FILTER SETTINGS
    'filter_type': 'equal',  # How to apply filter ('equal', 'below' or 'above')
    'value_column': 'year',  # column for filtering
    'cutoff_value': 2015,    # filter selects values higher than this
    # ANALYSIS SETTINGS
    'analyse_column': 'frp',    # column for sorting top values
    'top_row_number': 100,       # number of top FirePoints to analyse
    'distance_cutoff': 10,      # distance (in kilometers) for considering a FirePoint as being close to another
    'temporal_cutoff': 30,      # time window (in days) for considering a FirePoint as being close to another
}


def main(input_dir: str, output_dir: str, filter_type: str, value_column: str, cutoff_value: float,
         analyse_column: str, top_row_number: int, distance_cutoff: float, temporal_cutoff: float) -> None:
    """Main function of NASA fire data module.
    Parameters are read from the SETTINGS dictionary in the settings.py file"""
    print('creating output directory...')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    print('loading data...')
    df = load_dataset(input_dir=input_dir)

    print(f'Adding date columns to dataset...')
    add_dates(df=df)

    print(f'filtering dataset by {value_column} {filter_type} {cutoff_value} ...')
    df = filter_dataset(df=df, value_column=value_column, cutoff_value=cutoff_value)

    print('converting to geopandas GeoDataFrame...')
    gdf = to_geopandas(df=df)

    print(f'selecting top FRP points...')
    for instrument in ('MODIS', 'VIIRS'):
        instrument_gdf = filter_by_instrument(gdf=gdf, instrument=instrument)
        analyse_dataset(gdf=instrument_gdf, output_dir=output_dir, analyse_column=analyse_column,
                        top_row_number=top_row_number, distance_cutoff=distance_cutoff,
                        temporal_cutoff=temporal_cutoff, cutoff_value=cutoff_value, instrument=instrument)
    # Shows resulting plots on the screen
    print('showing all data...')
    plt.show()


@lru_cache(maxsize=32)
def load_dataset(input_dir: str) -> pd.DataFrame:
    """Loads dataset from zip files. Returns a dictionary in the format {instrument name: pandas DataFrame}"""
    datasets = []
    zip_files = [os.path.join(input_dir, z) for z in os.listdir(input_dir) if z.endswith('.zip')]
    for zip_file in zip_files:
        with ZipFile(zip_file) as zip_input:
            datasets.append(load_csvs_from_zip_file(zip_file=zip_input))
    return pd.concat(datasets, sort=False, ignore_index=True)


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
    add_date(df=df, date_col='acq_date')
    add_time(df=df, time_col='acq_time')
    add_datetime(df=df, date_col='acq_date', time_col='acq_time')
    add_month_names(df=df, month_col='month')


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_date(df: pd.DataFrame, date_col: str) -> None:
    """Adds year, month and day columns to DataFrame, based on a date string column formatted as YYYY-MM-DD"""
    for index, date in enumerate(['year', 'month', 'day']):
        df[date] = df[date_col].apply(lambda x: int(x.split('-')[index]))


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_time(df: pd.DataFrame, time_col: str) -> None:
    """Adds hour and minute columns to DataFrame, based on an UTC hour/minute integer"""
    df['hour'] = df[time_col].apply(hour_from_utc_integer)
    df['minute'] = df[time_col].apply(str).str[-2:].apply(int)


def hour_from_utc_integer(time: int) -> int:
    """Returns the number of hours from an UTC integer"""
    time_str = str(time)
    try:
        return int(time_str[:len(time_str)-2])  # digits after excluding two last digits
    except ValueError:  # no digits left - hour is zero
        return 0


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_datetime(df: pd.DataFrame) -> None:
    """Adds column with datetime instances to DataFrame based on a date and time column (strings)"""
    df['datetime'] = np.vectorize(datetime.datetime)(df['year'], df['month'], df['day'], df['hour'], df['minute'])


@ignore_pandas_warning  # ignores SettingWithCopyWarning
def add_month_names(df: pd.DataFrame, month_col: str) -> None:
    """Adds month_name column to DataFrame based on a date string column formatted as YYYY-MM-DD"""
    df['month_name'] = df[month_col].apply(month_abbr)


def filter_dataset(df: pd.DataFrame, value_column: str, cutoff_value: float) -> pd.DataFrame:
    """Filters a DataFrame by selecting rows whose values in the column_name column are equal to the value_cutoff"""
    return df.loc[df[value_column] == cutoff_value]


def to_geopandas(df: pd.DataFrame) -> GeoDataFrame:
    """Converts a pandas DataFrame to a geopandas GeoDataFrame"""
    return geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.longitude, df.latitude))


def filter_by_instrument(gdf: GeoDataFrame, instrument: str) -> GeoDataFrame:
    """Returns a GeoDataFrame containing only rows from a specific instrument"""
    return gdf.loc[gdf['instrument'] == instrument]


# noinspection PyTypeChecker
def analyse_dataset(gdf: GeoDataFrame, output_dir: str, analyse_column: str, top_row_number: int,
                    distance_cutoff: float, temporal_cutoff: float, cutoff_value: Union[float, str],
                    instrument: str) -> None:
    """Selects the top FRP points and saves to """
    csv_path = os.path.join(output_dir, f'{instrument}_{cutoff_value}_firepoints.csv')
    for index, top_point in enumerate(yield_top_points(gdf=gdf, column_name=analyse_column, n=top_row_number), 1):
        dist_subset = apply_distance_cutoff(gdf=gdf, top_point=top_point, distance_cutoff=distance_cutoff)
        time_subset = apply_temporal_cutoff(gdf=dist_subset, top_point=top_point, temporal_cutoff=temporal_cutoff)
        time_subset.reset_index(inplace=True)
        append_series_to_top_of_dataframe(df=time_subset, series=top_point)
        time_subset.to_csv(csv_path)


def add_header(csvfile: TextIOWrapper) -> None:
    """Adds the first line (table header) to the output csv file"""
    csvfile.write('frp,day,time,latitude,longitude,instrument,is_top_point,group_id\n')


def yield_top_points(gdf: GeoDataFrame, column_name: str, n: int) -> Generator[pd.Series, None, None]:
    """Yields the top n rows from the GeoDataFrame, regarding values in the column_name column"""
    top_points = gdf.sort_values(by=column_name).tail(n)
    for _, row in top_points.iterrows():
        yield row


def apply_distance_cutoff(gdf: GeoDataFrame, top_point: pd.Series, distance_cutoff: float) -> GeoDataFrame:
    """Returns a GeoDataFrame of points inside top_point, considering the distance cutoff argument"""
    distance = km_to_degrees(km=distance_cutoff)
    buffer = top_point.geometry.buffer(distance)
    return gdf.loc[gdf['geometry'].apply(buffer.contains)]


def km_to_degrees(km: float) -> float:
    """Returns the result of the conversion from km to degrees across the Earth's surface. Answer from:
    https://stackoverflow.com/questions/5217348/how-do-i-convert-kilometres-to-degrees-in-geodjango-geos"""
    return (km / 40_000) * 360


def apply_temporal_cutoff(gdf: GeoDataFrame, top_point: pd.Series, temporal_cutoff: float) -> GeoDataFrame:
    """Returns a GeoDataFrame of points inside top_point, considering the distance cutoff argument"""
    delta = days_to_seconds(days=temporal_cutoff)
    return gdf.loc[abs(gdf['datetime'] - top_point['datetime']) <= delta]


def days_to_seconds(days: float) -> float:
    """Returns the result of the conversion from days to seconds"""
    return days * 24 * 60 * 60


def append_series_to_top_of_dataframe(df: pd.DataFrame, series: pd.Series) -> None:
    """Inserts a pandas Series as the first row of a pandas DataFrame (or GeoDataFrame).
    Assumes that the DataFrame has indices from 0 to len(df) -1"""
    df.loc[-1] = series
    df.index = df.index + 1
    df.sort_index(inplace=True)


if __name__ == '__main__':
    main(**SETTINGS)