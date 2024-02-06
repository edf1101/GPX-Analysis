"""
This script contains the main GUI class
The AppGUI class is the only one to use outside of this class
"""
# Pylint ignores
# pylint: disable=R0902
# pylint: disable=R0914
# pylint: disable=R0904

import tkinter as tk
from tkinter import ttk
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # for importing figs to mpl

# import the individual separate classes
try:
    from gpx_analysis import graph_handler as gh
    from gpx_analysis.gui_control_menu import ControlMenuFrame
    from gpx_analysis.gui_finishline_menu import FinishlineMenuFrame
    from gpx_analysis.gui_playback_menu import PlaybackMenuFrame
    from gpx_analysis.gui_stats_menu import StatsMenuFrame
    from gpx_analysis.tkscrolledframe import ScrolledFrame
except ImportError:
    from .gui_control_menu import ControlMenuFrame
    from .gui_finishline_menu import FinishlineMenuFrame
    from .gui_playback_menu import PlaybackMenuFrame
    from .gui_stats_menu import StatsMenuFrame
    from gpx_analysis import graph_handler as gh
    from gpx_analysis.tkscrolledframe import ScrolledFrame


class AppGUI:
    """
    Class containing the entire GUI for the GPX Analysis App, using OOP so encapsulation makes
    it better for modularity, readability etc.
    """

    def __init__(self, window: tk.Tk, map_class: gh.MapClass) -> None:
        """
        Constructor for the AppGUI Class

        :param window: the root for the Tk window, created in the global scope
        :param map_class: Reference to the graph_handler.MapClass handler for the mpl map
        """

        self.ready = False
        self.__mpl_graph = map_class
        self.__window = window
        self.__window.title("GPX Analysis")  # Set the window title

        self.__scroll_window = ScrolledFrame(self.__window, width=880, height=600)
        self.__scroll_window.pack(side="top", expand=1, fill="both")
        self.__scroll_window.bind_scroll_wheel(self.__window)

        self.__inner_frame = self.__scroll_window.display_widget(tk.Frame)
        # self.__window.geometry('400x400')

        # Configure the layout of the basic 2x2 grid
        self.__inner_frame.rowconfigure(0, minsize=500, weight=3)
        self.__inner_frame.rowconfigure(1, minsize=250, weight=1)
        self.__inner_frame.columnconfigure(1, minsize=500, weight=8)
        self.__inner_frame.columnconfigure(0, minsize=260, weight=1)

        # Holds the last stats update time so we can do it only every .5s
        self.__last_stats_update = time.time()
        self.__last_map_update = time.time()

        # Set the map widget in the TOP RIGHT corner
        self.__map_widget = None
        self.update_map()

        # Create the menus and submenus down the side
        # First initialise the main menus as None
        self.__frm_map_menu = None
        self.__frm_stats_menu = None
        # Now initialise the submenu classes as None
        self.__control_menu = None
        self.__finishline_menu = None
        self.__playback_menu = None

        # Function for removing focus from widgets once they have been clicked off
        self.__window.bind_all("<Button-1>", self.__remove_entry_focus)

        # Create the stats menu
        self.__stats_menu = StatsMenuFrame(self, self.__inner_frame)

        # create callback function references
        self.__open_file_callback = None
        self.__change_name_callback = None
        # reference these quickly to make pylint happy
        if self.__open_file_callback == self.__change_name_callback:
            pass

        # These are public as they'll turn into public methods for the sub frames to use
        self.get_playing = None
        self.set_playing = None

        self.set_playback_speed = None

        self.set_playback_time = None
        self.get_playback_time = None

        self.set_zoom_level = None

        self.set_start_finish_time = None
        self.get_start_finish_time = None

        self.on_colour_change = None

        # Athlete list
        self.__athletes = {}

        # Set the submenus here after the other variables have been set
        self.__set_submenus()

        # create the map here and its canvas
        self.__canvas = FigureCanvasTkAgg(self.__mpl_graph.get_figure(), master=self.__inner_frame)
        self.__map_widget = self.__canvas.get_tk_widget()
        self.__map_widget.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

        # Is it set up: this gets set to true when init is finished
        self.ready = True

    def gui_loop(self) -> None:
        """
        The GUI code to loop through each frame in the simulation

        :return: None
        """

        # if its playing then update stats every 1s
        if time.time() - self.__last_stats_update >= 1.0:
            self.__last_stats_update = time.time()
            self.update_stats()

    def update_stats(self) -> None:
        """
        update the statistics menu display

        :return: None
        """

        self.__stats_menu.update_stats()

    def stop_finish_start_editing(self) -> None:
        """
        disables the start/finish editing menu

        :return: None
        """
        self.__finishline_menu.stop_editing()

    def set_finishline_athlete_selected(self, athlete_key):
        """
        Pass the athlete data held by athlete key to the currently selected field
        in the finishline menu

        :param athlete_key: The athlete whose data we are sending
        :return: None
        """

        if athlete_key:
            self.__finishline_menu.set_currently_selected(self.__athletes[athlete_key])
        else:
            self.__finishline_menu.set_currently_selected(None)

    def update_athletes(self, new_athletes: dict[dict],
                        remake_widgets: bool = True) -> None:
        """
        Updates the GUI's list of athletes

        :param new_athletes: the new list
        :param remake_widgets: Whether or not to rebuild the widgets
        :return: None
        """
        self.__athletes = new_athletes

        self.__control_menu.update_athlete_data(new_athletes, remake_widgets)
        self.__stats_menu.set_athlete_list(new_athletes)

    def __remove_entry_focus(self, event) -> None:
        """
        This function removes focuses from widgets when they are clicked off

        :param event:
        :return:
        """
        if not isinstance(event.widget, ttk.Entry):
            self.__window.focus()

    def update_map(self,force:bool = False) -> None:
        """
        This sets/ updates the mpl figure map on the GUI

        :param force: whether to force an update regardless of whether it's too soon
        :return: None
        """

        if time.time() - self.__last_map_update < 0.2 and not force:
            return
        self.__last_map_update = time.time()

        self.__canvas.draw()

    def __set_submenus(self) -> None:
        """
        This creates and initialises the submenus

        :return: None
        """

        #  Set up the two menus (map menu on top, stats menu on bottom)
        self.__frm_map_menu = ttk.Frame(self.__inner_frame, relief=tk.RAISED, borderwidth=5)
        self.__frm_map_menu.grid(row=0, column=0, sticky='nsew')

        # Configure the arrangement of the map menu frame so the child frames
        # span its height equally
        self.__frm_map_menu.grid_rowconfigure(0, weight=1)
        self.__frm_map_menu.grid_rowconfigure(1, weight=1)
        self.__frm_map_menu.grid_rowconfigure(2, weight=1)
        self.__frm_map_menu.grid_columnconfigure(0, weight=1)

        # Create the frames to contain the menus inside the map menu frame
        # using smaller classes for readability
        self.__control_menu = ControlMenuFrame(self)

        # Next the start/finish line menu
        self.__finishline_menu = FinishlineMenuFrame(self)
        # Next the playback menu
        self.__playback_menu = PlaybackMenuFrame(self)

    def get_tk_window(self) -> tk.Tk:
        """
        Getter for the private tk window variable

        :return: the tk window
        """
        return self.__window

    def get_frm_map_menu(self) -> None | tk.Frame:
        """
        Getter for the private variable frm_map_menu

        :return: frm_map_menu
        """
        return self.__frm_map_menu

    def get_frm_stats_menu(self) -> None | tk.Frame:
        """
        Getter for the private variable frm_stats_menu

        :return: frm_stats_menu
        """
        return self.__frm_stats_menu

    # Lots setter for callback functions!
    def set_open_callback(self, func) -> None:  # Open file callbacks
        """
        Set the callback function to be used when a file is opened

        :param func: The function to be called when a file is opened in control window
        :return: None
        """
        self.__control_menu.set_open_callback(func)

    def set_delete_callback(self, func) -> None:  # Open file callbacks
        """
        Set the callback function to be used when a file is opened

        :param func: The function to be called when an athlete is deleted
        :return: None
        """
        self.__control_menu.set_delete_callback(func)

    def set_changename_callback(self, func) -> None:
        """
        Sets the callback function to be used when an athlete changes display name

        :param func: The function to be called
        :return: None
        """
        self.__control_menu.set_changename_callback(func)

    def set_get_playback_callback(self, func) -> None:
        """
        Sets the callback function to be used when a class requests playback state

        :param func: The function to be called
        :return: None
        """
        self.get_playing = func

    def set_set_playback_callback(self, func) -> None:
        """
        Sets the callback function to be used when a class sets playback state

        :param func: The function to be called
        :return: None
        """
        self.set_playing = func

    def set_set_plaback_speed_callback(self, func) -> None:
        """
        Sets the callback function to be used when a class sets playback speed

        :param func: The function to be called
        :return: None
        """
        self.set_playback_speed = func

    def set_get_playback_time_callback(self, func) -> None:
        """
        Sets the callback function to be used when a class requests playback state

        :param func: The function to be called
        :return: None
        """
        self.get_playback_time = func

    def set_set_playback_time_callback(self, func) -> None:
        """
        Sets the callback function to be used when a class sets playback state

        :param func: The function to be called
        :return: None
        """
        self.set_playback_time = func

    def set_gui_playback_time(self, time_val: float, max_time: float) -> None:
        """
        Set the time passed on the GUI

        :param time_val: the time passed
        :param max_time: how much total time
        :return: None
        """
        self.__playback_menu.set_playback_time(time_val, max_time)

    def set_zoom_level_callback(self, func) -> None:
        """
        Sets the callback function to be used when the zoom level changes

        :param func: The function to be called
        :return: None
        """
        self.set_zoom_level = func

    def set_set_start_finish_time_callback(self, func) -> None:
        """
        Sets the callback function to be used when a start or finish time is set

        :param func: The function to be called
        :return: None
        """
        self.set_start_finish_time = func

    def set_get_start_finish_time_callback(self, func) -> None:
        """
        Sets the callback function to be used when a start or finish time is requested

        :param func: The function to be called
        :return: None
        """
        self.get_start_finish_time = func

    def set_on_colour_change(self,func) -> None:
        """
        Setter for on colour change callback func

        :param func: the function to be called
        :return: None
        """
        self.on_colour_change = func
