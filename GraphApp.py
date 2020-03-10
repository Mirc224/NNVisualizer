import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib import backend_bases
import mpl_toolkits.mplot3d as plt3d
import matplotlib.animation as animation
import numpy as np
import tkinter as tk
from GraphicalComponents import *
from tensorflow import keras

LARGE_FONT = ('Verdana', 12)
# style.use('seaborn-whitegrid')
tmp = None


class VisualizationApp(tk.Tk):
    def __init__(self, *args, **kwargs):
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


class GraphPage(tk.Frame):
    def __init__(self, parent, controller):
        '''
        Popis
        --------
        Podstránka, na ktorej je zobrazovaný rámec s grafmi, váhami a okno s detailmi vrstvy.

        :param parent: nadradený tkinter Widget
        '''
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Graph Page', font=LARGE_FONT)
        label.pack()
        self.__logic_layer = GraphLogicLayer(self)
        button1 = ttk.Button(self, text='Back to home',
                             command=lambda: controller.show_frame(StartPage))
        button1.pack()


class GraphLogicLayer:
    def __init__(self, parent):
        '''
        Popis
        -------
        Trieda, ktorá sa stará o logiku podstaty aplikácie, inicializuje základné grafické časti aplikácie, stará sa aj
        o výpočty.

        Atribúty
        --------
        :var self.__graph_page: odkaz na nadradený tkinter widget
        :var self.__main_graph_frame: odkaz na hlavné okno, v ktorom sú vykresľované grafy pre jednotlivé vrstvy
        :var self.__number_of_points: počet bodov na vstupe
        :var self.__NNStructure: štruktúra neuronovej siete
        :var self.__layer_points_values: obsahuje hodnoty súradnínc bodov na jednotlivých vrstvách
        :var self.__points: súradnice bodov na vstupe
        :var self.__number_of_layers: počet vrstiev v neurónovej sieti
        :var self.__weights: list držiaci hodnoty váh v jednotlivých vrstvách pre jednotlivé kombinácie neurónov na
                             určitej vrstve a vrstve za ňou nasledujúcej
        :var self.__bias: list držiaci hodnoty bias pre výpočet hodnoty vybudenia neurónu na nasledujúcej vrstve

        Parametre
        --------
        :param parent:
        '''
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

        self.__neural_layers = []

        self.__keras_model = keras.models.load_model('modelik.h5')

        self.__polygon = None
        self.__polygon_cords = None
        self.__polygon_edges = None
        self.__shared_line_cords_tuples = None

        self.__main_graph_frame.pack(side='bottom', fill='both', expand=True)
        struct = []
        for i in range(5):
            struct.append([4])

        # struct.append([2])
        #self.initialize([[2], [3]])
        self.initialize([[3], [2]])
        #self.initialize([[3], [2]])
        #self.initialize(struct)

    def initialize(self, NNStructure: list):
        '''
        Popis
        --------
        Inicializuje hodnoty pre triedu GraphLogicLayer a tak isto aj pre triedy MainGraphFrame.

        :param NNStructure: Štruktúra neurónovej siete
        :type NNStructure: list
        '''
        self.__polygon = None
        self.__polygon_cords = None
        self.__polygon_edges = None
        self.__NNStructure = NNStructure
        self.__number_of_layers = len(NNStructure)

        # Vytvorí v rámci listu vytvorí, ďalšie listy, ktorých počet predstavuje jednotlivé vrstvy a ich poradie.
        # Pre jednotlivé vrstvy vygeneruje ďalšie listy, ktorých počet sa rovná počtu súradníc na vykreslenie daného
        # bodu.

        self.__layer_points_values = [[[] for y in range(layer[0])] for layer in NNStructure]

        self.__neural_layers = []

        if NNStructure[0][0] < 4:
            if NNStructure[0][0] == 3:
                self.__polygon = Polygon([0, 0, 0], [10, 10, 10], [5, 5, 5])
            elif NNStructure[0][0] == 2:
                self.__polygon = Polygon([0, 0], [10, 10], [5, 5, 5])

            self.__shared_line_cords_tuples = [[] for layer in NNStructure]
            self.__polygon_cords = [[[] for y in range(layer[0])] for layer in NNStructure]
            self.__polygon_cords[0] = self.__polygon.Peaks
            self.__polygon_edges = self.__polygon.Edges

            self.asign_shared_cord_tuples(0)

        # Referencia na vstupnú vrstvu, do ktorej budú pridávané body.
        self.__points = self.__layer_points_values[0]

        # Vymazanie starých hodnôt váh a biasov.
        self.__weights = []
        self.__bias = []

        # Vytvorenie potrebnej štruktúry listu. Na základe štruktúry neurónovej siete je vytvorený list, ktorý obsahuje
        # ďalšie listy. Tieto listy predstavujú jednotlivé vrstvy. V rámci týchto vnorených listov je vytvorený ďalší
        # list, ktorý predstavuje jednotlivé neuróny na vrstve. Do listu predstavujúceho vstupný neurón je potom
        # priradená hodnota váhy pre zodpovedajúci neurón na nasledujúcej vrstve.
        # Pre poslednú vrstvu nie je táto štruktúra vytvorená.
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
            for j in range(10):
                if i % 2:
                    self.__points[i].append(j)
                else:
                    self.__points[i].append(j - 2)

        self.recalculate_cords()

        for layer_number in range(len(NNStructure)):
            layer = NeuralLayer(self.__main_graph_frame, self)
            shared_line_cords = None
            if self.__shared_line_cords_tuples:
                shared_line_cords = self.__shared_line_cords_tuples[layer_number]
            if layer_number < self.__number_of_layers - 1:
                layer.initialize(layer_number, self.__layer_points_values[layer_number], self.__weights[layer_number],
                                 self.__bias[layer_number], None, shared_line_cords)
            else:
                layer.initialize(layer_number, self.__layer_points_values[layer_number], None,
                                 None, None, shared_line_cords)
            self.__neural_layers.append(layer)

        # Prepočítanie súradníc podľa zodpovedajúcich dát
        self.broadcast_changes()
        self.__main_graph_frame.initialize(NNStructure, self.__neural_layers)

    def recalculate_cords(self, starting_layer=0):
        '''
        Popis
        --------
        Prepočíta súradnice bodov na jednotlivých vrstvách na základe nastavených váh.
        '''
        for layer_number in range(starting_layer, self.__number_of_layers):
            if layer_number < self.__number_of_layers - 1:

                self.__layer_points_values[layer_number + 1][:] = self.apply_weights_and_biases(
                    self.__layer_points_values[layer_number],
                    layer_number).transpose().tolist()

                # Ak existuje polygon
                if self.__polygon:
                    self.__polygon_cords[layer_number + 1][:] = self.apply_weights_and_biases(
                        self.__polygon_cords[layer_number], layer_number).transpose().tolist()
                    self.asign_shared_cord_tuples(layer_number + 1)
            else:
                break

    def apply_weights_and_biases(self, cords, layer_number):
        # Transponované súradnice bodov, aby ich bolo možné násobiť pomocou maticového násobenia.
        cord_arr = np.array(cords).transpose()
        # Predstavuje hodnoty váh pre danú vrstvu
        weight_vec = np.array(self.__weights[layer_number])
        # Násobenie matíc. Výsledkom sú súradnice bodov na nasledujúcej vrstve. K týmto hodnotám je však
        # potrebné priratať hodnotu bias. To sa uskutoční v rámci cyklu.
        tmp = cord_arr.dot(weight_vec)
        vec = np.array(self.__bias[layer_number])
        result = np.empty_like(tmp)

        for i in range(tmp.shape[0]):
            result[i, :] = tmp[i, :] + vec
        result = np.maximum(result, 0)
        return result

    def add_point(self, *args):
        self.__number_of___points += 1
        for cord in range(len(self.__points)):
            self.__points[cord].append(args[cord])
        print(self.__layer_points_values)

    def test(self):
        print('starting test')
        self.recalculate_cords()

    def asign_shared_cord_tuples(self, layer_number):
        tmpArr = np.array(self.__polygon_cords[layer_number]).transpose()
        tmp = []
        for edge in self.__polygon_edges:
            tmp.append((tmpArr[edge[0]], tmpArr[edge[1]]))
        self.__shared_line_cords_tuples[layer_number][:] = tmp

    def broadcast_changes(self, start_layer=0):
        self.__main_graph_frame.apply_changes(start_layer)


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
        '''
        :param parent: nadradený tkinter widget
        :type parent: tk.Widget
        :param logic_layer: odkaz na logickú vrstvu
        :type logic_layer: GraphLogicLayer
        '''
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)

        self.__logic_layer = logic_layer
        self.__number_of_layers = 0

        self.__NNStructure = []
        # self.__layers_points = []
        # self.__layers_weights = []
        # self.__layers_biases = []

        self.__neural_layers = None

        self.__name_to_order_dict = {}
        self.__order_to_name_dict = {}

        self.__active_layers = []
        self.__active_layers_dict = {}

        self.__shared_line_cords_tuples = None

        self.CalculationRunning = False

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

    def initialize(self, NNStructure: list, neural_layers: list):
        '''
        Popis
        --------
        Inicializačná funkcia. Inicializuje všetky potrbné komponenty tejto vrstvy. Na začiatku funkcie vyčistí vrstvy,
        ak sa nejaké nachádzali medzi aktívnymi vrstvami.
        Vytvorí predbežný zoznam názvov jednotlivých vrstiev. Po inicializácií AddRemoveComboboxFrame budú získane
        unikátne mená, ktoré sa použijú ako kľúče v slovníku.

        Na základe unikátnych mien je vytvorený slovník, ktorý prevádza meno vrstvy na jej poradové číslo a spätný
        slovník, ktorý prvádza poradové číslo na názov vrstvy.

        Sú priradené referencie na body, váhy a biasy.

        Parametre
        --------
        :param NNStructure:
        [[počet neuronov vo vrstve 0],...,[počet neuronov vo vrstve n]] - poradie vnoreného listu určuje poradové číslo
                                                                          vrstvy
        :type NNStructure: list

        :param layer_points_ref:
        [[vrstva 0],...,[vrstva n]] - poradie prvého vnoreného listu určuje poradové číslo vrstvy
        [[[sur 0],...,[sur n]]] - v rámci vnoreného listu, ktorý je určený číslom strany, sú v rámci tohto vnoreného
                                  listu poradím určené jednotlivé súradnice.
        :type layer_points_ref: list

        :param weights_ref:
        [[vrstva 0],...,[vrstva n]] - poradie prvého vnoreného listu určuje poradové číslo vrstvy
        [[[začiatočný neurón 0],...,[začiatočný neurón n]]] - poradie druhého vnoreného listu určuje poradové číslo
                                                              neurónu na príslušnej vrstve
        [[[váha koncový neurón 0,...,váha koncový neurón n]] - poradie v rámcie druhého vnoreného listu predstavuje
                                                               poradové číslo neurónu na nasledujúcej vrstve
        :type weights_ref: list

        :param bias_ref: obdobne ako weights_ref
        :type bias_ref: list
        '''

        # Zmazanie vrstiev, ak sa nejaké nachádali medzi aktívnymi vrstvami.
        for layer in self.__active_layers_dict.values():
            layer.clear()

        # Vyčistenie slovníkov.
        self.__order_to_name_dict = {}
        self.__name_to_order_dict = {}

        self.__active_layers = []
        self.__active_layers_dict = {}

        self.__NNStructure = NNStructure
        self.__neural_layers = neural_layers
        self.__input_frame.initialize(NNStructure[0][0])
        self.__number_of_layers = len(NNStructure)

        # Vytvorenie predbežného zoznamu názvov vrstiev.
        layer_name_list = []
        for i in range(self.__number_of_layers):
            layer_name_list.append('Layer{}'.format(i))

        # Inicializácia AddRemoveComboboxFrame. Funkcia navracia list unikátnych názvov vrstiev.
        # Unikátne názvy su použité ako kľúče v slovníku.
        unique_name_list = self.__add_graph_list_frame.initialize(layer_name_list, self.show_layer, 'Add layer', True,
                                                                  'Select layer')
        for i, layerName in enumerate(unique_name_list):
            self.__neural_layers[i].layer_name = layerName
            self.__order_to_name_dict[i] = layerName
            self.__name_to_order_dict[layerName] = i

        if len(self.__active_layers) < self.__number_of_layers:
            self.__add_graph_list_frame.pack(side='right', fill='y', expand=True)
        self.show_layer((0, 'Layer0'))

    def apply_changes(self, starting_layer: int = 0):
        '''
        Popis
        --------
        Na základe parametra starting_layer, zavolá pre aktívne vrstvy, ktorých poradové číslo je väčsie ako hodnota
        starting_layer, metódu na aplikovanie zmien na týchto vrstách.

        Parametre
        --------
        :param starting_layer: int
        - poradie vrstvy, od ktorej je potrebné aplikovať zmeny.
        '''
        if not self.CalculationRunning:
            self.CalculationRunning = True
            updated_layer = [layer_number for layer_number in self.__active_layers if layer_number >= starting_layer]
            for layer_number in updated_layer:
                self.__active_layers_dict[layer_number].apply_changes()
            self.CalculationRunning = False

    def show_layer(self, layer_tuple: tuple):
        '''
        Popis
        --------
        Metóda na základe parametra obdržaného z triedy AddRemoveCombobox vytvorí a následne zobrazí zvolenú vrstvu.

        Parametre
        --------
        :param layer_tuple:
        (poradové číslo vrstvy ,názov vrstvy) - obashuje hodnotu z triedy AddRemoveCombobox
        '''
        layer_name = layer_tuple[1]
        layer_number = self.__name_to_order_dict[layer_name]

        # Otestuje, či je číslo vrstvy valídne.
        if 0 <= layer_number < self.__number_of_layers:
            layer_to_show = None

            # Ak nejde o poslednú vrstvu (posledná vrstva má iné inicializačné údaje) je vrstva inicializovaná aj s
            # parametrami referencií na váhy a biasy v danej vrstve
            if layer_number < self.__number_of_layers:
                layer_to_show = self.__neural_layers[layer_number]

                layer_to_show.show(self.__scroll_frame.Frame)

            layer_to_show.pack(side='left', fill=tk.BOTH, expand=True)
            # Po zobrazení vrstvy, je odkaz na túto vrstvu vložený do slovníka aktívnych vrstiev, kde je kľúčom poradové
            # číslo vrstvy. Ďalej je poradové číslo vrstvy vložené aj do listu aktívnych vrstiev, ktorý sa využíva pri
            # efektívnejšom updatovaní vykresľovaných grafov.
            self.__active_layers_dict[layer_number] = layer_to_show
            self.__active_layers.append(layer_number)
            self.__add_graph_list_frame.hide_item(layer_name)

            # Ak je počet aktívnych vrstiev rovný celkovému počtu vrstiev je skrytý panel pre pridávanie nových vrstiev.
            if len(self.__active_layers) == self.__number_of_layers:
                self.__add_graph_list_frame.pack_forget()

    def hide_layer(self, layer_number: int):
        '''
        Popis
        --------
        Skryje vrstvu, podľa jej poradového čísla

        Parametre
        --------
        :param layer_number: číslo vrstvy, ktorá má byť skrytá
        :type layer_number: int
        '''
        if layer_number in self.__active_layers:
            layer_name = self.__order_to_name_dict[layer_number]
            layer = self.__active_layers_dict.pop(layer_number)
            layer.clear()
            self.__active_layers.remove(layer_number)
            self.__add_graph_list_frame.show_item(layer_name)
            if len(self.__active_layers) < self.__number_of_layers:
                self.__add_graph_list_frame.pack(side='right', fill='y', expand=True)

    def show_layer_options_frame(self, layer_number, config):
        self.__input_frame.initialize_with_layer_config(self.__neural_layers[layer_number], config)


class InputDataFrame(tk.LabelFrame):
    def __init__(self, parent, logicalLayer: GraphLogicLayer, *args, **kwargs):
        '''
        Popis
        --------
        Obsahuje ovladacie prvky pre jednotlivé vrstvy. V rámci nej je možne navoliť zobrazované súradnice ako aj
        povoliť zobrazenie mriežky, ak je to možné. Je možné aj zvoliť redukciu priestoru a zobraziť požadovaný
        PCA komponent alebo použiť metódu t-SNE.
        V spodnej časti panelu sa budú zobrazovať informácie o rozkliknutom bode.

        :param parent: nadradený tkinter Widget
        :param logicalLayer: odkaz na logickú vrstvu grafu
        '''
        tk.LabelFrame.__init__(self, parent, width=285, *args, **kwargs)
        self.__graph_logic = logicalLayer
        self.__layer_number_dimension = 3
        self.pack_propagate(0)
        self.__cords_entries_list = []
        self.__labels_entries_list = []
        self.__entries_list = []

        self.__options_wrapper = tk.Frame(self)
        self.__options_wrapper.pack(fill='x')
        self.__layer_options_frame = tk.LabelFrame(self.__options_wrapper)
        self.__layer_name_label = tk.Label(self.__layer_options_frame, text='Layer name', relief='raised')

        self.__cords_choose_labels_frame = tk.Frame(self.__layer_options_frame)

        self.__cords_choose_title = tk.Label(self.__cords_choose_labels_frame, text='Visible cords')

        self.__possible_cords_label = tk.Label(self.__cords_choose_labels_frame)

        for i in range(3):
            rewritable_label = RewritableLabel(self.__cords_choose_labels_frame, i, self.validate_cord_entry,
                                               'Suradnica {}:'.format(i), '-')
            self.__cords_entries_list.append(rewritable_label)
            rewritable_label.set_entry_width(3)

        self.__label_choose_labels_frame = tk.LabelFrame(self.__layer_options_frame)

        self.__label_choose_title = tk.Label(self.__label_choose_labels_frame, text='Label names')

        label_name = ['Label X', 'Label Y', 'Label Z']
        for i in range(3):
            rewritable_label = RewritableLabel(self.__label_choose_labels_frame, i, self.validate_label_entry,
                                               '{} axe:'.format(label_name[i]), label_name[i])
            self.__labels_entries_list.append(rewritable_label)

        self.__graph_view_options_frame = tk.Frame(self.__layer_options_frame)

        self.__graph_view_title = tk.Label(self.__graph_view_options_frame, text='Graph view options')

        self.__lock_view = tk.BooleanVar()
        self.__lock_view_check = tk.Checkbutton(self.__graph_view_options_frame, text='Lock view', command=self.on_lock_view_check, variable=self.__lock_view)

        self.__3d_graph = tk.BooleanVar()
        self.__3d_graph_check = tk.Checkbutton(self.__graph_view_options_frame, text='3D view', command=self.on_3d_graph_check, variable=self.__3d_graph)

        self.__show_polygon_value = tk.BooleanVar()
        self.__show_polygon_check = tk.Checkbutton(self.__graph_view_options_frame, text='Show polygon', command=self.on_show_polygon_check, variable=self.__show_polygon_value)

        # var = tk.BooleanVar()
        # check = tk.Checkbutton(self, text='skus', variable=var)
        # print(var.get())
        # check.select()
        # print(var.get())
        # check.pack()

        self.__active_layer = None
        self.__changed_config = None

        but1 = tk.Button(self, text='Add point', command=self.add_point)
        but1.pack()

        but2 = tk.Button(self, text='Test', command=self.__graph_logic.test)
        but2.pack()

        but3 = tk.Button(self, text='New initilization', command=self.new_init)
        but3.pack()


    def on_lock_view_check(self):
        if self.__changed_config:
            self.__changed_config['locked_view'] = self.__lock_view.get()
            self.__active_layer.use_config()

    def on_show_polygon_check(self):
        if self.__changed_config:
            self.__changed_config['show_polygon'] = self.__show_polygon_value.get()
            self.__active_layer.use_config()

    def on_3d_graph_check(self):
        if self.__changed_config:
            self.__changed_config['draw_3d'] = self.__3d_graph.get()
            self.__active_layer.use_config()

    def validate_cord_entry(self, id, value):
        try:
            if not (0 <= int(value) < self.__changed_config['number_of_dimensions']):
                self.__cords_entries_list[id].set_entry_text('err')
                return False
            self.__cords_entries_list[id].set_variable_label(value)
            self.__cords_entries_list[id].show_variable_label()
            self.__changed_config['visible_cords'][id] = int(value)
            self.__changed_config['cords_change'] = True
            self.__active_layer.use_config()
            return True
        except ValueError:
            self.__cords_entries_list[id].set_entry_text('err')
            return False

    def validate_label_entry(self, id, value):
        self.__labels_entries_list[id].set_variable_label(value)
        self.__labels_entries_list[id].show_variable_label()
        self.__changed_config['axis_labels'][id] = value
        self.__active_layer.use_config()

    def new_init(self):
        self.__graph_logic.initialize([[2], [2], [2]])

    def initialize(self, number_of_inputs: int):
        self.__changed_config = None
        self.__active_layer = None
        self.hide_all()

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

    def hide_all(self):
        self.__options_wrapper.pack_forget()
        self.__layer_options_frame.pack_forget()
        self.__layer_name_label.pack_forget()
        self.__cords_choose_labels_frame.pack_forget()
        self.__label_choose_labels_frame.pack_forget()
        self.__graph_view_options_frame.pack_forget()
        self.__cords_choose_title.pack_forget()
        self.__possible_cords_label.pack_forget()
        for i in range(3):
            self.__cords_entries_list[i].pack_forget()
            self.__labels_entries_list[i].pack_forget()

        self.__label_choose_title.pack_forget()
        self.__graph_view_title.grid_forget()
        self.__lock_view_check.grid_forget()
        self.__3d_graph_check.grid_forget()
        self.__show_polygon_check.grid_forget()


    def initialize_with_layer_config(self, neural_layer, config):
        self.hide_all()
        self.__active_layer = neural_layer
        self.__changed_config = config
        self.__options_wrapper.pack(side='top', fill='x')
        self.__layer_options_frame.pack(fill='x')
        self.__layer_name_label.configure(text=config['layer_name'])
        self.__layer_name_label.pack(fill='x')
        self.__cords_choose_labels_frame.pack(fill='x')
        self.__label_choose_labels_frame.pack(fill='x')
        self.__graph_view_options_frame.pack(fill='x')

        self.__cords_choose_title.pack()

        self.__possible_cords_label.configure(text='Possible cords: 0-{}'.format(config['number_of_dimensions'] - 1))
        self.__possible_cords_label.pack()

        number_of_possible_dim = config['max_visible_dim']

        for i in range(number_of_possible_dim):
            cord_entry = self.__cords_entries_list[i]
            cord_entry.set_variable_label(config['visible_cords'][i])
            cord_entry.pack(fill='x')

        self.__label_choose_title.pack(fill='x')

        for i in range(number_of_possible_dim):
            label_entry = self.__labels_entries_list[i]
            label_entry.set_variable_label(config['axis_labels'][i])
            label_entry.pack(fill='x')

        self.__graph_view_title.grid(row=0, column=1, columnspan=2, sticky='we')

        if config['locked_view']:
            self.__lock_view_check.select()
        else:
            self.__lock_view_check.deselect()
        self.__lock_view_check.grid(row=1, column=0, sticky='w')

        if number_of_possible_dim >= 3:
            if config['draw_3d']:
                self.__3d_graph_check.select()
            else:
                self.__3d_graph_check.deselect()

            self.__3d_graph_check.grid(row=2, column=0, sticky='w')

        if config['possible_polygon']:
            if config['show_polygon']:
                self.__show_polygon_check.select()
            else:
                self.__show_polygon_check.deselect()
            self.__show_polygon_check.grid(row=3, column=0, sticky='w')


class NeuralLayer:
    def __init__(self, mainGraph: MainGraphFrame, logicLayer: GraphLogicLayer, *args, **kwargs):
        '''
        Popis
        --------
        Trieda predstavuje vrstvu neurónovej siete. V rámci nej budú do grafu volené zobrazované súradnice bodov.
        Bude uskutočňovať PCA redukciu priestoru.

        Aribúty
        --------
        :var self.__graph_frame: udržuje v sebe triedu GraphFrame, ktorá vytvá zobrazovací graf a ovládač váh
        :var self.__layer_name: názov vrstvy
        :var self.__layer_number: poradové číslo vrstvy
        :var self.__point_cords: referencia na súradnice bodov v danej vrstve. (hodnoy sa menia v GraphLogicLayer)
        :var self.__displayed_cords: obsahuje súradnice, ktoré budú zobrazené v grafe. Referenciu na tento objekt
                                     obsahuje aj PlotingFrame

        Parametre
        --------
        :param parent: nadradený tkinter Widget
        :param mainGraph: odkaz na MainGraph
        :param logicLayer: odkaz na logicku vrstvu GraphLogicLayer
        :param args:
        :param kwargs:
        '''
        self.__layer_wrapper = None

        self.__layer_options_container = None

        self.__options_button = None
        self.__hide_button = None

        self.__computation_in_process = False

        self.__shared_polygon_cords_tuples = None
        self.__displayed_lines_cords = None

        self.__layer_config = {}

        self.__main_graph_frame = mainGraph
        self.__logic_layer = logicLayer
        self.__layer_name = ''
        self.__layer_number = -1
        self.__number_of_dimension = -1
        self.__point_cords = []
        self.__displayed_cords = []
        self.__used_cords = []
        self.__axis_labels = []

        self.__layer_weights = []
        self.__layer_biases = []

        self.__visible = False

    def pack(self, *args, **kwargs):
        if self.__visible:
            self.__layer_wrapper.pack(*args, **kwargs)

    def initialize(self, layer_number: int, layer_point_cords: list, layer_weights: list = None,
                   layer_bias: list = None, layer_name: str = None, shared_polygon_cords=None):
        '''
        Parametre
        --------
        :param layer_number: poradové číslo vrstvy
        :param layer_point_cords: refrencia na zoznam súradníc bodov pre danú vrstvu
        :param layer_weights: referencia na hodnoty váh v danej vrstve. Hodnoty sú menené v controllery a používajú sa
                              pri prepočítavaní súradnic v GraphLogicLayer.
        :param layer_bias: referencia na hodnoty bias v danej vrstve. Podobne ako pr layer_weights
        :param layer_name: názov vrstvy, je unikátny pre každú vrstvu, spolu s poradovým číslom sa používa ako ID.
        '''
        # Počet dimenzií, resp. počet súradníc zistíme podľa počtu vnorených listov.

        self.__layer_config = {}

        self.__computation_in_process = False
        self.__number_of_dimension = len(layer_point_cords)
        self.__layer_number = layer_number
        self.__layer_name = layer_name
        self.__point_cords = []
        self.__layer_weights = layer_weights
        self.__layer_biases = layer_bias

        self.__point_cords = layer_point_cords

        self.__displayed_lines_cords = []
        self.__shared_polygon_cords_tuples = shared_polygon_cords

        # Počet súradníc ktoré sa majú zobraziť určíme ako menšie z dvojice čísel 3 a počet dimenzií, pretože max počet,
        # ktorý bude možno zoraziť je max 3
        number_of_cords = min(3, self.__number_of_dimension)
        axis_default_names = ['Label X', 'Label Y', 'Label Z']
        self.__axis_labels = []
        for i in range(number_of_cords):
            self.__displayed_cords.append(self.__point_cords[i])
            self.__used_cords.append(i)
            self.__axis_labels.append(axis_default_names[i])

        self.__layer_config['cords_change'] = False
        self.__layer_config['layer_name'] = self.__layer_name
        self.__layer_config['number_of_dimensions'] = self.__number_of_dimension
        self.__layer_config['max_visible_dim'] = number_of_cords
        self.__layer_config['visible_cords'] = self.__used_cords
        self.__layer_config['axis_labels'] = self.__axis_labels
        self.__layer_config['locked_view'] = False
        if number_of_cords >= 3:
            self.__layer_config['draw_3d'] = True
        else:
            self.__layer_config['draw_3d'] = False
        if shared_polygon_cords:
            self.__layer_config['possible_polygon'] = True
        else:
            self.__layer_config['possible_polygon'] = False
        self.__layer_config['show_polygon'] = False

        if shared_polygon_cords:
            tmp1 = np.array(self.__shared_polygon_cords_tuples)[:, 0, self.__used_cords]
            tmp2 = np.array(self.__shared_polygon_cords_tuples)[:, 1, self.__used_cords]
            self.__displayed_lines_cords[:] = (list(zip(tmp1, tmp2)))
        else:
            self.__displayed_lines_cords = None

    def apply_changes(self):
        '''
        Popis
        --------
        Aplikovanie zmien po prepočítaní súradníc.
        '''
        # Je potrbné podľa navolených zobrazovaných súradníc priradiť z prepočítaných jednotlivé súradnice do súradníc
        # zobrazovaných.
        for i, used_cord in enumerate(self.__used_cords):
            self.__displayed_cords[i] = self.__point_cords[used_cord]
        if self.__shared_polygon_cords_tuples:
            tmp1 = np.array(self.__shared_polygon_cords_tuples)[:, 0, self.__used_cords]
            tmp2 = np.array(self.__shared_polygon_cords_tuples)[:, 1, self.__used_cords]
            self.__displayed_lines_cords[:] = list(zip(tmp1, tmp2))
        self.__graph_frame.apply_changes()

    def hide_graph_frame(self):
        '''
        Popis
        --------
        Skrytie tejto vrstvy.
        '''
        self.__main_graph_frame.hide_layer(self.__layer_number)

    def clear(self):
        '''
        Popis
        --------
        Používat sa pri mazaní. Vyčistí premenné a skryje danú vrstvu.
        '''
        if self.__visible:
            self.__graph_frame.clear()
            self.__layer_options_container.destroy()
            self.__options_button.destroy()
            self.__layer_wrapper.destroy()
            self.__hide_button.destroy()
            self.__layer_options_container = None
            self.__options_button = None
            self.__layer_wrapper = None
            self.__hide_button = None
            self.__visible = False

    def hide(self):
        self.clear()

    def show(self, parent, *args, **kwargs):
        if self.__visible:
            self.clear()

        self.__layer_wrapper = tk.LabelFrame(parent)

        self.__layer_options_container = tk.Frame(self.__layer_wrapper)
        self.__layer_options_container.pack(side='top', fill='x')

        self.__options_button = ttk.Button(self.__layer_options_container, command=self.show_layer_options, text='Options')
        self.__options_button.pack(side='left')
        self.__hide_button = ttk.Button(self.__layer_options_container, command=self.hide_graph_frame, text='Hide')
        self.__hide_button.pack(side='right')

        self.__graph_frame = GraphFrame(self, self.__layer_wrapper, *args, **kwargs)
        self.__graph_frame.pack()

        number_of_cords = min(3, self.__number_of_dimension)

        self.__graph_frame.initialize(self, number_of_cords, self.__layer_name, self.__displayed_cords,
                                      self.__layer_weights, self.__layer_biases, self.__displayed_lines_cords)
        self.__graph_frame.pack(fill='both', expand=True)

        self.__visible = True

        self.use_config()
        self.apply_changes()

    def signal_change(self):
        if not self.__computation_in_process:
            self.__computation_in_process = True
            self.__logic_layer.recalculate_cords(self.__layer_number)
            self.__logic_layer.broadcast_changes(self.__layer_number + 1)
            self.__computation_in_process = False

    def use_config(self):
        if self.__visible:
            if self.__layer_config['cords_change']:
                print('zmenene')
                self.apply_changes()
                self.__layer_config['cords_change'] = False
            self.__graph_frame.apply_config(self.__layer_config)

    def show_layer_options(self):
        self.__main_graph_frame.show_layer_options_frame(self.__layer_number, self.__layer_config)

    def __del__(self):
        print('neural layer destroyed')

    @property
    def layer_name(self):
        return self.__layer_name

    @layer_name.setter
    def layer_name(self, name):
        self.__layer_config['layer_name'] = name
        self.__layer_name = name

    @property
    def config(self):
        return self.__layer_config

class GraphFrame(tk.LabelFrame):
    def __init__(self, neural_layer: NeuralLayer, parent, *args, **kwargs):
        '''
        Popis
        --------
        Obaľovacia trieda. Zodpovedá za vytvorenie vykaresľovacieho grafu a ovládača váh.

        Atribúty
        --------
        :var self.__graph: vykresľovacia trieda, zodpoveda za vykresľovanie bodov na vrstve
        :var self.__weight_controller: zmena koeficientov váh v danej vrstve

        Parametre
        --------
        :param neural_layer: odkaz na NeuralLayer, pod ktroú patrí daný GraphFrame
        :param parent: nadradený tkinter Widget
        '''
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.__neural_layer = neural_layer

        self.__graph = PlotingFrame(self, self)
        self.__weight_controller = LayerWeightControllerFrame(self, self)

    def initialize(self, neuralLayer: int, numOfDimensions: int, layer_name: str, pointCords: list, layer_weights: list,
                   layerBias: list, shared_polygon_layer_cords):
        self.__neural_layer = neuralLayer
        self.__graph.initialize(numOfDimensions, pointCords, layer_name, shared_polygon_layer_cords)
        self.__weight_controller.initialize(layer_weights, layerBias)

        self.__graph.pack(side=tk.TOP)
        self.__weight_controller.pack(side=tk.TOP, fill='both', expand=True)

    def apply_changes(self):
        self.__graph.update_graph()

    def hide_graph_frame(self):
        self.__neural_layer.hide_graph_frame()

    def clear(self):
        '''
        Popis
        --------
        Vyčistenie pri mazaní okna.
        '''
        self.pack_forget()
        self.__weight_controller.clear()
        self.__graph.clear()
        self.__weight_controller = None
        self.__neural_layer = None
        self.__graph = None

    def controller_signal(self):
        '''
        Popis
        --------
        Posúva signál o zmene váhy neurónovej vrstve.
        '''

        self.__neural_layer.signal_change()

    def apply_config(self, config):
        self.__graph.draw_polygon = config['show_polygon']
        self.__graph.locked_view = config['locked_view']
        self.__graph.graph_labels = config['axis_labels']
        self.__graph.is_3d_graph = config['draw_3d']
        self.apply_changes()


class PlotingFrame:
    def __init__(self, parent, main_graph_frame, *args, **kwargs):
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
        self.__main_graph_frame = main_graph_frame

        self.__graph_container = tk.LabelFrame(self.__plot_wrapper_frame, relief=tk.FLAT)

        self.__figure = Figure(figsize=(4, 4), dpi=100)
        self.__canvas = FigureCanvasTkAgg(self.__figure, self.__graph_container)
        self.__canvas.draw()
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
        self.__ani = animation.FuncAnimation(self.__figure, self.update_changed, interval=100)

    def initialize(self, numberOfDim: int, pointCords: list, layerName: str, shared_polygon_layer_cords):
        if shared_polygon_layer_cords:
            self.__line_cords_tuples = shared_polygon_layer_cords
            self.__draw_polygon = True
        self.__change_in_progress = False
        self.__cords = pointCords
        self.__graph_container.pack(side=tk.TOP)
        self.set_graph_dimension(numberOfDim)
        self.__graph_title = layerName

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
            self.__ani.event_source.start()

    def redraw_graph(self):
        if self.__locked_view:
            tmpX = self.__axis.get_xlim()
            print(tmpX)
            tmpY = self.__axis.get_ylim()
            if self.__number_of_dim == 3:
                tmpZ = self.__axis.get_zlim()
        else:
            print('teraz',self.__axis.get_xlim())
        self.__axis.clear()
        self.__axis.grid()

        if self.__draw_polygon:
            if self.__number_of_dim >= 3:
                for hrana in self.__line_cords_tuples:
                    xs = hrana[0][0], hrana[1][0]
                    ys = hrana[0][1], hrana[1][1]
                    zs = hrana[0][2], hrana[1][2]
                    line = plt3d.art3d.Line3D(xs, ys, zs, color='black', linewidth=1, alpha=0.3)
                    self.__axis.add_line(line)
            if self.__number_of_dim == 2:
                for hrana in self.__line_cords_tuples:
                    xs = hrana[0][0], hrana[1][0]
                    ys = hrana[0][1], hrana[1][1]
                    self.__axis.plot(xs, ys, linestyle='-', color='black', linewidth=1, alpha=0.5)

        if self.__number_of_dim >= 3:
            if len(self.__cords) > 2:
                self.__axis.scatter(self.__cords[0], self.__cords[1], self.__cords[2])
            else:
                self.__axis.scatter(self.__cords[0], self.__cords[1])
            self.__axis.set_zlabel(self.__graph_labels[2])
        else:
            if len(self.__cords) == 1:
                zero_list = np.zeros(len(self.__cords[0]))
                self.__axis.scatter(self.__cords[0], zero_list)
            else:
                self.__axis.scatter(self.__cords[0], self.__cords[1])
        self.__axis.set_title(self.__graph_title)
        self.__axis.set_xlabel(self.__graph_labels[0])
        if len(self.__cords) != 1:
            self.__axis.set_ylabel(self.__graph_labels[1])

        if self.__locked_view:
            self.__axis.set_xlim(tmpX)
            print(self.__axis.get_xlim())
            self.__axis.set_ylim(tmpY)
            if self.__number_of_dim == 3:
                self.__axis.set_zlim(tmpZ)

    def set_graph_dimension(self, dimension: int):
        if dimension >= 3:
            self.__draw_3D = True
        else:
            self.__draw_3D = False
        text = ''
        self.__figure.clf()

        if self.__draw_3D:
            self.__graph_container.pack()
            self.__axis = self.__figure.add_subplot(111, projection='3d')
            self.__number_of_dim = 3
            text = 'Make 2D'
            for item in self.__toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack_forget()
                else:
                    item.pack(pady=(4, 5))
        else:
            self.__axis = self.__figure.add_subplot(111)
            self.__number_of_dim = 2
            self.__graph_container.pack()
            text = 'Make 3D'
            for item in self.__toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack(side='left')

        # self.__graph_title = 'Graph {}D'.format(self.NumberOfDim)
        self.__changed = True
        self.__ani.event_source.start()

    def clear(self):
        print('Cistime plott')
        self.__toolbar.destroy()
        self.__canvas.get_tk_widget().destroy()
        self.__plot_wrapper_frame.destroy()
        self.__figure.delaxes(self.__axis)
        self.__graph_container.destroy()
        self.__figure.clf()
        self.__axis.cla()
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


class Testovacia():
    def __init__(self, ref):
        self._tmp = []
        for i in range(len(ref)):
            self._tmp.append(ref[i])

    def zmazaj(self):
        self.destroy()

    def __del__(self):
        print('mazem')


class Polygon:
    def __init__(self, lower_list, upper_list, divide_list=[2, 2, 2]):
        numberOfCords = min(len(lower_list), len(upper_list))
        self.Peaks = [[] for x in range(numberOfCords)]
        self.Edges = []
        max_size = []
        cord_sign = []
        for i in range(numberOfCords):
            max_size.append(math.fabs(lower_list[i] - upper_list[i]))
            cord_sign.append(1 if lower_list[i] < upper_list[i] else -1)

        new_divide = []
        if len(divide_list) != numberOfCords:
            number_of_divide = min(len(divide_list), numberOfCords)
            for i in range(number_of_divide):
                new_divide.append(divide_list[i])
                if new_divide[i] < 1:
                    new_divide[i] = 1
            for i in range(numberOfCords - number_of_divide):
                new_divide.append(1)
        else:
            new_divide = divide_list

        offset_list = []
        for i in range(numberOfCords):
            offset_list.append(cord_sign[i] * (max_size[i] / new_divide[i]))

        if numberOfCords == 3:
            for z in range(new_divide[2] + 1):
                for y in range(new_divide[1] + 1):
                    for x in range(new_divide[0] + 1):
                        pointNumber = z * ((new_divide[1] + 1) * (new_divide[0] + 1)) + y * (new_divide[0] + 1) + x
                        self.Peaks[0].append(lower_list[0] + x * offset_list[0])
                        self.Peaks[1].append(lower_list[1] + y * offset_list[1])
                        self.Peaks[2].append(lower_list[2] + z * offset_list[2])
                        if x != new_divide[0]:
                            self.Edges.append([pointNumber, pointNumber + 1])
                        if y != new_divide[1]:
                            self.Edges.append([pointNumber, pointNumber + (new_divide[0] + 1)])
                        if z != new_divide[2]:
                            self.Edges.append([pointNumber, pointNumber + (new_divide[1] + 1) * (new_divide[0] + 1)])
        else:
            for y in range(new_divide[1] + 1):
                for x in range(new_divide[0] + 1):
                    pointNumber = y * (new_divide[0] + 1) + x
                    self.Peaks[0].append(lower_list[0] + x * offset_list[0])
                    self.Peaks[1].append(lower_list[1] + y * offset_list[1])
                    if x != new_divide[0]:
                        self.Edges.append([pointNumber, pointNumber + 1])
                    if y != new_divide[1]:
                        self.Edges.append([pointNumber, pointNumber + (new_divide[0] + 1)])


app = VisualizationApp()
app.mainloop()
