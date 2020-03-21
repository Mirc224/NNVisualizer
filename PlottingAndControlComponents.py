import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import backend_bases
import mpl_toolkits.mplot3d as plt3d
from mpl_toolkits.mplot3d import proj3d
import matplotlib.animation as animation
from GraphicalComponents import *
import numpy as np

BASIC_POINT_COLOUR = '#04B2D9'

class PlotingFrame:
    def __init__(self, parent, graph_frame, *args, **kwargs):
        '''
        Popis
        --------
        Obsahuje v sebe graf z knižnice matplotlib. Zobrazuje ako vyzerjú transformované body v danej vrstve. Zobrazuje
        aj mriežku.

        Atribúty
        --------
        :var self.__cords = obsahuje odkaz na súradnice bofob, ktoré budú zobrazované
        :var self.__number_of_dim: udáva počet vykresľovaných dimenzií
        :var self.__graph_title: názov, ktorý sa bude zobrazovať vo vykresľovanom grafe
        :var self.__graph_labels: názvy jednotlivých osí
        :var self.__main_graph_frame: odkaz na graph frame, bude použitý na zobrazovanie informácií o rozkliknutom bode
        :var self.__figure: matplotlib figúra
        :var self.__canvas: ide o plátno, na to aby bolo možné použiť matplolib grafy v rámci tkinter
        :var self.__axis: matplotlib osi, získane z figúry
        :var self.__draw_2D: vyjadruje, či sa má graf vykresliť ako 2D
        :var self.__toolbar: matplotlib toolbar na posúvanie približovanie a podobne. Zobrazovaný len pri 2D. Pri 3D
                             je pohľad ovládaný myšou
        :var self.__changed: pre efektívnejší update
        :var self.__ani: animácia pre prekresľovanie grafu pri zmenách. Najjedoduchší spôsob pre interaktívne a
                         dynamické grafy
        '''
        self.__plot_wrapper_frame = tk.Frame(parent, *args, **kwargs)
        self.__plot_wrapper_frame.pack()
        self.__cords = [[], [], []]
        self.__line_cords_tuples = None

        self.__draw_polygon = False

        self.__number_of_dim = -1
        self.__graph_title = 'Graf'
        self.__graph_labels = ['Label X', 'Label Y', 'Label Z']
        self.__parent_controller = graph_frame

        self.__points_config = None
        self.__points_colour = None
        self.__used_colour = None
        self.__points_label = None
        self.__active_points_label = None
        self.__different_points_colour = None

        self.__graph_container = tk.LabelFrame(self.__plot_wrapper_frame, relief=tk.FLAT)

        self.__figure = Figure(figsize=(4, 4), dpi=100)
        self.__canvas = FigureCanvasTkAgg(self.__figure, self.__graph_container)
        self.__canvas.draw()
        self.__canvas.mpl_connect('button_press_event', self.on_mouse_double_click)
        self.__axis = None
        self.__draw_3D = False

        backend_bases.NavigationToolbar2.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to  previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        )

        self.__toolbar = NavigationToolbar2Tk(self.__canvas, self.__graph_container)
        self.__toolbar.update()
        self.__canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.__changed = False
        self.__change_in_progress = False
        self.__locked_view = True
        self.__ani = animation.FuncAnimation(self.__figure, self.update_changed, interval=105)

    def initialize(self, displayed_cords, points_config: dict, layer_name: str):
        self.__change_in_progress = False
        if len(displayed_cords) != 0:
            self.__cords = displayed_cords
        self.__graph_container.pack(side=tk.TOP)
        self.__graph_title = layer_name
        self.__points_config = points_config
        self.__used_colour = self.__points_config['default_colour']
        self.__points_colour = []
        self.__different_points_colour = self.__points_config['different_points_color']
        self.__points_label = self.__points_config['label']
        self.__active_points_label = self.__points_config['active_labels']
        self.set_graph_dimension(len(displayed_cords))

    def set_point_color(self):
        self.__points_colour = self.__used_colour.copy()
        for point, colour in self.__different_points_colour:
            self.__points_colour[point] = colour

    def on_mouse_double_click(self, event):
        if event.dblclick and event.button == 1:
            self.__different_points_colour.clear()
            self.__active_points_label.clear()

            nearest_x = 3
            nearest_y = 3
            closest_point = -1
            number_of_points = len(self.__cords[0])
            X_point_cords = self.__cords[0]
            if len(self.__cords) > 1:
                Y_point_cords = self.__cords[1]
            else:
                Y_point_cords = np.zeros_like(self.__cords[0])

            if self.__draw_3D:
                if len(self.__cords) == 3:
                    Z_point_cords = self.__cords[2]
                else:
                    Z_point_cords = np.zeros_like(self.__cords[0])
            # Rychlejsie pocita ale prehadzuje riadky, neviem to vyriesit
            for point in range(number_of_points):
                if self.__draw_3D:
                    x_2d, y_2d, _ = proj3d.proj_transform(X_point_cords[point], Y_point_cords[point],
                                                          Z_point_cords[point], self.__axis.get_proj())
                    pts_display = self.__axis.transData.transform((x_2d, y_2d))
                else:
                    pts_display = self.__axis.transData.transform((X_point_cords[point], Y_point_cords[point]))

                if math.fabs(event.x - pts_display[0]) < 3 and math.fabs(event.y - pts_display[1]) < 3:
                    if nearest_x > math.fabs(event.x - pts_display[0]) and nearest_y > math.fabs(
                            event.y - pts_display[1]):
                        nearest_x = math.fabs(event.x - pts_display[0])
                        nearest_y = math.fabs(event.y - pts_display[1])
                        closest_point = point

            if closest_point != -1:
                self.__different_points_colour.append((closest_point, '#F25D27'))
                if len(self.__points_label) > 0:
                    self.__active_points_label.append((closest_point, self.__points_label[closest_point]))
            self.__parent_controller.require_graphs_redraw()

    def change_graph_dimension(self):
        if self.__draw_3D:
            self.set_graph_dimension(2)
        else:
            self.set_graph_dimension(3)

    def update_changed(self, i):
        if self.__changed:
            self.__changed = False
            self.__change_in_progress = True
            self.redraw_graph()
            self.__change_in_progress = False
        else:
            self.__ani.event_source.stop()

    def update_graph(self):
        self.__changed = True
        if not self.__change_in_progress:
            if self.__ani is not None:
                self.__ani.event_source.start()

    def redraw_graph(self):
        if self.__locked_view:
            tmpX = self.__axis.get_xlim()
            tmpY = self.__axis.get_ylim()
            if self.__number_of_dim == 3:
                tmpZ = self.__axis.get_zlim()
        self.__axis.clear()
        self.__axis.grid()

        number_of_cords = len(self.__cords)

        if self.__draw_polygon:
            if self.__number_of_dim == 3:
                for edge in self.__line_cords_tuples:
                    xs = edge[0][0], edge[1][0]
                    ys = edge[0][1], edge[1][1]
                    zs = edge[0][2], edge[1][2]
                    line = plt3d.art3d.Line3D(xs, ys, zs, color='black', linewidth=1, alpha=0.3)
                    self.__axis.add_line(line)
            if self.__number_of_dim == 2:
                for edge in self.__line_cords_tuples:
                    xs = edge[0][0], edge[1][0]
                    if number_of_cords == 1:
                        ys = 0, 0
                    else:
                        ys = edge[0][1], edge[1][1]

                    self.__axis.plot(xs, ys, linestyle='-', color='black', linewidth=1, alpha=0.5)
        x_axe_cords = self.__cords[0]
        y_axe_cords = np.zeros_like(self.__cords[0])
        z_axe_cords = np.zeros_like(self.__cords[0])
        self.set_point_color()
        self.__axis.set_title(self.__graph_title)
        self.__axis.set_xlabel(self.__graph_labels[0])
        if len(self.__cords[0]) == len(self.__points_colour):
            if number_of_cords >= 2:
                self.__axis.set_ylabel(self.__graph_labels[1])
                y_axe_cords = self.__cords[1]
                if number_of_cords > 2:
                    z_axe_cords = self.__cords[2]
                    if self.__draw_3D:
                        self.__axis.set_zlabel(self.__graph_labels[2])

            if self.__draw_3D:
                self.__axis.scatter(x_axe_cords, y_axe_cords, z_axe_cords, c=self.__points_colour)
                for point in self.__active_points_label:
                    self.__axis.text(x_axe_cords[point[0]], y_axe_cords[point[0]], z_axe_cords[point[0]], point[1])
            else:
                self.__axis.scatter(x_axe_cords, y_axe_cords, c=self.__points_colour)
                for point in self.__active_points_label:
                    self.__axis.annotate(point[1], (x_axe_cords[point[0]], y_axe_cords[point[0]]))

        if self.__locked_view:
            self.__axis.set_xlim(tmpX)
            self.__axis.set_ylim(tmpY)
            if self.__number_of_dim == 3:
                self.__axis.set_zlim(tmpZ)

    def set_graph_dimension(self, dimension: int):
        if dimension >= 3:
            self.__draw_3D = True
        else:
            self.__draw_3D = False
        self.__figure.clf()

        if self.__draw_3D:
            self.__graph_container.pack()
            self.__axis = self.__figure.add_subplot(111, projection='3d')
            self.__number_of_dim = 3
            for item in self.__toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack_forget()
                else:
                    item.pack(pady=(4, 5))
        else:
            self.__axis = self.__figure.add_subplot(111)
            self.__number_of_dim = 2
            self.__graph_container.pack()
            for item in self.__toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack(side='left')

        self.__changed = True
        self.__ani.event_source.start()

    def clear(self):
        print('Cistime plott')
        self.__ani.event_source.stop()
        self.__toolbar.destroy()
        self.__canvas.get_tk_widget().destroy()
        self.__plot_wrapper_frame.destroy()
        self.__figure.delaxes(self.__axis)
        self.__graph_container.destroy()
        self.__figure.clf()
        self.__axis.cla()
        self.__parent_controller = None
        self.__graph_container = None
        self.__graph_labels = None
        self.__graph_title = None
        self.__toolbar = None
        self.__canvas = None
        self.__figure = None
        self.__axis = None
        self.__ani = None

    def pack(self, *args, **kwargs):
        self.__plot_wrapper_frame.pack(*args, **kwargs)

    def set_color_label(self, new_value):
        if new_value:
            self.__used_colour = self.__points_config['label_colour']
        else:
            self.__used_colour = self.__points_config['default_colour']

    def __del__(self):
        print('Mazanie plotting graph')

    @property
    def graph_title(self):
        return self.__graph_title

    @graph_title.setter
    def graph_title(self, new_title):
        self.__graph_title = new_title

    @property
    def graph_labels(self):
        return self.__graph_labels

    @graph_labels.setter
    def graph_labels(self, new_labels_list):
        self.__graph_labels = new_labels_list

    @property
    def locked_view(self):
        return self.__locked_view

    @locked_view.setter
    def locked_view(self, value):
        self.__locked_view = value

    @property
    def draw_polygon(self):
        return self.__draw_polygon

    @draw_polygon.setter
    def draw_polygon(self, value):
        self.__draw_polygon = value

    @property
    def is_3d_graph(self):
        return self.__draw_3D

    @is_3d_graph.setter
    def is_3d_graph(self, value):
        if self.__draw_3D != value:
            self.__draw_3D = value
            if self.__draw_3D:
                self.set_graph_dimension(3)
            else:
                self.set_graph_dimension(2)

    @property
    def points_cords(self):
        return self.__cords

    @points_cords.setter
    def points_cords(self, new_cords):
        self.__cords = new_cords

    @property
    def line_tuples(self):
        return self.__line_cords_tuples

    @line_tuples.setter
    def line_tuples(self, new_tuples):
        self.__line_cords_tuples = new_tuples

    @property
    def point_colour(self):
        return self.__points_colour

    @point_colour.setter
    def point_colour(self, new_value):
        self.__points_colour = new_value


class LayerWeightControllerFrame:
    def __init__(self, parent, controller):
        self.__plot_wrapper_frame = tk.LabelFrame(parent)
        self.__controller = controller
        self.__weights_reference = None
        self.__bias_reference = None
        self.__active_slider_dict = {}
        self.__slider_dict = {}
        self.__possible_number_of_sliders = 0
        self.__scrollable_window = ScrollableWindow(self.__plot_wrapper_frame, 'vertical', border=0)
        self.__scrollable_window.pack(side='bottom', fill='both', expand=True)
        self.__add_slider_list = ComboboxAddRemoveFrame(self.__scrollable_window.Frame, height=58)
        self.__add_slider_list.pack(side='bottom', fill='x', expand=True)

    def initialize(self, layer_weights: list, layer_bias: list):
        for weight_slider in self.__active_slider_dict.values():
            weight_slider.pack_forget()
            weight_slider.destroy()

        self.__possible_number_of_sliders = 0
        self.__slider_dict = {}
        self.__active_slider_dict = {}
        self.__weights_reference = layer_weights
        self.__bias_reference = layer_bias

        tmp_ordered_sliders_names = []
        tmp_ordered_sliders_config = []
        if layer_weights is not None:
            for start_neuron in range(len(self.__weights_reference)):
                for end_neuron in range(len(self.__weights_reference[start_neuron])):
                    layer_name = 'Vaha {}-{}'.format(start_neuron, end_neuron)
                    tmp_ordered_sliders_names.append(layer_name)
                    tmp_ordered_sliders_config.append((True, start_neuron, end_neuron))
        if layer_bias is not None:
            for end_neuron in range(len(layer_bias)):
                layer_name = 'Bias {}'.format(end_neuron)
                tmp_ordered_sliders_names.append(layer_name)
                tmp_ordered_sliders_config.append((False, end_neuron))

        self.__possible_number_of_sliders = len(tmp_ordered_sliders_names)

        final_name_list = self.__add_slider_list.initialize(tmp_ordered_sliders_names, self.handle_combobox_input,
                                                            'Add weight', False, 'Select weight')
        for i, slider_name in enumerate(final_name_list):
            self.__slider_dict[slider_name] = tmp_ordered_sliders_config[i]
        self.addSlider_visibility_test()
        special = 'Vsetky'
        special = self.__add_slider_list.add_special(special)

    def addSlider_visibility_test(self):
        if len(self.__active_slider_dict) == self.__possible_number_of_sliders:
            self.__add_slider_list.pack_forget()
        else:
            self.__add_slider_list.pack(side='bottom', fill='x', expand=True)

    def create_weight_slider(self, start_neuron: int, end_neuron: int):
        slider_name = 'Vaha {}-{}'.format(start_neuron, end_neuron)
        slider = ModifiedClickableSlider(self.__scrollable_window.Frame, slider_name, self.remove_slider, from_=-1,
                                         to=1,
                                         resolution=0.01, digits=3,
                                         text=slider_name, command=self.on_slider_change)
        slider.set_variable(self.__weights_reference[start_neuron], end_neuron)
        slider.pack_propagate(0)
        slider.pack(fill='x', expand=True, padx=(0, 2), pady=0)
        self.__active_slider_dict[slider_name] = slider
        self.addSlider_visibility_test()

    def create_bias_slider(self, end_neuron: int):
        slider_name = 'Bias {}'.format(end_neuron)
        slider = ModifiedClickableSlider(self.__scrollable_window.Frame, slider_name, self.remove_slider, from_=-10,
                                         to=10,
                                         resolution=0.01, digits=3,
                                         text=slider_name, command=self.on_slider_change)
        slider.set_variable(self.__bias_reference, end_neuron)
        slider.pack(fill='x', expand=True, padx=(0, 2), pady=0)
        self.__active_slider_dict[slider_name] = slider
        self.addSlider_visibility_test()

    def remove_slider(self, slider_id: str):
        slider = self.__active_slider_dict.pop(slider_id)
        slider.clear()
        self.__add_slider_list.show_item(slider_id)
        self.addSlider_visibility_test()

    def on_slider_change(self, value):
        self.__controller.controller_signal()

    def add_slider(self, slider_name: str):
        if slider_name not in self.__active_slider_dict.keys():
            slider_config = self.__slider_dict[slider_name]
            if slider_config[0]:
                self.create_weight_slider(slider_config[1], slider_config[2])
            else:
                self.create_bias_slider(slider_config[1])
            self.__add_slider_list.hide_item(slider_name)

    def handle_combobox_input(self, item: tuple):
        if item[0] >= 0:
            self.add_slider(item[1])
        else:
            list_of_remaining = self.__add_slider_list.get_list_of_visible()
            # prve dva su default a vsetky, to treba preskocit
            list_of_remaining = list_of_remaining[1:].copy()
            for name in list_of_remaining:
                self.add_slider(name)

    def clear(self):
        print('Cistime controller')
        self.__plot_wrapper_frame.destroy()
        self.__scrollable_window.clear()
        self.__add_slider_list.clear()
        self.__active_slider_dict = None
        self.__weights_reference = None
        self.__scrollable_window = None
        self.__add_slider_list = None
        self.__bias_reference = None
        self.__slider_dict = None

    def pack(self, *args, **kwargs):
        self.__plot_wrapper_frame.pack(*args, **kwargs)

    def __del__(self):
        print('Mazanie controller')
