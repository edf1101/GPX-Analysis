"""
This script is the main entry point for the program
"""

import gpx_parser as gpx
import graph_handler as gh
import sporting as sport


track_1 = gpx.Track("example_data/Exeter-take-1.gpx")
track_2 = gpx.Track("example_data/Exeter-take-2.gpx")

mpl_graph = gh.MapClass()
mpl_graph.add_track(track_1)
mpl_graph.plot_images()

mpl_graph.draw_track(0, color='red')


mpl_graph.draw_point(sport.get_position_at_time(track_1, 30))
mpl_graph.show_plot()
