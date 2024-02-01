import time

import numpy as np
import tkinter as tk
import random
import matplotlib

# matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

root = tk.Tk()

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

def plot(time_plot):

    pos_1 = sport.get_position_at_time(track_1, time_plot)
    pos_2 = sport.get_position_at_time(track_2, time_plot)
    mpl_graph.draw_point(0, pos_1, size=5, color='#AA0000')
    mpl_graph.draw_point(1, pos_2, size=5, color='#00AA00')
    mpl_graph.center_viewpoint([pos_1, pos_2])
    fig = mpl_graph.get_figure()


plot(TIME_TO_INSPECT)
mpl_graph.get_figure().set_dpi(100)

canvas = FigureCanvasTkAgg(mpl_graph.get_figure(), master=root)

plot_widget = canvas.get_tk_widget()
start_time = time.time()


def update():
    plot(10 + (time.time() - start_time) * 4)
    mpl_graph.get_figure().canvas.draw()
    root.after(100, update)


plot_widget.grid(row=0, column=0)
tk.Button(root, text="Update", command=update).grid(row=1, column=0)
root.after(50,update)
root.mainloop()
