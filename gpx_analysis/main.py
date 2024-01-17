"""
This script is the main entry point for the program
"""

import gpx_parser as gpx
import graph_handler as gh
import sporting as sport


track_1 = gpx.Track("example_data/Race-take-1.gpx")
track_2 = gpx.Track("example_data/Race-take-2.gpx")

mpl_graph = gh.MapClass()
mpl_graph.add_track(track_1)
mpl_graph.plot_images()

mpl_graph.draw_track(0, color='red')

time_to_inspect = 200
# Mark it on a map
mpl_graph.draw_point(sport.get_position_at_time(track_1, time_to_inspect))

# print some stats about that time
raw_speed = sport.get_speed_at_time(track_1, time_to_inspect)
print(sport.convert_speed_units(raw_speed, 's/500m'))
print(sport.get_cadence_at_time(track_1, time_to_inspect))
print(sport.get_cumulative_dist_at_time(track_1, time_to_inspect),' out of ',
      sport.get_total_distance(track_1))

# Draw the mpl graph
mpl_graph.show_plot()
