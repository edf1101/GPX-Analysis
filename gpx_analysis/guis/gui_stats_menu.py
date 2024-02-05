"""
This script contains the playback menu sub frame class related to the tk GUI
The AppGUI class is the only one to use outside of this class
"""
# Pylint ignores
# pylint: disable=R0902
# pylint: disable=R0914

# Import external libs
import tkinter as tk
from tkinter import ttk
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # for importing figs to mpl

# import our own library
try:
    from gpx_analysis import sporting as sport
    from gpx_analysis import stats_graph_handler as sgh
except ImportError:
    from .. import sporting as sport
    from .. import stats_graph_handler as sgh


class StatsMenuFrame:
    """
    This widget contains and abstracts the features of the stats menu
    """

    def __init__(self, parent_class, total_frame):
        """
        Constructor for the StatsMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
         :param total_frame: The whole frame all of the sim/graph elements are in
        """
        self.__parent_class = parent_class

        self.__total_frame = total_frame

        # Athlete data
        self.__athlete_data = {}

        # Create the surrounding frame for the graph
        self.__frm_stats_menu = None
        self.__frm_stats_menu = ttk.Frame(self.__total_frame, relief=tk.RAISED, borderwidth=5)
        self.__frm_stats_menu.grid(row=1, column=0, sticky='nsew')
        self.__frm_stats_menu.grid_columnconfigure(0, weight=1)  # center it

        # Create the stats menu widgets
        # Create the title
        label_stats_menu = ttk.Label(master=self.__frm_stats_menu,
                                     text="Statistics Menu",
                                     font=('Minion Pro', 14, 'bold'))
        label_stats_menu.grid(row=0, column=0, sticky='s')
        self.__frm_stats_menu.rowconfigure(2, minsize=20)

        # Create a dropdown speed units menu
        self.__frm_stats_dropdown = None
        self.__value_speed_selected_option = None  # this is the value of the units
        self.__create_units_menu()

        # Create a dropdown graph menu
        self.__frm_stats_graph_dropdown = None
        self.__value_graph_selected_option = None
        self.__create_graph_type_dropdown()

        # Create the checklist
        self.__menu_choices = None
        self.__menubutton = None
        self.__menu = None
        self.__create_athlete_selection_menu()  # make it empty at the start

        # Space in the grid
        self.__frm_stats_menu.rowconfigure(5, minsize=20)

        # Big label below to show all the stats
        test_data = {}
        self.__label_stats_text = None
        self.__display_text(test_data)

        # Create the graph frame
        self.__frm_stats_graph = None
        self.__frm_stats_graph = ttk.Frame(self.__total_frame, relief=tk.RAISED, borderwidth=5)
        self.__frm_stats_graph.grid(row=1, column=1, sticky='nsew')
        self.__last_graph_update = time.time()  # this makes sure we don't update too often

        # Create and add the graph plot to it
        self.__map_widget = None
        self.__stats_graph = sgh.StatsGraph()

        # update the stats graph with starting values
        option = (f'{self.__value_graph_selected_option.get()}|'
                  f'{self.__value_speed_selected_option.get()}')
        self.__stats_graph.draw_base_graph(option)

        self.__canvas = FigureCanvasTkAgg(self.__stats_graph.get_fig(),
                                          master=self.__frm_stats_graph)
        self.__map_widget = self.__canvas.get_tk_widget()
        self.__map_widget.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        self.__update_graph()

    def __update_graph(self) -> None:
        """
        This sets/ updates the mpl figure graph on the GUI

        :return: None
        """
        # make sure hasn't been called too recently
        if time.time() - self.__last_graph_update < 0.5:
            return

        self.__canvas.draw()

    def __create_graph_type_dropdown(self) -> None:
        """
        Create the graph type dropdown menu

        :return: None
        """
        # Encapsulate dropdown and dropdown label in a frame
        self.__frm_stats_graph_dropdown = ttk.Frame(self.__frm_stats_menu,
                                                    relief=tk.FLAT, borderwidth=0)
        self.__frm_stats_graph_dropdown.grid(row=1, column=0, sticky='nsew')

        # Create the dropdown menu
        graph_options = ['Speed', 'Distance', 'Gap', 'Rate', 'Speed & Rate']  # options for it

        root = self.__parent_class.get_tk_window()
        self.__value_graph_selected_option = tk.StringVar(master=root)
        self.__value_graph_selected_option.set(graph_options[0])  # s/500m is default unit

        # This doesn't need to be an instance var since we won't modify it again
        graph_dropdown = tk.OptionMenu(self.__frm_stats_graph_dropdown,
                                       self.__value_graph_selected_option,
                                       *graph_options,
                                       command=self.__on_graph_option_change)

        graph_dropdown.grid(row=0, column=1, sticky='nsew')

        # Create the label for it
        label_stats_graph_choice = ttk.Label(master=self.__frm_stats_graph_dropdown,
                                             text="Choose Graph Type:     ")
        label_stats_graph_choice.grid(row=0, column=0)

    def update_stats(self) -> None:
        """
        Updates the text statistics based on the time and who's selected
        
        :return: None
        """

        if self.__parent_class.ready is False:  # if everything isn't set up don't run
            return

        # get current time
        playback_time = self.__parent_class.get_playback_time()

        # put the data into a dict
        stats_data = {}
        for athlete in self.__athlete_data.values():

            # ignore this athlete if they're not in the selector options
            if athlete['filename'] not in self.__menu_choices:
                continue

            # ignore this athlete if they aren't selected
            if (isinstance(self.__menu_choices[athlete['filename']], tk.IntVar)
                    and self.__menu_choices[athlete['filename']].get() == 0):
                continue

            # Fetch all the data needed for this entry
            athlete_time = playback_time + athlete['start_time']
            name = athlete['display_name']

            # this makes sure no matter the modified start line it starts at a dist of 0m
            start_dist = sport.get_cumulative_dist_at_time(athlete['track'],
                                                           athlete['start_time'])
            current_dist = sport.get_cumulative_dist_at_time(athlete['track'], athlete_time)
            dist = round(current_dist - start_dist)

            # determine if the athlete has finished or not
            athlete_track_time = athlete['finish_time'] - athlete['start_time']
            if playback_time >= athlete_track_time:  # finished
                # so its high enough to trigger finished and its in order of finish time
                dist = 10000000 - athlete_track_time

            speed = sport.get_speed_at_time(athlete['track'], athlete_time)
            cad = sport.get_cadence_at_time(athlete['track'], athlete_time)

            # change speed so its in correct units
            units = self.__value_speed_selected_option.get()
            speed = sport.convert_speed_units(speed, units)
            if units in ['s/500m', 's/km']:  # for units measured in mins and secs write diff format
                mins = int(speed / 60)
                secs = round(speed % 60, 1)
                if secs < 10:  # so seconds starts with a preceeding 0
                    secs = f'0{secs}'
                speed = f'{mins}:{secs} {units}'
            else:
                speed = f'{speed} {units}'

            stats_data[name] = {'dist': dist, 'spd': speed, 'cad': cad}  # add to the dict

        self.__display_text(stats_data)

        self.__stats_graph.draw_time_line(playback_time)
        self.__update_graph()

    def set_athlete_list(self, athletes: dict) -> None:
        """
        Setter for the athlete list

        :param athletes: The athletes to set
        :return: None
        """
        self.__athlete_data = athletes

        # remake athlete list
        self.__create_athlete_selection_menu()


        # Set the athlete list on the graph
        self.__stats_graph.set_athletes(athletes)
        option = (f'{self.__value_graph_selected_option.get()}|'
                  f'{self.__value_speed_selected_option.get()}')
        self.__stats_graph.draw_base_graph(option)
        self.__update_graph()

    def __display_text(self, data_in: dict) -> None:
        """
        Displays the stats text

        :param data_in: A dictionary where boat display name is key and data is the value
        :return: None
        """

        # if nothing in the dictionary then set the text blank
        disp_text = ''
        if data_in:
            # Sort the athletes by highest dist, dodgy insertion sort
            modified_data = []
            while len(data_in):
                max_dist = -1  # no distance will not be greater than this
                max_key = None
                for key, value in data_in.items():
                    test_val = value['dist']
                    if test_val > max_dist:
                        max_dist = test_val
                        max_key = key

                # Make sure athlete distance renders correctly
                if max_dist > 100000:
                    # if its over 100,000m (unrealistic number) say its finished
                    new_dist = 'FIN'
                else:
                    new_dist = f'{max_dist}m'
                modified_data.append({'name': max_key, 'dist': new_dist,
                                      'spd': data_in[max_key]['spd'],
                                      'cad': data_in[max_key]['cad']})
                del data_in[max_key]

            disp_text = ''

            max_athlete_dist_len = max(len(i['dist']) for i in modified_data) + 2

            for position, athlete_data in enumerate(modified_data):
                # make it so all the data starts lining up after names
                athlete_name = athlete_data['name']
                athlete_dist = athlete_data['dist']
                athlete_spd = athlete_data['spd']
                athlete_cad = athlete_data['cad']

                disp_text += (f'{position + 1}. ' + athlete_name + '\n' + '   ' +
                              athlete_dist + ' ' * (max_athlete_dist_len - len(
                            athlete_dist)) + athlete_spd + '   ' + f'{athlete_cad} s/m')

                disp_text += '\n'  # so it starts on a new line

        # If its been made before just modify text
        if isinstance(self.__label_stats_text, ttk.Label):
            self.__label_stats_text.configure(text=disp_text)

        else:
            self.__label_stats_text = ttk.Label(master=self.__frm_stats_menu, text=disp_text,
                                                font='Courier')
            self.__label_stats_text.grid(row=6, column=0, sticky='w')

    def __create_athlete_selection_menu(self) -> None:
        """
        Creates the athlete selection menu from the athlete variable

        :return: None
        """
        self.__menubutton = tk.Menubutton(self.__frm_stats_menu,
                                          text="Choose Which athletes to show:",
                                          indicatoron=True)
        self.__menu = tk.Menu(self.__menubutton, tearoff=False)
        self.__menubutton.configure(menu=self.__menu)
        self.__menubutton.grid(row=4, column=0, sticky='w')
        self.__menu_choices = {}
        root = self.__parent_class.get_tk_window()

        for athlete in self.__athlete_data.values():
            display_name = athlete['display_name']
            filename = athlete['filename']

            self.__menu_choices[filename] = tk.IntVar(master=root, value=1)
            self.__menu.add_checkbutton(label=display_name, variable=self.__menu_choices[filename],
                                        onvalue=1, offvalue=0, command=self.__on_athlete_change)
        self.__on_athlete_change()

    def __create_units_menu(self) -> None:
        """
        Create the frame with a units dropdown and button to confirm

        :return: None
        """
        # Encapsulate dropdown and dropdown label in a frame
        self.__frm_stats_dropdown = ttk.Frame(self.__frm_stats_menu, relief=tk.FLAT, borderwidth=0)
        self.__frm_stats_dropdown.grid(row=3, column=0, sticky='nsew')

        # Create the dropdown menu
        speed_options = ['s/500m', 's/km', 'm/s', 'km/h', 'mph']  # options for it
        root = self.__parent_class.get_tk_window()

        self.__value_speed_selected_option = tk.StringVar(master = root)
        self.__value_speed_selected_option.set(speed_options[0])  # s/500m is default unit

        # This doesn't need to be an instance var since we won't modify it again
        speed_dropdown = tk.OptionMenu(self.__frm_stats_dropdown,
                                       self.__value_speed_selected_option,
                                       *speed_options,
                                       command=self.__on_speed_option_change)
        speed_dropdown.grid(row=0, column=1, sticky='nsew')

        # Create the label for it
        label_stats_speed_choice = ttk.Label(master=self.__frm_stats_dropdown,
                                             text="Choose Speed Units:     ")
        label_stats_speed_choice.grid(row=0, column=0)

    def __on_athlete_change(self, *args) -> None:
        """
        This gets called when an athlete gets selected or deselected
        in the dropdown checklist

        :param args: *args
        :return: None
        """

        # *args is never used in this function but pylint will be upset it's not used
        # Do some random stuff to it
        if args == 1:
            pass

        # update the stats with the new selection
        self.update_stats()

        # only include the athletes selected on the graph
        graph_athletes = {}
        for key, value in self.__athlete_data.items():
            if (isinstance(self.__menu_choices[value['filename']], tk.IntVar)
                    and self.__menu_choices[value['filename']].get() == 0):
                continue
            graph_athletes[key] = value

        if self.__parent_class.ready:

            self.__stats_graph.set_athletes(graph_athletes)
            option = (f'{self.__value_graph_selected_option.get()}|'
                      f'{self.__value_speed_selected_option.get()}')
            self.__stats_graph.draw_base_graph(option)
            self.__update_graph()

    def __on_speed_option_change(self, *args) -> None:
        """
        Called when speed option changes

        :return: None
        """

        # *args is never used in this function but pylint will be upset it's not used
        # Do some random stuff to it
        if args == 1:
            pass

        # update the stats with the new units
        self.update_stats()

        # update the stats graph
        option = (f'{self.__value_graph_selected_option.get()}|'
                  f'{self.__value_speed_selected_option.get()}')
        self.__stats_graph.draw_base_graph(option)
        self.__update_graph()

    def __on_graph_option_change(self, *args) -> None:
        """
        Called when graph option changes

        :return: None
        """

        # *args is never used in this function but pylint will be upset it's not used
        # Do some random stuff to it
        if args == 1:
            pass

        # update the stats graph
        option = (f'{self.__value_graph_selected_option.get()}|'
                  f'{self.__value_speed_selected_option.get()}')
        self.__stats_graph.draw_base_graph(option)
        self.__update_graph()
