"""
This script contains classes related to the tk GUI
The AppGUI class is the only one to use outside of this class
"""
# Pylint ignores
# pylint: disable=R0902


import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import graph_handler as gh
    from gpx_analysis import sporting as sport

except ImportError:
    import gpx_parser as gpx
    import graph_handler as gh
    import sporting as sport

track_1 = gpx.Track("../example_data/Race-take-1.gpx")

mpl_graph = gh.MapClass()
mpl_graph.add_track(track_1)
mpl_graph.plot_images()

mpl_graph.draw_track(0, color='red')
mpl_graph.get_figure().set_dpi(100)


pos_1 = sport.get_position_at_time(track_1, 100)
mpl_graph.center_viewpoint([pos_1])


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

        self.__mpl_graph = map_class
        self.__window = window
        self.__window.title("GPX Analysis")  # Set the window title

        # Configure the layout of the basic 2x2 grid
        self.__window.rowconfigure(0, minsize=500, weight=3)
        self.__window.rowconfigure(1, minsize=250, weight=1)
        self.__window.columnconfigure(1, minsize=500, weight=8)
        self.__window.columnconfigure(0, minsize=260, weight=1)

        # Set the map widget in the TOP RIGHT corner
        self.__map_widget = None
        self.__set_map_widget()

        # Create the menus and submenus down the side
        # First initialise the main menus as None
        self.__frm_map_menu = None
        self.__frm_stats_menu = None
        # Now initialise the submenu classes as None
        self.__control_menu = None
        self.__finishline_menu = None
        self.__playback_menu = None
        # Then set their values here
        self.__set_submenus()

        # Function for removing focus from widgets once they have been clicked off
        self.__window.bind_all("<Button-1>", self.__remove_entry_focus)

        # Create the stats menu
        self.__stats_menu = StatsMenuFrame(self)

    def __remove_entry_focus(self, event) -> None:
        """
        This function removes focuses from widgets when they are clicked off
        :param event:
        :return:
        """
        if not isinstance(event.widget, ttk.Entry):
            self.__window.focus()

    def __set_map_widget(self) -> None:
        """
        This displays the mpl figure map on the GUI

        :return: None
        """

        canvas = FigureCanvasTkAgg(self.__mpl_graph.get_figure(), master=self.__window)
        self.__map_widget = canvas.get_tk_widget()
        self.__map_widget.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

    def __set_submenus(self) -> None:
        """
        This creates and initialises the submenus

        :return: None
        """

        #  Set up the two menus (map menu on top, stats menu on bottom)
        self.__frm_map_menu = ttk.Frame(self.__window, relief=tk.RAISED, borderwidth=5)
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


class ControlMenuFrame:
    """
    This widget contains and abstracts the features of the control menu
    """

    def __init__(self, parent_class: AppGUI):
        """
        Constructor for the ControlMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
        """
        self.__parent_class = parent_class
        self.__window = parent_class.get_tk_window()
        # First the open / master menu (open file, name boats etc)

        self.__frm_map_control_menu = ttk.Frame(self.__parent_class.get_frm_map_menu(),
                                                relief=tk.RIDGE, borderwidth=2)
        self.__frm_map_control_menu.grid(row=0, column=0, sticky='nsew')

        # Create the control menu items

        # This centers the items (unless we specify a stickiness)
        self.__frm_map_control_menu.grid_columnconfigure(0, weight=1)

        # Set up the widgets that won't ever change
        self.__setup_static_widgets()

        # Create the name selector / deletion menu and initialise its variables here
        self.__last_selected = None  # Holds the last athlete selected so we know what swapped
        self.__athlete_names = ['BoatA', 'BoatB', 'BoatC']
        self.__frm_map_control_dropdown = None
        self.__dropdown_map_control = None
        self.__value_map_dropdown = None
        self.__create_name_selector()

        # Athlete and file name labels
        self.label_control_menu_file = None
        self.label_control_menu_display = None
        self.set_athlete_data('test.gpx', 'boatA')

        # Encapsulate change name entry field and button in a frame
        self.frm_map_control_changename = None
        self.text_map_control_changename = None  # The value of the entry field
        self.__setup_namechange()

    def __setup_namechange(self) -> None:
        """
        Sets up the name change frame data
        :return: None
        """
        # Encapsulate change name entry field and button in a frame

        # Create the frame
        self.frm_map_control_changename = ttk.Frame(self.__frm_map_control_menu, relief=tk.FLAT,
                                                    borderwidth=0)
        self.frm_map_control_changename.grid(row=8, column=0, sticky='nsew')

        self.text_map_control_changename = tk.StringVar()

        # The entry widget doesn't need to be an instance var as we won't modify it again
        entry_map_control_changename = ttk.Entry(self.frm_map_control_changename,
                                                 textvariable=self.text_map_control_changename)
        entry_map_control_changename.grid(row=0, column=1, sticky='nswe')

        # Create a confirm button doesn't need to be instance as we won't modify it
        btn_control_changename = ttk.Button(self.frm_map_control_changename, text='\U00002713',
                                            width=2, command=self.__on_name_change)
        btn_control_changename.grid(row=0, column=2, sticky='')

    def set_athlete_data(self, filename: str, display_name: str) -> None:
        """
        This sets the text fields for the athlete

        :param filename: The filename to display
        :param display_name: The display name
        :return: None
        """
        self.label_control_menu_file = ttk.Label(master=self.__frm_map_control_menu,
                                                 text=f"Filename: {filename}")
        self.label_control_menu_file.grid(row=5, column=0, sticky='s')
        self.label_control_menu_display = ttk.Label(master=self.__frm_map_control_menu,
                                                    text=f"Display Name: {display_name}")
        self.label_control_menu_display.grid(row=6, column=0, sticky='s')

    def __create_name_selector(self) -> None:
        """
        This creates the name selector widgets, dropdown button frame etc

        :return: None
        """
        # Encapsulate dropdown and delete in a frame

        # Create the frame to hold the widgets in
        self.__frm_map_control_dropdown = ttk.Frame(self.__frm_map_control_menu,
                                                    relief=tk.FLAT, borderwidth=0)
        self.__frm_map_control_dropdown.grid(row=3, column=0, sticky='nsew')

        # Create the dropdown menu
        self.__create_dropdown()

        # Create a remove name button, we don't need to reference this button again so no need
        # to make it an instance variable
        btn_control_del = ttk.Button(self.__frm_map_control_dropdown, text='\U0001F5D1',
                                     width=2, command=self.__on_remove_press)
        btn_control_del.grid(row=0, column=1, sticky='swen')

    def __create_dropdown(self) -> None:
        """
        Creates/ recreates the dropdown menu with a set of athletes

        :return: None
        """
        self.__value_map_dropdown = tk.StringVar()
        self.__value_map_dropdown.set(self.__athlete_names[0])
        self.__value_map_dropdown.trace('w', self.__on_athlete_swap)
        self.__last_selected = self.__athlete_names[0]

        self.__dropdown_map_control = tk.OptionMenu(self.__frm_map_control_dropdown,
                                                    self.__value_map_dropdown,
                                                    *self.__athlete_names)
        self.__dropdown_map_control.grid(row=0, column=0, sticky='nsew')

    def __setup_static_widgets(self) -> None:
        """
        Set up the labels and buttons that won't be overwritten / modified at any point
        :return: None
        """
        # The title label will never change so set it here and doesn't need
        # to be an instance variable
        label_control_menu = ttk.Label(master=self.__frm_map_control_menu,
                                       text="Athlete Menu",
                                       font=('Minion Pro', 14, 'bold'))
        label_control_menu.grid(row=0, column=0, sticky='s')

        # This button also won't change so lets declare it here
        btn_control_open = ttk.Button(self.__frm_map_control_menu,
                                      text="Open File",
                                      command=self.__on_open_press)
        btn_control_open.grid(row=1, column=0, sticky="nsew")

        # Select/ Remove althletes label
        label_control_menu_select = ttk.Label(master=self.__frm_map_control_menu,
                                              text="Select & Remove Athletes:")
        label_control_menu_select.grid(row=2, column=0, sticky='w', )

        # Have an empty row on row 4 for aesthetics
        self.__frm_map_control_menu.rowconfigure(4, minsize=30)

        # This won't be modified either
        label_control_menu_changename = ttk.Label(master=self.__frm_map_control_menu,
                                                  text="Change name:")
        label_control_menu_changename.grid(row=7, column=0, sticky='w', )

    def __on_open_press(self) -> None:
        """
        When the open file button is pressed this is called

        :return: None
        """

        print('opening')

    def __on_remove_press(self) -> None:
        """
        When the remove athlete button is pressed this is called

        :return: None
        """

        print('removing')

    def __on_athlete_swap(self, *args) -> None:
        """
        Gets called when you change which athlete is selected in the dropdown
        :return:
        """
        # *args must be here as we get 4 params, yet we do nothing with them so pylint unhappy
        # Thus do something random with them
        for arg in args:
            if arg == 1:
                pass

        swapped_from = self.__last_selected
        self.__last_selected = self.__value_map_dropdown.get()
        swapped_to = self.__last_selected
        print(f'athlete swapped: {swapped_from} swapped to {swapped_to}')

    def __on_name_change(self) -> None:
        """
        This gets triggered when the name change confirm button is pressed

        :return: None
        """
        changed_to = self.text_map_control_changename.get()
        print(f'name change: changed to {changed_to}')


class FinishlineMenuFrame:
    """
    This widget contains and abstracts the features of the finishline menu
    """

    def __init__(self, parent_class: AppGUI):
        """
        Constructor for the FinishlineMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
        """
        self.__parent_class = parent_class

        # Set up the frame to contain the widgets
        self.__frm_map_finishline_menu = ttk.Frame(self.__parent_class.get_frm_map_menu(),
                                                   relief=tk.RIDGE, borderwidth=2)
        self.__frm_map_finishline_menu.grid(row=1, column=0, sticky='nsew')
        self.__frm_map_finishline_menu.grid_columnconfigure(0, weight=1)  # centers it
        # have a blank row on row 2 for aesthetics
        self.__frm_map_finishline_menu.rowconfigure(2, minsize=15)

        # Put buttons etc. in the Start finish line menu
        # Create the title for the frame
        # doesn't need to be instance var as not referenced elsewhere
        label_finishline_menu = ttk.Label(master=self.__frm_map_finishline_menu,
                                          text="Start/Finish Line Menu",
                                          font=('Minion Pro', 14, 'bold'))
        label_finishline_menu.grid(row=0, column=0, sticky='s')

        # Display the status of the menu (cant do as running, or who editing) on a label
        self.label_finishline_menu_status = None
        self.__set_status()

        # Encapsulate start slider precise entry and label in a frame
        self.__frm_map_finishline_start = None
        self.__label_finishline_menu_start = None
        self.__slider_finishline_menu_start = None
        self.__text_finishline_start_precise = None  # holds the precise data for start line time
        self.__setup_start_frame()

        # Encapsulate finish slider precise entry and label in a frame
        self.__frm_map_finishline_end = None
        self.__label_finishline_menu_end = None
        self.__slider_finishline_menu_end = None
        self.__text_finishline_end_precise = None
        self.__setup_end_frame()

    def __set_status(self) -> None:
        """
        Sets the status for whether you are able to modify start lines

        :return: None
        """
        self.label_finishline_menu_status = ttk.Label(master=self.__frm_map_finishline_menu,
                                                      text="Currently editing: Boat 1")
        self.label_finishline_menu_status.grid(row=1, column=0, sticky='nswe')

    def __setup_start_frame(self) -> None:
        """
        Set up the start frame widgets

        :return: None
        """

        # Encapsulate slider precise entry and label in a frame
        self.__frm_map_finishline_start = ttk.Frame(self.__frm_map_finishline_menu)
        self.__frm_map_finishline_start.grid(row=3, column=0, sticky='w')

        # Set up the start line info text
        self.__label_finishline_menu_start = ttk.Label(master=self.__frm_map_finishline_start,
                                                       text=f"Start Line: {0}s  Total: {0}s")
        self.__label_finishline_menu_start.grid(row=0, column=0, columnspan=3)

        # Set up the slider
        self.__slider_finishline_menu_start = ttk.Scale(master=self.__frm_map_finishline_start,
                                                        orient=tk.HORIZONTAL,
                                                        from_=0, to=100,
                                                        command=self.__on_start_slider_changed)
        self.__slider_finishline_menu_start.grid(row=1, column=0)

        # entry box for precise entry
        self.__text_finishline_start_precise = tk.StringVar()

        # This doesn't need to be an instance variable as not used again
        entry__start_precise = ttk.Entry(self.__frm_map_finishline_start,
                                         textvariable=self.__text_finishline_start_precise,
                                         width=5)
        entry__start_precise.grid(row=1, column=1)

        # button for entry box, his doesn't need to be an instance variable as not used again
        btn_finishline_start = ttk.Button(self.__frm_map_finishline_start,
                                          text='SET',
                                          command=self.__on_precise_button_start_pressed)
        btn_finishline_start.grid(row=1, column=2, sticky='nsew')

    def __setup_end_frame(self) -> None:
        """
        Set up the frame containing all the end widgets

        :return: None
        """
        # Set up the bounding frame
        self.__frm_map_finishline_end = ttk.Frame(self.__frm_map_finishline_menu)
        self.__frm_map_finishline_end.grid(row=4, column=0, sticky='w')

        # set up the text saying where the finish line is
        self.__label_finishline_menu_end = ttk.Label(master=self.__frm_map_finishline_end,
                                                     text=f"Finish Line: {0}s  Total: {0}s")
        self.__label_finishline_menu_end.grid(row=0, column=0, columnspan=3)

        # set up the slider
        self.__slider_finishline_menu_end = ttk.Scale(master=self.__frm_map_finishline_end,
                                                      orient=tk.HORIZONTAL,
                                                      from_=0, to=100, value=100,
                                                      command=self.__on_end_slider_changed)
        self.__slider_finishline_menu_end.grid(row=1, column=0)

        # entry box for precise entry
        # the text data needs to be accessible outside but entry itself won't be modified again
        self.__text_finishline_end_precise = tk.StringVar()
        entry_finishline_end_precise = ttk.Entry(self.__frm_map_finishline_end,
                                                 textvariable=self.__text_finishline_end_precise,
                                                 width=5)
        entry_finishline_end_precise.grid(row=1, column=1)

        # button for entry box
        btn_finishline_end = ttk.Button(self.__frm_map_finishline_end,
                                        text='SET', command=self.__on_precise_button_end_pressed)
        btn_finishline_end.grid(row=1, column=2, sticky='nsew')

    def __on_precise_button_start_pressed(self) -> None:
        """
        This gets called when the start precise button gets pressed

        :return: None
        """
        print("precise start pressed")
        value = self.__text_finishline_start_precise.get()
        valid = validate_float_input(value)
        if valid:
            print(f"precise start pressed value: {value}")

    def __on_start_slider_changed(self, event) -> None:
        """
        This gets called when the start slider changed

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        value = self.__slider_finishline_menu_start.get()
        print(f'start slider changed to {value}')

    def __on_precise_button_end_pressed(self) -> None:
        """
        This gets called when the end precise button gets pressed

        :return: None
        """
        value = self.__text_finishline_end_precise.get()
        valid = validate_float_input(value)
        if valid:
            print(f"precise end pressed value: {value}")

    def __on_end_slider_changed(self, event) -> None:
        """
        This gets called when the end slider changed

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        value = self.__slider_finishline_menu_end.get()
        print(f'end slider changed to {value}')


class PlaybackMenuFrame:
    """
    This widget contains and abstracts the features of the playback menu
    """

    def __init__(self, parent_class: AppGUI):
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

        # Put buttons etc in the playback menu

        # Add a title
        label_playback_menu = ttk.Label(master=self.__frm_map_playback_menu,
                                        text="Simulation Menu",
                                        font=('Minion Pro', 14, 'bold'))
        label_playback_menu.grid(row=0, column=0, sticky='n')

        # create the playback time label
        self.__label_playback_time = None
        self.set_playback_time(0)

        # create the playback time slider
        self.__slider_playback_time = ttk.Scale(master=self.__frm_map_playback_menu,
                                                from_=0, to=100, length=250,
                                                command=self.__on_time_slider_changed)
        self.__slider_playback_time.grid(row=2, column=0)

        # Create playback speed label
        self.__label_playback_speed = None
        self.set_playback_speed(1)

        # Create playback slider
        self.__slider_playback_speed = ttk.Scale(master=self.__frm_map_playback_menu,
                                                 from_=-2, to=2, length=100,
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
                                                from_=5, to=500, length=100,
                                                command=self.__on_zoom_slider_changed,
                                                value=50)
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
        self.__but_playback_menu = ttk.Button(master=self.__frm_map_playback_menu, text=char,
                                              style='playback.TButton', width=1,
                                              command=self.__on_button_pressed)
        self.__but_playback_menu.grid(row=6, column=0)

    def set_playback_time(self, playback_time: float) -> None:
        """
        Set the playback time of the simulation and display it on the text

        :param playback_time: The playback time to set
        :return: None
        """

        # round the data to make it nice
        playback_time = round(playback_time, 1)

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

        self.__label_playback_speed = ttk.Label(master=self.__frm_map_playback_menu,
                                                text=f"Playback speed: {playback_speed}x")
        self.__label_playback_speed.grid(row=3, column=0, sticky='n')

    def __on_button_pressed(self) -> None:
        """
        Gets triggered when the playback button is pressed

        :return: None
        """
        # Swap its state
        self.__button_playing = not self.__button_playing
        self.__create_playback_button()

    def __on_time_slider_changed(self, event) -> None:
        """
        This gets called when the time slider changed

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        value = self.__slider_playback_time.get()

        # update the text too
        self.set_playback_time(value)

    def __on_speed_slider_changed(self, event) -> None:
        """
        This gets called when the speed slider changed

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        value = self.__slider_playback_speed.get()
        # convert with exponents so instead of -2 to 2 its 0.25x to 4x
        value = 2.0 ** value
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

        value = self.__slider_playback_zoom.get()
        print(value)


class StatsMenuFrame:
    """
    This widget contains and abstracts the features of the stats menu
    """

    def __init__(self, parent_class: AppGUI):
        """
        Constructor for the StatsMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
        """
        self.__parent_class = parent_class
        self.__window = self.__parent_class.get_tk_window()

        # Create the surrounding frame
        self.__frm_stats_menu = None
        self.__frm_stats_menu = ttk.Frame(self.__window, relief=tk.RAISED, borderwidth=5)
        self.__frm_stats_menu.grid(row=1, column=0, sticky='nsew')
        self.__frm_stats_menu.grid_columnconfigure(0, weight=1)  # center it

        # Create the stats menu widgets
        # Create the title
        label_stats_menu = ttk.Label(master=self.__frm_stats_menu,
                                     text="Statistics Menu",
                                     font=('Minion Pro', 14, 'bold'))
        label_stats_menu.grid(row=0, column=0, sticky='s')
        self.__frm_stats_menu.rowconfigure(1, minsize=20)

        # Create a dropdown speed units menu
        self.__frm_stats_dropdown = None
        self.__value_speed_selected_option = None  # this is the value of the units
        self.__create_units_menu()

        # Create the checklist
        options = ['BoatA', 'BoatB', 'BoatC']
        self.__menu_choices = None
        self.__menubutton = None
        self.__menu = None
        self.__create_athlete_selection_menu(options)

        # Space in the grid
        self.__frm_stats_menu.rowconfigure(4, minsize=20)

        # Big label below to show all of the stats
        test_data = {'Canford': {'dist': 1000, 'spd': '1:53.2 s/500m', 'cad': 38},
                     'Winchester': {'dist': 900, 'spd': '1:55.6 s/500m', 'cad': 40},
                     'Bryanston': {'dist': 800, 'spd': '1:59.8 s/500m', 'cad': 28}}
        self.__label_stats_text = None
        self.display_text(test_data)

    def display_text(self, data_in: dict) -> None:
        """
        Displays the stats text

        :param data_in: A dictionary where boat display name is key and data is the value
        :return: None
        """
        # Get the length of the longest name

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
            new_dist = ''
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

        max_athlete_name_len = max(len(i['name']) for i in modified_data) + 2
        max_athlete_dist_len = max(len(i['dist']) for i in modified_data) + 2

        for athlete_data in modified_data:
            # make it so all the data starts lining up after names
            athlete_name = athlete_data['name']
            athlete_dist = athlete_data['dist']
            athlete_spd = athlete_data['spd']
            athlete_cad = athlete_data['cad']

            disp_text += (athlete_name + ' ' * (max_athlete_name_len - len(athlete_name)) +
                          athlete_dist + ' ' * (max_athlete_dist_len - len(
                        athlete_dist)) + athlete_spd + '   ' + f'{athlete_cad}s/m')

            disp_text += '\n'  # so it starts on a new line

        self.__label_stats_text = ttk.Label(master=self.__frm_stats_menu, text=disp_text,
                                            font='Courier')
        self.__label_stats_text.grid(row=5, column=0, sticky='w')

    def __create_athlete_selection_menu(self, options) -> None:
        """
        Creates the athlete selection menu

        :param options: The options for the list
        :return: None
        """
        self.__menubutton = tk.Menubutton(self.__frm_stats_menu,
                                          text="Choose Which athletes to show:",
                                          indicatoron=True)
        self.__menu = tk.Menu(self.__menubutton, tearoff=False)
        self.__menubutton.configure(menu=self.__menu)
        self.__menubutton.grid(row=3, column=0, sticky='w')
        self.__menu_choices = {}
        options = ['BoatA', 'BoatB', 'BoatC']
        for choice in options:
            self.__menu_choices[choice] = tk.IntVar(value=0)
            self.__menu.add_checkbutton(label=choice, variable=self.__menu_choices[choice],
                                        onvalue=1, offvalue=0, command=self.__on_athlete_change)

    def __create_units_menu(self) -> None:
        """
        Create the frame with a units dropdown and button to confirm

        :return: None
        """
        # Encapsulate dropdown and dropdown label in a frame
        self.__frm_stats_dropdown = ttk.Frame(self.__frm_stats_menu, relief=tk.FLAT, borderwidth=0)
        self.__frm_stats_dropdown.grid(row=2, column=0, sticky='nsew')

        # Create the dropdown menu
        speed_options = ['s/500m', 'm/s', 'kmh', 'mph']  # options for it

        self.__value_speed_selected_option = tk.StringVar()
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

        print('change')
        for key, value in self.__menu_choices.items():
            print(key, value.get())

    def __on_speed_option_change(self, *args) -> None:
        """
        Called when speed option changes

        :return: None
        """

        # *args is never used in this function but pylint will be upset it's not used
        # Do some random stuff to it
        if args == 1:
            pass

        value = self.__value_speed_selected_option.get()
        print(value)


def validate_float_input(number: str) -> bool:
    """
    Validates whether a string can be a float or not

    :param number: string form of the number to enter
    :return: whether it is (true) or isn't (false)
    """
    try:
        float(number)
        return True
    except ValueError:
        # display a warning popup
        msgbox.showerror("Invalid input", "This was an invalid input, must be a decimal number")
        return False


# Test it
root = tk.Tk()
app = AppGUI(root, mpl_graph)

root.mainloop()
