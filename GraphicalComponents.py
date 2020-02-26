import math
import tkinter as tk
from tkinter import ttk

class ScrollableWindow(tk.Frame):
    def __init__(self, parent, orientation):
        tk.Frame.__init__(self, parent, bg='#ffffff')
        self.Orientation = orientation
        self.WindowItems = {}

        canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.WindowItems['Canvas'] = canvas

        vsb = None
        if orientation == 'horizontal':
            vsb = tk.Scrollbar(self, orient="horizontal", command=canvas.xview, background='#ffffff')
            vsb.pack(side='bottom', fill='x')
        elif orientation == 'vertical':
            vsb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
            vsb.pack(side='right', fill='y')
        else:
            raise Exception("Scrollable window: unknown orientation '{}'".format(orientation))

        self.WindowItems['Scrollbar'] = vsb
        frame = tk.LabelFrame(canvas, background="#ffffff")
        self.WindowItems['Frame'] = frame
        canvas.pack(fill='both', expand=True)

        self.CanvasFrameId = canvas.create_window((0, 0), window=frame, anchor="nw",
                                   tags="self.frame")
        frame.bind("<Configure>", self.onFrameConfigure)
        canvas.bind("<Configure>", self.canvasChange)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        if self.Orientation == 'horizontal':
            self.WindowItems['Canvas'].configure(scrollregion=self.WindowItems['Canvas'].bbox("all"), xscrollcommand=self.WindowItems['Scrollbar'].set)
        else:
            self.WindowItems['Canvas'].configure(scrollregion=self.WindowItems['Canvas'].bbox("all"),
                                                 yscrollcommand=self.WindowItems['Scrollbar'].set)

    def canvasChange(self, event):
        if self.Orientation == 'horizontal':
            self.WindowItems['Canvas'].itemconfig(self.CanvasFrameId, height=event.height)
        else:
            self.WindowItems['Canvas'].itemconfig(self.CanvasFrameId, width=event.width)

    def __del__(self):
        print('Mazanie scrollable')


class ClickableSlider(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        if 'text' in kwargs:
            tk.LabelFrame.__init__(self, parent, text=kwargs.pop('text'), bg='#fafafa')
        else:
            tk.LabelFrame.__init__(self, parent)
        showvalue = kwargs.pop('showvalue', True)
        if showvalue:
            kwargs['showvalue'] = False
            self.Start = 0
            self.Ending = 100
            if 'to' in kwargs:
                self.Ending = kwargs['to']
            if 'from_' in kwargs:
                self.Start = kwargs['from_']
            self.extent = self.Ending - self.Start
            self.digits = kwargs.pop('digits', '0')
            if 'resolution' in kwargs:
                resolution = kwargs['resolution']
                tmp = (resolution % 1)
                if tmp:
                    tmp = -1 - math.log10(tmp)
                    if tmp >= self.digits - 1:
                        kwargs['resolution'] = math.pow(0.1, self.digits - 1)

            if 'command' in kwargs:
                # add self.display_value to the command
                fct = kwargs['command']

                def cmd(value):
                    print(value)
                    self.display_value(value)
                    fct(value)

                kwargs['command'] = cmd
            else:
                kwargs['command'] = self.display_value
            self.CallBackFunction = kwargs['command']
            self.Slider = tk.Scale(self, orient=tk.HORIZONTAL, **kwargs)
            self.Slider.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

            style = ttk.Style(self)

            style_name = kwargs.get('style', '%s.TScale' % (str(self.Slider.cget('orient')).capitalize()))
            self.sliderlength = style.lookup(style_name, 'sliderlength', default=20)

            tk.Label(self, text=' ', bg=self['bg'], height=0, pady=0, padx=0).pack(side=tk.TOP)
            self.ClickableLabelContainer = tk.Frame(self)
            self.Entry = tk.Entry(self.ClickableLabelContainer, width=4, background=self['bg'])
            self.ValueLabel = tk.Label(self.ClickableLabelContainer, text='0', bg=self['bg'])
            self.ValueLabel.pack(side=tk.TOP)
            self.ClickableLabelContainer.place(in_=self.Slider, bordermode='outside', x=0, y=0, anchor='s')
            self.ValueLabel.bind('<Enter>', self.show_label_entry)
            self.Entry.bind('<Return>', self.validate_entry)
            self.Entry.bind('<Leave>', self.on_entry_leave)
            self.Slider.bind('<Configure>', self.on_configure)
        else:
            kwargs['showvalue'] = False
            self.Slider = tk.Scale(self, orient=tk.HORIZONTAL, **kwargs)
            self.Slider.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def convert_to_pixels(self, value):
        return (((value - self.Start) / self.extent) * (
                    self.Slider.winfo_width() - 2 * self.sliderlength) + self.sliderlength)

    def display_value(self, value):
        x = self.convert_to_pixels(float(value))
        self.ClickableLabelContainer.place_configure(x=x)
        formatter = '{:.' + str(self.digits - 1) + 'f}'
        self.ValueLabel.configure(text=formatter.format(float(value)))

    def validate_entry(self, event):
        try:
            if not (self.Start <= float(self.Entry.get()) <= self.Ending):
                return False
            self.Slider.set(float(self.Entry.get()))
            return True
        except ValueError:
            return False

    def on_configure(self, event):
        self.display_value(self.Slider.get())

    def show_label_entry(self, event):
        self.ValueLabel.pack_forget()
        self.Entry.delete(0, tk.END)
        self.Entry.insert(0, self.Slider.get())
        self.Entry.pack()

    def on_entry_leave(self, event):
        self.Entry.pack_forget()
        self.ValueLabel.pack()

    def get_value(self):
        return self.Slider.get()

    def __del__(self):
        print('Mazanie clickable')


class ModifiedClickableSlider(ClickableSlider):
    def __init__(self, parent, *args, **kwargs):
        ClickableSlider.__init__(self, parent, *args, **kwargs)
        self.WeightList = None
        self.Index = None

    def set_variable(self, varList, index):
        self.WeightList = varList
        self.Index = index

    def display_value(self, value):
        if self.WeightList:
            self.WeightList[self.Index] = float(value)
        super().display_value(value)

    def validate_entry(self, event):
        if super().validate_entry(event):
            if self.WeightList:
                self.WeightList[self.Index] = float(super().get_value())