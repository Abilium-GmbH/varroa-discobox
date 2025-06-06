import tkinter as tk
from tkinter import ttk
from vmbpy import *
import logging
from tkinter import font

from .controller import DiscoboxController
from .settings import Settings

_logger = logging.getLogger(__name__)


class SettingsView(tk.Toplevel):

    def __init__(self, master, settings: Settings, update_settings):
        super().__init__(master=master)
        self.title('Settings')
        self.resizable(width=False, height=False)
        self.ctrl = DiscoboxController()

        self.time_value = tk.StringVar(value=str(settings.time))
        self.time_value.trace_add(mode='write', callback=self.time_value_change)
        self.fps_value = tk.StringVar(value=str(settings.fps))
        self.fps_value.trace_add(mode='write', callback=self.fps_value_change)

        self.led1_on = settings.led1_on
        self.led1_value = tk.StringVar(value=str(settings.led1))
        self.led2_on = settings.led2_on
        self.led2_value = tk.StringVar(value=str(settings.led2))
        self.vent_on = settings.vent_on
        self.vent_value = tk.StringVar(value=str(settings.vent))

        self.settings = settings
        self.update_settings = update_settings

        self.style = ttk.Style(self)

        self._build_settings_ui()

    def _build_settings_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill='both', expand='true', padx=(10, 10), pady=(10, 10))
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)


        self.recording_settings_frame = tk.Frame(self.frame)
        self.recording_settings_frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(self.recording_settings_frame, text='Aufnahmeeinstellungen', font=('Noto Sans', 12, 'bold'), anchor='w')
        label.pack(side='top', fill='both', expand='false', pady=(0, 5))

        recording_settings = [
            ('Dauer (Sekunden)', self.time_value),
            ('FPS (Bilder pro Sekunde)', self.fps_value),
        ]

        for setting in recording_settings:
            frame = tk.Frame(self.recording_settings_frame)
            frame.pack(side='top', fill='x', expand='false')
            label = tk.Label(frame, text=setting[0], anchor='w', width=22)
            label.pack(side='left', fill='both', expand='false')
            input = tk.Entry(frame, textvariable=setting[1])
            input.pack(side='left', fill='both', expand='true')

        self.confirm_frame = tk.Frame(self.recording_settings_frame)
        button = tk.Button(self.confirm_frame, text='Anwenden', command=self.confirm)
        button.pack(side='right', fill='x', expand='false', padx=(5, 0))
        button = tk.Button(self.confirm_frame, text='Zurücksetzen', command=self.cancel, fg="#c40000")
        button.pack(side='right', fill='x', expand='false')


        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='LEDs und Ventilator', font=('Noto Sans', 12, 'bold'), anchor='w')
        label.pack(side='left', fill='y', expand='false', pady=(10, 5))

        led_vent_settings = [
            ('Led 1', 'On/Off', self.toggle_led_1, self.set_led_1, self.led1_value),
            ('Led 2', 'On/Off', self.toggle_led_2, self.set_led_2, self.led2_value),
            ('Fan', 'On/Off', self.toggle_vent, self.set_vent, self.vent_value),
        ]

        for setting in led_vent_settings:
            frame = tk.Frame(self.frame)
            frame.pack(side='top', fill='x', expand='false')
            label = tk.Label(frame, text=setting[0], anchor='w', width=8)
            label.pack(side='left', fill='both', expand='false')
            button = tk.Button(frame, text=setting[1], command=setting[2])
            button.pack(side='left', fill='both', expand='false')
            scale = tk.Scale(frame, variable=setting[4], to=255, orient='horizontal', command=setting[3], length=250, sliderlength=20)
            scale.pack(side='right', fill='both', expand='false')

    def time_value_change(self, value, index, mode):
        if self.settings.time != int(self.time_value.get()):
            self.confirm_frame.pack(side='top', fill='x', expand='false', pady=(5, 0))
        else:
            self.confirm_frame.pack_forget()

    def fps_value_change(self, *args, **kwargs):
        if self.settings.fps != int(self.fps_value.get()):
            self.confirm_frame.pack(side='top', fill='x', expand='false', pady=(5, 0))
        else:
            self.confirm_frame.pack_forget()
    
    def confirm(self):
        self.settings.time = int(self.time_value.get())
        self.settings.fps = int(self.fps_value.get())
        self.update_settings(self.settings)
        self.confirm_frame.pack_forget()
    
    def cancel(self):
        self.time_value.set(str(self.settings.time))
        self.fps_value.set(str(self.settings.fps))
        self.confirm_frame.pack_forget()

    def toggle_led_1(self):
        with self.ctrl as s:
            self.led1_on = not self.led1_on
            s.write(self.ctrl.set_led1_on(self.led1_on))
        self.settings.led1_on = self.led1_on
    
    def set_led_1(self, value):
        with self.ctrl as s:
            s.write(self.ctrl.set_led1(int(value)))
        self.settings.led1 = int(value)

    def toggle_led_2(self):
        with self.ctrl as s:
            self.led2_on = not self.led2_on
            s.write(self.ctrl.set_led2_on(self.led2_on))
        self.settings.led2_on = self.led2_on

    def set_led_2(self, value):
        with self.ctrl as s:
            s.write(self.ctrl.set_led2(int(value)))
        self.settings.led2 = int(value)
    
    def toggle_vent(self):
        with self.ctrl as s:
            self.vent_on = not self.vent_on
            s.write(self.ctrl.set_vent_on(self.vent_on))
        self.settings.vent_on = self.vent_on

    def set_vent(self, value):
        with self.ctrl as s:
            s.write(self.ctrl.set_vent(int(value)))
        self.settings.vent = int(value)
    