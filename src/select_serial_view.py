import tkinter as tk
from vmbpy import *
import logging

_logger = logging.getLogger(__name__)


class SelectSerialView(tk.Tk):

    def __init__(self, select_callback, serial_ports):
        super().__init__()

        self.title('Select Arduino Controller')
        self.resizable(width=False, height=False)
        self.serial_ports = serial_ports
        self.select_callback = select_callback
        self._build_ui()

    def start(self):
        self.mainloop()

    def _build_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill="both", expand="true", padx=(10, 10), pady=(10, 10))
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.serials = tk.Variable(value=[])
        self.serials.set(sorted([f'{port.manufacturer} [{port.device}]' for port in self.serial_ports]))
        self.serials_list = tk.Listbox(self.frame, listvariable=self.serials, selectmode='single', height=5, width=0)
        self.serials_list.pack(side='top', fill="x", expand="false", pady=10)
        if len(self.serial_ports) > 0:
            self.serials_list.selection_set(0)

        self.select_serial_button = tk.Button(self.frame, text='Select Controller', command=self.select_serial, width=15)
        self.select_serial_button.pack(side='top', fill="x", expand="false")

        self.no_serial_button = tk.Button(self.frame, text='Start without Controller', command=self.no_serial, width=15)
        self.no_serial_button.pack(side='top', fill="x", expand="false")

    def select_serial(self):
        selected = [self.serial_ports[i] for i in self.serials_list.curselection()]
        if len(selected) == 1:
            self.destroy()
            self.select_callback(selected[0].device)
    
    def no_serial(self):
        self.destroy()
        self.select_callback()
