from flask import Flask, render_template
import mpld3
import gpx_parser as gpx
import graph_handler as gh

app = Flask(__name__)


@app.route('/')
def index():

    graph_data = mpld3.fig_to_dict(mpl_graph.get_figure())
    return render_template('index.html', title='Daily update', mpl_data = graph_data)


if __name__ == '__main__':
    track_1 = gpx.Track("example_data/Race-take-1.gpx")
    mpl_graph = gh.MapClass()
    mpl_graph.add_track(track_1)
    mpl_graph.plot_images()
    mpl_graph.draw_track(0, color='red')
    mpl_graph.get_figure().set_size_inches(2.5,2.5)
    app.run()
