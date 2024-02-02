"""
This script contains the app class for the GPX analysis tool.
Controls the GUI, MapHandler and more.
"""

# Import external libs
import time
import tkinter as tk
import pathlib
import random

# Import our own libraries using this try except block as sometimes in terminal,
# or pytest it had issues with either type, so make sure it's always good here.
try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import graph_handler as gh
    from gpx_analysis import sporting as sport
    from gpx_analysis import gui

except ImportError:
    import gpx_parser as gpx
    import graph_handler as gh
    import sporting as sport
    import gui


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

        # Now instantiate the gui
        self.__root = tk.Tk()  # Create the tk window
        self.__gui = gui.AppGUI(window=self.__root, map_class=self.__mpl_map)

        # Athletes are a dict: key = simple filename, value = dict of other properties
        self.__athletes = {}

        # Link the callback functions
        self.__gui.set_open_callback(self.__on_open_file)
        self.__gui.set_changename_callback(self.__on_display_name_change)
        self.__gui.set_delete_callback(self.__on_athlete_deleted)

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

    def __on_open_file(self, filename: str) -> None:
        """
        Gets called when a file is opened to make a new GPX track

        :param filename: filename to open
        :return: None
        """
        print(f'app opened {filename}')

        new_track = gpx.Track(filename)

        # check if the same file is already there
        same_as = False
        for athlete_data in self.__athletes.values():
            if filename == athlete_data['track'].get_filename():
                same_as = True
                break

        if same_as:
            # Already been imported
            print("Already been imported")
            return

        # Clean up the filename
        path = pathlib.PurePath(filename)
        clean_path = f'/{path.parent.name}/{path.name}'

        # We will put the athlete data into the list as a dict of the important parts
        athlete_data = {'track': new_track,
                        "filename": clean_path,
                        'display_name': clean_path,
                        'colour': self.__assign_colour()}

        self.__athletes[clean_path] = athlete_data

        self.__mpl_map.add_athlete(clean_path, athlete_data)  # add it to the map

        # update the gui's list of athletes
        self.__gui.update_athletes(self.__athletes)

        # update the GUI's map as a new track is there
        self.__gui.update_map()

    def __on_display_name_change(self, athlete_key: str, changed_to: str) -> None:
        """
        Callback function for when a display name is changed for an athlete

        :param athlete_key: the filename of the athlete that's changing their name
        :param changed_to: What they change their display name to
        :return: None
        """

        print(f'{athlete_key} changed their name to {changed_to}')

        # modify athlete data in this class
        self.__athletes[athlete_key]['display_name'] = changed_to

        # update the gui's list of athletes
        self.__gui.update_athletes(self.__athletes)

        # update the map's list of athletes and then update the map image on the GUI
        self.__mpl_map.modify_athlete(athlete_key, self.__athletes[athlete_key])
        self.__gui.update_map()

    def __on_athlete_deleted(self, athlete_key: str) -> None:
        """
        Callback function for when an athlete is deleted

        :param athlete_key: The dictionary key for the athlete we are deleting
        :return: None
        """
        print(f'{athlete_key} got deleted')

        # first remove from the map and update it
        self.__mpl_map.remove_athlete(athlete_key)
        self.__gui.update_map()

        # next remove from our list of athletes and update the gui's list
        del self.__athletes[athlete_key]
        self.__gui.update_athletes(self.__athletes)

    def run_app(self) -> None:
        """
        Starts running the App

        :return: None
        """
        self.__root.mainloop()

# # Run the app if this script is being run as itself
# if __name__ == '__main__':
#     app = GpxAnalysisApp()
#     app.run_app()
