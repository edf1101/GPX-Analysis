"""
This module handles the graphing of the GPX file and the fetching of OSM tiles
"""
# pylint: disable=R0902

import math
import urllib.request
import io
import os.path
import PIL.Image
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl

try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import geo_components as geo

except ImportError:
    import geo_components as geo
    import gpx_parser as gpx


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


def get_images(bounds: tuple[float, float, float, float],
               zoom_level: int = 17):
    """
    Get all the images for the graph background

    :param bounds: The bounds of the track (NESW)
    :param zoom_level: How much we want to zoom in on the tiles
    :return: The collection of images
    """

    bottom_left_tile_num = deg2num(bounds[2], bounds[3], zoom_level)
    top_right_tile_num = deg2num(bounds[0], bounds[1], zoom_level)
    print(bottom_left_tile_num)
    print(top_right_tile_num)


def get_img(x_coord: int, y_coord: int, zoom: int):
    """
    Get the image from the tile either from cache or downloading

    :param x: The x tile index
    :param y: The y tile index
    :param zoom: The zoom tile index
    :return: The image
    """

    # get abs path
    working_directory = os.path.dirname(os.path.abspath(__file__))

    # Check if its cached first
    endings = ['jpg', 'jpeg', 'png']  # the acceptable filetypes to use
    img = None
    for f_type in endings:
        name = os.path.join(working_directory, f'image_cache/{zoom}-{y_coord}-{x_coord}.{f_type}')
        if os.path.isfile(name):
            img = PIL.Image.open(name)

    if img is None:  # Otherwise download it and cache
        image_url = (f'https://server.arcgisonline.com/ArcGIS/rest/services/'
                     f'World_Topo_Map/MapServer/tile/{zoom}/{y_coord}/{x_coord}')
        with urllib.request.urlopen(image_url) as response:
            img = PIL.Image.open(io.BytesIO(response.read()))
            path = os.path.join(working_directory, f'image_cache/{zoom}-{y_coord}-{x_coord}.jpg')
            img.save(path)  # Save as jpg into cache folder

    return img


def get_all_images_in_bounds(bounds):
    """
    Get all the images in the bounds and put them in a dictionary with their
    tile index as the key

    :param bounds:  The bounds of the track (NESW)
    :return:  The collection of images
    """

    bottom_left_tile_num = deg2num(bounds[3], bounds[2], 17)
    top_right_tile_num = deg2num(bounds[1], bounds[0], 17)

    tiles = {}
    for x_coord in range(bottom_left_tile_num[0] - 1, top_right_tile_num[0] + 1):
        for y_coord in range(top_right_tile_num[1] - 1, bottom_left_tile_num[1] + 1):
            if (x_coord, y_coord) not in tiles:
                tiles[(x_coord, y_coord)] = get_img(x_coord, y_coord, 17)

    return tiles


class MapClass:
    """
    Class for converting scales between the GPX file and the graph
    """

    def __init__(self):
        # Set up the matplotlib figure
        # mpl.use('macosx')  # if macOS need to sort out Windows version
        # mpl.use("Qt5Agg")

        self.tile_size = 50
        self.__image_dict = {}
        self.__raw_image_dict = {}

        self.gpx_bounds_deg = None
        self.tile_bounds_plt = None
        self.tile_bounds_deg = None

        self.gpx_tracks = []

        self.__boat_markers = {}

    def add_track(self, track: gpx.Track) -> None:
        """
        Add a track to the graph handler instance

        :param track: The track to add
        :return: None
        """
        self.gpx_tracks.append(track)

        # Add its bounds to the graph handler's bounds
        self.__set_gpx_bounds(geo.get_track_bounds(track))

        # Redo the images for the graph handler with the new bounds
        self.__add_images(get_all_images_in_bounds(self.gpx_bounds_deg))

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
            plt.imshow(np.asarray(image), extent=(tile_index[0] * self.tile_size,
                                                  (tile_index[0] + 1) * self.tile_size,
                                                  tile_index[1] * self.tile_size,
                                                  (tile_index[1] + 1) * self.tile_size))

    def show_plot(self) -> None:
        """
        Show the plot
        :return: None
        """

        plt.show()
        plt.gcf().canvas.draw()
        plt.gcf().canvas.flush_events()

    def __remove_axis(self):
        axis =plt.gca()
        axis.get_xaxis().set_visible(False)
        axis.get_yaxis().set_visible(False)
        pass
    def get_plt(self):
        self.__remove_axis()
        return plt

    def get_figure(self) -> plt.Figure:
        """
        Return the figure

        :return: The figure
        """
        self.__remove_axis()
        plt.gcf().tight_layout()
        # plt.gca().set_position((0, 0, 1, 1))
        plt.gcf().set_size_inches(4.8,4.8)
        plt.gcf().set_dpi(100)
        return plt.gcf()

    def reset_viewpoint(self) -> None:
        """
        Make the viewpoint start around the 100px square around the start of the track

        :return: None
        """
        if self.gpx_bounds_deg is None:
            raise ValueError("GPX bounds not set")

        if self.tile_bounds_deg is None:
            raise ValueError("Tile bounds not set")

        # Get the start of the track
        start = self.gpx_tracks[0].get_track_points()[0].get_position_degrees()

        # Get the start of the track in graph coordinates
        start_graph_pos = self.degrees_to_graph(start)

        # Set the viewpoint to be a 100px square around the start of the track
        plt.axis((start_graph_pos[0] - self.tile_size, start_graph_pos[0] + self.tile_size,
                  start_graph_pos[1] - self.tile_size, start_graph_pos[1] + self.tile_size))

    def center_viewpoint(self, positions: list[tuple[float, float]]) -> None:
        """
        This rebounds the viewpoint of the mpl figure so it includes all the boats
        and its roughly centered around them

        :param positions: A list of the tuple (lat,lon) coordinates of the boats
        :return: None
        """

        # convert all lat lon positions to x,y graph coords
        positions = [self.degrees_to_graph(pos) for pos in positions]

        offset = 20  # offset of 50px around the bounds

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
        plt.axis((center_x - graph_size / 2 - offset, center_x + graph_size / 2 + offset,
                  center_y - graph_size / 2 - offset, center_y + graph_size / 2 + offset))

    def draw_track(self, track_index: int, color: str = 'green') -> None:
        """
        Draw a track on the graph

        :param track_index: The index of the track to draw in the track list
        :param color: The color of the track
        :return: None
        """
        track = self.gpx_tracks[track_index]
        for i in range(len(track.get_track_points()) - 1):
            self.draw_line(track.get_track_points()[i].get_position_degrees(),
                           track.get_track_points()[i + 1].get_position_degrees(),
                           color=color)

    def draw_line(self, start: tuple[float, float],
                  end: tuple[float, float],
                  color: str = 'green', width: int = 2) -> None:
        """
        Draw a line on the graph

        :param start: tuple lat,lon coordinates
        :param end: tuple lat,lon coordinates
        :param color: colour of the point default green
        :param width: width of the line default 2
        :return: None
        """

        start_graph_pos = self.degrees_to_graph(start)
        end_graph_pos = self.degrees_to_graph(end)
        plt.plot([start_graph_pos[0], end_graph_pos[0]],
                 [start_graph_pos[1], end_graph_pos[1]],
                 color=color, linewidth=width)

    def draw_point(self, boat_id: int,
                   pos: tuple[float, float],
                   color: str = 'green',
                   size: float = 1) -> None:
        """
        Draw a point on the graph

        :param boat_id: The id of the boat, mainly used for removing points
        :param pos: tuple (lat,lon) coordinates
        :param color: colour of the point default green
        :param size: radius of the point default 1
        :return: None
        """
        if boat_id in self.__boat_markers:
            self.remove_point(boat_id)

        graph_pos = self.degrees_to_graph(pos)
        self.__boat_markers[boat_id] = plt.plot(graph_pos[0], graph_pos[1], marker="o",
                                                markersize=size, markeredgecolor=color,
                                                markerfacecolor=color)

    def remove_point(self, boat_id: int) -> None:
        """
        Remove a point plotted earlier

        :param boat_id: The int id of the boat marked earlier
        :return:  None
        """

        if boat_id in self.__boat_markers:
            self.__boat_markers[boat_id][0].remove()

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
