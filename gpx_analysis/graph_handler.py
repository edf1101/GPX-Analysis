"""
This module handles the graphing of the GPX file and the fetching of OSM tiles
"""
import math
import urllib.request
import io
import os.path
import PIL.Image
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl

import geo_components as geo
import gpx_parser as gpx


def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    """
    Code for converting lat lon to tile number from
    https://stackoverflow.com/questions/28476117/easy-openstreetmap-tile-displaying-for-python
    ~ BenrdGit

    :param lat_deg: Input latitude
    :param lon_deg: Input longitude
    :param zoom: OSM zoom level
    :return: the OSM tile position
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile


def num2deg(xtile: int, ytile: int, zoom: int) -> tuple[float, float]:
    """
    Code for converting tile number to lat lon from
    https://stackoverflow.com/questions/28476117/easy-openstreetmap-tile-displaying-for-python
    ~ BenrdGit

    :param xtile: The tile x coordinate
    :param ytile: The tile y corrdinate
    :param zoom: The osm zoom level
    :return: (latitude, longitude)
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
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


def get_img(x: int, y: int, zoom: int):
    """
    Get the image from the tile either from cache or downloading

    :param x: The x tile index
    :param y: The y tile index
    :param zoom: The zoom tile index
    :return: The image
    """

    # Check if its cached first
    if os.path.isfile(f'image_cache/{zoom}-{y}-{x}.jpg'):
        img = PIL.Image.open(f'image_cache/{zoom}-{y}-{x}.jpg')
    elif os.path.isfile(f'image_cache/{zoom}-{y}-{x}.jpg'):
        img = PIL.Image.open(f'image_cache/{zoom}-{y}-{x}.jpeg')
    elif os.path.isfile(f'image_cache/{zoom}-{y}-{x}.jpg'):
        img = PIL.Image.open(f'image_cache/{zoom}-{y}-{x}.png')

    else:  # Otherwise download it and cache
        image_url = (f'https://server.arcgisonline.com/ArcGIS/rest/services/'
                     f'World_Topo_Map/MapServer/tile/{zoom}/{y}/{x}')
        response = urllib.request.urlopen(image_url)
        img = PIL.Image.open(io.BytesIO(response.read()))
        img.save(f'image_cache/{zoom}-{y}-{x}.jpg')  # Save as jpg into cache folder

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
    for x in range(bottom_left_tile_num[0] - 1, top_right_tile_num[0] + 1):
        for y in range(top_right_tile_num[1] - 1, bottom_left_tile_num[1] + 1):
            if (x, y) not in tiles:
                tiles[(x, y)] = get_img(x, y, 17)

    return tiles


class MapClass:
    """
    Class for converting scales between the GPX file and the graph
    """

    def __init__(self):
        # Set up the matplotlib figure
        mpl.use('macosx')  # if macOS need to sort out Windows version

        self.fig = plt.figure()
        self.fig.patch.set_facecolor('white')

        self.tile_size = 50
        self.__image_dict = {}
        self.__raw_image_dict = {}

        self.gpx_bounds_deg = None
        self.tile_bounds_plt = None
        self.tile_bounds_deg = None

        self.gpx_tracks = []

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
        for k, v in _image_dict.items():
            if k not in self.__raw_image_dict:
                self.__raw_image_dict[k] = v

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
        if self.__raw_image_dict == {}:
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

    def draw_point(self, pos: tuple[float, float],
                   color: str = 'green',
                   size: float = 1) -> None:
        """
        Draw a point on the graph

        :param pos: tuple x,y coordinates
        :param color: colour of the point default green
        :param size: radius of the point default 1
        :return: None
        """
        graph_pos = self.degrees_to_graph(pos)
        plt.plot(graph_pos[0], graph_pos[1], marker="o", markersize=size,
                 markeredgecolor=color, markerfacecolor=color)

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

        y = ((degrees[0] - self.tile_bounds_deg[2]) /
             (self.tile_bounds_deg[0] - self.tile_bounds_deg[2])) * self.tile_bounds_plt[0]
        x = ((degrees[1] - self.tile_bounds_deg[3]) /
             (self.tile_bounds_deg[1] - self.tile_bounds_deg[3])) * self.tile_bounds_plt[1]

        return x, y
