"""
This script contains the app class for the GPX analysis tool.
Controls the GUI, MapHandler and more.
"""
# Pylint ignores
# pylint: disable=R0902
# pylint: disable=R0914

import time
# Import external libs
import tkinter as tk
import pathlib
import random

try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import graph_handler as gh
    from gpx_analysis.gui import AppGUI
    from gpx_analysis import sporting as sport
    from gpx_analysis import components as geo
except ImportError:
    import gpx_parser as gpx
    import graph_handler as gh
    from gpx_analysis.gui import AppGUI
    import sporting as sport
    import components as geo


class GpxAnalysisApp:
    """
    This app handles all the functionality of the GPX analysis tool
    """

    def __init__(self) -> None:
        """
        Constructor for GpxAnalysisApp
        """

        # Instantiate the important 2 mpl helper classes, MapClass and TODO statsGraph
        self.__mpl_map = gh.MapClass()

        # Now instantiate the guis
        self.__root = tk.Tk()  # Create the tk window
        self.__root.protocol("WM_DELETE_WINDOW", self.__shutdown)
        self.__gui = AppGUI(window=self.__root, map_class=self.__mpl_map)

        # Athletes are a dict: key = simple filename, value = dict of other properties
        self.__athletes = {}

        # playback attributes
        self.__playing = False
        self.__playback_time = 0
        self.__playback_speed = 1
        self.__max_time = 100  # The longest time on any of the athletes
        self.__zoom_level = 0.1  # the border zoom

        # Link the callback functions
        self.__link_callback_functions()

        # Things for the update function
        self.update_speed = 50  # how many ms between each update call
        self.__last_update = time.time() + (self.update_speed / 1000)
        # MUST be last otherwise things may not be initialised
        self.__root.after(ms=self.update_speed, func=self.__update)

    def __shutdown(self) -> None:
        """
        Shuts down the app

        :return:None
        """

        self.__root.quit()
        self.__root.destroy()

    def __link_callback_functions(self) -> None:
        """
        Link the callback attributes from this app class to the child gui class

        :return: None
        """
        # Link the callback functions
        self.__gui.set_open_callback(self.__on_open_file)
        self.__gui.set_changename_callback(self.__on_display_name_change)
        self.__gui.set_delete_callback(self.__on_athlete_deleted)
        self.__gui.set_get_playback_callback(self.__get_playing)
        self.__gui.set_set_playback_callback(self.__set_playing)
        self.__gui.set_set_plaback_speed_callback(self.__set_playback_speed)
        self.__gui.set_set_playback_time_callback(self.set_playback_time)
        self.__gui.set_get_playback_time_callback(self.get_playback_time)
        self.__gui.set_zoom_level_callback(self.__set_zoom_level)
        self.__gui.set_set_start_finish_time_callback(self.__set_start_finish_times)
        self.__gui.set_get_start_finish_time_callback(self.__get_start_finish_times)
        self.__gui.set_on_colour_change(self.__on_athlete_colour_change)

    def __get_playing(self) -> bool:
        """
        A getter for the playing variable

        :return: is the simulation playing or not
        """
        return self.__playing

    def __set_playing(self, value: bool) -> None:
        """
        A setter for the playing variable

        :return: None
        """
        self.__playing = value

    def get_playback_time(self) -> float:
        """
        A getter for the playback_time variable

        :return: the playback_time
        """
        return self.__playback_time

    def set_playback_time(self, value: float) -> None:
        """
        A setter for the playback_time variable

        :param value: the time to set
        :return: None
        """
        self.__playback_time = value

        # update the map too
        self.__draw_athletes_on_map()

    def __set_playback_speed(self, value: float) -> None:
        """
        A setter for the playback_speed variable

        :param value: the speed to set
        :return: None
        """
        self.__playback_speed = value

    def __set_zoom_level(self, value: float) -> None:
        """
        A setter for the zoom variable

        :param value: float between 0 and 1
        :return: None
        """
        value = max(min(1.0, value), 0.0)  # clamp it between 0 and 1
        self.__zoom_level = value
        # update the map to show new zoom
        self.__draw_athletes_on_map()

    def __assign_colour(self) -> tuple[float, float, float]:
        """
        Makes sure each boat has a unique colour

        :return: The tuple colour of floats each float ranges 0.0 -> 1.0
        """

        # Define some predetermined nice but spaced out colours,
        # they are in order of most far from each other roughly,
        # so go down the list to find next colour

        colours = [(0.169, 0.161, 0.671),  # Blue
                   (0.859, 0.494, 0.153),  # Orange
                   (0.235, 0.710, 0.169),  # green
                   (0.709, 0.168, 0.639),  # Pink
                   (0.902, 0.930, 0.054),  # Yellow
                   (0.768, 0.290, 0.247),  # red
                   ]

        # remove all items from the list that have been used already
        for athlete_data in self.__athletes.values():
            their_colour = athlete_data['colour']
            if their_colour in colours:
                colours.remove(their_colour)

        if colours:  # if there are any left
            return colours[0]

        # If they have all been used return a random colour
        return random.random(), random.random(), random.random()

    def __set_start_finish_times(self, athlete_key: str,
                                 start_time: float | None,
                                 finish_time: float | None) -> None:
        """
        Sets the start and finish times for an athlete

        :param athlete_key: The key of the athlete we are modifying
        :param start_time: The new start time or none if not setting one
        :param finish_time: The new end time or none if not setting one
        :return: None
        """

        # fill in the missing info for the data checks
        if start_time is None:
            start_time = self.__athletes[athlete_key]['start_time']

        if finish_time is None:
            finish_time = self.__athletes[athlete_key]['finish_time']

        # check if data is invalid
        if start_time >= finish_time:
            return

        max_time = self.__athletes[athlete_key]['track'].get_total_time()
        if (start_time >= max_time or finish_time > max_time or
                start_time < -0.1 or finish_time < -0.1):
            return

        # set the new times
        self.__athletes[athlete_key]['start_time'] = start_time

        self.__athletes[athlete_key]['finish_time'] = finish_time

        # update the athlete lists with the new times
        self.__gui.update_athletes(self.__athletes, remake_widgets=False)

        # update the max time
        self.__max_time = self.__calculate_longest_time()
        self.__gui.set_gui_playback_time(self.__playback_time, self.__max_time)

        # change the map's start finish times
        self.__mpl_map.modify_start_finish_times(athlete_key, start_time, finish_time)
        self.__gui.update_map()

    def __get_start_finish_times(self, athlete_key: str) -> tuple[float, float]:
        """
        get the athlete's start and finish times

        :param athlete_key: the athlete to check
        :return: a tuple (start_time, finish_time)
        """
        athlete = self.__athletes[athlete_key]
        return athlete['start_time'], athlete['finish_time']

    def __on_open_file(self, filename: str) -> None:
        """
        Gets called when a file is opened to make a new GPX track

        :param filename: filename to open
        :return: None
        """
        # print(f'app opened {filename}')

        new_track = gpx.Track(filename)

        # check if the same file is already there
        same_as = False
        for athlete_data in self.__athletes.values():
            if filename == athlete_data['track'].get_filename():
                same_as = True
                break

        if same_as:
            # Already been imported
            # print("Already been imported")
            return

        # Clean up the filename
        path = pathlib.PurePath(filename)
        clean_path = f'/{path.parent.name}/{path.name}'

        # We will put the athlete data into the list as a dict of the important parts
        athlete_data = {'track': new_track,
                        "filename": clean_path,
                        'display_name': clean_path,
                        'colour': self.__assign_colour(),
                        'start_time': 0,
                        'finish_time': new_track.get_total_time()}

        self.__athletes[clean_path] = athlete_data

        self.__mpl_map.add_athlete(clean_path, athlete_data)  # add it to the map

        # update the GUI's list of athletes
        self.__gui.update_athletes(self.__athletes)

        # update the GUI's map as a new track is there
        self.__gui.update_map()

        # update the gui stats
        self.__gui.update_stats()

        # check if this is a new longest_time
        self.__max_time = self.__calculate_longest_time()

        # center view around all the athletes
        self.__draw_athletes_on_map()

    def __calculate_longest_time(self) -> float:
        """
        Get the longest time amongst the athletes

        :return: the longest time
        """

        if self.__athletes:
            max_time = max((v['finish_time'] - v['start_time']) for v in self.__athletes.values())
        else:
            max_time = 100  # default max value

        self.__playback_time = min(self.__playback_time, max_time)
        self.__gui.set_gui_playback_time(self.__playback_time, max_time)

        return max_time

    def __on_display_name_change(self, athlete_key: str, changed_to: str) -> None:
        """
        Callback function for when a display name is changed for an athlete

        :param athlete_key: the filename of the athlete that's changing their name
        :param changed_to: What they change their display name to
        :return: None
        """

        # print(f'{athlete_key} changed their name to {changed_to}')

        # modify athlete data in this class
        self.__athletes[athlete_key]['display_name'] = changed_to

        # update the guis's list of athletes
        self.__gui.update_athletes(self.__athletes)

        # update the map's list of athletes and then update the map image on the GUI
        self.__mpl_map.modify_athlete(athlete_key, self.__athletes[athlete_key])
        self.__gui.update_map()

        # update the gui's stats display with the new name
        self.__gui.update_stats()

    def __on_athlete_colour_change(self, athlete_key: str,
                                   colour: tuple[float, float, float]) -> None:
        """
        Gets called when an athlete changes their colour

        :param athlete_key: The key of the athlete changing colour
        :param colour: The colour changing to
        :return: None
        """

        # update the data in the app class dict
        self.__athletes[athlete_key]['colour'] = colour

        # update the guis's list of athletes
        self.__gui.update_athletes(self.__athletes,remake_widgets=False)

        # update the map
        self.__mpl_map.modify_athlete(athlete_key, self.__athletes[athlete_key])
        self.__gui.update_map()

    def __on_athlete_deleted(self, athlete_key: str) -> None:
        """
        Callback function for when an athlete is deleted

        :param athlete_key: The dictionary key for the athlete we are deleting
        :return: None
        """
        # print(f'{athlete_key} got deleted')

        if len(self.__athletes) - 1 == 0:  # if its now empty
            self.__mpl_map.reset()
            self.__gui.update_map()
        else:
            # first remove from the map and update it
            self.__mpl_map.remove_athlete(athlete_key)
            self.__gui.update_map()

        # next remove from our list of athletes and update the guis's list
        del self.__athletes[athlete_key]
        self.__gui.update_athletes(self.__athletes)
        self.__max_time = self.__calculate_longest_time()
        self.__gui.update_stats()

    def __set_athlete_positions(self, set_time: float) -> list[tuple[float, float]]:
        """
        Gets called to change the athletes' markers to a point in time

        :param set_time: the time which we'll draw the point at on the athlete's track
        :return: a list of the athlete positions
        """
        athlete_positions = []

        for athlete in self.__athletes.values():
            # set time is relative to the athlete
            # as diff athletes start at diff times on their track, change this
            athlete_time = min(athlete['start_time'] + set_time, athlete['finish_time'])
            pos = sport.get_position_at_time(athlete['track'], athlete_time)
            athlete_positions.append(pos)

            # create a new lighter colour for the athlete to make
            # the point stand out from the track
            rgb_light = geo.lighten_color(athlete['colour'], 0.65)
            self.__mpl_map.draw_point(athlete_key=athlete['filename'],
                                      pos=pos,
                                      color=rgb_light,
                                      size=8)

        return athlete_positions

    def __draw_athletes_on_map(self) -> None:
        """
        Draws athletes markers on the map

        :return: None
        """
        # check we have something to draw
        if self.__athletes:
            # update the athletes positions
            positions = self.__set_athlete_positions(self.__playback_time)
            # center the map around them
            self.__mpl_map.center_viewpoint(positions, offset=self.__zoom_level)
            self.__gui.update_map()

    def __update(self) -> None:
        """
        Loop function, called every simulation frame

        :return: None
        """
        # calculate the deltaTime
        current_time = time.time()
        delta_time = current_time - self.__last_update
        self.__last_update = current_time

        self.__gui.gui_loop()  # call the gui loop

        # Update the positions on the map
        if self.__playing:
            self.__draw_athletes_on_map()

        # Increase the time if playing
        if self.__playing:
            self.__playback_time = min(self.__playback_time + (delta_time * self.__playback_speed),
                                       self.__max_time)
            self.__gui.set_gui_playback_time(self.__playback_time, self.__max_time)

        # Call the update function again in
        self.__root.after(ms=self.update_speed, func=self.__update)

    def run_app(self) -> None:
        """
        Starts running the App

        :return: None
        """
        self.__root.mainloop()
