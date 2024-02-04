"""
This module contains the functions needed for the sporting analysis
eg. getting position,velocity etc. at a given time
"""

try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import components as geo
except ImportError:
    import gpx_parser as gpx
    import components as geo


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


def get_surrounding_points_at_time(track: gpx.Track, time: float) \
        -> tuple[gpx.TrackPoint | None, gpx.TrackPoint | None]:
    """
    Returns the two points either side of a given time

    :param track: The input track
    :param time: The time to get the points at
    :return: Two gpx.Trackpoint points
    """


    track_points = track.get_track_points()

    # Iterate through all points to find the two points either side of the position
    # Also get the time the boat was at these two points

    point_id_above, point_id_below = None, None
    for point_id, point in enumerate(track_points):
        if point.get_relative_time() > time:
            point_id_above = point_id
            point_id_below = point_id - 1
            return track_points[point_id_below], track_points[point_id_above]

    return None, None


def get_position_at_time(track: gpx.Track, time: float) -> tuple[float, float]:
    """
    Returns the position on a gpx track at a given time

    :param track: The track to get the position from
    :param time: The time to get the position at
    :return: The lat lon position at the given time
    """

    track_points = track.get_track_points()

    last_point = track_points[-1]
    if time >= last_point.get_relative_time():
        # WARNING this time is after the end time it is technically invalid
        return last_point.get_position_degrees()

    # Iterate through all points to find the two points either side of the position
    # Also get the time the boat was at these two points

    point_below, point_above = get_surrounding_points_at_time(track, time)
    time_below = point_below.get_relative_time()
    time_above = point_above.get_relative_time()

    # Interpolate the position between the two points
    position_above = point_above.get_position_degrees()
    position_below = point_below.get_position_degrees()
    new_lat = map_ranges(time, time_below, time_above, position_below[0], position_above[0])
    new_lon = map_ranges(time, time_below, time_above, position_below[1], position_above[1])

    return new_lat, new_lon


def get_speed_at_time(track: gpx.Track, time: float) -> float:
    """
    Returns the speed on a gpx track at a given time

    :param track: The track to get the speed from
    :param time: The time to get the speed at
    :return: The speed at the given time
    """

    track_points = track.get_track_points()

    last_point = track_points[-1]
    if time > last_point.get_relative_time():
        # WARNING this time is after the end time it is technically invalid
        return 0.1

    # Get the points above and below
    point_below, point_above = get_surrounding_points_at_time(track, time)

    try:
        position_below = point_below.get_position_degrees()
        position_above = point_above.get_position_degrees()
    except AttributeError:  # when out of range this happens
        return 0.1

    time_below = point_below.get_relative_time()
    time_above = point_above.get_relative_time()
    time_delta = time_above - time_below

    # Get distance between two points
    distance = geo.geo_distance(position_below[0], position_below[1],
                                position_above[0], position_above[1])

    speed = distance / time_delta  # Speeds are always in m/s

    return round(speed, 2)


def get_cadence_at_time(track: gpx.Track, time: float) -> float:
    """
    Returns the cadence on a gpx track at a given time

    :param track: The track to get the cadence from
    :param time: The time to get the cadence at
    :return: The cadence at the given time
    """

    track_points = track.get_track_points()

    last_point = track_points[-1]
    if time > last_point.get_relative_time():
        # WARNING this time is after the end time it is technically invalid
        return 0.0

    # Get the points above and below
    point_below, point_above = get_surrounding_points_at_time(track, time)

    try:
        cadence_below = point_below.get_cadence()
        cadence_above = point_above.get_cadence()
    except AttributeError:  # When out of range
        return 0.0

    time_below = point_below.get_relative_time()
    time_above = point_above.get_relative_time()

    cadence = round(map_ranges(time, time_below, time_above, cadence_below, cadence_above), 1)

    return cadence


def get_cumulative_dist_at_time(track: gpx.Track, time: float) -> float:
    """
    Returns the cumulative distance on a gpx track at a given time

    :param track: The track to get the cumulative distance from
    :param time: The time to get the cumulative distance at
    :return: The cumulative distance at the given time (in meters)
    """
    track_points = track.get_track_points()

    total_dist = 0
    # Iterate through all points until I get to one greater than my time

    for point_id, point in enumerate(track_points[1:]):  # Ignore the first item as we use it
        # Is this the set of points I'm currently between at this time
        point_id = point_id + 1  # So enumerate id starts at 1

        if point.get_relative_time() > time:
            # Yes get the distance I am from the point before and add it on then return
            point_below = track_points[point_id - 1]
            time_below = point_below.get_relative_time()
            time_above = point.get_relative_time()
            dist_between = abs(geo.geo_distance(point.get_position_degrees()[0],
                                                point.get_position_degrees()[1],
                                                point_below.get_position_degrees()[0],
                                                point_below.get_position_degrees()[1]))
            # print(dist_between)

            total_dist += map_ranges(time, time_below, time_above, 0, dist_between)
            break

        # No need for an else since it broke in the last if
        # No Add the distance between this point and the last point to the total distance
        point_below = track_points[point_id - 1]
        total_dist += abs(geo.geo_distance(point.get_position_degrees()[0],
                                           point.get_position_degrees()[1],
                                           point_below.get_position_degrees()[0],
                                           point_below.get_position_degrees()[1]))

    return round(total_dist, 2)


def get_total_distance(track: gpx.Track) -> float:
    """
    Returns the total distance of a track

    :param track: The track to get the distance from
    :return: The total distance of the track
    """

    return get_cumulative_dist_at_time(track, track.get_track_points()[-1].get_relative_time())


def convert_speed_units(speed: float, unit: str) -> float:
    """
    Converts the speed from m/s to another unit

    :param speed: The speed in m/s
    :param unit: The unit to convert to either: m/s, km/h, mph, s/500m or s/km
    :return: The speed in the new unit
    """

    if not isinstance(speed, float):
        raise TypeError("Speed must be a float")
    if not isinstance(unit, str):
        raise TypeError("Unit must be a string")

    speed = speed if speed != 0 else 0.1

    if unit == "m/s":
        return round(speed, 1)
    if unit == "km/h":
        return round(speed * 3.6, 1)
    if unit == "mph":
        return round(speed * 2.237, 1)
    if unit == "s/500m":
        total = round(500 / speed, 1)
        return total
    if unit == "s/km":
        total = round(1000 / speed, 1)
        return total

    raise ValueError("Unit must be one of: m/s, km/h, mph, s/500m or s/km")
