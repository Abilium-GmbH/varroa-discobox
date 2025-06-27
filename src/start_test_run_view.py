import tkinter as tk
from vmbpy import *
from datetime import date
import logging
import os

_logger = logging.getLogger(__name__)


class StartTestRunView(tk.Toplevel):

    def __init__(self, start_test_run):
        super().__init__()

        self.title('Start Test Run')
        self.resizable(width=False, height=False)

        self.start_test_run = start_test_run

        val = f'test_run_{date.today().strftime("%Y-%m-%d")}'
        self.name_value = tk.StringVar(master=self, value=val)
        self.name_value.trace_add('write', self.name_value_change)

        self._build_ui()

    def start(self):
        self.mainloop()

    def _build_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill="both", expand="true", padx=(10, 10), pady=(10, 10))
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='Test Run Name', anchor='w', width=20)
        label.pack(side='left', fill='both', expand='false')
        self.name_input = tk.Entry(frame, textvariable=self.name_value)
        self.name_input.pack(side='left', fill='both', expand='true')
        self.name_input.focus()

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        self.error_label = tk.Label(frame, text='', font=('Noto Sans', 9), fg='#ff0000', anchor='e')
        
        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false', pady=(5, 0))
        button = tk.Button(self.frame, text='Start', command=self.action_start, width=8)
        button.pack(side='right', fill="both", expand="false")
        button = tk.Button(self.frame, text='Cancel', command=self.action_cancel, width=8)
        button.pack(side='right', fill="both", expand="false")

    def name_value_change(self, value, index, mode):
        name = self.name_value.get()
        if not name:
            self.error_label.configure(text='Enter a name for your Test Run.')
            self.error_label.pack(side='right', fill='both', expand='true')
        else:
            if os.path.isdir(f'output/{name}'):
                self.error_label.configure(text='A Test Run with this name already exists.')
                self.error_label.pack(side='right', fill='both', expand='true')
            else:
                self.error_label.pack_forget()

    def action_start(self):
        name = self.name_value.get()
        if not name or os.path.isdir(f'output/{name}'):
            return
        self.destroy()
        self.start_test_run(name)
    
    def action_cancel(self):
        self.destroy()
