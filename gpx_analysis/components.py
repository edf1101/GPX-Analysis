"""
This file contains functions used for doing geographic calculations
"""
import math
from copy import deepcopy
import colorsys
import matplotlib.colors

try:
    from gpx_analysis import gpx_parser as gpx
except ImportError:
    import gpx_parser as gpx


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
    a_val = math.sin(d_lat / 2) * math.sin(d_lat / 2) + \
        math.cos(latitude1 * math.pi / 180) * math.cos(latitude2 * math.pi / 180) * \
        math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c_val = 2 * math.atan2(math.sqrt(a_val), math.sqrt(1 - a_val))
    return radius * c_val * 1000  # meters


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

    bounds = get_track_bounds(modify_track)
    bottom_left = (bounds[3], bounds[2])

    # Convert all the points to meters from the bottom left
    for point in all_track_points:
        point_lon, point_lat = point.get_position_degrees()

        new_y = geo_distance(bottom_left[1], bottom_left[0], point_lat, bottom_left[0])
        new_x = geo_distance(bottom_left[1], bottom_left[0], bottom_left[1], point_lon)

        point.set_position_standard(new_x, new_y)  # Update the point

    return modify_track


def get_track_bounds(input_track: gpx.Track) -> tuple:
    """
    Return the bounding regions of the track

    :param input_track: The input track
    :return: North latitude, east longitude, south latitude, west longitude
    """
    # Get the bottom left of the track
    all_track_points = input_track.get_track_points()

    west = min(i.get_position_degrees()[0] for i in all_track_points)
    south = min(i.get_position_degrees()[1] for i in all_track_points)
    east = max(i.get_position_degrees()[0] for i in all_track_points)
    north = max(i.get_position_degrees()[1] for i in all_track_points)

    return north, east, south, west


def union_bounds(bounds1: tuple, bounds2: tuple) -> tuple:
    """
    Return the union of two bounds

    :param bounds1: The first bounds
    :param bounds2: The second bounds
    :return: The union of the two bounds
    """
    return (max(bounds1[0], bounds2[0]),
            max(bounds1[1], bounds2[1]),
            min(bounds1[2], bounds2[2]),
            min(bounds1[3], bounds2[3]))


def lighten_color(colour, amount=0.5):
    """
    lightens a given rgb colour

    :param colour: RGB tuple colour
    :param amount: the lower the number below 0 the lighter
    :return: An rgb colour lightened
    """

    colour = colorsys.rgb_to_hls(*matplotlib.colors.to_rgb(colour))
    return colorsys.hls_to_rgb(colour[0], 1 - amount * (1 - colour[1]), colour[2])
