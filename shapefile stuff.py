# https://docs.google.com/spreadsheets/d/1Xe2Xz0HhE7hPK0yxOGD-5hYinNR4DJV9vEFWWS9lBjY/edit#gid=1517145762
# https://docs.google.com/spreadsheets/d/10YEkF8PVy8N2wuSDzwj_rqdYisncUQsCtvnzjT5WeDQ/edit#gid=1490814289
# https://data.census.gov/table?g=050XX00US06037$1400000&tid=ACSST5Y2021.S1901

# Next things to do: add a select box to the graph where it highlights shapes
# Add a residual plot
# fix discontinuities in shapefiles

import tkinter as tk
import shapefile
from scipy.stats import linregress

s = shapefile.Reader("Census_Tracts_2020.shp")
data = open('results.txt')


def split_row_txt(row: str):
    res = [0]
    for j,char in enumerate(row):
        if char == ',' and row[j + 1] == ' ':
            res.append(j+2)
    res.append(len(row) + 1)
    return [row[res[n0]:res[n0+1] - 2] for n0 in range(len(res)-1)]


data_list = data.readlines()
shapes = s.shapes()

discontinuity = shapes[-2].points
start_cords = discontinuity[0]
results = []
for i,pair in enumerate(discontinuity[1:]):
    pass

shape_clipping_bounds: list[list[float]] = []  # order: [min long, max long, min lat, max lat]
for n in range(len(shapes)):
    shape_clipping_bounds.append([
        min([k[0] for k in shapes[n].points]),
        max([k[0] for k in shapes[n].points]),
        min([k[1] for k in shapes[n].points]),
        max([k[1] for k in shapes[n].points])]
    )

tract_ids,elevation,income = [],[],[]
for i in data_list[1:]:
    k = split_row_txt(i)
    tract_ids.append(k[0])
    elevation.append(k[1])
    income.append(k[2])
data.close()

max_long, min_long, max_lat, min_lat = -180, 181, 0, 91
for i in range(len(shapes)):
    for p in shapes[i].points:
        if p[0] > max_long:
            max_long = p[0]
        elif p[0] < min_long:
            min_long = p[0]
        elif p[1] > max_lat:
            max_lat = p[1]
        elif p[1] < min_lat:
            min_lat = p[1]
# max_lat,max_long,min_lat,min_long = max_lat * 1.001,max_long * 1.001,min_lat * 0.999,min_long * 1.001

window = tk.Tk()
canvas_width,canvas_height = 500,850
reg_line_on = False

scale_factor = min((canvas_height / (max_lat - min_lat)), (canvas_width / (max_long - min_long)))
min_long_scaled,min_lat_scaled = - min_long * scale_factor,-min_lat * scale_factor
tract_map = tk.Canvas(window, width=canvas_width, height=canvas_height)
graph_width,graph_height = 550,450
graph = tk.Canvas(window,width=graph_width,height=graph_height)
graph.pack(side='right')
tract_map.pack()


def draw_dashes(x: float,y: float,direction: str,length: float):
    if direction == 'horizontal':
        graph.create_line(x,y,x - length,y)
    elif direction == 'vertical':
        graph.create_line(x,y, x, y + length)


def draw_axis(max_x,max_y):
    graph.create_line(graph_width*0.05,graph_height*0.95,graph_width*0.95,graph_height*0.95,fill='#000000')
    graph.create_line(graph_width * 0.05, graph_height * 0.05, graph_width * 0.05, graph_height * 0.95,fill='#000000')
    graph.create_text(graph_width * 0.03, graph_height * 0.05,text=round(max_y), angle=90)
    graph.create_text(graph_width * 0.95, graph_height * 0.975, text=round(max_x))
    graph.create_text(graph_width * 0.055, graph_height * 0.965, text='0')
    graph.create_text(graph_width * 0.04, graph_height * 0.94, text='0',angle=90)
    draw_dashes(graph_width * 0.05, graph_height * 0.05,'horizontal',graph_width * 0.01)
    draw_dashes(graph_width * 0.95, graph_height * 0.95, 'vertical', graph_width * 0.01)


def plot_point(x0, y0, x_max, y_max,color):  # x and y are not 'flipped' or adjusted to the 0.05 -> 0.95 bounds on the actual graph compared to the canvas
    if x0 != -1 and y0 != -1:
        c = color
        if color == '#ffffff':
            c = '#222222'
        x = x0 / x_max * graph_width
        y = y0 / y_max * graph_height
        x = (x * 0.9) + (0.05 * graph_width)
        y = (y * 0.9) + (0.05 * graph_height)
        # y = graph_height - y
        # print(str(x0) + ' -> ' + str(x), str(y0) + ' -> ' + str(y))
        size = 1 if c == '#222222' else 2
        graph.create_oval(x - size,graph_height - (y - size),x + size,graph_height - (y + size),fill=c,outline=c)


def translate(x0,y0,x_max,y_max):
    x = ((x0 / x_max * graph_width) * 0.9) + (0.05 * graph_width)
    y = ((y0 / y_max * graph_height) * 0.9) + (0.05 * graph_height)
    return x,graph_height - y


def chart():
    global lbl_reg,reg_line_on
    graph.delete('all')
    cleaned_x,cleaned_y = [],[]
    for m,n in zip(elevation,income):
        cleaned_x.append(float(m))
        if n == '-':
            cleaned_y.append(-1)
        elif n == '250000+':
            cleaned_y.append(250001)
        else:
            cleaned_y.append(float(n))
    x_max,y_max = max(cleaned_x),max(cleaned_y)
    draw_axis(x_max, y_max)
    for a,b,c in zip(cleaned_x,cleaned_y,selected):
        plot_point(a,b,x_max,y_max,c)
    if len(x_selected) > 0 and len(y_selected) > 0:
        lin_regression_list = linregress(x_selected,y_selected)
        m,b = round(lin_regression_list[0],3),round(lin_regression_list[1],3)
        r = round(lin_regression_list[2],4)
        regression_var.set('Line of best fit equation: ' + str(m) + 'x + ' + str(b) + '\n  R^2 value: ' + str(r))
        if reg_line_on:
            graph.create_line(translate(0,b,x_max,y_max),translate(x_max,m*x_max + b,x_max,y_max))
            print(lin_regression_list)


def convert(cord: tuple):  # converts raw lat/long to points on the tkinter canvas, using min/max lat/long
    return cord[0] * scale_factor + min_long_scaled, canvas_height - (cord[1] * scale_factor + min_lat_scaled)


def revert(cord: tuple):  # converts canvas cords into lat/long
    return cord[0] / scale_factor + min_long, (canvas_height - cord[1]) / scale_factor + min_lat


def scale(canvas_cords: tuple,offsets,z):
    return z * canvas_cords[0] + offsets[0],z * canvas_cords[1] + offsets[1]


def descale(scaled_cords: tuple,offsets,z):
    return (scaled_cords[0] - offsets[0]) / z,(scaled_cords[1] - offsets[1]) / z


selected = ["#ffffff" for _ in shapes]
outlines = ["#000000" for _ in shapes]
x_selected,y_selected = [],[]
current_zoom_boundaries = [0,0,0,0]


def draw_zoomed_view(max_x,min_x,max_y,min_y):
    global current_zoom_boundaries
    current_zoom_boundaries = [min_x,max_x,min_y,max_y]
    z = min(canvas_height / (max_y - min_y), canvas_width / (max_x - min_x))
    scale_offsets = -z * min_x,-z * min_y
    tract_map.delete('all')
    for n in range(len(shapes)):
        tract_map.create_polygon([scale(convert(j),scale_offsets,z) for j in shapes[n].points],
                                             fill=selected[n],outline=outlines[n])


def zoom_out_stuff(a):
    global zoomed
    if zoomed:
        zoomed = not zoomed
        draw_zoomed_view(canvas_width, 0, canvas_height, 0)


def draw_same_scale_clear(a):
    global selected,outlines,x_selected, y_selected
    selected,outlines = ["#ffffff" for _ in shapes],["#000000" for _ in shapes]
    x_selected, y_selected = [],[]
    draw_zoomed_view(current_zoom_boundaries[1],current_zoom_boundaries[0],current_zoom_boundaries[3],current_zoom_boundaries[2])
    regression_var.set('Select an area')
    chart()


start_drag = (0, 0)
start_drag_left = (0,0)
mouse_pos = (0, 0)
drag_box = tract_map.create_rectangle(0, 0, 0, 0)
select_box = tract_map.create_rectangle(0, 0, 0, 0)
regression_line = 0


def mouse_position_update(e):
    global mouse_pos
    mouse_pos = (e.x, e.y)


def mouse_click(a):
    global start_drag
    start_drag = mouse_pos


def mouse_left_click(a):
    global start_drag_left
    start_drag_left = mouse_pos


def mouse_release(a):
    global drag_box
    global zoomed
    tract_map.delete(drag_box)
    if not zoomed and start_drag != mouse_pos:
        draw_zoomed_view(max(start_drag[0],mouse_pos[0]),min(start_drag[0],mouse_pos[0]),
                         max(start_drag[1],mouse_pos[1]),min(start_drag[1],mouse_pos[1]))
        zoomed = not zoomed


def select_shapes(p1: tuple,p2: tuple):
    global selected,outlines
    # selected = ["#ffffff" for _ in shapes]  # OPTIONAL <<<
    # outlines = ["#000000" for _ in shapes]  # OPTIONAL <<<
    min_x,max_x,min_y,max_y = min(p1[0],p2[0]),max(p1[0],p2[0]),min(p1[1],p2[1]),max(p1[1],p2[1])
    for n in range(min(len(income),len(elevation))):
        if shape_clipping_bounds[n][0] > max_x or shape_clipping_bounds[n][1] < min_x or \
           shape_clipping_bounds[n][2] > max_y or shape_clipping_bounds[n][3] < min_y:
            pass  # don't color the shape
        else:
            for t in shapes[n].points:
                if min_x < t[0] < max_x and min_y < t[1] < max_y:
                    selected[n] = '#ff0000'
                    if income[n].isnumeric():
                        test_x,test_y = float(elevation[n]),float(income[n])
                        if test_x not in x_selected or test_y not in y_selected:  # this could definitely break something
                            x_selected.append(test_x)
                            y_selected.append(test_y)
                    elif income[n] == '250000+':
                        test_x, test_y = float(elevation[n]), 250001
                        if test_x not in x_selected or test_y not in y_selected:
                            x_selected.append(test_x)
                            y_selected.append(test_y)
                    else:
                        pass
                    break


def mouse_left_release(a):
    global drag_box
    tract_map.delete(select_box)
    z0 = min(canvas_height / (current_zoom_boundaries[3] - current_zoom_boundaries[2]), canvas_width / (current_zoom_boundaries[1] - current_zoom_boundaries[0]))
    offsets = -z0 * current_zoom_boundaries[0],-z0 * current_zoom_boundaries[2]
    select_shapes(revert(descale(start_drag_left,offsets,z0)),revert(descale(mouse_pos,offsets,z0)))
    draw_zoomed_view(current_zoom_boundaries[1],current_zoom_boundaries[0],current_zoom_boundaries[3],current_zoom_boundaries[2])
    chart()


def dragging(e):
    global drag_box
    global mouse_pos
    mouse_pos = (e.x, e.y)
    tract_map.delete(drag_box)
    drag_box = tract_map.create_rectangle(start_drag[0], start_drag[1], e.x, e.y,outline='#000000')


def left_dragging(e):
    global select_box
    global mouse_pos
    mouse_pos = (e.x, e.y)
    tract_map.delete(select_box)
    select_box = tract_map.create_rectangle(start_drag_left[0], start_drag_left[1], e.x, e.y, outline='#ff0000')


def show_income(a):
    global selected
    global outlines
    mx = 250001  # kinda cheating
    for i,item in enumerate(income):
        if item.isnumeric():
            selected[i] = "#%02x%02x%02x" % (255 - int(float(item) / mx * 255), 40, int(float(item) / mx * 255))
            outlines[i] = "#%02x%02x%02x" % (255 - int(float(item) / mx * 255), 40, int(float(item) / mx * 255))
        elif item == '250000+':
            selected[i] = "#%02x%02x%02x" % (255 - int(250001 / mx * 255), 40, int(250001 / mx * 255))
            outlines[i] = "#%02x%02x%02x" % (255 - int(250001 / mx * 255), 40, int(250001 / mx * 255))
        else:
            selected[i] = '#dddddd'
            outlines[i] = '#dddddd'
    draw_zoomed_view(current_zoom_boundaries[1],current_zoom_boundaries[0],current_zoom_boundaries[3],current_zoom_boundaries[2])
    chart()


def show_elevation(a):
    global selected
    global outlines
    mx = max([float(n) for n in elevation])
    for i,item in enumerate(elevation):
        selected[i] = "#%02x%02x%02x" % (255 - int(float(item) / mx * 255), 0, int(float(item) / mx * 255))
        outlines[i] = "#%02x%02x%02x" % (255 - int(float(item) / mx * 255), 0, int(float(item) / mx * 255))
    draw_zoomed_view(current_zoom_boundaries[1],current_zoom_boundaries[0],current_zoom_boundaries[3],current_zoom_boundaries[2])
    chart()


def flip_reg_line(a):
    global reg_line_on
    reg_line_on = not reg_line_on
    chart()


window.bind('<Motion>', mouse_position_update)

window.bind('<Button-1>', mouse_click)
window.bind('<Button-2>', mouse_left_click)

window.bind('<B1-Motion>', dragging)
window.bind('<B2-Motion>',left_dragging)

window.bind('<ButtonRelease-1>', mouse_release)
window.bind('<ButtonRelease-2>', mouse_left_release)

window.bind('i',show_income)
window.bind('e',show_elevation)
window.bind('z',zoom_out_stuff)
window.bind('c',draw_same_scale_clear)
window.bind('r',flip_reg_line)


regression_var = tk.StringVar()
regression_var.set('Select an area')

instructions = tk.Label(window, text='z: zoom out c: clear selection \ni: income e: elevation \n').pack(side='right')
lbl_reg = tk.Label(window, textvariable=regression_var).pack(side='top')

zoomed = False
draw_zoomed_view(canvas_width,0,canvas_height,0)
chart()
window.mainloop()
