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
import weakref
import sys
from GraphicalComponents import *

LARGE_FONT = ('Verdana', 12)
#style.use('seaborn-whitegrid')
tmp = None

class VisualizationApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        super().geometry('%dx%d+0+0' % (super().winfo_screenwidth() - 8 , super().winfo_screenheight() - 70))
        self.title('Bakalarka')
        container = tk.Frame(self)

        container.pack(side='top', fill='both', expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, GraphPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame(GraphPage)

        print(self.winfo_children())

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Start Page', font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        button3 = ttk.Button(self, text='Graph Page',
                             command=lambda: controller.show_frame(GraphPage))
        button3.pack()

class GraphLogicLayer:
    def __init__(self, parent):
        self.GraphPage = parent
        self.GraphAreaFrame = tk.LabelFrame(self.GraphPage, relief='sunken')
        self.GraphAreaFrame.pack(side='bottom', fill='both', expand=True)
        self.InputFrame = InputDataFrame(self.GraphAreaFrame, self)

        self.InputFrame.pack(side='left', fill='y')
        self.NumberOfPoints = 0
        self.NumberOfBufferedLayers = 0

        self.NumberOfLayers = 0
        # second DIM is layer  third are cords
        self.NNStructure = None
        self.Points = []
        self.LayerPointsValues = []
        self.Layers = []
        self.Weights = []
        self.Bias = []
        # print(self.Points)

        self.scrollFrame = ScrollableWindow(self.GraphAreaFrame, 'horizontal')
        self.scrollFrame.pack(side='right', fill=tk.BOTH, expand=True)

        graph_container_frame = self.scrollFrame.WindowItems['Frame']

        self.initialize([[2], [3], [2], [3], [3]])

    def initialize(self, NNStructure):
        print('tu som')
        self.NNStructure = NNStructure
        self.NumberOfLayers = len(NNStructure)
        self.LayerPointsValues = [[[] for y in range(layer[0])] for layer in NNStructure]
        self.Points = [[] for x in range(NNStructure[0][0])]
        self.LayerPointsValues[0] = self.Points
        self.InputFrame.initialize(NNStructure[0][0])

        if self.NumberOfBufferedLayers < len(NNStructure):
            missing_Layers = len(NNStructure) - self.NumberOfBufferedLayers
            self.NumberOfBufferedLayers = len(NNStructure)
            print('Vyrabam', missing_Layers, 'novych vrstiev')
            graph_container_frame = self.scrollFrame.WindowItems['Frame']
            for i in range(missing_Layers):
                self.Layers.append(NeuralLayer(graph_container_frame, self))


        self.Weights = []
        self.Bias = []
        for layerNumber, layer in enumerate(NNStructure):
            if layerNumber < self.NumberOfLayers - 1:
                self.Weights.append([])
                self.Bias.append([])
                for endNeuronNumber in range(NNStructure[layerNumber+1][0]):
                    self.Bias[layerNumber].append(0)
            else:
                break
            for startNeuronNumber in range(layer[0]):
                    self.Weights[layerNumber].append([])
                    for endNeuronNumber in range(NNStructure[layerNumber + 1][0]):
                        self.Weights[layerNumber][startNeuronNumber].append(0)

        for i in range(NNStructure[0][0]):
            for j in range(4000):
                self.Points[i].append(j)

        self.recalculate_cords()
        print(self.LayerPointsValues)

        for i, neuralLayer in enumerate(self.Layers):
            if i < self.NumberOfLayers - 1:
                neuralLayer.initialize(NNStructure[i][0], i, self.LayerPointsValues[i], self.Weights[i], self.Bias[i])
            else:
                neuralLayer.initialize(NNStructure[i][0], i, self.LayerPointsValues[i])
            neuralLayer.pack(side='left', fill=tk.BOTH, expand=True)

    def recalculate_cords(self):
        for layerNumber, layerPoints in enumerate(self.LayerPointsValues):
            if layerNumber < self.NumberOfLayers - 1:
                na = np.array(layerPoints).transpose()
                print(na)
                b = np.array(self.Weights[layerNumber])

                tmp = na.dot(b)
                vec = np.array(self.Bias[layerNumber])
                result = np.empty_like(tmp)
                for i in range(tmp.shape[0]):
                    result[i, :] = tmp[i, :] + vec

                self.LayerPointsValues[layerNumber + 1][:] = result.transpose().tolist()
            else:
                break
        print(self.LayerPointsValues)
        for layer in self.Layers:
            layer.apply_changes()

    def addGraph(self):
        tmpGraph = GraphFrame(self.scrollFrame.WindowItems['Frame'], self, 2)
        tmpGraph.pack(side='left', fill=tk.BOTH, expand=True)
        self.Graphs.append(tmpGraph)

    def removeGraph(self, graph):
        self.Graphs.remove(graph)
        print(len(self.Graphs))

    def destroyAllGraphs(self):
        self.Graphs = []

    def updateGraphs(self):
        for layer in self.Layers:
            layer.apply_changes()

    def addPoint(self, *args):
        self.NumberOfPoints += 1
        print(args)
        for cord in range(len(self.Points)):
            self.Points[cord].append(args[cord])

        print(self.LayerPointsValues)

    def test(self):
        #print(self.Weights)
        #print(self.Bias)
        self.recalculate_cords()

class GraphPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text='Graph Page', font=LARGE_FONT)
        label.pack()
        self.LogicLayer = GraphLogicLayer(self)
        button1 = ttk.Button(self, text='Back to home',
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()


class InputDataFrame(tk.LabelFrame):
    def __init__(self, parent, logicalLayer):
        self.GraphLogic = logicalLayer
        tk.LabelFrame.__init__(self, parent, width=300)
        self.pack_propagate(0)
        but = tk.Button(self, text='Show points', command=self.GraphLogic.updateGraphs)
        but.pack()

        self.EntriesList = []
        but1 = tk.Button(self, text='Add point', command=self.addPoint)
        but1.pack()

        but2 = tk.Button(self, text='Test', command=self.GraphLogic.test)
        but2.pack()

    def initialize(self, numberOfInputs):
        for entry in self.EntriesList:
            entry.destroy()
            entry = None
        self.EntriesList = []

        for entry in range(numberOfInputs):
            entry = tk.Entry(self, width=10)
            entry.pack(side=tk.TOP)
            self.EntriesList.append(entry)

    def addPoint(self):
        inputList = []
        for entry in self.EntriesList:
            value = entry.get()
            if value:
                value = float(value)
            else:
                value = 0
            inputList.append(value)
            entry.delete(0, tk.END)
        self.GraphLogic.addPoint(*inputList)

class NeuralLayer:
    def __init__(self, parent, logicLayer, *args, **kwargs):
        self.GraphFrame = GraphFrame(parent, *args, **kwargs)
        self.LogicLayer = logicLayer
        self.LayerNumber = -1
        self.NumberOfDimension = -1
        self.PointCords = []

    def pack(self, *args, **kwargs):
        self.GraphFrame.pack(*args, **kwargs)

    def initialize(self, numOfDim, layerNumber, layerPoinCords, layerWeights = None, layerBias = None):
        # print('Toto je vrstva cislo {} ma zobrazovat {} dimenzii'.format(layerNumber, numOfDim))
        # print('Vahy vyzeraju nasledovne')
        # print(layerWeights)
        self.NumberOfDimension = numOfDim
        self.LayerNumber = layerNumber
        self.PointCords = layerPoinCords
        self.GraphFrame.initialize(self, self.NumberOfDimension, self.PointCords, layerWeights, layerBias)

    def apply_changes(self):
        self.GraphFrame.apply_changes()


class GraphFrame(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.NeuralLayer = None
        self.LayerNumber = -1
        self.NumberOfDim = -1

        self.Graph = LayerGraphFrame(self)
        self.WeightController = LayerWeightControllerFrame(self)


    def initialize(self, neuralLayer, numOfDimensions, pointCords, layerWeights, layerBias):
        self.NeuralLayer = neuralLayer
        self.Graph.initialize(numOfDimensions, pointCords)
        self.WeightController.initialize(layerWeights, layerBias)

        self.Graph.pack(side=tk.TOP)
        self.WeightController.pack(side=tk.TOP, fill='both', expand=True)

    def apply_changes(self):
        self.Graph.update_graph()

class LayerGraphFrame(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.Cords = [[], [], []]

        self.NumberOfDim = -1

        self.GraphTitle = 'Graf'
        self.GraphLabels = ['Label X', 'Label Y', 'Label Z']

        self.FrameItems = {}

        self.FrameItems['DimChangeBut'] = ttk.Button(self, command=self.change_graph_dimension)

        graphContainerFrame = tk.LabelFrame(self, relief=tk.FLAT)
        self.FrameItems['GraphContainer'] = graphContainerFrame

        self.f = Figure(figsize=(4, 4), dpi=100)
        canvas = FigureCanvasTkAgg(self.f, graphContainerFrame)
        self.FrameItems['GraphCanvas'] = canvas

        canvas.draw()
        self.ax = None
        self.is2DGraph = True

        backend_bases.NavigationToolbar2.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to  previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        )

        self.Toolbar = NavigationToolbar2Tk(canvas, graphContainerFrame)
        self.Toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.Changed = False
        self.ani = animation.FuncAnimation(self.f, self.update_changed, interval=100)

    def initialize(self, numberOfDim, pointCords):
        self.Cords = pointCords
        self.FrameItems['DimChangeBut'].pack(side=tk.TOP)
        self.FrameItems['GraphContainer'].pack(side=tk.TOP)
        self.set_graph_dimension(numberOfDim)

    def change_graph_dimension(self):
        if self.is2DGraph:
            self.set_graph_dimension(3)
        else:
            self.set_graph_dimension(2)

    def update_changed(self, i):
        if self.Changed:
            self.redraw_graph()
            self.Changed = False
        else:
            self.ani.event_source.stop()

    def update_graph(self):
        self.Changed = not self.Changed
        self.ani.event_source.start()

    def redraw_graph(self):
        self.ax.clear()
        self.ax.grid()
        if self.NumberOfDim == 3:
            if len(self.Cords) > 2:
                self.ax.scatter(self.Cords[0], self.Cords[1], self.Cords[2])
            else:
                self.ax.scatter(self.Cords[0], self.Cords[1])
            self.ax.set_zlabel(self.GraphLabels[2])
        else:
            # tmp = np.zeros(len(self.Cords[0])).tolist()
            self.ax.scatter(self.Cords[0], self.Cords[1])
        self.ax.set_title(self.GraphTitle)
        self.ax.set_xlabel(self.GraphLabels[0])
        self.ax.set_ylabel(self.GraphLabels[1])

    def set_graph_dimension(self, dimension):
        if dimension == 3:
            self.is2DGraph = False
        else:
            self.is2DGraph = True
        text = ''
        self.f.clf()

        if self.is2DGraph:
            self.ax = self.f.add_subplot(111)
            self.NumberOfDim = 2
            self.FrameItems['GraphContainer'].pack()
            text = 'Make 3D'
            for item in self.Toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack(side='left')
        else:
            self.FrameItems['GraphContainer'].pack()
            self.ax = self.f.add_subplot(111, projection='3d')
            self.NumberOfDim = 3
            text = 'Make 2D'
            for item in self.Toolbar.winfo_children():
                if not isinstance(item, tk.Label):
                    item.pack_forget()
                else:
                    item.pack(pady=(4, 5))

        self.GraphTitle = 'Graph {}D'.format(self.NumberOfDim)
        self.Changed = True
        self.FrameItems['DimChangeBut'].configure(text=text)
        self.ani.event_source.start()


class LayerWeightControllerFrame(tk.LabelFrame):
    def __init__(self, parent):
        tk.LabelFrame.__init__(self, parent)
        self.WeightsReference = None
        self.SliderList = []
        self.ScrollableWindow = ScrollableWindow(self, 'vertical')
        self.ScrollableWindow.pack(side='bottom', fill='both', expand=True)

    def initialize(self, layerWeights, layerBias):
        for weightSlider in self.SliderList:
            weightSlider.pack_forget()
            weightSlider.destroy()
        self.SliderList = []

        self.WeightsReference = layerWeights
        scroll_frame = self.ScrollableWindow.WindowItems['Frame']
        if layerWeights:
            for startNeuron in range(len(self.WeightsReference)):
                for endNeuron in range(len(self.WeightsReference[startNeuron])):
                    slider = ModifiedClickableSlider(scroll_frame, from_=-1, to=1, resolution=0.01, digits=3, text='Vaha{}-{}'.format(startNeuron, endNeuron))
                    slider.set_variable(layerWeights[startNeuron], endNeuron)
                    slider.pack(fill='x', expand=True, padx=(0, 2), pady=0)
                    self.SliderList.append(slider)
        if layerBias:
            for endNeuron in range(len(layerBias)):
                slider = ModifiedClickableSlider(scroll_frame, from_=-10, to=10, resolution=0.01, digits=3,
                                                 text='Bias {}'.format(endNeuron))
                slider.set_variable(layerBias, endNeuron)
                slider.pack(fill='x', expand=True, padx=(0, 2), pady=0)
                self.SliderList.append(slider)


    def vypis(self, value):
        print(self.WeightsReference)

# na = np.array([[1, 2, 3],
#          [4, 5, 6]]).transpose()
#
# vec = np.array([1, 2])
#
# result = np.empty_like(na)
# print(na.shape[0])
# for i in range(2):
#     result[i,:] = na[i, :] + vec
#
# print(result)
app = VisualizationApp()
app.mainloop()

