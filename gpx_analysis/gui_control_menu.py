"""
This script contains the athlete menu sub frame class related to the tk GUI
The AppGUI class is the only one to use outside of this class
"""
# Pylint ignores
# pylint: disable=R0902
# pylint: disable=R0914

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox  # for popups
from tkinter import filedialog  # for choosing gpx file to open
from tkinter import colorchooser


class ControlMenuFrame:
    """
    This widget contains and abstracts the features of the control menu
    """

    def __init__(self, parent_class):
        """
        Constructor for the ControlMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
        """
        self.__parent_class = parent_class
        # First the open / master menu (open file, name boats etc)

        self.__frm_map_control_menu = ttk.Frame(self.__parent_class.get_frm_map_menu(),
                                                relief=tk.RIDGE, borderwidth=2)
        self.__frm_map_control_menu.grid(row=0, column=0, sticky='nsew')

        # Create the control menu items
        # Athlete Data
        self.__athlete_data = {}

        # This centers the items (unless we specify a stickiness)
        self.__frm_map_control_menu.grid_columnconfigure(0, weight=1)

        # Set up the widgets that won't ever change
        self.__setup_static_widgets()

        # Create the name selector / deletion menu and initialise its variables here
        self.__last_selected = None  # Holds the last athlete selected so we know what swapped
        self.__athlete_names = ['None']
        self.__frm_map_control_dropdown = None
        self.__dropdown_map_control = None
        self.__value_map_dropdown = None
        self.__create_name_selector()

        # Athlete and file name labels
        self.__label_control_menu_file = None
        self.__label_control_menu_display = None
        self.__set_athlete_data()

        # Encapsulate change name entry field and button in a frame
        self.__frm_map_control_changename = None
        self.__text_map_control_changename = None  # The value of the entry field
        self.__setup_namechange()

        # Callbacks
        self.__open_file_callback = None
        self.__changename_callback = None
        self.__delete_callback = None

    def update_athlete_data(self, athlete_data: dict,
                            remake_widgets: bool = True) -> None:
        """
        Set the athlete data in this class (setter method)

        :param athlete_data: Data to set
        :param remake_widgets: whether or not to remake the widgets
        :return: None
        """
        self.__athlete_data = athlete_data
        if len(athlete_data):
            self.__athlete_names = [v['display_name'] for v in athlete_data.values()]
        else:
            self.__athlete_names = ['None']

        if remake_widgets:
            self.__create_name_selector()  # recreate name selector with new fields
            self.__set_athlete_data()

    def __setup_namechange(self) -> None:
        """
        Sets up the name change frame data

        :return: None
        """
        # Encapsulate change name entry field and button in a frame

        # Create the frame
        self.__frm_map_control_changename = ttk.Frame(self.__frm_map_control_menu, relief=tk.FLAT,
                                                      borderwidth=0)
        self.__frm_map_control_changename.grid(row=8, column=0, sticky='nsew')
        root = self.__parent_class.get_tk_window()
        self.__text_map_control_changename = tk.StringVar(master=root)

        # The entry widget doesn't need to be an instance var as we won't modify it again
        entry_map_control_changename = ttk.Entry(self.__frm_map_control_changename,
                                                 textvariable=self.__text_map_control_changename)
        entry_map_control_changename.grid(row=0, column=1, sticky='nswe')

        # Create a confirm button doesn't need to be instance as we won't modify it
        btn_control_changename = ttk.Button(self.__frm_map_control_changename, text='\U00002713',
                                            width=2, command=self.__on_name_change)
        btn_control_changename.grid(row=0, column=2, sticky='')

    def __set_athlete_data(self) -> None:
        """
        This sets the text fields for the athlete

        :return: None
        """

        current_option = self.__last_selected
        if current_option == 'None':
            filename, display_name = 'None', 'None'
        else:
            # initialise here in case we cant find right values
            filename, display_name = current_option, current_option

            # find the athlete with the same display name and get its filename
            for key, value in self.__athlete_data.items():
                if value['display_name'] == current_option:
                    filename = key
                    break

        # If we have made it before destroy the old copy
        if isinstance(self.__label_control_menu_file, ttk.Label):
            self.__label_control_menu_file.destroy()

        self.__label_control_menu_file = ttk.Label(master=self.__frm_map_control_menu,
                                                   text=f"Filename: {filename}")
        self.__label_control_menu_file.grid(row=5, column=0, sticky='s')

        # If we have made it before destroy the old copy
        if isinstance(self.__label_control_menu_display, ttk.Label):
            self.__label_control_menu_display.destroy()
        self.__label_control_menu_display = ttk.Label(master=self.__frm_map_control_menu,
                                                      text=f"Display Name: {display_name}")
        self.__label_control_menu_display.grid(row=6, column=0, sticky='s')

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
        root = self.__parent_class.get_tk_window()
        self.__value_map_dropdown = tk.StringVar(master=root)
        self.__value_map_dropdown.set(self.__athlete_names[0])
        self.__last_selected = self.__athlete_names[0]

        # If we have made it before destroy the old copy
        if isinstance(self.__dropdown_map_control, ttk.OptionMenu):
            self.__dropdown_map_control.destroy()

        self.__dropdown_map_control = tk.OptionMenu(self.__frm_map_control_dropdown,
                                                    self.__value_map_dropdown,
                                                    *self.__athlete_names,
                                                    command=self.__on_athlete_swap)
        self.__dropdown_map_control.grid(row=0, column=0, sticky='nsew')

        # if athlete data has been created, run this so it also updates the finishline menu
        # when athletes are modified / deleted
        athlete_key = None
        if self.__athlete_data:
            # Also need to find the current athlete key
            for key, value in self.__athlete_data.items():

                if value['display_name'] == self.__last_selected:
                    athlete_key = key

            self.__parent_class.set_finishline_athlete_selected(athlete_key)
            self.__parent_class.stop_finish_start_editing()

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
                                                  text="Change display name:")
        label_control_menu_changename.grid(row=7, column=0, sticky='w', )

        # add the button to change colours
        self.__btn_colour_picker = ttk.Button(master=self.__frm_map_control_menu,
                                              text="Change colour",
                                              command=self.__on_change_colour)
        self.__btn_colour_picker.grid(row=9, column=0, sticky='w')

    def __on_open_press(self) -> None:
        """
        When the open file button is pressed this is called

        :return: None
        """

        file_path = filedialog.askopenfilename()  # get the file path
        if file_path != '':  # check it's not blank
            self.__open_file_callback(file_path)

    def __on_change_colour(self) -> None:
        """
        Gets called when the change colour button is pressed

        :return: None
        """
        if self.__athlete_data == {}:  # no one to assign to
            return

        color_tuple = colorchooser.askcolor(title="Choose color")[0]
        if color_tuple is None:
            return  # no colour picked

        # modify the colours so they are 0-1
        color_tuple = (color_tuple[0] / 255.0, color_tuple[1] / 255.0, color_tuple[2] / 255.0)

        # Get the athlete's key
        athlete_key = None

        # Also need to find the current filename.
        for key, value in self.__athlete_data.items():

            if value['display_name'] == self.__last_selected:
                athlete_key = key

        # if it is found then change it in the callback function
        if athlete_key:
            self.__parent_class.on_colour_change(athlete_key, color_tuple)

    def __on_remove_press(self) -> None:
        """
        When the remove athlete button is pressed this is called

        :return: None
        """

        # Get the athlete being removed
        athlete_key = None

        for key, value in self.__athlete_data.items():

            if value['display_name'] == self.__last_selected:
                athlete_key = key

        if athlete_key:
            self.__delete_callback(athlete_key)

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

        self.__last_selected = self.__value_map_dropdown.get()

        # update the info labels
        self.__set_athlete_data()

        # Get the athlete currently on
        athlete_key = None

        # Also need to find the current athlete key
        for key, value in self.__athlete_data.items():

            if value['display_name'] == self.__last_selected:
                athlete_key = key

        self.__parent_class.set_finishline_athlete_selected(athlete_key)
        self.__parent_class.stop_finish_start_editing()

    def __on_name_change(self) -> None:
        """
        This gets triggered when the name change confirm button is pressed

        :return: None
        """
        changed_to = self.__text_map_control_changename.get()

        athlete_key = None
        valid_key = True

        # Also need to find the current filename.
        for key, value in self.__athlete_data.items():

            if value['display_name'] == self.__last_selected:
                athlete_key = key

            # If the name we want to change to is already taken then its invalid
            if value['display_name'] == changed_to:
                valid_key = False

        # Make sure an athlete is selected and the new name isn't blank
        valid_key = False if (changed_to == '') or (athlete_key is None) else valid_key

        if valid_key:
            self.__changename_callback(athlete_key, changed_to)  # execute callback
        else:
            msgbox.showerror("Invalid input",
                             "This was an invalid input,"
                             " must be unique and athlete must be selected")

        self.__text_map_control_changename.set('')  # clear the entry field

    def set_open_callback(self, func) -> None:  # Open file callbacks
        """
        Set the callback function to be used

        :param func: The function to be called when a file is opened in control window
        :return: None
        """
        self.__open_file_callback = func

    def set_changename_callback(self, func) -> None:
        """
        Set the callback function to be used

        :param func: The function to be called when a display name is changed
        :return: None
        """
        self.__changename_callback = func

    def set_delete_callback(self, func) -> None:
        """
        Set the callback function to be used

        :param func: The function to be called when an athlete is deleted
        :return: None
        """
        self.__delete_callback = func
