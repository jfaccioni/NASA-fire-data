import os
from typing import Generator

import geopandas
import matplotlib.pyplot as plt
import seaborn as sns

use_top_points = True
instrument = 'VIIRS'

INPUT_FILE = f'local/{instrument}10k.csv' if not use_top_points else f'output/results/firepoints_{instrument}.csv'


def geopandas_demo(input_file: str) -> None:
    """geopandas module demo"""
    print('loading data...')
    fig, ax = plt.subplots()
    gdf = get_geodataframe(input_file=input_file)
    gdf['datetime'] = gdf['date'] + ' ' + gdf['time']
    draw_brazil_axes(ax=ax)
    for top_slice in yield_top_point_slices(data=gdf):
        sns.relplot(figure=fig, ax=ax, data=top_slice, x='longitude', y='latitude', hue='datetime', palette='Blues_d')
    plt.show()


def get_geodataframe(input_file: str) -> geopandas.GeoDataFrame:
    """Returns a GeoDataFrame from an input file"""
    df = geopandas.read_file(input_file)
    for coord in ('latitude', 'longitude', 'frp'):
        df.loc[:, coord] = df[coord].apply(float)
    df.loc[:, 'is_top_point'] = df['is_top_point'].map({'True': True, 'False': False})
    return geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df.longitude, df.latitude))


def draw_brazil_axes(ax: plt.Axes, show_ucs: bool = False) -> None:
    """Returns an Axes instance containing a map from Brazil"""
    for folder, subfolders, files in os.walk('resources'):
        shapefiles = [s for s in os.listdir(folder) if s.endswith('.shp')]
        for shapefile in shapefiles:
            if 'ucs' in shapefile and show_ucs is False:
                continue
            path = os.path.join(folder, shapefile)
            data = geopandas.read_file(path)
            data.plot(ax=ax, color='white', edgecolor='black')


def yield_top_point_slices(data: geopandas.GeoDataFrame) -> Generator[geopandas.GeoDataFrame, None, None]:
    """Yields slices of the GeoDataFrame containing the top FRP point and the corresponding nearby points"""
    start = 0
    for index, row in data.iterrows():
        if index == 0:  # avoid yielding first row by itself
            continue
        if row.is_top_point is True:
            stop = index
            yield data.iloc[start:stop, :]
            start = stop


if __name__ == '__main__':
    geopandas_demo(input_file=INPUT_FILE)
