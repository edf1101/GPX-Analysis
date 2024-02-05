"""
This script contains the finishline sub frame class related to the tk GUI
The AppGUI class is the only one to use outside of this class
"""
# Pylint ignores
# pylint: disable=R0902
# pylint: disable=R0914
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox  # for popups


class FinishlineMenuFrame:
    """
    This widget contains and abstracts the features of the finishline menu
    """

    def __init__(self, parent_class):
        """
        Constructor for the FinishlineMenuFrame class

        :param parent_class: pass in the parent_class so we can access its window and
         other frames etc
        """
        self.__parent_class = parent_class

        # The data for the athlete currently selected by the athlete menu
        self.__currently_selected = None
        self.__total_time = 100

        # Set up the frame to contain the widgets
        self.__frm_map_finishline_menu = ttk.Frame(self.__parent_class.get_frm_map_menu(),
                                                   relief=tk.RIDGE, borderwidth=2)
        self.__frm_map_finishline_menu.grid(row=1, column=0, sticky='nsew')
        self.__frm_map_finishline_menu.grid_columnconfigure(0, weight=1)  # centers it
        # have a blank row on row 2 for aesthetics
        self.__frm_map_finishline_menu.rowconfigure(3, minsize=15)

        # Put buttons etc. in the Start finish line menu
        # Create the title for the frame
        # doesn't need to be instance var as not referenced elsewhere
        label_finishline_menu = ttk.Label(master=self.__frm_map_finishline_menu,
                                          text="Start/Finish Line Menu",
                                          font=('Minion Pro', 14, 'bold'))
        label_finishline_menu.grid(row=0, column=0, sticky='s')

        # Put a checkbox below to enable or disable it
        self.__checkbox_finishline_status = None
        self.__checkbox_value = None
        self.__create_checkbox()

        # Encapsulate start slider precise entry and label in a frame
        self.__frm_map_finishline_start = None
        self.__label_finishline_menu_start = None
        self.__slider_finishline_menu_start = None
        self.__text_finishline_start_precise = None  # holds the precise data for start line time

        # Encapsulate finish slider precise entry and label in a frame
        self.__frm_map_finishline_end = None
        self.__label_finishline_menu_end = None
        self.__slider_finishline_menu_end = None
        self.__text_finishline_end_precise = None
        self.__enable_widgets()

    def stop_editing(self) -> None:
        """
        Gets called when a different class wants to stop editing the finish/start lines
        ie when athlete focus is swapped or started playback

        :return: None
        """
        self.__checkbox_value.set(False)

    def __enable_widgets(self) -> None:
        """
        enables widgets for the GUI that are required for editing start/finish locations

        :return: None
        """
        self.__setup_start_frame()
        self.__setup_end_frame()

        if self.__currently_selected:
            self.__update_start_finish_times_text()

    def __create_checkbox(self) -> None:
        """
        Create the checkbox and containing frame which enable or disable the menu

        :return: None
        """
        root = self.__parent_class.get_tk_window()
        self.__checkbox_value = tk.BooleanVar(master=root)
        self.__checkbox_value.set(False)
        self.__checkbox_finishline_status = ttk.Checkbutton(master=self.__frm_map_finishline_menu,
                                                            text='Enable start/finish modifying?',
                                                            command=self.__on_checkbox_changed,
                                                            variable=self.__checkbox_value)
        self.__checkbox_finishline_status.grid(row=2, column=0, sticky='w')

    def set_currently_selected(self, athlete_data: dict) -> None:
        """
        setter for private variable self.__currently_selected

        :param athlete_data: The data to set to it
        :return: None
        """
        self.__currently_selected = athlete_data

        if athlete_data:  # if its a real athlete not None then modify the fields
            self.__total_time = athlete_data['track'].get_total_time()

    def __update_start_finish_times_text(self) -> None:
        """
        update the text for what the real start finish time is

        :return: None
        """

        if not self.__parent_class.ready:  # don't execute if not fully set up
            return

        athlete_key = self.__currently_selected['filename']
        start_time, finish_time = self.__parent_class.get_start_finish_time(athlete_key)

        # update the text labels
        self.__label_finishline_menu_start.configure(text=f"Start Line: {start_time}s"
                                                          f"  Total: {self.__total_time}s")

        self.__label_finishline_menu_end.configure(text=f"Finish Line: {finish_time}s"
                                                        f"  Total: {self.__total_time}s")

    def __setup_start_frame(self) -> None:
        """
        Set up the start frame widgets

        :return: None
        """
        if self.__parent_class.ready:
            personal_total = self.__currently_selected['track'].get_total_time()
        else:
            personal_total = 100

        # Encapsulate slider precise entry and label in a frame
        self.__frm_map_finishline_start = ttk.Frame(self.__frm_map_finishline_menu)
        self.__frm_map_finishline_start.grid(row=4, column=0, sticky='w')

        # Set up the start line info text
        self.__label_finishline_menu_start = ttk.Label(master=self.__frm_map_finishline_start,
                                                       text=f"Start Line: {0}s"
                                                            f"  Total: {personal_total}s")
        self.__label_finishline_menu_start.grid(row=0, column=0, columnspan=3)

        # Set up the slider
        self.__slider_finishline_menu_start = ttk.Scale(master=self.__frm_map_finishline_start,
                                                        orient=tk.HORIZONTAL,
                                                        from_=0, to=100,
                                                        command=self.__on_start_slider_changed)
        self.__slider_finishline_menu_start.grid(row=1, column=0)

        # entry box for precise entry
        root = self.__parent_class.get_tk_window()
        self.__text_finishline_start_precise = tk.StringVar(master=root)

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

        if self.__parent_class.ready:
            personal_total = self.__currently_selected['track'].get_total_time()
        else:
            personal_total = 100

        # Set up the bounding frame
        self.__frm_map_finishline_end = ttk.Frame(self.__frm_map_finishline_menu)
        self.__frm_map_finishline_end.grid(row=5, column=0, sticky='w')

        # set up the text saying where the finish line is
        self.__label_finishline_menu_end = ttk.Label(master=self.__frm_map_finishline_end,
                                                     text=f"Finish Line: {0}s "
                                                          f" Total: {personal_total}s")
        self.__label_finishline_menu_end.grid(row=0, column=0, columnspan=3)

        # set up the slider
        self.__slider_finishline_menu_end = ttk.Scale(master=self.__frm_map_finishline_end,
                                                      orient=tk.HORIZONTAL,
                                                      from_=0, to=100, value=100,
                                                      command=self.__on_end_slider_changed)
        self.__slider_finishline_menu_end.grid(row=1, column=0)

        # entry box for precise entry
        # the text data needs to be accessible outside but entry itself won't be modified again
        root = self.__parent_class.get_tk_window()
        self.__text_finishline_end_precise = tk.StringVar(master=root)
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
        if self.__checkbox_value.get() is False:
            return

        # print("precise start pressed")
        value = self.__text_finishline_start_precise.get()
        valid = validate_float_input(value)
        if valid:
            if valid:
                # print(f"precise end pressed value: {value}")
                athlete_key = self.__currently_selected['filename']
                self.__parent_class.set_start_finish_time(athlete_key,
                                                          round(float(value), 1), None)
                self.__update_start_finish_times_text()

    def __on_start_slider_changed(self, event) -> None:
        """
        This gets called when the start slider changed

        :param event: doesn't get used
        :return: None
        """

        if event == 1:  # test to keep pylint happy
            pass

        # Not allowed to change when not editing, ignore it
        if self.__checkbox_value.get() is False:
            return

        value = round(self.__slider_finishline_menu_start.get() * self.__total_time / 100.0, 1)
        # print(f'start slider changed to {value}')

        athlete_key = self.__currently_selected['filename']
        self.__parent_class.set_start_finish_time(athlete_key, value, None)
        self.__update_start_finish_times_text()

    def __on_precise_button_end_pressed(self) -> None:
        """
        This gets called when the end precise button gets pressed

        :return: None
        """
        if self.__checkbox_value.get() is False:
            return

        value = self.__text_finishline_end_precise.get()
        valid = validate_float_input(value)
        if valid:
            # print(f"precise end pressed value: {value}")
            athlete_key = self.__currently_selected['filename']
            self.__parent_class.set_start_finish_time(athlete_key,
                                                      None, round(float(value), 1))
            self.__update_start_finish_times_text()

    def __on_end_slider_changed(self, event) -> None:
        """
        This gets called when the end slider changed

        :param event: doesn't get used
        :return: None
        """
        if self.__checkbox_value.get() is False:
            return

        if event == 1:  # test to keep pylint happy
            pass

        value = round(self.__slider_finishline_menu_end.get() * self.__total_time / 100.0, 1)
        # print(f'end slider changed to {value}')

        athlete_key = self.__currently_selected['filename']
        self.__parent_class.set_start_finish_time(athlete_key, None, value)
        self.__update_start_finish_times_text()

    def __on_checkbox_changed(self) -> None:
        """
        Gets called when the checkbox changes state

        :return: None
        """
        # Get the state It's trying to switch to
        state = self.__checkbox_value.get()
        # print(f'changed state {state}')

        # Find out if it's allowed to switch
        # (ie if playing then cant switch on or if nothing selected it cant modify)
        if self.__currently_selected is None or self.__parent_class.get_playing():
            state = False
            self.__checkbox_value.set(False)
            return

        if state:
            self.__enable_widgets()


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
