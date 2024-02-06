"""
This script contains the playback menu sub frame class related to the tk GUI
The AppGUI class is the only one to use outside of this class
"""
# Pylint ignores
# pylint: disable=R0902
# pylint: disable=R0914

import tkinter as tk
from tkinter import ttk


class PlaybackMenuFrame:
    """
    This widget contains and abstracts the features of the playback menu
    """

    def __init__(self, parent_class):
        """
        Constructor for the PlaybackMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
        """
        self.__parent_class = parent_class

        # Create the basic frame
        self.__frm_map_playback_menu = ttk.Frame(self.__parent_class.get_frm_map_menu(),
                                                 relief=tk.RIDGE, borderwidth=2)
        self.__frm_map_playback_menu.grid(row=2, column=0, sticky='nsew')
        self.__frm_map_playback_menu.grid_columnconfigure(0, weight=1)

        self.__max_time = 100  # The upper end of the slider and max time for the athletes

        # Add a title
        label_playback_menu = ttk.Label(master=self.__frm_map_playback_menu,
                                        text="Simulation Menu",
                                        font=('Minion Pro', 14, 'bold'))
        label_playback_menu.grid(row=0, column=0, sticky='n')

        # create the playback time slider
        self.__slider_playback_time = ttk.Scale(master=self.__frm_map_playback_menu,
                                                from_=0, to=1, length=250,
                                                command=self.__on_time_slider_changed)
        self.__slider_playback_time.grid(row=2, column=0)
        # create the playback time label
        self.__label_playback_time = None
        self.set_playback_time(0, 100)

        # Create playback speed label
        self.__label_playback_speed = None
        self.set_playback_speed(1)

        # Create speed slider
        self.__slider_playback_speed = ttk.Scale(master=self.__frm_map_playback_menu,
                                                 from_=0.1, to=10, length=100, value=1,
                                                 command=self.__on_speed_slider_changed)
        self.__slider_playback_speed.grid(row=4, column=0)

        # Create a zoom slider with label
        self.__frm_zoom = None
        self.__slider_playback_zoom = None
        self.__create_zoom_frame()

        # Create playback button
        self.__button_playing = False
        self.__style_playback_button = None
        self.__but_playback_menu = None
        self.__create_playback_button()

    def __create_zoom_frame(self) -> None:
        """
        Create the frame containing the zoom label and slider

        :return: None
        """

        # Create the frame to contain the widgets
        self.__frm_zoom = ttk.Frame(master=self.__frm_map_playback_menu)
        self.__frm_zoom.grid(row=5, column=0, sticky='')
        self.__frm_zoom.grid_columnconfigure(0, weight=1)

        # Create the label
        label_zoom = ttk.Label(master=self.__frm_zoom, text="Zoom:")
        label_zoom.grid(row=0, column=0, sticky='e')

        # Create zoom slider
        self.__slider_playback_zoom = ttk.Scale(master=self.__frm_zoom,
                                                from_=0.0, to=1.0, length=100,
                                                command=self.__on_zoom_slider_changed,
                                                value=0.9)
        self.__slider_playback_zoom.grid(row=0, column=1, sticky='w')

    def __create_playback_button(self) -> None:
        """
        create the playback button widget with its current state

        :return: None
        """

        char = '\u23F8'  # paused
        if not self.__button_playing:
            char = '\u23F5'

        self.__style_playback_button = ttk.Style()
        self.__style_playback_button.configure('playback.TButton', font=('Helvetica', 40))

        # If we have made it before destroy the old copy
        if isinstance(self.__but_playback_menu, ttk.Button):
            self.__but_playback_menu.destroy()

        self.__but_playback_menu = ttk.Button(master=self.__frm_map_playback_menu, text=char,
                                              style='playback.TButton', width=1,
                                              command=self.__on_button_pressed)
        self.__but_playback_menu.grid(row=6, column=0)

    def set_playback_time(self, playback_time: float, total_time: float) -> None:
        """
        Set the playback time of the simulation and display it on the text

        :param playback_time: The playback time to set
        :param total_time: The maximum time
        :return: None
        """
        self.__max_time = total_time

        # round the data to make it nice
        playback_time = round(playback_time, 1)

        # set it on the label
        self.__set_playback_time_label(playback_time)

        # update the slider position too
        if self.__slider_playback_time:  # check it's been defined
            self.__slider_playback_time.set(playback_time / self.__max_time)

    def __set_playback_time_label(self, playback_time: float) -> None:
        """
        sets the playback time on the gui label

        :param playback_time: the playback time to set
        :return: None
        """

        if isinstance(self.__label_playback_time, ttk.Label):
            self.__label_playback_time.destroy()

        self.__label_playback_time = ttk.Label(master=self.__frm_map_playback_menu,
                                               text=f"Playback Time: {playback_time}s")
        self.__label_playback_time.grid(row=1, column=0, sticky='n')

    def set_playback_speed(self, playback_speed: float) -> None:
        """
        Set the playback speed of the simulation and display it on the text

        :param playback_speed: The playback speed to set
        :return: None
        """

        # round the data to make it nice
        playback_speed = round(playback_speed, 1)

        # If we have made it before destroy the old copy
        if isinstance(self.__label_playback_speed, ttk.Label):
            self.__label_playback_speed.destroy()

        self.__label_playback_speed = ttk.Label(master=self.__frm_map_playback_menu,
                                                text=f"Playback speed: {playback_speed}x")
        self.__label_playback_speed.grid(row=3, column=0, sticky='n')

        if self.__parent_class.set_playback_speed:  # check it's been defined
            self.__parent_class.set_playback_speed(playback_speed)

    def __on_button_pressed(self) -> None:
        """
        Gets triggered when the playback button is pressed

        :return: None
        """
        # Swap its state
        self.__button_playing = not self.__button_playing

        # tell the app class what the state is
        self.__parent_class.set_playing(self.__button_playing)
        self.__parent_class.stop_finish_start_editing()  # close the finishline menu

        self.__create_playback_button()  # remake the button with new icon

    def __on_time_slider_changed(self, event) -> None:
        """
        This gets called when the time slider changed and its not playing

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        value = self.__slider_playback_time.get()

        # check its been defined and not playing now
        if self.__parent_class.set_playback_time and not self.__parent_class.get_playing():
            # update the app class's time
            self.__parent_class.set_playback_time(value * self.__max_time)
            # update the label in GUI too
            self.__set_playback_time_label(round(value * self.__max_time, 1))

    def __on_speed_slider_changed(self, event) -> None:
        """
        This gets called when the speed slider changed

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        value = self.__slider_playback_speed.get()
        # # convert with exponents so instead of -2 to 2 its 0.25x to 4x
        # value = 2.0 ** value
        self.set_playback_speed(value)

    def __on_zoom_slider_changed(self, *args) -> None:
        """
        This gets called when the zoom slider changes

        :return: None
        """

        # *args is never used in this function but pylint will be upset it's not used
        # Do some random stuff to it
        if args == 1:
            pass

        value = 1.0 - self.__slider_playback_zoom.get()
        self.__parent_class.set_zoom_level(value)
