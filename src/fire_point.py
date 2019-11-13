from __future__ import annotations

from typing import TYPE_CHECKING

from geopy import Point, distance
from datetime import datetime

if TYPE_CHECKING:
    import pandas as pd


class FirePoint:
    """Class representing a possible fire in Brazil"""
    pixel_size = {
        'MODIS': 1,     # in kilometers
        'VIIRS': 0.375  # in kilometers
    }

    # noinspection PyInitNewSignature
    def __init__(self, instrument: str, day: str, time: int, latitude: float, longitude: float):
        """Initialization function for FirePoint class"""
        self.date = self.convert_to_datetime(day=day, time=time)
        self.point = Point(latitude=latitude, longitude=longitude)
        self.instrument = instrument
        self.radius = self.pixel_size[self.instrument]

    @classmethod
    def from_dataset_row(cls, row: pd.Series) -> FirePoint:
        """Alternative constructor for instantiating a FirePoint from a row of NASA's dataset"""
        return cls(instrument=row.instrument, day=row.acq_date, time=row.acq_time, latitude=row.latitude,
                   longitude=row.longitude)

    def __repr__(self) -> str:
        """String representation of a FirePoint instance"""
        return f'FirePoint(date={self.date}, point={self.point}, instrument={self.instrument}, radius={self.radius})'

    def convert_to_datetime(self, day: str, time: int) -> datetime:
        """Converts a day (YYYY-MM-DD) and time (UTC int) into a datetime object"""
        year, month, day = [int(d) for d in day.split('-')]
        hour = self.hour_from_utc_integer(time=time)
        minute = int(str(time)[-2:])
        return datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    @staticmethod
    def hour_from_utc_integer(time: int) -> int:
        """Returns the number of hours from an UTC integer"""
        time_str = str(time)
        try:
            return int(time_str[:len(time_str)-2])
        except ValueError:
            return 0

    def is_neighbor_of(self, other: FirePoint, time_delta: float, distance_delta: float):
        """Returns whether two FirePoint instances are close to each other, both spatially and temporally"""
        return (self.is_spatially_close_to(other=other, distance_delta=distance_delta) and
                self.is_temporally_close_to(other=other, time_delta=time_delta))

    def is_spatially_close_to(self, other: FirePoint, distance_delta: float) -> bool:
        """Returns whether two FirePoint instances are within a certain distance from one another"""
        distance_between_points = distance.distance(self.point, other.point).km  # in kilometers
        return distance_between_points < distance_delta

    def is_temporally_close_to(self, other: FirePoint, time_delta: float) -> bool:
        """Returns whether two FirePoint instances are within a certain time interval from one another"""
        time_between_points = abs(self.date - other.date)  # in days
        return time_between_points.total_seconds() < (time_delta * 3600 * 24)
