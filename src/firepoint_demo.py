import pandas as pd
from random import randint
from src.firepoint import FirePoint
from geopy import distance


def firepoint_demo(instrument: str = 'VIIRS'):
    """FirePoint class demo"""
    print('loading data...')
    viirs = pd.read_csv(f'local/{instrument}.csv', low_memory=False)
    print('Done loading!')
    points = {1: None, 2: None}
    for point_number in points:
        p = randint(0, len(viirs))
        r = viirs.iloc[p]
        fp = FirePoint(instrument=instrument, day=r.acq_date, time=r.acq_time, latitude=r.latitude,
                       longitude=r.longitude)
        points[point_number] = fp
    p1, p2 = points.values()
    print(f'FirePoint 1: {p1}')
    print(f'FirePoint 2: {p2}')
    d = distance.distance(p1.point, p2.point)
    print(f'Spatial Distance: {d.km} Km')
    t = abs(p1.date - p2.date)
    print(f'Temporal Distance: {t}')
    max_dist = 2000  # Km
    max_time = 3650  # Days
    are_close = p1.is_neighbor_of(other=p2, distance_delta=max_dist, time_delta=max_time)
    print('Are they close?')
    print(f'Considering point within {max_dist} kilometers and {max_time} days as being close, '
          f'the points ARE{"" if are_close else " NOT"} close')


if __name__ == '__main__':
    firepoint_demo()
