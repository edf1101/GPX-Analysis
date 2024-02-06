"""
This module handles the graphing of the GPX file and the fetching of OSM tiles
"""
# pylint: disable=R0902

import math
import urllib.request
import io
import os.path
from sys import platform as sys_pf
import PIL.Image
import numpy as np
from appdirs import user_data_dir

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

try:
    from gpx_analysis import components as geo
    from gpx_analysis import gpx_parser as gpx
except ImportError:
    import components as geo
    import gpx_parser as gpx

# If we are on macos then run this to fix the issues
if sys_pf == 'darwin':
    matplotlib.use("TkAgg")


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    """
    Code for converting lat lon to tile number from
    https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

    :param lat_deg: Input latitude
    :param lon_deg: Input longitude
    :param zoom: OSM zoom level
    :return: the OSM tile position
    """
    lat_rad = math.radians(lat_deg)
    exp_zoom = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * exp_zoom)
    ytile = int((1.0 - math.log(math.tan(lat_rad) +
                                (1 / math.cos(lat_rad))) / math.pi) / 2.0 * exp_zoom)
    return xtile, ytile


def num2deg(xtile: int, ytile: int, zoom: int) -> tuple[float, float]:
    """
    Code for converting tile number to lat lon from
    https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

    :param xtile: The tile x coordinate
    :param ytile: The tile y corrdinate
    :param zoom: The osm zoom level
    :return: (latitude, longitude)
    """
    exp_zoom = 2.0 ** zoom
    lon_deg = xtile / exp_zoom * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / exp_zoom)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg


def get_img(x_coord: int, y_coord: int, zoom: int):
    """
    Get the image from the tile either from cache or downloading

    :param x_coord: The x tile index
    :param y_coord: The y tile index
    :param zoom: The zoom tile index
    :return: The image
    """

    # get the app data path and add the image cache folder on

    app_data_path = user_data_dir("GPX Analysis", 'edf1101')
    image_cache_dir = os.path.join(app_data_path, 'image_cache')

    # create the image cache if it doesn't already exist
    if not os.path.exists(image_cache_dir):
        os.makedirs(image_cache_dir)

    # Check if its cached first
    endings = ['jpg', 'jpeg', 'png']  # the acceptable filetypes to use
    img = None
    for f_type in endings:
        name = os.path.join(image_cache_dir, f'{zoom}-{y_coord}-{x_coord}.{f_type}')
        if os.path.isfile(name):
            img = PIL.Image.open(name)

    if img is None:  # Otherwise download it and cache
        image_url = (f'https://server.arcgisonline.com/ArcGIS/rest/services/'
                     f'World_Topo_Map/MapServer/tile/{zoom}/{y_coord}/{x_coord}')
        with urllib.request.urlopen(image_url) as response:
            img = PIL.Image.open(io.BytesIO(response.read()))
            path = os.path.join(image_cache_dir, f'{zoom}-{y_coord}-{x_coord}.jpg')
            img.save(path)  # Save as jpg into cache folder

    return img


def get_all_images_in_bounds(bounds) -> dict[tuple, PIL.Image]:
    """
    Get all the images in the bounds and put them in a dictionary with their
    tile index as the key

    :param bounds:  The bounds of the track (NESW)
    :return:  The collection of images as a dict key = image pos, value = image
    """

    bottom_left_tile_num = deg2num(bounds[3], bounds[2], 17)
    top_right_tile_num = deg2num(bounds[1], bounds[0], 17)

    tiles = {}
    for x_coord in range(bottom_left_tile_num[0] - 1, top_right_tile_num[0] + 1):
        for y_coord in range(top_right_tile_num[1] - 1, bottom_left_tile_num[1] + 1):
            if (x_coord, y_coord) not in tiles:
                tiles[(x_coord, y_coord)] = get_img(x_coord, y_coord, 17)

    return tiles


def get_all_images_near_track(track: gpx.Track) -> dict[tuple, PIL.Image]:
    """
    More Tile server friendly way of getting images, by only fetching the ones near the track

    :param track: The track to get images of nearby
    :return: The collection of images as a dict key = image pos, value = image
    """

    radius = 1

    tiles = {}  # a dict of the tile indexes we have found

    all_track_points = track.get_track_points()  # all the points we'll iterate through

    for point in all_track_points:
        pos = point.get_position_degrees()  # the point's degrees value
        tile_ind = deg2num(pos[0], pos[1], 17)

        # Look in a radius around this point
        for x_pos in range(tile_ind[0] - radius, tile_ind[0] + radius + 1):
            for y_pos in range(tile_ind[1] - radius, tile_ind[1] + radius + 1):

                # skip this position if we have already fetched it
                if (x_pos, y_pos) in tiles:
                    continue

                # check its within a smooth radius
                mag_sqr = pow(x_pos - tile_ind[0], 2) + pow(y_pos - tile_ind[1], 2)
                if mag_sqr > pow(radius + 0.5, 2):
                    continue

                tiles[(x_pos, y_pos)] = get_img(x_pos, y_pos, 17)

    return tiles


class MapClass:
    """
    Class for converting scales between the GPX file and the graph
    """

    def __init__(self):

        self.__fig, self.__ax = plt.subplots()
        self.__fig.set_size_inches(4.8, 4.8)

        self.tile_size = 50
        self.__image_dict = {}
        self.__raw_image_dict = {}

        self.gpx_bounds_deg = None
        self.tile_bounds_plt = None
        self.tile_bounds_deg = None

        self.__athletes = {}

    def reset(self) -> None:
        """
        Resets the map to a blank state

        :return: None
        """
        self.__ax.cla()
        self.tile_size = 50
        self.__image_dict = {}
        self.__raw_image_dict = {}

        self.gpx_bounds_deg = None
        self.tile_bounds_plt = None
        self.tile_bounds_deg = None

        self.__athletes = {}

        for axis in self.__fig.get_axes():
            axis.legend_ = None
            if axis.get_legend():
                axis.get_legend().remove()

    def add_athlete(self, athlete_key: str, athlete_value: dict) -> None:
        """
        Add a track to the graph handler instance

        :param athlete_key: The key that gets added to the dictionary (simple filename)
        :param athlete_value: The dict of athlete data
        :return: None
        """
        self.__athletes[athlete_key] = athlete_value

        # Add its bounds to the graph handler's bounds
        new_bounds = geo.get_track_bounds(athlete_value['track'])
        self.__set_gpx_bounds(new_bounds)

        # Redo the images for the graph handler with the new bounds
        self.__add_images(get_all_images_near_track(athlete_value['track']))

        self.__ax.cla()
        self.plot_images()
        for athlete in self.__athletes.values():
            self.draw_track(athlete['filename'], athlete['colour'])
        self.__draw_legend()

    def modify_athlete(self, athlete_key: str, new_value: dict) -> None:
        """
        gets called when an athlete changes something (either a colour or display name)

        :param athlete_key: The key to modify in the dictionary
        :param new_value: The new value
        :return: None
        """

        # modify new parts individually so we don't remove references to drawn tracks/ points
        self.__athletes[athlete_key]['colour'] = new_value['colour']
        self.__athletes[athlete_key]['display_name'] = new_value['display_name']

        # redo track / legend which contain old data / colours
        self.draw_track(athlete_key, new_value['colour'])
        self.__draw_legend()

    def modify_start_finish_times(self, athlete_key: str, start: float, finish: float) -> None:
        """
        Modifies the start and finish times for an athlete

        :param athlete_key: The key to modify in the dictionary
        :param start: The new start time
        :param finish: The new finish time
        :return: None
        """

        self.__athletes[athlete_key]['start_time'] = start
        self.__athletes[athlete_key]['finish_time'] = finish

        # redraw the track with new size
        self.draw_track(athlete_key, self.__athletes[athlete_key]['colour'])

    def remove_athlete(self, athlete_key: str) -> None:
        """
        Remove an athlete + track and points from the graph

        :param athlete_key: the dictionary key to remove
        :return: None
        """

        athlete_data = self.__athletes[athlete_key]

        # first remove any points if they have them
        if 'draw_point' in athlete_data:
            self.remove_point(athlete_key)

        # next remove any lines if they have them
        if 'draw_track' in athlete_data:
            self.__remove_drawn_track(athlete_key)

        # then we can remove them from the athletes dict
        del self.__athletes[athlete_key]

        # update the legend
        self.__draw_legend()

    def __add_images(self, _image_dict: dict[tuple[int, int], PIL.Image]) -> None:
        """
        Set the image dictionary

        :param _image_dict: The image dictionary
        """

        # Only add the new images to the dict
        for key, value in _image_dict.items():
            if key not in self.__raw_image_dict:
                self.__raw_image_dict[key] = value

        # recalibrate this dict
        self.__reindex_tiles()

    def __set_gpx_bounds(self, _gpx_bounds: tuple[int, int, int, int]) -> None:
        """
        Set the gpx bounds

        :param _gpx_bounds: The gpx bounds
        """

        if self.gpx_bounds_deg is None:  # If it hasn't been set yet just set it
            self.gpx_bounds_deg = _gpx_bounds
        else:  # Otherwise do a union of the two bounds
            self.gpx_bounds_deg = geo.union_bounds(_gpx_bounds, self.gpx_bounds_deg)

    def __set_tile_bounds(self) -> None:
        """
        Set the tile bounds based on the tile image array
        """
        if not self.__raw_image_dict:
            raise ValueError("Image dictionary not set")

        tile_indexes = self.__raw_image_dict.keys()

        # North (min y val since it goes up as you go down on OSM tiles)
        tile_ind_bounds = (min(i[1] for i in tile_indexes),  # north
                           max(i[0] for i in tile_indexes),  # east
                           max(i[1] for i in tile_indexes),  # south
                           min(i[0] for i in tile_indexes))  # west

        self.tile_bounds_plt = ((tile_ind_bounds[2] - tile_ind_bounds[0] + 1) * self.tile_size,
                                (tile_ind_bounds[1] - tile_ind_bounds[3] + 1) * self.tile_size,
                                0, 0)

        bottom_left = num2deg(tile_ind_bounds[3], tile_ind_bounds[2] + 1, 17)
        top_right = num2deg(tile_ind_bounds[1] + 1, tile_ind_bounds[0], 17)
        self.tile_bounds_deg = (top_right[0], top_right[1], bottom_left[0], bottom_left[1])

    def __reindex_tiles(self) -> None:
        """
        Make it so the bottom left tile is (0, 0) and then as it goes up and right
        It increments(1,1) etc ...
        """
        # Make sure we set tile bounds before we remove original tile indexes in this func
        self.__set_tile_bounds()

        tile_indexes = self.__raw_image_dict.keys()

        # North (min y val since it goes up as you go down on OSM tiles)
        tile_ind_bounds = (min(i[1] for i in tile_indexes),  # north
                           max(i[0] for i in tile_indexes),  # east
                           max(i[1] for i in tile_indexes),  # south
                           min(i[0] for i in tile_indexes))  # west

        # Go through the dict and remake it with keys starting at (0, 0)
        new_dict = {}
        for old_key, value in self.__raw_image_dict.items():
            new_key = (old_key[0] - tile_ind_bounds[3], tile_ind_bounds[2] - old_key[1])
            new_dict[new_key] = value

        self.__image_dict = new_dict

    def plot_images(self) -> None:
        """
        Plots all the images in the image dictionary
        :return: None
        """

        for tile_index, image in self.__image_dict.items():
            self.__ax.imshow(np.asarray(image), extent=(tile_index[0] * self.tile_size,
                                                        (tile_index[0] + 1) * self.tile_size,
                                                        tile_index[1] * self.tile_size,
                                                        (tile_index[1] + 1) * self.tile_size))

    def __remove_axis(self) -> None:
        """
        Removes the axis from a graph

        :return: None
        """
        self.__ax.get_xaxis().set_visible(False)
        self.__ax.get_yaxis().set_visible(False)

    def get_figure(self) -> plt.Figure:
        """
        Return the figure

        :return: The figure
        """
        self.__remove_axis()
        self.__fig.tight_layout()
        # self.__fig.set_dpi(100)
        return self.__fig

    def scale_zoom(self, input_value: float) -> float:
        """
        This takes an input zoom level and scales it exponentially to be max
        the max size of the image

        :param input_value: input value between 0 and 1
        :return: the scaled zoom value
        """

        smallest_zoom_level = 5  # the most zoomed in we want is an offset of 5

        exp_value = pow(6.0, -2.3 + 3.7 * input_value)
        # So we can get the smallest zoom better
        # could probs precompute for speed but this makes sense
        exp_value_at_0 = pow(6.0, -2.3 + 3.7 * 0)

        max_map_size = max(self.tile_bounds_plt) - smallest_zoom_level + exp_value_at_0
        return ((exp_value - exp_value_at_0) * max_map_size) + smallest_zoom_level

    def center_viewpoint(self, positions: list[tuple[float, float]], offset: float = 0.1) -> None:
        """
        This rebounds the viewpoint of the mpl figure so it includes all the boats
        and it's roughly centered around them

        :param positions: A list of the tuple (lat,lon) coordinates of the boats
        :param offset: The border around the points (how zoomed it is) between 0 and 1
        :return: None
        """

        # convert the relative offset to the actual border value
        offset = self.scale_zoom(offset)

        # convert all lat lon positions to x,y graph coords
        positions = [self.degrees_to_graph(pos) for pos in positions]

        # Get the highest and lowest position for the boats
        max_x, max_y = max(pos[0] for pos in positions), max(pos[1] for pos in positions)
        min_x, min_y = min(pos[0] for pos in positions), min(pos[1] for pos in positions)

        # We always want the viewpoint to be a square, this determines whether we
        # Scale by the y or the x-axis. Pick the larger one so we always fit everything in
        focus_on = 'y' if abs(max_y - min_y) > abs(max_x - min_x) else 'x'

        if focus_on == 'y':  # focusing on the y-axis
            graph_size = abs(max_y - min_y)
        else:  # focusing on the x-axis
            graph_size = abs(max_x - min_x)

        # get the center of the boats
        center_x, center_y = (max_x + min_x) / 2, (max_y + min_y) / 2

        left = max(0.0, center_x - graph_size / 2 - offset)
        right = min(center_x + graph_size / 2 + offset, self.tile_bounds_plt[1])
        down = max(0.0, center_y - graph_size / 2 - offset)
        above = min(center_y + graph_size / 2 + offset, self.tile_bounds_plt[0])
        self.__ax.axis((left, right, down, above))

    def draw_track(self, athlete_key: str, color: str | tuple = 'green') -> None:
        """
        Draw a track on the graph

        :param athlete_key: The key of the athlete's track to draw in the track list (filename)
        :param color: The color of the track
        :return: None
        """

        if ('draw_track' in self.__athletes[athlete_key] and
                self.__athletes[athlete_key]['draw_track'] is not None):
            self.__remove_drawn_track(athlete_key)

        track = self.__athletes[athlete_key]['track']
        line_data = []

        for i in range(len(track.get_track_points()) - 1):
            start_point = track.get_track_points()[i]  # get start and end points of line
            end_point = track.get_track_points()[i + 1]

            # dont plot this line if its out of the start finish zone
            if (end_point.get_relative_time() < self.__athletes[athlete_key]['start_time'] or
                    start_point.get_relative_time() > self.__athletes[athlete_key]['finish_time']):
                continue

            single_line = self.draw_line(start_point.get_position_degrees(),
                                         end_point.get_position_degrees(),
                                         color=color)
            line_data.append(single_line)

        self.__athletes[athlete_key]['draw_track'] = line_data

    def __remove_drawn_track(self, athlete_key: str) -> None:
        """
        Removes a track drawn onto the map

        :param athlete_key: The athletes track to remove
        :return: None
        """

        if ('draw_track' in self.__athletes[athlete_key] and
                self.__athletes[athlete_key]['draw_track'] is not None):

            # Go through the list of lines making up the track we drew and remove each
            for line in self.__athletes[athlete_key]['draw_track']:
                line.remove()

            # Set the list to be None at the end
            self.__athletes[athlete_key]['draw_track'] = None

    def draw_line(self, start: tuple[float, float],
                  end: tuple[float, float],
                  color: str = 'green', width: int = 2) -> plt.Line2D:
        """
        Draw a line on the graph

        :param start: tuple lat,lon coordinates
        :param end: tuple lat,lon coordinates
        :param color: colour of the point default green
        :param width: width of the line default 2
        :return: the line data
        """

        start_graph_pos = self.degrees_to_graph(start)
        end_graph_pos = self.degrees_to_graph(end)

        # return the plotted line, its default in a list, but its only ever of
        # length one so take it out of the list
        return self.__ax.plot([start_graph_pos[0], end_graph_pos[0]],
                              [start_graph_pos[1], end_graph_pos[1]],
                              color=color, linewidth=width)[0]

    def draw_point(self, athlete_key: str,
                   pos: tuple[float, float],
                   color: str | tuple = 'green',
                   size: float = 1) -> None:
        """
        Draw a point on the graph

        :param athlete_key: The key of the athlete whose marker we're adding
        :param pos: tuple (lat,lon) coordinates
        :param color: colour of the point default green
        :param size: radius of the point default 1
        :return: None
        """

        # if this athlete has a point already remove it
        if ('draw_point' in self.__athletes[athlete_key] and
                self.__athletes[athlete_key]['draw_point'] is not None):
            self.remove_point(athlete_key)

        graph_pos = self.degrees_to_graph(pos)
        self.__athletes[athlete_key]['draw_point'] = self.__ax.plot(graph_pos[0], graph_pos[1],
                                                                    marker="o", markersize=size,
                                                                    markeredgecolor=color,
                                                                    markerfacecolor=color)[0]

    def remove_point(self, athlete_key: str) -> None:
        """
        Remove a point plotted earlier

        :param athlete_key: The str key of the athlete in the dict (simple filename usually)
        :return:  None
        """

        if ('draw_point' in self.__athletes[athlete_key] and
                self.__athletes[athlete_key]['draw_point'] is not None):
            self.__athletes[athlete_key]['draw_point'].remove()
            self.__athletes[athlete_key]['draw_point'] = None

    def degrees_to_graph(self, degrees: tuple[float, float]) -> tuple[float, float]:
        """
        Convert the degrees to the graph coordinates

        :param degrees: The degrees to convert (lat,lon)
        :return: The graph coordinates
        """
        if self.gpx_bounds_deg is None:
            raise ValueError("GPX bounds not set")

        if self.tile_bounds_deg is None:
            raise ValueError("Tile bounds not set")

        y_coord = ((degrees[0] - self.tile_bounds_deg[2]) /
                   (self.tile_bounds_deg[0] - self.tile_bounds_deg[2])) * self.tile_bounds_plt[0]
        x_coord = ((degrees[1] - self.tile_bounds_deg[3]) /
                   (self.tile_bounds_deg[1] - self.tile_bounds_deg[3])) * self.tile_bounds_plt[1]

        return x_coord, y_coord

    def __draw_legend(self) -> None:
        """
        draws a legend onto the plot

        :return: None
        """

        all_patches = []
        for single_athlete_data in self.__athletes.values():
            athlete_col = single_athlete_data['colour']
            athlete_name = single_athlete_data['display_name']
            all_patches.append(mpatches.Patch(color=athlete_col, label=athlete_name))

        if self.__ax.get_legend():
            self.__ax.get_legend().remove()

        self.__ax.legend(handles=all_patches, fontsize="9", loc='upper right')
