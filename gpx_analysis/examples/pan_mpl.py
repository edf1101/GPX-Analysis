"""
This script is the main entry point for the program
"""

import time

# Import our own modules
try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import sporting as sport
    from gpx_analysis import graph_handler as gh

except ImportError:
    import gpx_parser as gpx
    import sporting as sport
    import graph_handler as gh

track_1 = gpx.Track("../example_data/Race-take-1.gpx")
track_2 = gpx.Track("../example_data/Race-take-2.gpx")

mpl_graph = gh.MapClass()
mpl_graph.add_track(track_1)
mpl_graph.add_track(track_2)
mpl_graph.plot_images()

mpl_graph.draw_track(0, color='red')
mpl_graph.draw_track(1, color='green')

TIME_TO_INSPECT = 10
# Mark it on a map
pos_1 = sport.get_position_at_time(track_1, TIME_TO_INSPECT)
pos_2 = sport.get_position_at_time(track_2, TIME_TO_INSPECT)
mpl_graph.draw_point(0, pos_1, size=5, color='#AA0000')
mpl_graph.draw_point(1, pos_2, size=5, color='#00AA00')
mpl_graph.draw_point(1, sport.get_position_at_time(track_2, 20), size=5, color='#00AA00')

mpl_graph.reset_viewpoint()
mpl_graph.show_plot()

