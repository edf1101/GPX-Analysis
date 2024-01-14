"""
This module parses a GPX file into the track class which is made up of track points
(another new class).
"""

import xml.etree.ElementTree as ET
from datetime import datetime


class TrackPoint:
    """
    This class represents a track point in a GPX file.
    Also features cadence and time.
    """

    def __init__(self, lat: float, lon: float, cad: int, raw_time: str):
        """
        init function for setting up a track point

        :param lat: World latitude position
        :param lon: World longitude posisiton
        :param cad: The cadence (stroke rate)
        :param raw_time: the string form of the UTC time
        """
        self.lat = lat
        self.lon = lon
        self.cad = cad

        self.time = None
        self.formatted_time = datetime.strptime(raw_time, '%Y-%m-%dT%H:%M:%SZ')

    def get_latitude(self) -> float:
        """
        Getter for latitude

        :return: the latitude of the track point
        """
        return self.lat

    def get_longitude(self) -> float:
        """
        Getter for longitude

        :return: the longitude of the track point
        """
        return self.lon

    def get_cadence(self) -> int:
        """
        Getter for cadence

        :return: the cadence of the track point
        """
        return self.cad

    def get_formatted_time(self) -> datetime:
        """
        Getter for formatted datetime time

        :return: The datetime time
        """
        return self.formatted_time

    def set_relative_time(self, relative_time: float) -> None:
        """
        Setter for relative time

        :param relative_time: the relative time of the track point
        :return: None
        """
        self.time = relative_time

    def get_relative_time(self) -> float:
        """
        Getter for relative time

        :return: the relative time of the track point
        """
        return self.time


class Track:
    """
    This class represents a track in a GPX file.
    """

    def __init__(self, file_name: str):
        """
        This init func creates the track by parsing the gpx file

        :param file_name: path to gpx file
        """
        self.file_name = file_name
        self.namespaces = {'gpx': 'http://www.topografix.com/GPX/1/1',
                           'gpxdata': 'http://www.cluetrust.com/XML/GPXDATA/1/0'}
        self.track_points = []
        self.__create_track_points()

        self.redo_timings()

    def __create_track_points(self) -> None:
        """
        This function parses the gpx file and creates track points

        :return: None
        """
        tree = ET.parse(self.file_name)
        root = tree.getroot()

        # Define namespaces

        # Iterate through each track segment and track point
        for track_segment in root.findall(".//gpx:trkseg", namespaces=self.namespaces):
            for point in track_segment.findall("gpx:trkpt", namespaces=self.namespaces):
                lat = float(point.get('lat'))
                lon = float(point.get('lon'))

                time = None
                if point.find("gpx:time", namespaces=self.namespaces) is not None:
                    time = point.find("gpx:time", namespaces=self.namespaces).text

                cadence_element = point.find("gpx:extensions/gpxdata:cadence",
                                             namespaces=self.namespaces)

                if cadence_element is not None:
                    cadence = cadence_element.text
                else:
                    cadence_element = point.find("gpx:extensions/gpx:cadence",
                                                 namespaces=self.namespaces)
                    cadence = cadence_element.text if cadence_element is not None else None

                self.track_points.append(TrackPoint(lat, lon, int(cadence), time))

    def redo_timings(self) -> None:
        """
        Convert all the original datetime times into a relative time made of just seconds as a float

        :return: None
        """
        all_original_times = [i.get_formatted_time() for i in self.track_points]
        min_time = min(all_original_times)

        for point in self.track_points:
            point.set_relative_time((point.formatted_time - min_time).total_seconds())

    def get_track_points(self) -> list[TrackPoint]:
        """
        Getter for track points

        :return: The list of track points
        """
        return self.track_points
