import math
import tkinter as tk
from tkinter import ttk


class ScrollableWindow(tk.LabelFrame):
    def __init__(self, parent, orientation, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.__orientation = orientation

        self.__canvas = tk.Canvas(self, borderwidth=0, background="#ffffff", border=0, highlightthickness=0)

        vsb = None
        if orientation == 'horizontal':
            self.__scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.__canvas.xview)
            self.__scrollbar.pack(side='bottom', fill='x')
        elif orientation == 'vertical':
            self.__scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.__canvas.yview)
            self.__scrollbar.pack(side='right', fill='y')
        else:
            raise Exception("Scrollable window: unknown orientation '{}'".format(orientation))

        self.__inner_frame = tk.LabelFrame(self.__canvas, background="#ffffff", highlightthickness=0, border=0)
        self.__canvas.pack(fill='both', expand=True)

        self.__canvasFrameId = self.__canvas.create_window((0, 0), window=self.Frame, anchor="nw",
                                   tags="self.frame")
        self.__inner_frame.bind("<Configure>", self.on_frame_configure)
        self.__canvas.bind("<Configure>", self.canvas_change)

    def on_frame_configure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        if self.__orientation == 'horizontal':
            self.__canvas.configure(scrollregion=self.__canvas.bbox("all"), xscrollcommand=self.__scrollbar.set)
        else:
            self.__canvas.configure(scrollregion=self.__canvas.bbox("all"),
                                                 yscrollcommand=self.__scrollbar.set)

    def canvas_change(self, event):
        if self.__orientation == 'horizontal':
            self.__canvas.itemconfig(self.__canvasFrameId, height=event.height)
        else:
            self.__canvas.itemconfig(self.__canvasFrameId, width=event.width)

    def clear(self):
        self.__inner_frame.destroy()
        self.__scrollbar.destroy()
        self.__canvas.destroy()
        self.destroy()
        self.__orientation = None
        self.__inner_frame = None
        self.__scrollbar = None
        self.__canvas = None

    def __del__(self):
        print('Mazanie scrollable')

    @property
    def Frame(self):
        return self.__inner_frame


class ResizableWindow:
    def __init__(self, parent, possition='top', *args, **kwargs):
        self.__wrapper = tk.LabelFrame(parent, *args, **kwargs)
        self.__wrapper.pack_propagate(0)
        self.__upper_bar = tk.Frame(self.__wrapper)
        if possition == 'top':
            self.__upper_bar.pack(side=tk.TOP, fill='x')
            self.__dragger = tk.Frame(self.__upper_bar, width=5, height=5, bg='black')
        else:
            self.__upper_bar.pack(side=tk.BOTTOM, fill='x')
            self.__dragger = tk.Frame(self.__upper_bar, width=5, height=5, bg='black')
        self.__dragger.pack(side='right')
        self.__dragger._drag_start_x = 0
        self.__dragger._drag_start_y = 0
        self.__dragger.bind("<Button-1>", self.on_drag_start)
        # self.__dragger.bind("<Motion>", self.on_motion)
        self.__dragger.bind('<ButtonRelease-1>', self.on_drag_end)

    def on_drag_start(self, event):
        widget = event.widget
        widget._drag_start_x = event.x
        widget._drag_start_y = event.y

    def on_drag_end(self, event):
        widget = event.widget
        delta_x = event.x - widget._drag_start_x
        delta_y = event.y - widget._drag_start_y
        new_width = delta_x + self.__wrapper.winfo_width()
        new_height = delta_y + self.__wrapper.winfo_height()
        new_width = max(new_width, 100)
        new_height = max(new_height, 100)
        self.__wrapper.configure(width=new_width, height=new_height)

    def pack(self, *args, **kwargs):
        self.__wrapper.pack(*args, **kwargs)

    def clear(self):
        print('cistim resizable')
        self.__wrapper.destroy()
        self.__upper_bar.destroy()
        self.__dragger.destroy()
        self.__upper_bar = None
        self.__dragger = None

    @property
    def Frame(self):
        return self.__wrapper

    def __del__(self):
        print('mazem resizable')


class ComboboxAddRemoveFrame(tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)

        self.__default_text = ''
        self.__read_only = False
        self.__next_special_ID = None

        self.__all_values = {}
        self.__already_selected = []
        self.__ordered_values = []
        self.__backward_values = {}
        
        self.__combo_box = ttk.Combobox(self)
        self.__add_button = ttk.Button(self, text='Add', command=self.show_selected)

        self.grid_propagate(0)
        
        self.rowconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(2, weight=1)
        
        self.__combo_box.grid(row=1, column=1)
        self.__add_button.grid(row=2, column=1)
        self.__command = None

    def initialize(self, item_list, command=None, button_text: str='Add', read_only: bool = True, default_text: str = ''):
        self.__all_values = {}
        self.__already_selected = []
        self.__ordered_values = []
        self.__backward_values = {}
        self.__command = command
        self.__next_special_ID = 1

        self.__add_button.configure(text=button_text)
        self.__read_only = read_only
        self.__default_text = default_text
        if self.__read_only:
            self.__combo_box.configure(state='readonly')
        else:
            self.__combo_box.configure(state='normal')
        if self.__read_only and self.__default_text != '':
            self.__ordered_values.append(default_text)

        for i, item_name in enumerate(item_list):
            item_name = self.get_unique_name(item_name)
            self.__all_values[item_name] = i
            self.__ordered_values.append(item_name)
            self.__backward_values[i] = item_name
        self.__combo_box.configure(values=self.get_list_of_visible())

        if self.__read_only:
            if self.__default_text != '':
                self.__combo_box.current(0)
        else:
            self.__combo_box.set(self.__default_text)

        if self.__read_only and self.__default_text != '':
            return self.__ordered_values[1:]
        else:
            return self.__ordered_values

    def get_unique_name(self, item_name):
        if item_name in self.__all_values:
            new_name = item_name + ' ({})'
            number_of_copy = 1
            while True:
                if new_name.format(number_of_copy) in self.__all_values:
                    number_of_copy += 1
                    continue
                else:
                    item_name = new_name.format(number_of_copy)
                    break
        return item_name

    def get_list_of_visible(self):
        return [layer_name for layer_name in self.__ordered_values if layer_name not in self.__already_selected]

    def show_selected(self):
        selected = self.__combo_box.get()
        if self.__command and selected in self.__all_values:
            self.__command((self.__all_values[selected], selected))

    def update_list(self):
        visible_list = self.get_list_of_visible()
        self.__combo_box.configure(values=visible_list)
        if self.__read_only:
            if self.__default_text != '':
                self.__combo_box.current(0)
        else:
            self.__combo_box.set(self.__default_text)

    def hide_item(self, item_name):
        if item_name in self.__all_values:
            self.__already_selected.append(item_name)
            self.update_list()

    def show_item(self, item_name):
        if item_name in self.__already_selected:
            if self.__read_only:
                if self.__default_text != item_name:
                    self.__already_selected.remove(item_name)
                    self.update_list()
            else:
                self.__already_selected.remove(item_name)
                self.update_list()

    def add_special(self, item_name):
        new_list = []
        starting_index = 0
        if self.__read_only and self.__default_text != '':
            new_list.append(self.__default_text)
            starting_index += 1
        item_name = self.get_unique_name(item_name)
        new_list.append(item_name)
        new_list.extend(self.__ordered_values[starting_index:])
        self.__ordered_values = new_list
        self.__all_values[item_name] = -self.__next_special_ID
        self.__next_special_ID += 1
        self.update_list()
        return item_name


    def clear(self):
        self.__add_button.destroy()
        self.__combo_box.destroy()
        self.destroy()
        self.__already_selected = None
        self.__backward_values = None
        self.__add_button = None
        self.__all_values = None
        self.__combo_box = None
        self.__command = None

    def __del__(self):
        print('mazanie combobox')


class RewritableLabel(tk.Frame):
    def __init__(self, parent, id, enter_command, label_text, variable_text='',*args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.__id = id
        self.__name_variable = label_text + ' '
        self.__name_label = tk.Label(self, text=self.__name_variable)
        self.__name_label.pack(side='left')
        self.__changeable_label_frame = tk.Frame(self)
        self.__changeable_label_frame.pack(side='left')
        self.__variable_label = tk.Label(self.__changeable_label_frame, text=variable_text)
        self.__entry = tk.Entry(self.__changeable_label_frame)
        self.__variable_label.pack()
        self.__changeable_label_frame.pack()
        self.__variable_label.bind('<Double-1>', self.show_entry)
        self.__enter_function = enter_command
        self.__entry.bind('<Return>', self.on_enter)
        self.__entry.bind('<Escape>', self.show_variable_label)
        self.__mark_changed = False
        self.__variable_value = variable_text

    def on_enter(self, event):
        self.__enter_function(self.__id, self.__entry.get())

    def set_label_name(self, name):
        self.__name_variable = name + ' '
        self.__name_label.configure(text=self.__name_variable)

    def show_entry(self, event):
        self.__variable_label.pack_forget()
        self.set_entry_text(self.__variable_label.cget('text'))
        self.__entry.pack()

    def set_entry_text(self, text=''):
        self.__entry.delete(0, tk.END)
        self.__entry.insert(0, text)

    def set_variable_label(self, value):
        self.__variable_label.configure(text=value)
        self.__variable_value = value

    def show_variable_label(self, event=None):
        self.__entry.pack_forget()
        self.__variable_label.pack()

    def set_entry_width(self, new_width):
        self.__entry.configure(width=new_width)

    def get_variable_value(self):
        return self.__variable_value

    def set_mark_changed(self, value):
        self.__mark_changed = value
        if self.__mark_changed:
            self.__name_label.configure(text=self.__name_variable[:-1] + "*", foreground='red')
        else:
            self.__name_label.configure(text=self.__name_variable, foreground='black')


class ClickableSlider(tk.LabelFrame):
    def __init__(self, parent, slider_id, hide_command, *args, **kwargs):
        if 'text' in kwargs:
            tk.LabelFrame.__init__(self, parent, text=kwargs.pop('text'), bg='#fafafa', height=57)
        else:
            tk.LabelFrame.__init__(self, parent)
        showvalue = kwargs.pop('showvalue', True)
        if showvalue:
            kwargs['showvalue'] = False

            self.__slider_id = slider_id
            self.__start = 0
            self.__ending = 100

            if 'to' in kwargs:
                self.__ending = kwargs['to']
            if 'from_' in kwargs:
                self.__start = kwargs['from_']

            self.__extent = self.__ending - self.__start
            self.__digits = kwargs.pop('digits', '0')

            if 'resolution' in kwargs:
                resolution = kwargs['resolution']
                tmp = (resolution % 1)
                if tmp:
                    tmp = -1 - math.log10(tmp)
                    if tmp >= self.__digits - 1:
                        kwargs['resolution'] = math.pow(0.1, self.__digits - 1)

            if 'command' in kwargs:
                # add self.display_value to the command
                fct = kwargs['command']

                def cmd(value):
                    self.display_value(value)
                    fct(value)

                kwargs['command'] = cmd
            else:
                kwargs['command'] = self.display_value
            self.__call_back_function = kwargs['command']
            self.__slider_wrapper = tk.LabelFrame(self, border=0)
            self.__slider_wrapper.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
            self._slider = tk.Scale(self.__slider_wrapper, orient=tk.HORIZONTAL, **kwargs)
            self._slider.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            style = ttk.Style(self)

            style_name = kwargs.get('style', '%s.TScale' % (str(self._slider.cget('orient')).capitalize()))
            self.__slider_length = style.lookup(style_name, 'sliderlength', default=20)

            start_color = "#dddddd"
            self.__hide_button = tk.Label(self.__slider_wrapper, text='X', fg='red', background=start_color, relief='raised')
            tk.Label(self, text=' ', bg=self['bg'], height=0, pady=0, padx=0).pack(side=tk.TOP)
            self.__clickable_label_container = tk.Frame(self)
            self.__entry = ttk.Entry(self.__clickable_label_container, width=4, background=self['bg'])
            self.__value_label = ttk.Label(self.__clickable_label_container, text='0', background=self['bg'])

            self.__value_label.bind('<Enter>', self.show_label_entry)
            self.__entry.bind('<Return>', self.validate_entry)
            self.__entry.bind('<Leave>', self.on_entry_leave)
            self._slider.bind('<Configure>', self.on_configure)
            self.__hide_button.bind('<Enter>', lambda event: self.__hide_button.configure(background='#cccccc'))
            self.__hide_button.bind('<Leave>', lambda event: self.__hide_button.configure(background=start_color))
            self.__hide_button.bind('<Button-1>', lambda event: hide_command(self.__slider_id))

            self.__value_label.pack(side=tk.TOP)
            self.__clickable_label_container.place(in_=self._slider, bordermode='outside', x=0, y=0, anchor='s')
            self.__hide_button.pack(side='left', padx=(0, 4), pady=(0, 2))

        else:
            kwargs['showvalue'] = False
            self._slider = tk.Scale(self, orient=tk.HORIZONTAL, **kwargs)
            self._slider.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def test(self, event):
        print(event)

    def convert_to_pixels(self, value):
        return (((value - self.__start) / self.__extent) * (
                self._slider.winfo_width() - 2 * self.__slider_length) + self.__slider_length)

    def display_value(self, value):
        x = self.convert_to_pixels(float(value))
        self.__clickable_label_container.place_configure(x=x)
        formatter = '{:.' + str(self.__digits - 1) + 'f}'
        self.__value_label.configure(text=formatter.format(float(value)))

    def validate_entry(self, event):
        try:
            if not (self.__start <= float(self.__entry.get()) <= self.__ending):
                return False
            self._slider.set(float(self.__entry.get()))
            return True
        except ValueError:
            return False

    def on_configure(self, event):
        self.display_value(self._slider.get())

    def show_label_entry(self, event):
        self.__value_label.pack_forget()
        self.__entry.delete(0, tk.END)
        self.__entry.insert(0, self._slider.get())
        self.__entry.pack()

    def on_entry_leave(self, event):
        self.__entry.pack_forget()
        self.__value_label.pack()

    def get_value(self):
        return self._slider.get()

    def __del__(self):
        print('Mazanie clickable')

    def clear(self):
        if self.__clickable_label_container:
            self.__clickable_label_container.destroy()
        if self.__hide_button:
            self.__hide_button.destroy()
        if self.__entry:
            self.__entry.destroy()
        if self.__slider_wrapper:
            self.__slider_wrapper.destroy()
        self._slider.destroy()
        self.destroy()
        self.__clickable_label_container = None
        self.__call_back_function = None
        self.__slider_wrapper = None
        self.__slider_length = None
        self.__hide_button = None
        self.__slider_id = None
        self.__ending = None
        self.__extent = None
        self.__digits = None
        self._slider = None
        self.__entry = None
        self.__start = None


class ModifiedClickableSlider(ClickableSlider):
    def __init__(self, parent, *args, **kwargs):
        ClickableSlider.__init__(self, parent, *args, **kwargs)
        self.__weight_list = None
        self.__index = None

    def set_variable(self, varList, index):
        self.__weight_list = varList
        self.__index = index
        self._slider.set(varList[index])
        self.display_value(varList[index])

    def display_value(self, value):
        if self.__weight_list is not None:
            self.__weight_list[self.__index] = float(value)
        super().display_value(value)

    def validate_entry(self, event):
        if super().validate_entry(event):
            if self.__weight_list is not None:
                self.__weight_list[self.__index] = float(super().get_value())

    def clear(self):
        self.__weight_list = None
        self.__index = None
        super().clear()
