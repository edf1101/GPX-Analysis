"""
This module handles the small stats line graph at the bottom of the screen
"""

# import external modules
from sys import platform as sys_pf
import matplotlib
import matplotlib.pyplot as plt

# import our own
try:
    from gpx_analysis import sporting as sport
    from gpx_analysis.components import lighten_color
except ImportError:
    import sporting as sport
    from components import lighten_color

# If on macos then run this to fix the mpl issues
if sys_pf == 'darwin':
    matplotlib.use("TkAgg")


class StatsGraph:
    """
    This class holds the stats graph and functions relating to it
    """

    def __init__(self) -> None:
        """
        The constructor for the StatsGraph class
        """
        # Create the fig and axis for this class
        self.__fig, self.__ax = plt.subplots()
        self.__fig.set_size_inches(6, 2.5)
        self.__ax_2 = self.__ax.twinx()
        self.__secondary_visibility(False)

        self.__time_intervals = 5  # interval between points on the graph

        self.__athletes = {}  # initiate the dictionary of athletes

        self.__max_time = 1.0  # the max time of all the athletes
        self.__ax.set_xlabel("Time")
        self.__fig.subplots_adjust(bottom=0.2)

        self.__time_line = None  # Line on the graph to mark where the time is

    def draw_time_line(self, time: float) -> None:
        """
        Draw a line on the graph to mark what time it is in the simulation

        :param time: the current time
        :return: None
        """
        # remove a previous time line if there is one
        if self.__time_line:
            self.__time_line.remove()

        graph_height_range = self.__ax.get_ylim()
        height = graph_height_range[1] - graph_height_range[0]
        offset = height * 0.1

        self.__time_line = self.__ax.plot([time, time],
                                          [graph_height_range[0] + offset,
                                           graph_height_range[1] - offset],
                                          color=(0.3, 0.3, 0.3, 0.4),
                                          linewidth=2,
                                          linestyle='dashed')[0]

    def draw_base_graph(self, mode: str | None = None) -> None:
        """
        Draw a graph according to its mode

        :param mode:  clears the graph if none, otherwise draw according to the mode
        :return: None
        """
        mode, unit = mode.split('|')
        # print(f'new {unit}')

        self.__ax_2.cla()
        self.__ax.cla()

        # reset the time axis
        self.__max_time = self.__get_max_time()  # Update the max time
        self.__ax.set_xlabel("Time")
        self.__ax.set_xlim([0, self.__max_time])
        self.__fig.subplots_adjust(bottom=0.2)

        if mode == 'Distance':
            self.__ax.set_ylabel("meters")
            self.__secondary_visibility(False)

            self.__plot_graph(self.__ax, sport.get_cumulative_dist_at_time, None)

        elif mode == 'Gap':
            self.__ax.set_ylabel("meters")
            self.__secondary_visibility(False)

            self.__plot_gap()

        elif mode == 'Speed & Rate':
            self.__ax.set_ylabel(unit)
            self.__ax_2.set_ylabel("s/m")
            self.__ax_2.yaxis.set_label_position("right")
            self.__ax_2.yaxis.tick_right()
            self.__secondary_visibility(True)

            self.__plot_graph(self.__ax, sport.get_speed_at_time, unit)
            self.__plot_graph(self.__ax_2, sport.get_cadence_at_time, None)

        elif mode == 'Speed':
            self.__ax.set_ylabel(unit)
            self.__secondary_visibility(False)

            # plot a graph of the speeds
            self.__plot_graph(self.__ax, sport.get_speed_at_time, unit)

        elif mode == 'Rate':
            self.__ax.set_ylabel("s/m")
            self.__secondary_visibility(False)

            self.__plot_graph(self.__ax, sport.get_cadence_at_time, None)

    def __plot_graph(self, axis, func, units) -> None:
        """
        Plots a graph of the stats

        :param axis: The axis to plot onto
        :param func: The function to use for y values
        :param units: None if not plotting speed, else the units to convert
        :return: None
        """
        max_time = int(self.__max_time)
        time_intervals = int(self.__time_intervals)

        # plot a graph of the rates
        for athlete in self.__athletes.values():
            track = athlete['track']
            colour = athlete['colour']
            colour = lighten_color(colour, 0.6) if axis == self.__ax_2 else colour

            for time in range(0, max_time - time_intervals, time_intervals):
                start_point = time
                end_point = time + time_intervals

                # make these for averages
                smth_start = func(track, start_point + athlete['start_time'] - time_intervals)

                start_y = func(track, start_point + athlete['start_time'])
                end_y = func(track, end_point + athlete['start_time'])

                if start_y < 0.5 or end_y < 0.5 or smth_start < 0.5:
                    continue

                end_y = (end_y + start_y) / 2
                start_y = (start_y + smth_start) / 2

                if start_y < 0.5 or end_y < 0.5:
                    continue

                if units:
                    start_y = sport.convert_speed_units(start_y, units)
                    end_y = sport.convert_speed_units(end_y, units)

                axis.plot([start_point, end_point],
                          [start_y, end_y],
                          color=colour, linewidth=2,
                          linestyle='dotted' if axis == self.__ax_2 else 'solid')

    def __plot_gap(self) -> None:
        """
        It woudld be very inefficient to plot the gap using the same method
         as previously so we'll do it here

        :return: None
        """
        max_time = int(self.__max_time)
        time_intervals = int(self.__time_intervals)
        # self.__ax.plot([0,10,20],[20,30,10])
        athlete_points = {key: [] for key in self.__athletes.keys()}

        for time in range(0, max_time - time_intervals, time_intervals):

            cdf = sport.get_cumulative_dist_at_time  # abbreviation for get_cumulative_dist func

            # Get the furthest distance anyone has got at this time
            max_dist = max(cdf(data['track'], time + data['start_time']) -
                           cdf(data['track'], data['start_time'])  # Makes sure it starts at 0
                           for data in self.__athletes.values())

            # append each athletes dist to an list this will be the y values
            for key, data in self.__athletes.items():
                start_dist = cdf(data['track'],data['start_time'])
                current_dist = cdf(data['track'], time + data['start_time']) - start_dist
                athlete_points[key].append(max_dist - current_dist)

        # Plot the line for each athlete
        for key, athlete_data in self.__athletes.items():
            self.__ax.plot(range(0, max_time - time_intervals, time_intervals),
                           athlete_points[key],
                           color=athlete_data['colour'], linewidth=2,
                           linestyle='solid')

    def __secondary_visibility(self, state: bool) -> None:
        """
        Removes the axis from a graph

        :param state: whether we want it hidden or not
        :return: None
        """
        self.__ax_2.get_xaxis().set_visible(state)
        self.__ax_2.get_yaxis().set_visible(state)

    def set_athletes(self, athletes: dict) -> None:
        """
        Setter for the list of athletes then update the graph

        :param athletes: the new dictionary
        :return: None
        """
        self.__athletes = athletes  # set the new dictionary

        self.__max_time = self.__get_max_time()  # Update the max time
        self.__ax.set_xlim([0, self.__max_time])
        self.__ax.set_xlabel("Time")
        self.__fig.subplots_adjust(bottom=0.2)

    def get_fig(self) -> plt.Figure:
        """
        getter for the figure of the graph

        :return: The figure of the graph
        """
        # self.__fig.tight_layout()
        # self.__fig.set_size_inches(6, 2.5)
        # self.__fig.set_dpi(200)

        return self.__fig

    def __get_max_time(self) -> float:
        """
        Get the maximum race time for all the athletes

        :return: the maximum race time in the simulation
        """
        max_time = 1.0
        for athlete in self.__athletes.values():
            max_time = max(max_time, athlete['finish_time'] - athlete['start_time'])

        return max_time
