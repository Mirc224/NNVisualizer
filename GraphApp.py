import matplotlib

matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import backend_bases
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib import style
import numpy as np
import tkinter as tk
from tkinter import ttk
from GraphicalComponents import *

LARGE_FONT = ('Verdana', 12)
# style.use('seaborn-whitegrid')
tmp = None


class VisualizationApp(tk.Tk):
    '''
    Spúšťacia trieda. Je obalom celeje aplikácie. Vytvorí programové okno, na celú obrazovku. Táto trieda dedí od
    objektu Tk z build in knižnice tkinter.

    Atribúty
    --------
    __frames : dict
        je to dictionary, ktorý obsahuje jednotlivé hlavné stránky aplikácie. Kľúčom k týmto stránkam sú prototypy
        daných stránok

    Metódy
    --------
    show_frame(controller)
        Zobrazuje stránku na základe zvoleného kontrolera.
    '''

    def __init__(self, *args, **kwargs):

        # Konštruktor základnej triedy.
        tk.Tk.__init__(self, *args, **kwargs)
        # Zobrazenie okna na (takmer) celú obrazovku. Prvé dva čísla určujú rozmery obrazovky. Konštatny pri nich slúžia
        # na ich čiastočné vycentrovanie.
        super().geometry('%dx%d+0+0' % (super().winfo_screenwidth() - 8, super().winfo_screenheight() - 70))
        self.title('Bakalarka')

        container = ttk.Frame(self)
        container.pack(side='top', fill='both', expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.__frames = {}
        # Vytvorenie všetkých podstránok v rámci cyklu a ich pridelenie do dict. Kľúčom v dict je ich prototyp.
        for F in (StartPage, GraphPage):
            frame = F(container, self)
            self.__frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
        # Zobrazenie prvej stránky.
        self.show_frame(GraphPage)

    def show_frame(self, controller):
        '''
        Zobrazenie požadovanej stránky
        :param controller: ProtoypStranky
        '''
        frame = self.__frames[controller]
        frame.tkraise()


class StartPage(tk.Frame):
    '''
    Úvodné podstránka aplikácie, bude obsahovať tlačidlá na načítanie štruktúry neurónovej siete a bodov zo súboru.
    '''
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Start Page', font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        button3 = ttk.Button(self, text='Graph Page',
                             command=lambda: controller.show_frame(GraphPage))
        button3.pack()


class MainGraphFrame(tk.LabelFrame):
    '''
    Hlavné okno podstránky s grafmi. Okno vytvorí scrollovacie okno, do ktorého budú následne vkladané jednotlivé vrstvy
    s grafmi a ich ovládačmi. Vytvorí taktiež input okno, ktoré slúži na zobrazovanie informácii o zvolenem bode a
    možnosti nastavenia zobrazenia grafov v jednotlivých vrstvách.

    Atribúty
    --------
    __logic_layer : GraphLogicLayer
        obsahuje odkaz na vrstvu, ktorá sa zaoberá výpočtami a logickou reprezentáciou jednotlivých vrstiev a váh.
    __number_of_layers : int
        počet vrstiev načítanej neurónovej siete
    __NNStructure : list
        logicka štruktúra neuronovej siete má tvar [[počet neuronov v sieti], [počet neuronov v sieti]]. Vnorený list
        predstavuje jednotlivé vrstvy
    __layers_points : list
        referencia na list, ktorý obsahuje prepočítané súradnice pre jednotlivé vrstvy neurónovej siete.
    __layers_weights : list
        referencia na list, ktorý obsahuje hodnoty váh na jednotlivých vrstvách neurónovej siete
    __layers_biases : list
        referencia na list, ktorý obsahuje hodnoty bias na jednotlivých vrstvách neurónovej siete
    __name_to_order_dict : dict[str] = int
        každej vrstve je postupne prideľované poradové číslo vrstvy, tak ako ide od začiatku neurónovej siete. Ako kľúč
        je použitý názov vrstvy.
    __order_to_name : dict[int] = str
        podľa poradia je každej vrstve pridelené poradové číslo. Poradové číslo je kľúčom do dict. Jeho hodnotami sú
        názvy jedntlivých vrstiev. Ide o spätný dict k __name_to_order_dict.
    __active_layers : int
        obsahuje poradové čísla aktívnych vrstiev. Využíva sa na efektívnejšie prekresľovanie vrstiev, aby neboli
        zbytočne prekresľované vrstvy, ktoré neboli ovplyvnené.
    __active_layers_dict : dict
        slovník, ktorý obsahuje odkaz na aktívnu vrstvu. Kľúčom k odkazom na aktívnu vrstvu je poradové číslo vrstvy.
    __input_panned : PannedWindow
        obal pre komponenty InputDataFrame a PannedWindow. Umožňuje podľa potreby roztiahnuť alebo zúžiť veľkosť
        input panelu na úkor PannedWindow, ktoré obsahuje rámce s reprezentáciou jednotlivých vrstiev.
    __graph_panned : PannedWindow
        obal pre ScrollableWindow, ktoré obsahuje rámce v ktorých sú zobrazené jednotlivé vrstvy.
    __scroll_frame : ScrollableWindow
        obsahuje grafické zobrazenie zvolených vrstiev neurónovej siete a ComboboxAddRemoveFrame, v ktorom sú volené
        vrstvy, ktoré chceme zobraziť
    __add_graph_list_frame : ComboboxAddRemoveFrame
        combobox, z ktorého si vyberáme jednotlivé, ešte neaktívne vrstvy, ktoré tlačidlom následne zobrazíme. Zobrazuje
        sa, len ak nie sú zobrazené ešte všetky vrstvy.
    '''
    def __init__(self, parent, logic_layer, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)

        self.__logic_layer = logic_layer
        self.__number_of_layers = 0

        self.__NNStructure = []
        self.__layers_points = []
        self.__layers_weights = []
        self.__layers_biases = []

        self.__name_to_order_dict = {}
        self.__order_to_name_dict = {}

        self.__active_layers = []
        self.__active_layers_dict = {}

        self.__input_panned = tk.PanedWindow(self)
        self.__input_panned.pack(fill='both', expand=True)

        self.__input_frame = InputDataFrame(self.__input_panned, self.__logic_layer, border=0, highlightthickness=0)
        self.__input_panned.add(self.__input_frame)
        self.__graph_panned = ttk.PanedWindow(self.__input_panned)
        self.__input_panned.add(self.__graph_panned)

        self.__graph_area_frame = tk.LabelFrame(self.__graph_panned, relief='sunken', border=0, highlightthickness=0)
        self.__graph_panned.add(self.__graph_area_frame)

        self.__scroll_frame = ScrollableWindow(self.__graph_area_frame, 'horizontal', border=0, highlightthickness=0)
        self.__scroll_frame.pack(side='right', fill=tk.BOTH, expand=True)

        self.__add_graph_list_frame = ComboboxAddRemoveFrame(self.__scroll_frame.Frame, width=412, relief='sunken')
        self.__add_graph_list_frame.pack(side='right', fill='y')

    def initialize(self, NNStructure: list, layer_points_ref: list, weights_ref: list, bias_ref: list):
        for layer in self.__active_layers_dict.values():
            layer.clear()

        self.__order_to_name_dict = {}
        self.__name_to_order_dict = {}

        self.__active_layers = []
        self.__active_layers_dict = {}

        self.__NNStructure = NNStructure
        self.__layers_points = layer_points_ref
        self.__layers_weights = weights_ref
        self.__layers_biases = bias_ref
        self.__input_frame.initialize(NNStructure[0][0])
        self.__number_of_layers = len(NNStructure)

        # Ordered list of names which will be used for dictionary creation
        layer_name_list = []
        for i in range(self.__number_of_layers):
            layer_name_list.append('Layer{}'.format(i))

        # AddGraph frame initialization, which return ordered unique name list, which will be used in dictionary
        unique_name_list = self.__add_graph_list_frame.initialize(layer_name_list, self.show_layer, 'Add layer', True, 'Select layer')
        for i, layerName in enumerate(unique_name_list):
            self.__order_to_name_dict[i] = layerName
            self.__name_to_order_dict[layerName] = i

        self.show_layer((0, 'Layer0'))

    # A
    def apply_changes(self, starting_layer: int = 0):
        updated_layer = [layer_number for layer_number in self.__active_layers if layer_number >= starting_layer]
        for layer_number in updated_layer:
            self.__active_layers_dict[layer_number].apply_changes()

    def show_layer(self, layer_tuple: tuple):
        layer_name = layer_tuple[1]
        layer_number = self.__name_to_order_dict[layer_name]

        if 0 <= layer_number < self.__number_of_layers:
            layer_to_show = None
            if layer_number < self.__number_of_layers - 1:
                layer_to_show = NeuralLayer(self.__scroll_frame.Frame, self, self.__logic_layer)
                layer_to_show.initialize(self.__NNStructure[layer_number][0], layer_number, self.__layers_points[layer_number],
                                       self.__layers_weights[layer_number], self.__layers_biases[layer_number], layer_name)
            else:
                layer_to_show = NeuralLayer(self.__scroll_frame.Frame, self, self.__logic_layer)
                layer_to_show.initialize(self.__NNStructure[layer_number][0], layer_number, self.__layers_points[layer_number],
                                       None, None, layer_name)

            layer_to_show.pack(side='left', fill=tk.BOTH, expand=True)

            self.__active_layers_dict[layer_number] = layer_to_show
            self.__active_layers.append(layer_number)
            self.__add_graph_list_frame.hide_item(layer_name)

            if len(self.__active_layers) == self.__number_of_layers:
                self.__add_graph_list_frame.pack_forget()

    def hide_layer(self, layer_number: int):
        layer_name = self.__order_to_name_dict[layer_number]
        layer = self.__active_layers_dict.pop(layer_number)
        layer.clear()
        self.__active_layers.remove(layer_number)
        self.__add_graph_list_frame.show_item(layer_name)
        if len(self.__active_layers) < self.__number_of_layers:
            self.__add_graph_list_frame.pack(side='right', fill='y', expand=True)
# dokaze vykreslit max 285x2 okienok


class GraphLogicLayer:
    def __init__(self, parent):
        self._graph_page = parent

        self.__main_graph_frame = MainGraphFrame(parent, self, border=1)
        self.__number_of_points = 0

        # second DIM is layer  third are cords
        self.__number_of_layers = 0
        self.__NNStructure = None
        self.__points = []
        self.__layer_points_values = []
        self.__weights = []
        self.__bias = []

        self.__main_graph_frame.pack(side='bottom', fill='both', expand=True)
        struct = []
        for i in range(4):
            struct.append([2])
        self.initialize(struct)
        #self.initialize(struct)

    def initialize(self, NNStructure: list):
        self.__NNStructure = NNStructure
        self.__number_of_layers = len(NNStructure)
        self.__layer_points_values = [[[] for y in range(layer[0])] for layer in NNStructure]
        self.__points = [[] for x in range(NNStructure[0][0])]
        self.__layer_points_values[0] = self.__points

        self.__weights = []
        self.__bias = []
        for layer_number, layer in enumerate(NNStructure):
            if layer_number < self.__number_of_layers - 1:
                self.__weights.append([])
                self.__bias.append([])
                for end_neuron_number in range(NNStructure[layer_number + 1][0]):
                    self.__bias[layer_number].append(0)
            else:
                break
            for start_neuron_number in range(layer[0]):
                self.__weights[layer_number].append([])
                for end_neuron_number in range(NNStructure[layer_number + 1][0]):
                    self.__weights[layer_number][start_neuron_number].append(0)

        for i in range(NNStructure[0][0]):
            for j in range(4):
                if i % 2:
                    self.__points[i].append(j)
                else:
                    self.__points[i].append(j - 1)
        self.recalculate_cords()
        self.__main_graph_frame.initialize(NNStructure, self.__layer_points_values, self.__weights, self.__bias)

    def recalculate_cords(self):
        for layer_number, layer_points in enumerate(self.__layer_points_values):
            if layer_number < self.__number_of_layers - 1:
                na = np.array(layer_points).transpose()
                # print(na)
                b = np.array(self.__weights[layer_number])
                # print(b)
                tmp = na.dot(b)
                vec = np.array(self.__bias[layer_number])
                result = np.empty_like(tmp)
                for i in range(tmp.shape[0]):
                    result[i, :] = tmp[i, :] + vec

                self.__layer_points_values[layer_number + 1][:] = result.transpose().tolist()
            else:
                break
        # print(self.LayerPointsValues)
        self.__main_graph_frame.apply_changes()

    def add_point(self, *args):
        self.__number_of___points += 1
        # print(args)
        for cord in range(len(self.__points)):
            self.__points[cord].append(args[cord])

        print(self.__layer_points_values)

    def test(self):
        print('starting test')
        self.recalculate_cords()

class GraphPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Graph Page', font=LARGE_FONT)
        label.pack()
        self.__logic_layer = GraphLogicLayer(self)
        button1 = ttk.Button(self, text='Back to home',
                             command=lambda: controller.show_frame(StartPage))
        button1.pack()


class InputDataFrame(tk.LabelFrame):
    def __init__(self, parent, logicalLayer: GraphLogicLayer, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, width=285, *args, **kwargs)
        self.__graph_logic = logicalLayer
        self.pack_propagate(0)

        self.__entries_list = []
        but1 = tk.Button(self, text='Add point', command=self.add_point)
        but1.pack()

        but2 = tk.Button(self, text='Test', command=self.__graph_logic.test)
        but2.pack()

        but3 = tk.Button(self, text='New initilization', command=self.new_init)
        but3.pack()

    def new_init(self):
        self.__graph_logic.initialize([[2], [2], [2]])

    def initialize(self, number_of_inputs: int):
        for entry in self.__entries_list:
            entry.destroy()
            entry = None
        self.__entries_list = []

        for entry in range(number_of_inputs):
            entry = ttk.Entry(self, width=10)
            # entry.pack(side=tk.TOP)
            self.__entries_list.append(entry)

    def add_point(self):
        inputList = []
        for entry in self.__entries_list:
            value = entry.get()
            if value:
                value = float(value)
            else:
                value = 0
            inputList.append(value)
            entry.delete(0, tk.END)
        self.__graph_logic.add_point(*inputList)


class NeuralLayer:
    def __init__(self, parent, mainGraph: MainGraphFrame, logicLayer: GraphLogicLayer, *args, **kwargs):
        self.__graph_frame = GraphFrame(self, mainGraph, parent, *args, **kwargs)
        self.__main_graph_frame = mainGraph
        self.__logic_layer = logicLayer
        self.__layer_name = ''
        self.__layer_number = -1
        self.__number_of_dimension = -1
        self.__point_cords = []

    def pack(self, *args, **kwargs):
        self.__graph_frame.pack(*args, **kwargs)

    def initialize(self, num_of_dim: int, layer_number: int, layer_point_cords: list, layer_weights: list = None,
                   layer_bias: list = None, layer_name: str = None):
        self.__number_of_dimension = num_of_dim
        self.__layer_number = layer_number
        self.__point_cords = layer_point_cords
        if layer_name:
            self.__layer_name = layer_name
        else:
            self.__layer_name = 'Layer {}'.format(layer_number)
        self.__graph_frame.initialize(self, self.__number_of_dimension, self.__layer_name, self.__point_cords, layer_weights, layer_bias)

    def apply_changes(self):
        self.__graph_frame.apply_changes()

    def hide_graph_frame(self):
        self.__main_graph_frame.hide_layer(self.__layer_number)

    def clear(self):
        self.__graph_frame.clear()

    def signal_change(self):
        self.__logic_layer.recalculate_cords()


class GraphFrame(tk.LabelFrame):
    def __init__(self, neural_layer: NeuralLayer, main_graph: MainGraphFrame, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.__neural_layer = neural_layer
        self.__main_graph_frame = main_graph
        self.__layer_number = -1
        self.__number_of_dim = -1

        self.__graph = PlotingFrame(self, self)
        self.__weight_controller = LayerWeightControllerFrame(self, self)

    def initialize(self, neuralLayer: int, numOfDimensions: int, layer_name: str ,pointCords: list, layer_weights: list, layerBias: list):
        self.__neural_layer = neuralLayer
        self.__graph.initialize(numOfDimensions, pointCords, layer_name)
        self.__weight_controller.initialize(layer_weights, layerBias)

        self.__graph.pack(side=tk.TOP)
        self.__weight_controller.pack(side=tk.TOP, fill='both', expand=True)

    def apply_changes(self):
        self.__graph.update_graph()

    def hide_graph_frame(self):
        self.__neural_layer.hide_graph_frame()

    def clear(self):
        self.pack_forget()
        self.__weight_controller.clear()
        self.__graph.clear()
        self.__weight_controller = None
        self.__main_graph_frame = None
        self.__neural_layer = None
        self.__graph = None

    def controller_signal(self):
        self.__neural_layer.signal_change()

class PlotingFrame:
    def __init__(self, parent, controller, *args, **kwargs):
        self.__plot_wrapper_frame = tk.LabelFrame(parent, *args, **kwargs)
        self.__plot_wrapper_frame.pack()
        self.__cords = [[], [], []]
        self.__number_of_dim = -1
        self.__graph_frame = controller
        self.__graph_title = 'Graf'
        self.__graph_labels = ['Label X', 'Label Y', 'Label Z']

        self.__upper_bar = tk.LabelFrame(self.__plot_wrapper_frame, border=0)
        self.__upper_bar.pack(side='top', fill='x', expand=True)
        self.__dim_change_button = ttk.Button(self.__upper_bar, command=self.change_graph_dimension)
        self.__hide_button = ttk.Button(self.__upper_bar, command=self.__graph_frame.hide_graph_frame)
        #self.__hide_button = ttk.Button(self.__upper_bar)
        self.__hide_button.pack(side='right')

        self.__graph_container = tk.LabelFrame(self.__plot_wrapper_frame, relief=tk.FLAT)

        self.__figure = Figure(figsize=(4, 4), dpi=100)
        self.__canvas = FigureCanvasTkAgg(self.__figure, self.__graph_container)
        self.__canvas.draw()
        self.__axis = None
        self.__draw_2D = True

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
        self.__ani = animation.FuncAnimation(self.__figure, self.update_changed, interval=100)

    def initialize(self, numberOfDim: int, pointCords: list, layerName: str):
        self.__cords = pointCords
        self.__dim_change_button.pack(side=tk.LEFT)
        self.__graph_container.pack(side=tk.TOP)
        self.set_graph_dimension(numberOfDim)
        self.__graph_title = layerName

    def change_graph_dimension(self):
        if self.__draw_2D:
            self.set_graph_dimension(3)
        else:
            self.set_graph_dimension(2)

    def update_changed(self, i):
        if self.__changed:
            self.__changed = False
            self.redraw_graph()
        else:
            self.__ani.event_source.stop()

    def update_graph(self):
        self.__changed = True
        self.__ani.event_source.start()

    def redraw_graph(self):
        self.__axis.clear()
        self.__axis.grid()
        if self.__number_of_dim >= 3:
            if len(self.__cords) > 2:
                self.__axis.scatter(self.__cords[0], self.__cords[1], self.__cords[2])
            else:
                self.__axis.scatter(self.__cords[0], self.__cords[1])
            self.__axis.set_zlabel(self.__graph_labels[2])
        else:
            # tmp = np.zeros(len(self.__cords[0])).tolist()
            self.__axis.scatter(self.__cords[0], self.__cords[1])
        self.__axis.set_title(self.__graph_title)
        self.__axis.set_xlabel(self.__graph_labels[0])
        self.__axis.set_ylabel(self.__graph_labels[1])

    def set_graph_dimension(self, dimension: int):
        if dimension >= 3:
            self.__draw_2D = False
        else:
            self.__draw_2D = True
        text = ''
        self.__figure.clf()

        if self.__draw_2D:
            self.__axis = self.__figure.add_subplot(111)
            self.__number_of_dim = 2
            self.__graph_container.pack()
            text = 'Make 3D'
            for item in self.__toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack(side='left')
        else:
            self.__graph_container.pack()
            self.__axis = self.__figure.add_subplot(111, projection='3d')
            self.__number_of_dim = 3
            text = 'Make 2D'
            for item in self.__toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack_forget()
                else:
                    item.pack(pady=(4, 5))

        # self.__graph_title = 'Graph {}D'.format(self.NumberOfDim)
        self.__changed = True
        self.__dim_change_button.configure(text=text)
        self.__ani.event_source.start()

    def clear(self):
        print('Cistime plott')
        self.__toolbar.destroy()
        self.__canvas.get_tk_widget().destroy()
        self.__plot_wrapper_frame.destroy()
        self.__dim_change_button.destroy()
        self.__figure.delaxes(self.__axis)
        self.__graph_container.destroy()
        self.__hide_button.destroy()
        self.__upper_bar.destroy()
        self.__figure.clf()
        self.__axis.cla()
        self.__dim_change_button = None
        self.__graph_container = None
        self.__graph_labels = None
        self.__graph_title = None
        self.__hide_button = None
        self.__graph_frame = None
        self.__upper_bar = None
        self.__toolbar = None
        self.__canvas = None
        self.__figure = None
        self.__axis = None
        self.__ani = None

    def pack(self, *args, **kwargs):
        self.__plot_wrapper_frame.pack(*args, **kwargs)

    def __del__(self):
        print('Mazanie plotting graph')


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
        #self.pack_propagate(0)
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
        if layer_weights:
            for start_neuron in range(len(self.__weights_reference)):
                for end_neuron in range(len(self.__weights_reference[start_neuron])):
                    layer_name = 'Vaha {}-{}'.format(start_neuron, end_neuron)
                    tmp_ordered_sliders_names.append(layer_name)
                    tmp_ordered_sliders_config.append((True, start_neuron, end_neuron))
        if layer_bias:
            for end_neuron in range(len(layer_bias)):
                layer_name = 'Bias {}'.format(end_neuron)
                tmp_ordered_sliders_names.append(layer_name)
                tmp_ordered_sliders_config.append((False, end_neuron))

        self.__possible_number_of_sliders = len(tmp_ordered_sliders_names)

        final_name_list = self.__add_slider_list.initialize(tmp_ordered_sliders_names, self.handle_combobox_input, 'Add weight', False, 'Select weight')
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
        slider = ModifiedClickableSlider(self.__scrollable_window.Frame, slider_name, self.test, from_=-1, to=1,
                                         resolution=0.01, digits=3,
                                         text=slider_name, command=self.testovaci)
        slider.set_variable(self.__weights_reference[start_neuron], end_neuron)
        slider.pack_propagate(0)
        slider.pack(fill='x', expand=True, padx=(0, 2), pady=0)
        self.__active_slider_dict[slider_name] = slider
        self.addSlider_visibility_test()

    def create_bias_slider(self, end_neuron: int):
        slider_name = 'Bias {}'.format(end_neuron)
        slider = ModifiedClickableSlider(self.__scrollable_window.Frame, slider_name, self.test, from_=-10, to=10,
                                         resolution=0.01, digits=3,
                                         text=slider_name)
        slider.set_variable(self.__bias_reference, end_neuron)
        slider.pack(fill='x', expand=True, padx=(0, 2), pady=0)
        self.__active_slider_dict[slider_name] = slider
        self.addSlider_visibility_test()

    def test(self, slider_id: str):
        slider = self.__active_slider_dict.pop(slider_id)

        slider.clear()
        self.__add_slider_list.show_item(slider_id)
        self.addSlider_visibility_test()

    def testovaci(self, value):
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

    def vypis(self, value: int):
        print(self.__weights_reference)

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

class Testovacia(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # self.__figure = Figure(figsize=(4, 4), dpi=100)
        # self.__axis = self.__figure.add_subplot(111, projection='3d')
        # self.__canvas = Figure__canvasTkAgg(self.__figure, self)
        # self.__canvas.get_tk_widget().pack()
        # self.__axis.scatter([0, 1], [0, 1], [0, 1])
        # self.__canvas.draw()

    def zmazaj(self):
        # self.__canvas.get_tk_widget().destroy()
        # self.__axis.cla()
        # self.__figure.clear()
        # self.__figure.clf()
        # self.__canvas = None
        # self.__axis = None
        # self.__figure = None
        #self.destroy()
        self.destroy()

    def __del__(self):
        print('mazem')

# root = tk.Tk()
# plotting = LayerWeightControllerFrame(root)
# plotting.pack()
# plotting.clear()
# plotting = None
# root.mainloop()

# #__canvas = tk.Canvas(root)
# okno = tk.Frame(root)
# okno.pack()
# root = tk.Tk()
# test = Testovacia(root)
# test.zmazaj()
# test = None
# root.mainloop()
# test = {1: '3', 2:'2', 4:'3', 3:'4'}
#
# print(test)
# for key in test.keys():
#     if key > 2:
#         print(key)

app = VisualizationApp()
app.mainloop()

