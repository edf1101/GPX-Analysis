"""
This file contains functions used for doing geographic calculations
"""
import math
import gpx_parser as gpx
from copy import deepcopy


def geo_distance(latitude1: float, longitude1: float, latitude2: float, longitude2: float) -> float:
    """
    This function calculates the distance between two points in the world in meters

    :param latitude1: The latitude of the first point
    :param longitude1: The longitude of the first point
    :param latitude2: The latitude of the second point
    :param longitude2: The longitude of the second point
    :return: The distance between the two points in meters
    """

    radius = 6378.137  # Radius of earth in KM
    d_lat = latitude2 * math.pi / 180 - latitude1 * math.pi / 180
    d_lon = longitude2 * math.pi / 180 - longitude1 * math.pi / 180
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + \
        math.cos(latitude1 * math.pi / 180) * math.cos(latitude2 * math.pi / 180) * \
        math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c
    return d * 1000  # meters


def standardise_gpx_distances(input_track: gpx.Track) -> gpx.Track:
    """
    This function converts the original (lat lon) distances in the track into meters
    where 0,0 is bottom left of the track

    :param input_track: The already parsed GPX class
    :return: the modified track
    """

    # Deepcopy the track so we don't modify the original
    modify_track = deepcopy(input_track)

    # Get the bottom left of the track
    all_track_points = modify_track.get_track_points()

    most_left = min([i.get_position()[0] for i in all_track_points])
    most_bottom = min([i.get_position()[1] for i in all_track_points])
    bottom_left = (most_left, most_bottom)

    # Convert all the points to meters from the bottom left
    for point in all_track_points:
        point_lon, point_lat = point.get_position()

        new_y = geo_distance(bottom_left[1], bottom_left[0], point_lat, bottom_left[0])
        new_x = geo_distance(bottom_left[1], bottom_left[0], bottom_left[1], point_lon)

        point.set_position(new_x, new_y)  # Update the point

    return modify_track
