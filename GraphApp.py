import ntpath
import threading
import time
import tkinter as tk
from tkinter import Widget

import matplotlib.colors as mcolors
import pandas as pd
from sklearn import preprocessing
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from tensorflow import keras

from AdditionalComponents import *
from PlottingAndControlComponents import *

LARGE_FONT = ('Verdana', 12)
np.seterr(divide='ignore', invalid='ignore')


def load_model(initial_dir='.'):
    return tk.filedialog.askopenfilename(initialdir=initial_dir, title="Select file",
                                         filetypes=(("Keras model", "*.h5"),))


def load_input():
    return tk.filedialog.askopenfilename(initialdir='.', title="Select file", filetypes=(("Text files", ".txt .csv"),))


def save_model(initial_dir='.', initial_file=''):
    return tk.filedialog.asksaveasfilename(initialdir=initial_dir, initialfile=initial_file, title="Select file",
                                           defaultextension='.h5',
                                           filetypes=(("Keras model", "*.h5"),))


class VisualizationApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Spúšťacia trieda. Je obalom celeje aplikácie. Vytvorí programové okno, na celú obrazovku. Táto trieda dedí od
        objektu Tk z build in knižnice tkinter.

        Atribúty
        ----------------------------------------------------------------------------------------------------------------
        :var self.frames: je to dictionary, ktorý obsahuje jednotlivé hlavné stránky aplikácie. Kľúčom k týmto stránkam
                          sú prototypy daných stránok
        """
        # Konštruktor základnej triedy.
        tk.Tk.__init__(self, *args, **kwargs)

        # Zobrazenie okna na (takmer) celú obrazovku. Prvé dva čísla určujú rozmery obrazovky. Konštatny pri nich slúžia
        # na ich čiastočné vycentrovanie.
        super().geometry('%dx%d+0+0' % (super().winfo_screenwidth() - 8, super().winfo_screenheight() - 70))
        self.title('Bakalarka')

        container = ttk.Frame(self)
        container.pack(side='top', fill='both', expand=True)

        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.__frames = {}
        # Vytvorenie všetkých podstránok v rámci cyklu a ich pridelenie do dict. Kľúčom v dict je ich prototyp.
        for F in (GraphPage,):
            frame = F(container)
            self.__frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')
        # Zobrazenie prvej stránky.
        self.show_frame(GraphPage)

    def show_frame(self, controller):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Zobrazenie požadovanej stránky

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param controller: ProtoypStranky
        """
        frame = self.__frames[controller]
        frame.tkraise()


class GraphPage(tk.Frame):
    def __init__(self, parent):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Podstránka, na ktorej je zobrazovaný rámec s grafmi, váhami a okno s detailmi vrstvy.

        Atribúty
        ----------------------------------------------------------------------------------------------------------------
        :var self.__logic_layer: Referencia na logiku aplikácie.
        :var self.__keras_model: Načítaný model, jeho referencia je zaslaná do logic layer, kde sa menia váhy.
                                 Používa sa aj pri ukladaní.
        :var self.__file_path:   Cesta k súboru pre lepší konfort pri načítaní a ukladaní.
        :var self.__file_name:   Meno súboru pre lepší konfort pri ukladaní.
        :var self.__info_label:

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param parent: nadradený tkinter Widget
        """
        tk.Frame.__init__(self, parent)
        self.__logic_layer = GraphLogicLayer(self)
        self.__keras_model = None
        self.__file_path = '.'
        self.__file_name = ''
        wrapper = tk.Frame(self)
        wrapper.pack(fill='x')

        open_model_btn = ttk.Button(wrapper, text='Open model', command=self.try_open_model)
        open_model_btn.pack(side='left')
        load_points_btn = ttk.Button(wrapper, text='Load points', command=self.try_load_points)
        load_points_btn.pack(side='left')
        save_model_btn = ttk.Button(wrapper, text='Save model', command=self.save_model)
        save_model_btn.pack(side='right')
        self.__info_label = tk.Label(wrapper, text='Load keras model!', fg='orange')
        self.__info_label.pack(side='left')
        self.open_model('modelik.h5')
        self.load_points('input_data_2d.txt')

    def try_open_model(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Načítanie vybraného modelu, pokiaľ bola zvolená nejaká cesta k súboru.
        """
        file_path = load_model()
        if file_path != '':
            self.open_model(file_path)

    def open_model(self, filepath):
        """
        Popis:
        ----------------------------------------------------------------------------------------------------------------
        Rozdelenie zadanej cesty k súboru na absolútnu cestu a názov súboru.
        Načítanie súboru na základe cesty.
        Inicializácia logickej vrstvy, načítaným modelom.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param filepath: aboslutná cesta k súboru.
        """
        self.__file_path, self.__file_name = ntpath.split(filepath)
        self.__keras_model = keras.models.load_model(filepath)
        self.__logic_layer.initialize(self.__keras_model)
        self.__info_label.pack_forget()

    def try_load_points(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Získanie adresy k súboru s hodnotami bodov. Ak nie je načítaný model, zobrazí sa informácia o chybe.
        """
        if self.__keras_model is not None:
            file_path = load_input()
            if file_path != '':
                self.load_points(file_path)
        else:
            self.__info_label.configure(text='You have to load model first!', fg='red')
            self.__info_label.pack(side='left')

    def load_points(self, filepath: str):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Načítanie bodov do modelu na základe cesty k súboru so vstupnými dátami. Ak pri načítaní bodov dôjde ku chybe,
        je táto chyba zobrazená.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param filepath: cesta k súboru
        :type filepath:  str
        """
        error_message = self.__logic_layer.load_points(filepath)
        if error_message is not None:
            self.__info_label.configure(text=error_message, fg='red')
            self.__info_label.pack(side='left')
        else:
            self.__info_label.pack_forget()

    def save_model(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Uloženie modelu.
        """
        if self.__keras_model is not None:
            file_path = save_model(self.__file_path, self.__file_name)
            if file_path != '':
                self.__file_path, self.__file_name = ntpath.split(file_path)
                self.__keras_model.save(file_path)
            self.__info_label.pack_forget()
        else:
            self.__info_label.configure(text='You have to load model first!', fg='red')
            self.__info_label.pack(side='right')


class GraphLogicLayer:
    def __init__(self, parent):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Trieda, ktorá sa stará o logiku podstaty aplikácie, inicializuje základné grafické časti aplikácie, stará sa aj
        o výpočty.

        Atribúty
        ----------------------------------------------------------------------------------------------------------------
        :var self.__graph_page:        odkaz na nadradený tkinter widget
        :var self.__main_graph_frame:  odkaz na hlavné okno, v ktorom sú vykresľované grafy pre jednotlivé vrstvy
        :var self.__input_data:        vstupné dáta, načítané zo súboru
        :var self.__points_config:     informácie o jednotlivých bodoch
        :var self.__polygon_cords:     súradnice vrcholov zobrazovanej mriežky
        :var self.__number_of_layers:  počet vrstiev neurónovej siete
        :var self.__keras_model:       načítaný zo súboru, stará sa o výpočty. Sú v ňom menené váhy. Model so zmenenými
                                       váhami je možné uložiť.
        :var self.__active_layers:     obsahuje poradové čísla jednotlivých vrstiev, neurónovej siete,
                                       ktoré sú zobrazované
        :var self.__neural_layers:     list obsahujúci všetky vrstvy siete podľa ich poradia v rámci štruktúry NN
        :var self.__monitoring_thread: vlákno sledijúce zmenu váh a následne prepočítanie a prekreslenie grafov
        :var self.__is_running:        premmenná pre monitorovacie vlákno, ktorá značí, či ešte program beží
        :var self.__changed_layer_q:   zásobnik s unikátnymi id zmenených vrstiev. ID predstavuje poradové číslo vrstvy
        :var self.__condition_var:     podmienková premenná, signalizujúca zmenu a potrebu preopočítania súradníc

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param parent: odkaz na nadradený tkinter widget, v ktorom majú byť vykreslené jednotlivé komponenty
        """
        # Grafické komponenty
        self.__graph_page = parent
        self.__main_graph_frame = MainGraphFrame(parent, self, border=1)
        self.__main_graph_frame.pack(side='bottom', fill='both', expand=True)

        # Zobrazované dáta
        self.__input_data = None
        self.__points_config = None
        self.__polygon_cords = None

        # Štruktúra siete, jednotlivé vrstvy, aktívne vrstvy pre zrýchlenie výpočtu
        self.__number_of_layers = 0
        self.__keras_model = None
        self.__active_layers = None
        self.__neural_layers = list()
        self.__keras_layers = list()

        # Vlákno sledujúce zmeny, aby sa zlepšil pocit s používania - menej sekajúce ovládanie
        self.__changed_layer_q = QueueSet()
        self.__condition_var = threading.Condition()
        self.__monitoring_thread = threading.Thread(target=self.monitor_change)

        # Spustenie monitorovacieho vlákna.
        self.__is_running = True
        self.__monitoring_thread.setDaemon(True)
        self.__monitoring_thread.start()

        # self.initialize(keras.models.load_model('modelik.h5'))

    def initialize(self, model: keras.Model):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Inicializuje hodnoty pre triedu GraphLogicLayer a tak isto aj pre triedy MainGraphFrame.
        Vytvorí triedy NeuralLayer pre každú vrstvu v modeli.
        Spustí monitorovacie vlákno.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param model: načítaný keras model
        """
        for layer in self.__neural_layers:
            layer.clear()

        self.__keras_model = model
        self.__number_of_layers = len(self.__keras_model.layers)
        self.__neural_layers = list()
        self.__keras_layers = list()
        self.__active_layers = list()

        self.__polygon_cords = None
        self.__input_data = None

        # Nastavenie inicializácia konfigu pre vstupné body.
        self.__points_config = dict()
        self.__points_config['label'] = list()
        self.__points_config['default_colour'] = list()
        self.__points_config['different_points_color'] = list()
        self.__points_config['label_colour'] = list()
        self.__points_config['active_labels'] = list()

        # Nastavenie základnej konfiguracie.
        i = 0
        for layer in self.__keras_model.layers:
            self.__keras_layers.append(layer)
            neural_layer = NeuralLayer(self, layer, i)
            neural_layer.initialize(self.__points_config)
            self.__neural_layers.append(neural_layer)
            i += 1

        self.__main_graph_frame.initialize(self.__neural_layers, self.__active_layers)

    def recalculate_cords(self, starting_layer=0):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Prepočíta súradnice bodov na jednotlivých vrstvách na základe nastavených váh.
        Nie je možné použiť výstup jednej vrstvy ako vstup ďalšej vrstvy pre zrýchlenie výpočtu, aby sa nepočítali viac
        krát veci čo už boli vypočítané. Preto je použité pre čiastočné zrýchlenie výpočtu využité viac vlakien, každé
        pre jednu vrstvu.
        """
        # jedno vlakno 0.7328296000000023 s
        # viac vlakien rychlejsie o 100ms

        # Je možné paralelizovat výpočty. Pre každú rátanú vrstvu je použité jedno vlákno.
        threads = []
        start = time.perf_counter()
        for layer_number in self.__active_layers:
            if layer_number > starting_layer:
                t = threading.Thread(target=self.set_points_for_layer, args=(layer_number,))
                t.start()
                threads.append(t)
        # Po výpočtoch je potrebné počkať na dokončenie
        for thread in threads:
            thread.join()
        end = time.perf_counter()
        print(f'Calculation time {end - start} s')

    def monitor_change(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Metóda je spustená v monitorovaciom vlákne. Vlákno beží počas celého behu programu.
        """
        # Sleduje zmeny váh a biasov na vrstvách.
        while self.__is_running:
            self.__condition_var.acquire()

            # Čaká, kým sa neobjaví zmena a potom otestuje, či je v zásobníku nejaká vrstva.
            while not self.__changed_layer_q.is_empty():
                self.__condition_var.wait()
                # Otestuje či náhodou beh programu už neskončil.
                if not self.__is_running:
                    self.__condition_var.release()
                    return
            if not self.__is_running:
                self.__condition_var.release()
                return
            # Vytvorenie kópie zásobníka. Vyčistenie zásboníka.
            actual_changed = self.__changed_layer_q.copy()
            self.__changed_layer_q.clear()
            self.__condition_var.release()

            # Aplikovanie zmien na zmeneých vrstvách. Nájdenie vrstvy, od ktorej je potrebné aplikovať zmeny.
            starting_layer_number = self.__number_of_layers
            for layer_number in actual_changed:
                if layer_number < starting_layer_number:
                    starting_layer_number = layer_number
                layer = self.__neural_layers[layer_number]
                self.set_layer_weights_and_biases(layer_number, layer.layer_weights, layer.layer_biases)
            self.recalculate_cords(starting_layer_number)
            self.broadcast_changes(starting_layer_number)
            # time.sleep(0.05)

    def get_activation_for_layer(self, input_points, layer_number):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Vráti aktiváciu pre danú vrstvu na základe vstupných dát.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param input_points: vstupné body, ktorých aktiváciu chceme získať
        :param layer_number: číslo vrstvy, ktorej výstup chceme získať
        """
        # Aktivacia na jednotlivých vrstvách. Ak je to prvá, vstupná vrstva, potom je aktivácia len vstupné hodnoty.
        if layer_number == 0:
            return input_points
        else:
            intermediate_layer_mode = keras.Model(inputs=self.__keras_model.input,
                                                  outputs=self.__keras_layers[layer_number - 1].output)
            return intermediate_layer_mode.predict(input_points)

    def set_points_for_layer(self, layer_number):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Výpočet súradníc pre vstupy na zadanej vrstve a ich priradenie. Ak je na danej vrstve zvolená aj možnosť
        zobrazenia mriežky, sú aj tieto súradnice prepočítané a priradené.

        Parametre:
        ----------------------------------------------------------------------------------------------------------------
        :param layer_number: číslo vrstvy, pre ktorú sa počíta aktivácia
        """
        # nastavenie vstupných bodov
        if self.__input_data is not None:
            self.__neural_layers[layer_number].point_cords = self.get_activation_for_layer(self.__input_data,
                                                                                           layer_number).transpose()
        if self.__neural_layers[layer_number].calculate_polygon:
            self.set_polygon_cords(layer_number)

    def set_polygon_cords(self, layer_number):
        # Výpočet aktivácie pre jednotlivé body hrán polygonu.
        if self.__polygon_cords is not None:
            start_points = self.get_activation_for_layer(self.__polygon_cords[0], layer_number).transpose()
            end_points = self.get_activation_for_layer(self.__polygon_cords[1], layer_number).transpose()
            self.__neural_layers[layer_number].polygon_cords_tuples = [start_points, end_points]

    def broadcast_changes(self, start_layer=0):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Vyžiada aplikovanie zmien a prekreslenie grafu pre aktívne vrstvy, ktoré majú poradove číslo väčšie ako zadaný
        parameter.

        Paramatre
        ----------------------------------------------------------------------------------------------------------------
        :param start_layer: poradové číslo vrstvy. Vrstvy s poradovým číslom väčším ako je toto, budú prekreslené.
        :return:
        """
        # Pre aktívne vrstvy, ktoré sú väčšie ako začiatočná vrstva sa aplikujú vykonané zmeny.
        for layer_number in self.__active_layers:
            if layer_number > start_layer:
                self.__neural_layers[layer_number].apply_changes()
                self.__neural_layers[layer_number].redraw_graph_if_active()
        self.__main_graph_frame.update_active_options_layer(start_layer)

    def redraw_active_graphs(self, start_layer=0):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Prekreslenie aktívnych vrstiev na základe ich poradového čísla.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param start_layer: poradové číslo vrstvy. Vrstvy s poradovým číslom väčším ako je toto, budú prekreslené.
        """
        for layer_number in self.__active_layers:
            if layer_number > start_layer:
                self.__neural_layers[layer_number].redraw_graph_if_active()

    def set_layer_weights_and_biases(self, layer_number, layer_weights, layer_biases):
        # Nastvaenie hodnôt a biasu priamo do keras modelu.
        self.__keras_layers[layer_number].set_weights([np.array(layer_weights), np.array(layer_biases)])

    def signal_change_on_layer(self, layer_number):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Pridá do zásobníku zmien, poradové číslo vrstvy, na ktorej došlo k zmene váh.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param layer_number: poradové číslo vrstvy, na ktorej došlo k zmene váh
        """
        # Oznámi, že došlo k zmene na vrstve. Tá je zaradená do zásobníka.
        self.__condition_var.acquire()
        self.__changed_layer_q.add(layer_number)
        self.__condition_var.notify()
        self.__condition_var.release()

    def load_points(self, filepath):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Načítanie bodov zo súboru. Je možné načítať typ .txt a .csv .

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param filepath: cesta k súboru obashujúcemu vstupy.
        """
        # Načítanie bodov zo súboru.
        # Načítané súbory môžu byť typu txt alebo csv, na základe toho sa zvolí vetva. Txt súbory by mali byť oddelené
        # medzerou.
        if self.__keras_model is not None:
            file_ext = ntpath.splitext(filepath)[1]
            if file_ext == '.txt':
                data = pd.read_csv(filepath, sep=' ', header=None)
            else:
                data = pd.read_csv(filepath, header=None)

            # Načítanie configu do premenných.
            shape_of_input = self.__keras_model.layers[0].input_shape[1]
            points_colour = self.__points_config['default_colour']
            points_label = self.__points_config['label']
            label_colour = self.__points_config['label_colour']

            # Načítanie posledného stĺpca, ktorý by mal obsahovať labels pre jednotlivé vstupy.
            labels_data = data.iloc[:, -1]

            # Testovanie, či je každej hodnote priradený label. Ak nie, návrat s chybovou hláškou.
            if labels_data.isnull().sum() != 0:
                return 'Missing label values!'

            # Hodnoty labels sú zmenené v referencií na labels z posledného stĺpca.
            points_label[:] = labels_data
            # Zvyšné stĺpce okrem posledného sú použité ako vstupné dáta
            data = data.iloc[:, 0:-1]


            # Testovanie, či sa počet features rovná rozmeru vstupu.
            if len(data.columns) == shape_of_input:
                # Zistujeme, či sú všetky hodnoty číselné, ak nie návrat s chybovou hláškou. Ak áno, sú priradené do
                # premennej
                is_column_numeric = data.apply(lambda s: pd.to_numeric(s, errors='coerce').notnull().all()).to_list()
                if False in is_column_numeric:
                    return 'Data columns contains non numeric values!'
                self.__input_data = data.to_numpy()

                # Z farieb, ktoré sa nachádzajú v premennej matplotlibu sú zvolené základné farby a potom aj ďalšie
                # farby, z ktorých sú zvolené len tmavšie odtiene.
                possible_colors = list(mcolors.BASE_COLORS.values())
                for name, value in mcolors.CSS4_COLORS.items():
                    if int(value[1:], 16) < 15204888:
                        possible_colors.append(name)

                # Zistíme unikátne labels a na základe nich vytvoríme dict, kde je každej label priradená unikátna farba
                # ak je to možné.
                unique_labels = labels_data.unique()
                label_colour_dict = {}
                number_of_unique_colors = len(possible_colors)
                for i, label in enumerate(unique_labels):
                    label_colour_dict[label] = possible_colors[i % number_of_unique_colors]

                # Všetkým bodom je nastavená defaultná farba.
                points_colour.clear()
                label_colour.clear()
                for label in points_label:
                    points_colour.append(BASIC_POINT_COLOUR)
                    label_colour.append(label_colour_dict[label])

                # Ak je počet fetures medzi 1 a 4 je vytvorený polygon (mriežka, ktorú je možné zobraziť)
                if 1 < shape_of_input < 4:
                    # Zistí sa minimalná a maximálna hodnota pre každú súradnicu, aby mriežka nadobúdala len rozmery
                    # bodov
                    minimal_cord = np.min(self.__input_data[:, :shape_of_input], axis=0).tolist()
                    maximal_cord = np.max(self.__input_data[:, :shape_of_input], axis=0).tolist()
                    if shape_of_input == 3:
                        polygon = Polygon(minimal_cord, maximal_cord, [5, 5, 5])
                    elif shape_of_input == 2:
                        polygon = Polygon(minimal_cord, maximal_cord, [5, 5, 5])

                    polygon_peak_cords = np.array(polygon.Peaks)

                    edges_tuples = np.array(polygon.Edges)

                    self.__polygon_cords = []

                    self.__polygon_cords.append(polygon_peak_cords[:, edges_tuples[:, 0]].transpose())

                    self.__polygon_cords.append(polygon_peak_cords[:, edges_tuples[:, 1]].transpose())

                    for layer in self.__neural_layers:
                        layer.possible_polygon = True
                else:
                    for layer in self.__neural_layers:
                        layer.possible_polygon = False

                # Ak prebehlo načítvanaie bez chyby, sú aplikované zmeny,
                self.recalculate_cords(-1)
                self.broadcast_changes(-1)
                self.__main_graph_frame.apply_changes_on_options_frame()
                return None
            else:
                return 'Diffrent input point dimension!'
        else:
            return 'No Keras model loaded!'

    def __del__(self):
        self.__is_running = False
        self.__condition_var.acquire()
        self.__condition_var.notify()
        self.__condition_var.release()


class MainGraphFrame(tk.LabelFrame):
    """
    Popis
    --------------------------------------------------------------------------------------------------------------------
    Hlavné okno podstránky s grafmi. Okno vytvorí scrollovacie okno, do ktorého budú následne vkladané jednotlivé vrstvy
    s grafmi a ich ovládačmi. Vytvorí taktiež options okno, ktoré slúži na zobrazovanie informácii o zvolenem bode a
    možnosti nastavenia zobrazenia grafov v jednotlivých vrstvách.

     Atribúty
     -------------------------------------------------------------------------------------------------------------------
     :var self.__logic_layer:        obsahuje odkaz na vrstvu, ktorá sa zaoberá výpočtami a logickou reprezentáciou
                                     jednotlivých vrstiev a váh.

     :var self.__number_of_layers:   počet vrstiev načítanej neurónovej siete

     :var self.__name_to_order_dict: každej vrstve je postupne prideľované poradové číslo vrstvy, tak ako ide od
                                     začiatku neurónovej siete. Ako kľúč je použitý názov vrstvy.

     :var self.__order_to_name_dict: podľa poradia je každej vrstve pridelené poradové číslo. Poradové číslo je kľúčom
                                     do dict. Jeho hodnotami sú názvy jedntlivých vrstiev.
                                     Ide o spätný dict k __name_to_order_dict.

     :var self.__active_layers:      obsahuje poradové čísla aktívnych vrstiev, pre prídavanie a odoberanie vrstiev z
                                     add_graph_fame

     :var self.__input_panned:       obal pre komponenty InputDataFrame a PannedWindow. Umožňuje podľa potreby
                                     roztiahnuť alebo zúžiť veľkosť input panelu na úkor PannedWindow, ktoré obsahuje
                                     rámce s reprezentáciou jednotlivých vrstiev.

     :var self.__graph_panned:       obal pre ScrollableWindow, ktoré obsahuje rámce v ktorých sú zobrazené jednotlivé
                                     vrstvy.

     :var self.__options_frame:      okno, v ktorom sa zobrazujú možnosti pre zvolenú vrstvu.

     :var self.__scroll_frame:       obsahuje grafické zobrazenie zvolených vrstiev neurónovej siete a
                                     ComboboxAddRemoveFrame, v ktorom sú volené vrstvy, ktoré chceme zobraziť

     :var self.__add_graph_frame:    combobox, z ktorého si vyberáme jednotlivé, ešte neaktívne vrstvy, ktoré tlačidlom
                                     následne zobrazíme. Zobrazuje sa, len ak nie sú zobrazené ešte všetky vrstvy.
     """

    def __init__(self, parent, logic_layer, *args, **kwargs):
        """
        :param parent: nadradený tkinter widget
        :type parent: tk.Widget
        :param logic_layer: odkaz na logickú vrstvu
        :type logic_layer: GraphLogicLayer
        """
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)

        self.__logic_layer = logic_layer
        self.__number_of_layers = 0

        self.__neural_layers = None

        self.__name_to_order_dict = {}

        self.__order_to_name_dict = {}

        self.__active_layers = []

        # Grafické komponenty. Rozťahovateľné okno.
        self.__input_panned = tk.PanedWindow(self)
        self.__input_panned.pack(fill='both', expand=True)

        # Options bar pre jednotlivé vrstvy.
        self.__options_frame = OptionsFrame(self.__input_panned, self.__logic_layer, border=0, highlightthickness=0)
        self.__input_panned.add(self.__options_frame)
        # self.__graph_panned = tk.PanedWindow(self.__input_panned)
        # self.__input_panned.add(self.__graph_panned)

        # Posuvné okno, v ktorom sú zobrazované grafy zodpovedajúce jednotlivým vrstvám.
        self.__graph_area_frame = tk.LabelFrame(self.__input_panned, relief='sunken', border=0, highlightthickness=0)
        self.__input_panned.add(self.__graph_area_frame)
        self.__scroll_frame = ScrollableWindow(self.__graph_area_frame, 'horizontal', border=0, highlightthickness=0)
        self.__scroll_frame.pack(side='right', fill=tk.BOTH, expand=True)

        # Okno s možnosťou voľby vrstiev z načítaného modelu.
        self.__add_graph_frame = ComboboxAddRemoveFrame(self.__scroll_frame.Frame, width=412, relief='sunken')
        self.__add_graph_frame.pack(side='right', fill='y')

    def initialize(self, neural_layers: list, active_layer: list):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Inicializačná funkcia. Inicializuje všetky potrbné komponenty tejto vrstvy.
        Vytvorí predbežný zoznam názvov jednotlivých vrstiev. Po inicializácií AddRemoveComboboxFrame budú získane
        unikátne mená, ktoré sa použijú ako kľúče v slovníku.

        Na základe unikátnych mien je vytvorený slovník, ktorý prevádza meno vrstvy na jej poradové číslo a spätný
        slovník, ktorý prevádza poradové číslo na názov vrstvy.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param neural_layers: zoznam NeuralLayer, ktoré bude možné zobraziť.
        :param active_layer:  refenrencia na zoznam aktívnych vrstiev.
        """
        self.__options_frame.initialize()

        # Vyčistenie slovníkov.
        self.__order_to_name_dict = {}
        self.__name_to_order_dict = {}

        self.__active_layers = active_layer

        self.__neural_layers = neural_layers
        self.__number_of_layers = len(neural_layers)

        # Vytvorenie predbežného zoznamu názvov vrstiev.
        layer_name_list = []
        for i in range(self.__number_of_layers):
            layer_name_list.append(self.__neural_layers[i].layer_name)

        # Inicializácia AddRemoveComboboxFrame. Funkcia navracia list unikátnych názvov vrstiev.
        # Unikátne názvy su použité ako kľúče v slovníku.
        unique_name_list = self.__add_graph_frame.initialize(layer_name_list, self.show_layer, 'Add layer', True,
                                                                  'Select layer')
        for i, layerName in enumerate(unique_name_list):
            self.__neural_layers[i].layer_name = layerName
            self.__order_to_name_dict[i] = layerName
            self.__name_to_order_dict[layerName] = i

        if len(self.__active_layers) < self.__number_of_layers:
            self.__add_graph_frame.pack(side='right', fill='y', expand=True)

        first_layer_tuple = (self.__neural_layers[0].layer_number, self.__neural_layers[0].layer_name)
        self.show_layer(first_layer_tuple)

    def show_layer(self, layer_tuple: tuple):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Metóda na základe parametra obdržaného z triedy AddRemoveCombobox vytvorí a následne zobrazí zvolenú vrstvu.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param layer_tuple:
        (poradové číslo vrstvy ,názov vrstvy) - obashuje hodnotu z triedy AddRemoveCombobox
        """
        layer_name = layer_tuple[1]
        layer_number = self.__name_to_order_dict[layer_name]

        # Otestuje, či je číslo vrstvy valídne.
        if 0 <= layer_number < self.__number_of_layers:
            layer_to_show = None

            # Inicializácia vrstvy na zobrazenie.
            if layer_number < self.__number_of_layers:
                layer_to_show = self.__neural_layers[layer_number]
                layer_to_show.show(self.__scroll_frame.Frame, self.hide_layer, self.show_layer_options_frame)

            layer_to_show.pack(side='left', fill=tk.BOTH, expand=True)
            # Poradové číslo vrstvy je vložené do listu aktívnych vrstiev, ktorý sa využíva pri efektívnejšom updatovaní
            # vykresľovaných grafov.
            self.__active_layers.append(layer_number)
            self.__add_graph_frame.hide_item(layer_name)

            self.__logic_layer.set_points_for_layer(layer_number)
            layer_to_show.apply_changes()
            # Ak je počet aktívnych vrstiev rovný celkovému počtu vrstiev je skrytý panel pre pridávanie nových vrstiev.
            if len(self.__active_layers) == self.__number_of_layers:
                self.__add_graph_frame.pack_forget()

    def hide_layer(self, layer_number: int):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Skryje vrstvu, podľa jej poradového čísla.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param layer_number: číslo vrstvy, ktorá má byť skrytá
        :type layer_number: int
        """
        if layer_number in self.__active_layers:
            layer_name = self.__order_to_name_dict[layer_number]
            layer = self.__neural_layers[layer_number]
            layer.clear()

            self.__active_layers.remove(layer_number)
            self.__add_graph_frame.show_item(layer_name)
            if len(self.__active_layers) < self.__number_of_layers:
                self.__add_graph_frame.pack(side='right', fill='y', expand=True)
            if self.__options_frame.active_layer == layer:
                self.__options_frame.hide_all()

    def show_layer_options_frame(self, layer_number):
        if 0 <= layer_number < self.__number_of_layers:
            layer = self.__neural_layers[layer_number]
            self.__options_frame.initialize_with_layer_config(layer, layer.config)

    def apply_changes_on_options_frame(self):
        self.__options_frame.update_selected_config()

    def update_active_options_layer(self, start_layer):
        self.__options_frame.update_active_options_layer(start_layer)


class OptionsFrame(tk.LabelFrame):
    def __init__(self, parent, logicalLayer: GraphLogicLayer, *args, **kwargs):
        """"
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Obsahuje ovladacie prvky pre jednotlivé vrstvy. V rámci nej je možne navoliť zobrazované súradnice pre
        jednotlivé metódy, ofarbiť body na základe ich label, povoliť zobrazenie mriežky, ak je to možné, uzmaknutie
        pohľadu v grafe.
        Je možné aj zvoliť redukciu priestoru a zobraziť požadovaný PCA komponent alebo použiť metódu t-SNE.

        Atribúty
        ----------------------------------------------------------------------------------------------------------------
        :var self.__graph_logic:          odkaz na triedu, zaoberajúcu sa logikou aplikácie.
        :var self.__labels_entries_list:  list vstupnov pre zadávanie názvov osi v grafe aktívnej vrstvy.
        :var self.__cords_entries_list:   list vstupov na zadávanie zobrazovaných súradníc
        :var self.__bar_wrapper:          obaľovací widget, stále zobrazený
        :var self.__layer_options_frame:  obaľovací widget, ktorý obaľuje jedntolivé ucelené rámce s možnosťami
        :var self.__layer_name_label:     zobrazuje meno aktívnej vrstvy, pre ktorú sú zobrazované možnosti
        :var self.__cords_choose_frame:   rámec obsahujúci možnosti zobrazovaných súradníc
        :var self.__possible_cords_label: zobrazuje informáciu o rozsahu súradníc, ktoré môžu byť zobrazené.
        :var self.__label_choose_frame:   obaľuje widgety pre vsutpy, ktoré sú použité na načítanie názvu osí grafu
        :var self.__appearance_frame:     obľuje checkboxy, ktoré slúžia na úpravu vzhľadu grafu a jeho správania
                                          pri prekreslení
        :var self.__color_labels:         boolean premenná checboxu, ktorá označuje, či majú byť vstupy s
                                          rovnakým labelom, ofarbené rovnakou farbou
        :var self.__color_labels_check:   checkbox, ktorý zachytáva, či je táto možnosť zvolená alebo nie
        :var self.__lock_view:            boolean premenná checkboxu, ktorá určuje či má graf pri prekresľovaní zmeniť
                                          škálovanie a posun, alebo zachovať naposledy nastavené
        :var self.__lock_view_check:      checkbox, ktorý zachytáva, či je táto možnosť zvolená alebo nie
        :var self.__3d_graph:             boolean premenná checboxu, ktorá označuje či sa má zobrazovať 2D alebo 3D graf
                                          možnosť je dostupná ak je počet neuronov na vrstve väčší alebo rovný ako 3
        :var self.__show_polygon:         boolean premenná checboxu, ktorá označuje či sa má zobrazovať mriežka, v 2D
                                          alebo 3D. Táto možnosť je dostupná ak je vstup do modleu tvoreným 2 alebo 3
                                          vstupmi.
        :var self.__dim_reduction_frame:  obaľovací widget, ktorý drží zoznam možných metód na redukciu priestoru.
                                          Sú tu zobrazované aj informácie z metódy prípadne zoznam nastaviteľných
                                          parametrov, potrebných pre použitie metódy
        :var self.__actual_used_label:    label, ktorý oboznámjue používateľa s práve použitou metódou redukcie
        :var self.__no_method_radio:      radio button, ktorý označuje že je zvolená metóda no_method
        :var self.__PCA_method_radio:     radio button, ktorý označuje že je zvolená metóda PCA
        :var self.__tSNE_method_radio:    radio button, ktorý označuje že je zvolená metóda t-SNE
        :var self.__PCA_info_frame:       obaľuje listboxy obashujúce informácie po použití metódy PCA
        :var self.__PC_explanation_frame: obsahuje listbox, v ktorom je vyjadrená koľko percent variability je 
                                          vysvetelných jednotlivými komponentmi PCA
        :var self.__PC_explanation_lb:    listbox v ktorom je zobrazené aká variabilita je vyjadrená jednotlivými PC
        :var self.__PC_scores_frame:      obsahuje listbox, ktorý udáva ktoré neuróny majú najväčšiu váhu pri PCA
        :var self.__PC_scores_lb:         listbox v ktorom sú zoradené neuróny s najäčším vplyvom
        :var self.__tSNE_parameter_frame: obaľovací widget, obsahuje zoznam nastaviteľných parametrov, potrebných pre
                                          metódu t-SNE
        :var self.__tSNE_parameters_dict: slovník, ku v ktorom su k jednotlivým názvom parametrov priradené rewritable
                                          labels
        :var self.__apply_method_btn:     tlačidlo na použitie zvolenej metódy pomocou radio buttons

        Parmetre
        ----------------------------------------------------------------------------------------------------------------
        :param parent: nadradený tkinter Widget
        :param logicalLayer: odkaz na logickú vrstvu grafu
        """
        tk.LabelFrame.__init__(self, parent, width=285, *args, **kwargs)
        self.__graph_logic = logicalLayer
        self.pack_propagate(0)
        self.__labels_entries_list = []
        self.__cords_entries_list = []

        # Obalovaci element. Ostáva stále zobrazený.
        self.__bar_wrapper = tk.LabelFrame(self, text='Layer options')
        self.__bar_wrapper.pack(side='top', fill='both', expand=True)

        # Skupina komponentov pre nastavovanie vlastností vykresľovaného grafu.
        self.__layer_options_frame = tk.LabelFrame(self.__bar_wrapper)
        self.__layer_name_label = tk.Label(self.__layer_options_frame, text='Layer name', relief='raised')
        self.__layer_name_label.pack(fill='x')

        # Sekcia na výber zobrazovaných súradnic na jednltivých osiach.
        self.__cords_choose_frame = tk.LabelFrame(self.__layer_options_frame, text='Visible cords')
        self.__possible_cords_label = tk.Label(self.__cords_choose_frame)
        self.__cords_choose_frame.pack(fill='x')
        self.__possible_cords_label.pack(side=tk.TOP, fill='x', expand=True)

        self.__label_choose_frame = tk.LabelFrame(self.__layer_options_frame, text='Label names')
        self.__label_choose_frame.pack(fill='x')

        # Sekcia na zmenu vlastností zobrazenia.
        self.__appearance_frame = tk.LabelFrame(self.__layer_options_frame, text='Graph view options')
        self.__color_labels = tk.BooleanVar()
        self.__color_labels_check = tk.Checkbutton(self.__appearance_frame, text='Color labels',
                                                   command=self.on_color_label, variable=self.__color_labels)

        self.__lock_view = tk.BooleanVar()
        self.__lock_view_check = tk.Checkbutton(self.__appearance_frame, text='Lock view',
                                                command=self.on_lock_view_check, variable=self.__lock_view)
        self.__3d_graph = tk.BooleanVar()
        self.__3d_graph_check = tk.Checkbutton(self.__appearance_frame, text='3D view',
                                               command=self.on_3d_graph_check, variable=self.__3d_graph)
        self.__show_polygon = tk.BooleanVar()
        self.__show_polygon_check = tk.Checkbutton(self.__appearance_frame, text='Show polygon',
                                                   command=self.on_show_polygon_check,
                                                   variable=self.__show_polygon)

        self.__appearance_frame.pack(fill='x')
        self.__color_labels_check.grid(row=1, column=0, sticky='w')
        self.__lock_view_check.grid(row=2, column=0, sticky='w')

        # Sekcia na nastavenia redukcie priestoru.
        self.__dim_reduction_frame = tk.LabelFrame(self.__layer_options_frame, text='Dimension reduction')
        self.__dim_reduction_frame.pack(side='bottom', fill='x')

        self.__radio_button_group_frame = tk.Frame(self.__dim_reduction_frame)
        self.__radio_button_group_frame.pack(fill='x', expand=True)

        self.__actual_used_label = tk.Label(self.__radio_button_group_frame, text='Actual used: No method')
        self.__actual_used_label.pack()

        self.__currently_used_method = 'No method'

        # Jednotlivé metódy.
        self.__method_var = tk.StringVar()
        self.__no_method_radio = tk.Radiobutton(self.__radio_button_group_frame, command=self.on_method_change,
                                                text='No method', variable=self.__method_var, value='No method')
        self.__no_method_radio.select()
        self.__no_method_radio.pack(side='left')
        self.__PCA_method_radio = tk.Radiobutton(self.__radio_button_group_frame, command=self.on_method_change,
                                                 text='PCA', variable=self.__method_var, value='PCA')
        self.__PCA_method_radio.pack(side='left')
        self.__PCA_method_radio.deselect()
        self.__tSNE_method_radio = tk.Radiobutton(self.__radio_button_group_frame, command=self.on_method_change,
                                                  text='t-SNE', variable=self.__method_var, value='t-SNE')
        self.__tSNE_method_radio.pack(side='left')
        self.__tSNE_method_radio.deselect()

        self.__PCA_info_frame = tk.LabelFrame(self.__dim_reduction_frame, text='PCA information')

        self.__PC_explanation_frame = tk.LabelFrame(self.__PCA_info_frame, border=0,
                                                             text='PC variance explanation')
        self.__PC_explanation_frame.pack(side='left', fill='x')
        self.__PC_explanation_lb = tk.Listbox(self.__PC_explanation_frame, highlightthickness=0)
        self.__PC_explanation_lb.pack(fill='both')

        self.__PC_scores_frame = tk.LabelFrame(self.__PCA_info_frame, border=0,
                                                       text='Loading scores')
        self.__PC_scores_frame.pack(side='right', fill='x')
        self.__PC_scores_lb = tk.Listbox(self.__PC_scores_frame, highlightthickness=0)
        self.__PC_scores_lb.pack(fill='both')

        self.__tSNE_parameter_frame = tk.LabelFrame(self.__dim_reduction_frame, text='t-SNE parameters')
        self.__tSNE_parameters_dict = dict()

        t_sne_parameter_id_list = ['n_components', 'perplexity', 'early_exaggeration', 'learning_rate', 'n_iter']
        t_sne_parameter_label = ['Number of components:', 'Perplexity:', 'Early exaggeration:', 'Learning rate:',
                                 'Number of iteration:']

        for i in range(len(t_sne_parameter_id_list)):
            t_sne_parameter = RewritableLabel(self.__tSNE_parameter_frame, t_sne_parameter_id_list[i],
                                              self.validate_t_sne_entry, t_sne_parameter_label[i], '-')
            t_sne_parameter.set_entry_width(3)
            t_sne_parameter.pack(fill='x')
            self.__tSNE_parameters_dict[t_sne_parameter_id_list[i]] = t_sne_parameter

        self.__apply_method_btn = tk.Button(self.__dim_reduction_frame, text='Use method', command=self.use_selected_method)
        self.__apply_method_btn.pack(side='bottom')

        # Vytvorenie komponentov. Na konci v rámci jedného cyklu aby sa znížila duplicita kódu.
        label_name = ['Label X', 'Label Y', 'Label Z']
        for i in range(3):
            rewritable_label = RewritableLabel(self.__cords_choose_frame, i, self.validate_cord_entry,
                                               'Suradnica {}:'.format(i), '-')
            self.__cords_entries_list.append(rewritable_label)
            rewritable_label.set_entry_width(3)

            rewritable_label = RewritableLabel(self.__label_choose_frame, i, self.validate_label_entry,
                                               '{} axe:'.format(label_name[i]), label_name[i])
            self.__labels_entries_list.append(rewritable_label)

        self.__active_layer = None
        self.__changed_config = None

    def initialize(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Vyčistenie atribútov a skrytie celého options baru.
        """
        self.__changed_config = None
        self.__active_layer = None
        self.__PC_explanation_lb.delete(0, tk.END)
        self.__PC_scores_lb.delete(0, tk.END)
        self.hide_all()

    def initialize_label_options(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Nastavenie jednotlivých vstupov pre časť s názvami os grafov na základe načítaného configu.
        """
        number_of_possible_dim = self.__changed_config['max_visible_dim']
        for i in range(number_of_possible_dim):
            label_entry = self.__labels_entries_list[i]
            label_entry.set_variable_label(self.__changed_config['axis_labels'][i])
            label_entry.pack(fill='x')

    def initialize_view_options(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Nastavenie hodnôt jednotlivých vstupov pre časť s možnosťami zobrazovania grafu na základe načítaného configu.
        """
        if self.__changed_config['color_labels']:
            self.__color_labels_check.select()
        else:
            self.__color_labels_check.deselect()

        if self.__changed_config['locked_view']:
            self.__lock_view_check.select()
        else:
            self.__lock_view_check.deselect()

        number_of_possible_dim = self.__changed_config['max_visible_dim']

        if number_of_possible_dim >= 3:
            if self.__changed_config['draw_3d']:
                self.__3d_graph_check.select()
            else:
                self.__3d_graph_check.deselect()

            self.__3d_graph_check.grid(row=3, column=0, sticky='w')

        if self.__changed_config['possible_polygon']:
            if self.__changed_config['show_polygon']:
                self.__show_polygon_check.select()
            else:
                self.__show_polygon_check.deselect()
            self.__show_polygon_check.grid(row=4, column=0, sticky='w')

    def initialize_dimension_reduction_options(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Nastavenie hodnôt jednotlivých vstuov pre časť s možnosťami pre redukciu priestoru.
        """
        self.set_actual_method_lable(self.__currently_used_method)
        config_selected_method = self.__changed_config['config_selected_method']

        self.__no_method_radio.deselect()
        self.__PCA_method_radio.deselect()
        self.__tSNE_method_radio.deselect()

        if config_selected_method == 'No method':
            self.__no_method_radio.select()
        elif config_selected_method == 'PCA':
            self.__PCA_method_radio.select()
        elif config_selected_method == 't-SNE':
            self.__tSNE_method_radio.select()

        if self.__currently_used_method == 'PCA':
            self.update_PCA_information()

        self.initialize_t_sne_parameters()
        self.on_method_change()

    def initialize_with_layer_config(self, neural_layer, config):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Nastavenie aktuálnej aktívnej vrstvy a configu tejto vrstvy.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param neural_layer: odkaz na aktívnu vrstvu, pre ktorú sú menené nastavenia a ktoré budú následne na túto
                             vrstvu použité
        :param config: odkaz na config aktuálne zobrazovanej a upravovanej vrstvy
        """
        self.__active_layer = neural_layer
        self.__changed_config = config
        self.update_selected_config()

    def initialize_t_sne_parameters(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Predvyplnenie parametrov pre metódu t-SNE.
        """
        t_sne_config = self.__changed_config['t_SNE_config']
        actual_used_config = t_sne_config['used_config']
        options_config = t_sne_config['options_config']
        number_of_components = t_sne_config['parameter_borders']['n_components'][2]
        self.__tSNE_parameters_dict['n_components'].set_label_name(f'Number of components (max {number_of_components}):')
        for key in self.__tSNE_parameters_dict:
            rewritable_label = self.__tSNE_parameters_dict[key]
            rewritable_label.set_variable_label(options_config[key])

            # Ak sa aktuálne používaná hodnota parametra nerovná naposledy nastavenej hodnote parametra je tento
            # parameter označený ako zmenený no ešte nepoužitý.
            if actual_used_config[key] == options_config[key]:
                rewritable_label.set_mark_changed(False)
            else:
                rewritable_label.set_mark_changed(True)

    def update_selected_config(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Nastavenie jednotlivých možností na základe configu aktívnej vrstvy.
        """
        if self.__active_layer is not None and self.__changed_config is not None:
            self.__currently_used_method = self.__changed_config['used_method']
            self.hide_all()
            self.__layer_options_frame.pack(fill='x')
            self.__layer_name_label.configure(text=self.__changed_config['layer_name'])

            self.set_cords_entries_according_chosen_method()
            self.initialize_label_options()
            self.initialize_view_options()
            self.initialize_dimension_reduction_options()

    def update_PCA_information(self):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Vypísanie aktuálnych informácii o PCA.
        """
        variance_series = self.__changed_config['PCA_config']['percentage_variance']
        if variance_series is not None:
            self.__PC_explanation_lb.delete(0, tk.END)
            pc_labels = variance_series.index
            for i, label in enumerate(pc_labels):
                self.__PC_explanation_lb.insert(i, '{}: {:.2f}%'.format(label, round(variance_series[label], 2)))
            loading_scores = self.__changed_config['PCA_config']['largest_influence']

            self.__PC_scores_lb.delete(0, tk.END)
            # Zoradenie významností jednotlivých neurónov pri PCA
            sorted_loading_scores = loading_scores.abs().sort_values(ascending=False)
            sorted_indexes = sorted_loading_scores.index.values
            for i, label in enumerate(sorted_indexes):
                self.__PC_scores_lb.insert(i, '{}: {:.4f}'.format(label, round(loading_scores[label], 4)))

    def update_active_options_layer(self, start_layer=-1):
        """
        Popis
        ----------------------------------------------------------------------------------------------------------------
        Zobrazenie aktuálnych informácií pre aktívnu vrstvu, ktorej možnosti sú zobrazované.

        Parametre
        ----------------------------------------------------------------------------------------------------------------
        :param start_layer: poradové číslo najnižšej vrstvy, pri ktorej došlo ku zmene, ak je číslo menšie ako poradové
                            číslo aktívnej vrstvy, ktorej možnosti sú zobrazované, sú tieto možnosti aktualizované,
                            pretože mohlo dôjsť k zmenám v možných parametroch, prípadne k zmene hodnôt v rámci PCA.
        """
        if self.__active_layer is not None and self.__changed_config is not None:
            actual_method = self.__changed_config['used_method']
            if actual_method == 'PCA' and start_layer < self.__active_layer.layer_number:
                self.update_PCA_information()

    def use_selected_method(self):
        if self.__active_layer is not None:
            method = self.__method_var.get()
            need_recalculation = False
            if method == 't-SNE':
                need_recalculation = self.apply_t_SNE_options_if_changed()

            if method != self.__changed_config['used_method']:
                need_recalculation = True
                self.__changed_config['used_method'] = self.__currently_used_method = method
            if need_recalculation:
                self.__changed_config['apply_changes'] = True
                self.__active_layer.use_config()
                self.__actual_used_label.configure(text=f'Actual used: {method}')

                # Hide all informations
                self.hide_all_methods_information()
                if method == 'PCA':
                    self.update_PCA_information()
                    self.__PCA_info_frame.pack(fill='x', expand=True)
                elif method == 't-SNE':
                    self.__tSNE_parameter_frame.pack(fill='x', expand=True)

                self.set_actual_method_lable(method)
            self.set_cords_entries_according_chosen_method()

    def apply_t_SNE_options_if_changed(self):
        changed = False
        if self.__changed_config is not None:
            t_sne_config = self.__changed_config['t_SNE_config']
            used_config = t_sne_config['used_config']
            options_config = t_sne_config['options_config']
            for key in used_config:
                if used_config[key] != options_config[key]:
                    changed = True
                    used_config[key] = options_config[key]
            if changed:
                t_sne_config['displayed_cords'] = list(range(used_config['n_components']))
                self.set_entries_not_marked(self.__tSNE_parameters_dict.values())
        return changed

    def update_t_SNE_new_parameters(self):
        self.hide_cords_choose_options()
        number_of_components = self.__changed_config['t_SNE_config']['used_config']['n_components']
        for i in range(number_of_components):
            self.__cords_entries_list[i].pack()

    def hide_all(self):
        self.__layer_options_frame.pack_forget()
        # self.__layer_name_label.pack_forget()
        self.hide_choose_cords_entries()
        self.hide_label_options()
        self.hide_graph_view_options()
        self.hide_dimension_reduction_options()

    def hide_choose_cords_entries(self):
        for i in range(3):
            self.__cords_entries_list[i].pack_forget()

    def hide_label_options(self):
        # self.__label_choose_frame.pack_forget()
        for i in range(3):
            self.__labels_entries_list[i].pack_forget()

    def hide_graph_view_options(self):
        self.__3d_graph_check.grid_forget()
        self.__show_polygon_check.grid_forget()

    def hide_dimension_reduction_options(self):
        # self.__dim_reduction_frame.pack_forget()
        self.hide_all_methods_information()

    def hide_all_methods_information(self):
        self.__PCA_info_frame.pack_forget()
        self.__tSNE_parameter_frame.pack_forget()

    def set_actual_method_lable(self, method_name):
        self.__actual_used_label.configure(text=f'Actual used: {method_name}')

    def on_method_change(self):
        if self.__changed_config:
            method = self.__method_var.get()
            self.__changed_config['config_selected_method'] = method
            if method == 'PCA':
                if self.__changed_config['used_method'] == method:
                    self.__PCA_info_frame.pack(fill='x')
                self.__tSNE_parameter_frame.pack_forget()
            elif method == 't-SNE':
                self.__PCA_info_frame.pack_forget()
                self.__tSNE_parameter_frame.pack(fill='x')
            else:
                self.__PCA_info_frame.pack_forget()
                self.__tSNE_parameter_frame.pack_forget()

    def on_color_label(self):
        if self.__changed_config:
            self.__changed_config['color_labels'] = self.__color_labels.get()
            self.__active_layer.use_config()

    def on_lock_view_check(self):
        if self.__changed_config:
            self.__changed_config['locked_view'] = self.__lock_view.get()
            self.__active_layer.use_config()

    def on_show_polygon_check(self):
        if self.__changed_config:
            self.__changed_config[
                'show_polygon'] = self.__active_layer.calculate_polygon = self.__show_polygon.get()
            if self.__changed_config['show_polygon']:
                self.__active_layer.set_polygon_cords()
            self.__active_layer.use_config()

    def on_3d_graph_check(self):
        if self.__changed_config:
            self.__changed_config['draw_3d'] = self.__3d_graph.get()
            self.__active_layer.use_config()

    def validate_t_sne_entry(self, id, value):
        try:
            test_tuple = self.__changed_config['t_SNE_config']['parameter_borders'][id]
            if not (test_tuple[0] <= test_tuple[1](value) <= test_tuple[2]):
                self.__tSNE_parameters_dict[id].set_entry_text('err')
                return False
            parameter_label = self.__tSNE_parameters_dict[id]
            parameter_label.set_variable_label(value)
            parameter_label.show_variable_label()
            self.__changed_config['t_SNE_config']['options_config'][id] = test_tuple[1](value)
            if self.__changed_config['t_SNE_config']['options_config'][id] == self.__changed_config['t_SNE_config']['used_config'][id]:
                parameter_label.set_mark_changed(False)
            else:
                parameter_label.set_mark_changed(True)
            return True
        except ValueError:
            self.__tSNE_parameters_dict[id].set_entry_text('err')
            return False

    def validate_cord_entry(self, id, value):
        try:
            bottom_border = 0
            top_border = 0
            changed_cords = None
            if self.__currently_used_method == 'No method':
                bottom_border = 0
                top_border = self.__changed_config['number_of_dimensions']
                changed_cords = self.__changed_config['no_method_config']['displayed_cords']
                new_value = int(value)
            elif self.__currently_used_method == 'PCA':
                bottom_border = 1
                top_border = min(self.__changed_config['number_of_dimensions'], self.__changed_config['number_of_samples']) + 1
                changed_cords = self.__changed_config['PCA_config']['displayed_cords']
                new_value = int(value) - 1
            elif self.__currently_used_method == 't-SNE':
                bottom_border = 0
                top_border = self.__changed_config['t_SNE_config']['used_config']['n_components']
                changed_cords = self.__changed_config['t_SNE_config']['displayed_cords']
                new_value = int(value)

            if not (bottom_border <= int(value) < top_border):
                self.__cords_entries_list[id].set_entry_text('err')
                return False

            self.__cords_entries_list[id].set_variable_label(value)
            self.__cords_entries_list[id].show_variable_label()
            changed_cords[id] = int(new_value)
            self.__changed_config['cords_changed'] = True
            self.__active_layer.use_config()
            return True
        except ValueError:
            self.__cords_entries_list[id].set_entry_text('err')
            return False

    def set_entries_not_marked(self, entries_list):
        for entry in entries_list:
            entry.set_mark_changed(False)

    def validate_label_entry(self, id, value):
        self.__labels_entries_list[id].set_variable_label(value)
        self.__labels_entries_list[id].show_variable_label()
        self.__changed_config['axis_labels'][id] = value
        self.__active_layer.use_config()

    def set_cords_entries_according_chosen_method(self):
        if self.__currently_used_method == 'No method':
            entry_names = ['Axis X:', 'Axis Y:', 'Axis Z:']
            cords_label_text = 'Possible cords: 0-{}'.format(self.__changed_config['number_of_dimensions']-1)
            displayed_cords = self.__changed_config['no_method_config']['displayed_cords']
            possible_cords = self.__changed_config['max_visible_dim']
        elif self.__currently_used_method == 'PCA':
            entry_names = ['PC axis X:', 'PC axis Y:', 'PC axis Z:']
            number_of_pcs = min(self.__changed_config['number_of_dimensions'],
                                                                   self.__changed_config['number_of_samples'])
            if number_of_pcs == 0:
                cords_label_text = 'No possible PCs:'
            else:
                cords_label_text = 'Possible PCs: 1-{}'.format(number_of_pcs)
            possible_cords = min(number_of_pcs, self.__changed_config['max_visible_dim'])
            displayed_cords = self.__changed_config['PCA_config']['displayed_cords'].copy()
            displayed_cords = np.array(displayed_cords) + 1
        elif self.__currently_used_method == 't-SNE':
            entry_names = ['t-SNE X:', 't-SNE Y:', 't-SNE Z:']
            possible_cords = self.__changed_config['t_SNE_config']['used_config']['n_components']
            cords_label_text = 'Possible t-SNE components: 0-{}'.format(possible_cords - 1)
            displayed_cords = self.__changed_config['t_SNE_config']['displayed_cords'].copy()
        self.set_cords_entries(entry_names, cords_label_text, displayed_cords, possible_cords)

    def set_cords_entries(self, entry_name, cords_label_text, displayed_cords, possible_cords):
        self.hide_choose_cords_entries()
        self.__possible_cords_label.configure(text=cords_label_text)
        for i in range(possible_cords):
            cord_entry_rewritable_label = self.__cords_entries_list[i]
            cord_entry_rewritable_label.set_label_name(entry_name[i])
            cord_entry_rewritable_label.set_variable_label(displayed_cords[i])
            cord_entry_rewritable_label.pack(fill='x', expand=True)

    @property
    def active_layer(self):
        return self.__active_layer


class NeuralLayer:
    def __init__(self, logicLayer: GraphLogicLayer, keras_layer: keras.layers.Layer,
                 layer_number: int, *args, **kwargs):
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
        self.__layer_name = keras_layer.get_config()['name']
        self.__number_of_dimension = keras_layer.input_shape[1]
        self.__layer_number = layer_number

        if len(keras_layer.get_weights()) != 0:
            self.__layer_weights = keras_layer.get_weights()[0]
            self.__layer_biases = keras_layer.get_weights()[1]
        else:
            self.__layer_weights = None
            self.__layer_biases = None

        self.__layer_options_container = None
        self.__options_button = None
        self.__layer_wrapper = None
        self.__graph_frame = None
        self.__hide_button = None
        self.__has_points = False

        self.__computation_in_process = False

        self.__calculate_polygon = False

        self.__polygon_cords_tuples = None

        self.__layer_config = {}

        self.__points_config = None

        self.__logic_layer = logicLayer
        self.__layer_number = layer_number
        self.__point_cords = np.array([])
        self.__used_cords = []
        self.__axis_labels = []
        self.__neuron_labels = []
        self.__pc_labels = []

        self.__points_method_cords = []

        self.__points_colour = None

        self.__points_label = None

        self.__visible = False
        self.__weights_changed = False

    def pack(self, *args, **kwargs):
        if self.__visible:
            self.__layer_wrapper.pack(*args, **kwargs)

    def initialize(self, points_config):
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
        self.__point_cords = np.array([[] for _ in range(self.__number_of_dimension)])
        self.__points_config = points_config

        # Počet súradníc ktoré sa majú zobraziť určíme ako menšie z dvojice čísel 3 a počet dimenzií, pretože max počet,
        # ktorý bude možno zobraziť je max 3
        number_of_cords = min(3, self.__number_of_dimension)
        axis_default_names = ['Label X', 'Label Y', 'Label Z']
        self.__axis_labels = []
        self.__neuron_labels = []
        self.__pc_labels = []
        self.__points_method_cords = []
        used_t_sne_components = []
        used_no_method_cords = []
        used_PCA_components = []

        for i in range(self.__number_of_dimension):
            self.__neuron_labels.append(f'Neuron{i}')
            self.__pc_labels.append(f'PC{i + 1}')

        for i in range(number_of_cords):
            used_no_method_cords.append(i)
            used_t_sne_components.append(i)
            used_PCA_components.append(i)
            self.__axis_labels.append(axis_default_names[i])

        self.__layer_config['apply_changes'] = False
        self.__layer_config['layer_name'] = self.__layer_name
        self.__layer_config['number_of_dimensions'] = self.__number_of_dimension
        self.__layer_config['max_visible_dim'] = number_of_cords
        self.__layer_config['visible_cords'] = self.__used_cords
        self.__layer_config['axis_labels'] = self.__axis_labels
        self.__layer_config['locked_view'] = False
        self.__layer_config['cords_changed'] = False
        self.__layer_config['color_labels'] = False
        self.__layer_config['number_of_samples'] = 0
        if number_of_cords >= 3:
            self.__layer_config['draw_3d'] = True
        else:
            self.__layer_config['draw_3d'] = False
        self.__layer_config['used_method'] = 'No method'
        self.__layer_config['config_selected_method'] = 'No method'

        no_method_config = {'displayed_cords': used_no_method_cords}
        pca_config = {'displayed_cords': used_PCA_components,
                      'n_possible_pc': 0,
                      'percentage_variance': None,
                      'largest_influence': None,
                      'options_used_components': used_PCA_components.copy()}

        number_t_sne_components = min(self.__number_of_dimension, 3)
        used_config = {'n_components': number_t_sne_components, 'perplexity': 30, 'early_exaggeration': 12.0,
                       'learning_rate': 200, 'n_iter': 1000}
        parameter_borders = {'n_components': (1, int, number_t_sne_components),
                             'perplexity': (0, float, float("inf")),
                             'early_exaggeration': (0, float, 1000),
                             'learning_rate': (float("-inf"), float, float("inf")),
                             'n_iter': (250, int, float("inf"))
                             }

        t_sne_config = {'used_config': used_config, 'options_config': used_config.copy(),
                        'parameter_borders': parameter_borders,
                        'displayed_cords': used_t_sne_components}
        self.__layer_config['no_method_config'] = no_method_config
        self.__layer_config['PCA_config'] = pca_config
        self.__layer_config['t_SNE_config'] = t_sne_config

        self.__layer_config['possible_polygon'] = False
        self.__layer_config['show_polygon'] = False

    def apply_changes(self):
        '''
        Popis
        --------
        Aplikovanie zmien po prepočítaní súradníc.
        '''
        # Je potrbné podľa navolených zobrazovaných súradníc priradiť z prepočítaných jednotlivé súradnice do súradníc
        # zobrazovaných.
        self.set_used_cords()
        if self.__has_points:
            used_method = self.__layer_config['used_method']
            if used_method == 'No method':
                self.apply_no_method()
            elif used_method == 'PCA':
                self.apply_PCA()
            elif used_method == "t-SNE":
                self.apply_t_SNE()
            self.set_points_for_graph()

    def set_points_for_graph(self):
        used_method = self.__layer_config['used_method']
        self.set_displayed_cords()
        if used_method == 'No method':
            self.set_displayed_cords_for_polygon()

    def set_used_cords(self):
        used_method = self.__layer_config['used_method']
        if used_method == 'No method':
            self.__used_cords = self.__layer_config['no_method_config']['displayed_cords']
        elif used_method == 'PCA':
            self.__used_cords = self.__layer_config['PCA_config']['displayed_cords']
        elif used_method == 't-SNE':
            self.__used_cords = self.__layer_config['t_SNE_config']['displayed_cords']

    def set_displayed_cords_for_polygon(self):
        if self.__polygon_cords_tuples is not None:
            if self.__graph_frame is not None:
                tmp1 = self.__polygon_cords_tuples[0][self.__used_cords].transpose()
                tmp2 = self.__polygon_cords_tuples[1][self.__used_cords].transpose()
                self.__graph_frame.plotting_frame.line_tuples = list(zip(tmp1, tmp2))

    def set_displayed_cords(self):
        self.__graph_frame.plotting_frame.points_cords = self.__points_method_cords[self.__used_cords]

    def apply_no_method(self):
        #self.__used_cords = self.__layer_config['no_method_config']['displayed_cords']
        self.__points_method_cords = self.__point_cords[self.__used_cords]

    def apply_PCA(self):
        pca_config = self.__layer_config['PCA_config']
        #self.__used_cords = pca_config['displayed_cords']
        points_cords = self.__point_cords.transpose()
        scaled_data = preprocessing.StandardScaler().fit_transform(points_cords)
        pca = PCA()
        pca.fit(scaled_data)
        pca_data = pca.transform(scaled_data)
        pcs_components_transpose = pca_data.transpose()
        self.__points_method_cords = pcs_components_transpose
        number_of_pcs_indexes = min(self.__number_of_dimension, pca.explained_variance_ratio_.size)
        if number_of_pcs_indexes > 0:
            self.__layer_config['PCA_config']['percentage_variance'] = pd.Series(
                np.round(pca.explained_variance_ratio_ * 100, decimals=1), index=self.__pc_labels[:number_of_pcs_indexes])
            self.__layer_config['PCA_config']['largest_influence'] = pd.Series(pca.components_[0], index=self.__neuron_labels)

    def apply_t_SNE(self):
        t_sne_config = self.__layer_config['t_SNE_config']
        #self.__used_cords = t_sne_config['displayed_cords']
        points_cords = self.__point_cords.transpose()
        number_of_components = t_sne_config['used_config']['n_components']
        tsne = TSNE(**t_sne_config['used_config'])
        transformed_cords = tsne.fit_transform(points_cords).transpose()
        print(transformed_cords)
        self.__points_method_cords = transformed_cords

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
            self.__layer_wrapper.clear()
            self.__hide_button.destroy()
            self.__layer_options_container = None
            self.__options_button = None
            self.__layer_wrapper = None
            self.__hide_button = None
            self.__visible = False

    def hide(self):
        self.clear()

    def show(self, parent, hide_command, show_options_command, *args, **kwargs):
        if self.__visible:
            self.clear()

        # self.__layer_wrapper = tk.LabelFrame(parent)
        self.__layer_wrapper = ResizableWindow(parent, width=412, relief='sunken')

        self.__layer_options_container = tk.Frame(self.__layer_wrapper.Frame)
        self.__layer_options_container.pack(side='top', fill='x')

        self.__options_button = ttk.Button(self.__layer_options_container,
                                           command=lambda: show_options_command(self.__layer_number),
                                           text='Options')
        self.__options_button.pack(side='left')
        self.__hide_button = ttk.Button(self.__layer_options_container,
                                        command=lambda: hide_command(self.__layer_number), text='Hide')
        self.__hide_button.pack(side='right')

        self.__graph_frame = GraphFrame(self.__layer_wrapper.Frame, self, *args, **kwargs)
        self.__graph_frame.pack()

        self.__graph_frame.initialize(self, self.__layer_name, self.__point_cords[self.__used_cords], self.__points_config,
                                      self.__layer_weights, self.__layer_biases)
        self.__graph_frame.pack(fill='both', expand=True)

        self.__visible = True

        self.use_config()
        self.apply_changes()

    def signal_change(self):
        self.__logic_layer.signal_change_on_layer(self.__layer_number)

    def set_polygon_cords(self):
        self.__logic_layer.set_polygon_cords(self.__layer_number)
        self.apply_changes()

    def require_graphs_redraw(self):
        self.__logic_layer.redraw_active_graphs(-1)

    def redraw_graph_if_active(self):
        if self.__graph_frame is not None:
            self.__graph_frame.redraw_graph()

    def use_config(self):
        if self.__visible:
            if self.__layer_config['apply_changes']:
                print('zmenene')
                self.apply_changes()
                self.__layer_config['cords_changed'] = False
                self.__layer_config['apply_changes'] = False
            elif self.__layer_config['cords_changed']:
                self.set_used_cords()
                self.set_points_for_graph()
            self.__graph_frame.apply_config(self.__layer_config)

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
    def layer_number(self):
        return self.__layer_number

    @layer_number.setter
    def layer_number(self, new_value):
        self.__layer_number = new_value

    @property
    def config(self):
        return self.__layer_config

    @property
    def points_cords(self):
        return self.__point_cords

    @points_cords.setter
    def point_cords(self, new_cords):
        self.__point_cords = new_cords
        self.__layer_config['number_of_samples'] = len(new_cords.transpose())
        if self.__point_cords.size == 0:
            self.__has_points = False
        else:
            self.__has_points = True

    @property
    def polygon_cords_tuples(self):
        return self.__polygon_cords_tuples

    @property
    def possible_polygon(self):
        return self.__layer_config['possible_polygon']

    @possible_polygon.setter
    def possible_polygon(self, value):
        self.__layer_config['possible_polygon'] = value

    @polygon_cords_tuples.setter
    def polygon_cords_tuples(self, new_cords_tuples):
        self.__polygon_cords_tuples = new_cords_tuples
        if self.__polygon_cords_tuples is not None:
            self.__layer_config['possible_polygon'] = True
        else:
            self.__layer_config['possible_polygon'] = False
            self.__displayed_lines_cords = None

    @property
    def layer_weights(self):
        return self.__layer_weights

    @property
    def layer_biases(self):
        return self.__layer_biases

    @property
    def calculate_polygon(self):
        return self.__calculate_polygon

    @calculate_polygon.setter
    def calculate_polygon(self, value):
        self.__calculate_polygon = value

    @property
    def point_colour(self):
        return self.__points_colour

    @point_colour.setter
    def point_colour(self, new_value):
        self.__points_colour = new_value


class GraphFrame(tk.LabelFrame):
    def __init__(self,  parent, neural_layer: NeuralLayer, *args, **kwargs):
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

        self.__graph = PlotingFrame(self, self, height=420)
        self.__weight_controller = LayerWeightControllerFrame(self, self)

    def initialize(self, neural_layer: int, layer_name: str, point_cords: list, points_config: dict,
                   layer_weights: list, layer_bias: list):
        self.__neural_layer = neural_layer
        self.__graph.initialize(point_cords, points_config, layer_name)
        self.__weight_controller.initialize(layer_weights, layer_bias)

        self.__graph.pack(side=tk.TOP, fill='both', expand=True)
        self.__weight_controller.pack(side=tk.BOTTOM, fill='both', expand=True)

    def redraw_graph(self):
        self.__graph.update_graph()

    def hide_graph_frame(self):
        self.__neural_layer.hide_graph_frame()

    def clear(self):
        """
        Popis
        --------
        Vyčistenie pri mazaní okna.
        """
        self.pack_forget()
        self.__weight_controller.clear()
        self.__graph.clear()
        self.__weight_controller = None
        self.__neural_layer = None
        self.__graph = None

    def controller_signal(self):
        """
        Popis
        --------
        Posúva signál o zmene váhy neurónovej vrstve.
        """

        self.__neural_layer.signal_change()

    def apply_config(self, config):
        if config['used_method'] == 'No method':
            self.__graph.draw_polygon = config['show_polygon']
        else:
            self.__graph.draw_polygon = False
        self.__graph.locked_view = config['locked_view']
        self.__graph.graph_labels = config['axis_labels']
        self.__graph.is_3d_graph = config['draw_3d']
        self.__graph.set_color_label(config['color_labels'])
        self.redraw_graph()

    @property
    def plotting_frame(self):
        return self.__graph

    def require_graphs_redraw(self):
        self.__neural_layer.require_graphs_redraw()


app = VisualizationApp()
app.mainloop()



