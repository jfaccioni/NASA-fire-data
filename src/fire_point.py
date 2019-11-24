from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from geopy import Point, distance

if TYPE_CHECKING:
    import pandas as pd


class FirePoint:
    """Class representing a possible fire in Brazil"""
    pixel_size = {
        'MODIS': 1,     # in kilometers
        'VIIRS': 0.375  # in kilometers
    }

    # noinspection PyInitNewSignature
    def __init__(self, data: Dict[str: Any]) -> None:
        """Initialization function for FirePoint class"""
        self._data = data
        self.date = self.convert_to_datetime(day=self.day, time=self.time)
        self.point = Point(latitude=self.latitude, longitude=self.longitude)
        self.radius = self.pixel_size[self.instrument]

    def __repr__(self) -> str:
        """String representation of a FirePoint instance"""
        return f'FirePoint(frp={self.frp}, date={self.date}, coords={self.coords}, instrument={self.instrument})'

    @classmethod
    def from_dataset_row(cls, row: pd.Series) -> FirePoint:
        """Alternative constructor for instantiating a FirePoint from a row of NASA's dataset"""
        return cls(data=row.to_dict())

    @property
    def day(self) -> str:
        """Returns the acquisition day as a YYYY-MM-DD string"""
        return self._data['acq_date']

    @property
    def time(self) -> int:
        """Returns the acquisition time as an 2 to 4 digit UTC integer.
        Last 2 digits are minutes, first 0 to 2 digits are hours (if present)."""
        return self._data['acq_time']

    @property
    def latitude(self) -> float:
        """Returns the latitude of the FirePoint instance"""
        return self._data['latitude']

    @property
    def longitude(self) -> float:
        """Returns the longitude of the FirePoint instance"""
        return self._data['longitude']

    @property
    def instrument(self) -> str:
        """Returns the instrument used to measure the FirePoint instance (MODIS or VIIRS)"""
        return self._data['instrument']

    @property
    def frp(self) -> float:
        """Returns the FRP value of the FirePoint instance"""
        return self._data['frp']

    @property
    def coords(self) -> str:
        """Returns a Google Maps-friendly coordinate string"""
        return str(self.point).replace(',', '').replace('m', '\'').replace('s', '\'\'')

    @staticmethod
    def hour_from_utc_integer(time: int) -> int:
        """Returns the number of hours from an UTC integer"""
        time_str = str(time)
        try:
            return int(time_str[:len(time_str)-2])  # digits after excluding two last digits
        except ValueError:  # no digits left - hour is zero
            return 0

    def convert_to_datetime(self, day: str, time: int) -> datetime:
        """Converts a day (YYYY-MM-DD) and time (UTC integer) into a datetime object"""
        year, month, day = [int(d) for d in day.split('-')]
        hour = self.hour_from_utc_integer(time=time)
        minute = int(str(time)[-2:])  # last two digits
        return datetime(year=year, month=month, day=day, hour=hour, minute=minute)

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

    def as_csv_row(self, is_top_point: bool) -> str:
        """Returns a csv row representation of the FirePoint instance"""
        day, time = str(self.date).split()
        return f'{self.frp},{day},{time},{self.latitude},{self.longitude},{self.instrument},{is_top_point}'
