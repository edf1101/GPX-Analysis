import tkinter as tk
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

try:
    from gpx_analysis import gpx_parser as gpx
    from gpx_analysis import sporting as sport
    from gpx_analysis import graph_handler as gh

except ImportError:
    import gpx_parser as gpx
    import sporting as sport
    import graph_handler as gh

# matplotlib.use("Qt5Agg")
# generate map plot
track_1 = gpx.Track("../example_data/Race-take-1.gpx")

mpl_graph = gh.MapClass()
mpl_graph.add_track(track_1)
mpl_graph.plot_images()

mpl_graph.draw_track(0, color='red')
mpl_graph.get_figure().set_dpi(100)
pos_1 = sport.get_position_at_time(track_1, 100)
mpl_graph.center_viewpoint([pos_1])

window = tk.Tk()
window.title("GPX Analysis")

# Configure the layout of the basic 2x2 grid
window.rowconfigure(0, minsize=500, weight=3)
window.rowconfigure(1, minsize=300, weight=1)
window.columnconfigure(1, minsize=500, weight=8)
window.columnconfigure(0, minsize=260, weight=1)

# The map widget goes into the root grid at row 0 col 1 (TOP RIGHT)
canvas = FigureCanvasTkAgg(mpl_graph.get_figure(), master=window)
map_widget = canvas.get_tk_widget()
map_widget.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

#  Set up the two menus (map menu on top, stats menu on bottom)
frm_map_menu = ttk.Frame(window, relief=tk.RAISED, borderwidth=5)
frm_map_menu.grid(row=0, column=0, sticky='nsew')

# Configure the arrangement of the map menu frame so the child frames
# span its height equally
frm_map_menu.grid_rowconfigure(0, weight=1)
frm_map_menu.grid_rowconfigure(1, weight=1)
frm_map_menu.grid_rowconfigure(2, weight=1)
frm_map_menu.grid_columnconfigure(0, weight=1)

frm_stats_menu = ttk.Frame(window, relief=tk.RAISED, borderwidth=5)
frm_stats_menu.grid(row=1, column=0, sticky='nsew')

# Create the frames to contain the menus inside the map menu frame
# First the open / master menu (open file, name boats etc)
frm_map_control_menu = ttk.Frame(frm_map_menu, relief=tk.RIDGE, borderwidth=2)
frm_map_control_menu.grid(row=0, column=0, sticky='nsew')
# Next the start/finish line menu
frm_map_finishline_menu = ttk.Frame(frm_map_menu, relief=tk.RIDGE, borderwidth=2)
frm_map_finishline_menu.grid(row=1, column=0, sticky='nsew')
# Next the playback meny
frm_map_playback_menu = ttk.Frame(frm_map_menu, relief=tk.RIDGE, borderwidth=2)
frm_map_playback_menu.grid(row=2, column=0, sticky='nsew')

# Create the control menu items

frm_map_control_menu.grid_columnconfigure(0, weight=1)
label_control_menu = ttk.Label(master=frm_map_control_menu,
                               text="Control Menu",
                               font=('Minion Pro', 14, 'bold'))
label_control_menu.grid(row=0, column=0, sticky='s')

btn_control_open = ttk.Button(frm_map_control_menu, text="Open File")
btn_control_open.grid(row=1, column=0, sticky="nsew")

# Select/ Remove althlets label
label_control_menu_select = ttk.Label(master=frm_map_control_menu, text="Select & Remove Athletes:")
label_control_menu_select.grid(row=2, column=0, sticky='w', )

# Encapsulate dropdown and delete in a frame
frm_map_control_dropdown = ttk.Frame(frm_map_control_menu, relief=tk.FLAT, borderwidth=0)
frm_map_control_dropdown.grid(row=3, column=0, sticky='nsew')
# Create the dropdown menu
athlete_options = ['boatA', 'boatB', 'boatC']
value_control_selected_option = tk.StringVar()
value_control_selected_option.set(athlete_options[0])
dropdown = ttk.OptionMenu(frm_map_control_dropdown, value_control_selected_option, *athlete_options)
dropdown.grid(row=0, column=0, sticky='nsew')
# Create a bin button
btn_control_del = ttk.Button(frm_map_control_dropdown, text='\U0001F5D1')
btn_control_del.grid(row=0, column=1, sticky='swen')

# Have an empty row here
frm_map_control_menu.rowconfigure(4, minsize=30)

# Athlete filename and display name labels
label_control_menu_file = ttk.Label(master=frm_map_control_menu, text="Filename: test_a.gpx")
label_control_menu_file.grid(row=5, column=0, sticky='s')
label_control_menu_display = ttk.Label(master=frm_map_control_menu, text="Display Name: Boat 1")
label_control_menu_display.grid(row=6, column=0, sticky='s')

label_control_menu_changename = ttk.Label(master=frm_map_control_menu, text="Change name:")
label_control_menu_changename.grid(row=7, column=0, sticky='w', )

# Encapsulate change name entry field and button in a frame
frm_map_control_changename = ttk.Frame(frm_map_control_menu, relief=tk.FLAT, borderwidth=0)
frm_map_control_changename.grid(row=8, column=0, sticky='nsew')

text_map_control_changename = tk.StringVar()
entry_map_control_changename = ttk.Entry(frm_map_control_changename, textvariable=text_map_control_changename)
entry_map_control_changename.grid(row=0, column=1, sticky='nswe')


# Function for removing focus from widgets once they have been clicked off
def remove_entry_focus(event):
    if not isinstance(event.widget, ttk.Entry):
        window.focus()


window.bind_all("<Button-1>", remove_entry_focus)
# Create a confirm button
btn_control_changename = ttk.Button(frm_map_control_changename, text='\U00002713')
btn_control_changename.grid(row=0, column=2, sticky='')

# Put buttons etc in the Start finish line menu
frm_map_finishline_menu.grid_columnconfigure(0, weight=1)
label_finishline_menu = ttk.Label(master=frm_map_finishline_menu,
                                  text="Start/Finish Line Menu",
                                  font=('Minion Pro', 14, 'bold'))
label_finishline_menu.grid(row=0, column=0, sticky='s')

# Display the status of the menu (cant do as running, or who editing) on a label
label_finishline_menu_status = ttk.Label(master=frm_map_finishline_menu, text="Currently editing: Boat 1")
label_finishline_menu_status.grid(row=1, column=0, sticky='nswe')

# Encapsulate slider precise entry and label in a frame
frm_map_finishline_start = ttk.Frame(frm_map_finishline_menu)
frm_map_finishline_start.grid(row=3, column=0, sticky='w')

# have a blank row
frm_map_finishline_menu.rowconfigure(2, minsize=15)

label_finishline_menu_start = ttk.Label(master=frm_map_finishline_start, text=f"Start Line: {15.5}s  Total: {1050}s")
label_finishline_menu_start.grid(row=0, column=0, columnspan=3)
slider_finishline_menu_start = ttk.Scale(master=frm_map_finishline_start,
                                         orient=tk.HORIZONTAL,
                                         from_=0, to=100)
slider_finishline_menu_start.grid(row=1, column=0)

# entry box for precise entry
text_finishline_start_precise = tk.StringVar()
entry_finishline_start_precise = ttk.Entry(frm_map_finishline_start, textvariable=text_finishline_start_precise,
                                           width=5)
entry_finishline_start_precise.grid(row=1, column=1)
# button for entry box
btn_finishline_start = ttk.Button(frm_map_finishline_start, text='SET')
btn_finishline_start.grid(row=1, column=2, sticky='nsew')

# Encapsulate slider precise entry and label in a frame for finish now
frm_map_finishline_end = ttk.Frame(frm_map_finishline_menu)
frm_map_finishline_end.grid(row=4, column=0, sticky='w')
label_finishline_menu_end = ttk.Label(master=frm_map_finishline_end, text=f"Finish Line: {1002.5}s  Total: {1050}s")
label_finishline_menu_end.grid(row=0, column=0, columnspan=3)
slider_finishline_menu_end = ttk.Scale(master=frm_map_finishline_end,
                                       orient=tk.HORIZONTAL,
                                       from_=0, to=100)
slider_finishline_menu_end.set(100)
slider_finishline_menu_end.grid(row=1, column=0)

# entry box for precise entry
text_finishline_end_precise = tk.StringVar()
entry_finishline_end_precise = ttk.Entry(frm_map_finishline_end, textvariable=text_finishline_start_precise, width=5)
entry_finishline_end_precise.grid(row=1, column=1)
# button for entry box
btn_finishline_end = ttk.Button(frm_map_finishline_end, text='SET')
btn_finishline_end.grid(row=1, column=2, sticky='nsew')

# Put buttons etc in the playback menu
frm_map_playback_menu.grid_columnconfigure(0, weight=1)
# Title
label_playback_menu = ttk.Label(master=frm_map_playback_menu,
                                text="Playback Menu",
                                font=('Minion Pro', 14, 'bold'))
label_playback_menu.grid(row=0, column=0, sticky='n')
# playback time label and slider
label_playback_time = ttk.Label(master=frm_map_playback_menu,
                                text=f"Playback Time: {600.1}s")
label_playback_time.grid(row=1, column=0, sticky='n')
slider_playback_time = ttk.Scale(master=frm_map_playback_menu, from_=0, to=100, length=250)
slider_playback_time.grid(row=2, column=0)
# playback speed label and slider
label_playback_speed = ttk.Label(master=frm_map_playback_menu,
                                 text=f"Playback Speed: {1.0}x")
label_playback_speed.grid(row=3, column=0, sticky='n')
slider_playback_speed = ttk.Scale(master=frm_map_playback_menu, from_=-2, to=2, length=100)
slider_playback_speed.grid(row=4, column=0)

style_playback_button = ttk.Style()
style_playback_button.configure('playback.TButton', font=('Helvetica', 40))
but_playback_menu = ttk.Button(master=frm_map_playback_menu, text='\u23F8', style='playback.TButton', width=1)
but_playback_menu.grid(row=5, column=0)



window.mainloop()
