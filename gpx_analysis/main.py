"""
This script is the main entry point for the program
"""

import gpx_parser as gpx
import graph_handler as gh


track_1 = gpx.Track("example_data/Exeter-take-1.gpx")
track_2 = gpx.Track("example_data/Exeter-take-2.gpx")

mpl_graph = gh.MapClass()
mpl_graph.add_track(track_1)
mpl_graph.add_track(track_2)
mpl_graph.plot_images()

for point in track_1.get_track_points():
    mpl_graph.draw_point(point.get_position_degrees(),color='blue')
for point in track_2.get_track_points():
    mpl_graph.draw_point(point.get_position_degrees(),color='red')

mpl_graph.show_plot()
