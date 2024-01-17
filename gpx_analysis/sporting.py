"""
This module contains the functions needed for the sporting analysis
eg. getting position,velocity etc. at a given time
"""

# import geo_components as geo
import gpx_parser as gpx


def map_ranges(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    Maps a value from one range to another

    :param value: The value within the input range
    :param in_min: The lower end of the input range
    :param in_max: The upper end of the input range
    :param out_min: The lower end of the output range
    :param out_max: The upper end of the output range
    :return: The value mapped to the output range
    """
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def get_position_at_time(track: gpx.Track, time: float) -> tuple[float, float]:
    """
    Returns the position on a gpx track at a given time

    :param track: The track to get the position from
    :param time: The time to get the position at
    :return: The lat lon position at the given time
    """

    track_points = track.get_track_points()

    last_point = track_points[-1]
    if time > last_point.get_relative_time():
        # WARNING this time is after the end time it is technically invalid
        return last_point.get_position_degrees()

    # Iterate through all points to find the two points either side of the position
    # Also get the time the boat was at these two points

    point_id_above, point_id_below = None, None
    time_above, time_below = 0, 0
    for point_id, point in enumerate(track_points):
        if point.get_relative_time() > time:
            point_id_above = point_id
            point_id_below = point_id - 1
            time_above = point.get_relative_time()
            time_below = track_points[point_id_below].get_relative_time()
            break

    # Interpolate the position between the two points
    point_above = track_points[point_id_above].get_position_degrees()
    point_below = track_points[point_id_below].get_position_degrees()
    new_lat = map_ranges(time, time_below, time_above, point_below[0], point_above[0])
    new_lon = map_ranges(time, time_below, time_above, point_below[1], point_above[1])

    return new_lat, new_lon
