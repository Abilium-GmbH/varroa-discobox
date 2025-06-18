import tkinter as tk
from vmbpy import *
import logging

from .controller import DiscoboxController
from .settings import Settings
from .camera_utils import get_feature, set_feature

_logger = logging.getLogger(__name__)


# These numbers are set according to the limitations of the Camera (Mako G-319B)
FRAME_COUNT_RANGE = (1, 65535)
FPS_RANGE = (1, 33)


class SettingsView(tk.Toplevel):

    def __init__(self, master, cam: Camera, settings: Settings):
        super().__init__(master=master)
        self.title('Settings')
        self.resizable(width=False, height=False)
        self.ctrl = DiscoboxController()
        self.cam = cam

        self.frame_count_value = tk.StringVar(value=str(settings.frame_count))
        self.frame_count_value.trace_add(mode='write', callback=self.frame_count_value_change)
        fps = get_feature(self.cam, 'AcquisitionFrameRateAbs')
        self.fps_value = tk.StringVar(value=str(fps))
        self.fps_value.trace_add(mode='write', callback=self.fps_value_change)

        self.led1_on = settings.led1_on
        self.led1_value = tk.StringVar(value=str(settings.led1))
        self.led2_on = settings.led2_on
        self.led2_value = tk.StringVar(value=str(settings.led2))
        self.vent_on = settings.vent_on
        self.vent_value = tk.StringVar(value=str(settings.vent))

        self.settings = settings

        self._build_settings_ui()

    def _build_settings_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill='both', expand='true', padx=(10, 10), pady=(10, 10))
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='Recording', font=('Noto Sans', 12, 'bold'), anchor='w')
        label.pack(side='left', fill='y', expand='false', pady=(0, 5))

        recording_settings = [
            (f'Number of Frames [{FRAME_COUNT_RANGE[0]}, {FRAME_COUNT_RANGE[1]}]', self.frame_count_value, FRAME_COUNT_RANGE),
            (f'FPS (Frames per second) [{FPS_RANGE[0]}, {FPS_RANGE[1]}]', self.fps_value, FPS_RANGE),
        ]

        for setting in recording_settings:
            frame = tk.Frame(self.frame)
            frame.pack(side='top', fill='x', expand='false')
            label = tk.Label(frame, text=setting[0], anchor='w', width=30)
            label.pack(side='left', fill='both', expand='false')
            input = tk.Spinbox(frame, textvariable=setting[1], from_=setting[2][0], to=setting[2][1])
            input.pack(side='left', fill='both', expand='true')

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='LEDs & Fan', font=('Noto Sans', 12, 'bold'), anchor='w')
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
            label.pack(side='left', fill='x', expand='false')
            button = tk.Button(frame, text=setting[1], command=setting[2])
            button.pack(side='left', fill='x', expand='false')
            scale = tk.Scale(frame, variable=setting[4], to=255, orient='horizontal', command=setting[3], length=250, sliderlength=20)
            scale.pack(side='right', fill='x', expand='false')

    def frame_count_value_change(self, value, index, mode):
        frame_count = self.frame_count_value.get()
        if (frame_count and frame_count.isdigit() and
                FRAME_COUNT_RANGE[0] < int(frame_count) < FRAME_COUNT_RANGE[1]):
            self.settings.frame_count = int(frame_count)

    def fps_value_change(self, value, index, mode):
        fps = self.fps_value.get()
        if (fps and fps.isdigit() and
                FPS_RANGE[0] < int(fps) < FPS_RANGE[1]):
            set_feature(self.cam, 'AcquisitionFrameRateAbs', fps)
            self.settings.fps = fps

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
    