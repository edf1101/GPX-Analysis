import gpx_parser as gpx
import geo_components as geo
import graph_handler as gh


track = gpx.Track("example_data/Exeter Head.gpx")

track = geo.standardise_gpx_distances(track)

bounds = geo.get_track_bounds(track)
images = gh.get_all_images_in_bounds(bounds)

mpl_graph = gh.MapClass()
mpl_graph.set_image_dict(images)
mpl_graph.set_gpx_bounds(bounds)
mpl_graph.plot_images()

for point in track.get_track_points():
    # print(point.get_position_standard())
    mpl_graph.draw_point(point.get_position_degrees())

mpl_graph.show_plot()
