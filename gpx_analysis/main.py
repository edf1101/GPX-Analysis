import gpx_parser as gpx
import geo_components as geo
import matplotlib.pyplot as plt

track = gpx.Track("example_data/Exeter Head.gpx")

track_after = geo.standardise_gpx_distances(track)


for point in track_after.get_track_points():
    print(point.get_position())
