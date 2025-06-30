import tkinter as tk
from vmbpy import *
import logging

from .controller import DiscoboxController
from .settings import Settings
from .camera_utils import get_feature, set_feature
from .settings_help_view import SettingsHelpView

_logger = logging.getLogger(__name__)


RECORDING_COUNT_RANGE = (1, 576)
RECORDING_TIMEOUT_RANGE = (1, 1440)
DURATION_RANGE = (0, 3600)
# These numbers are set according to the limitations of the Camera (Mako G-319B)
FRAME_COUNT_RANGE = (1, 65535)
FPS_RANGE = (1, 33)

SLIDER_RANGE = (0, 255)


class SettingsView(tk.Toplevel):

    def __init__(self, master, cam: Camera, settings: Settings, ctrl: DiscoboxController):
        super().__init__(master=master)
        self.title('Settings')
        self.resizable(width=False, height=False)
        self.ctrl = ctrl
        self.cam = cam

        self.recording_count_value = tk.StringVar(master=self, value=str(settings.recording_count))
        self.recording_count_value.trace_add(mode='write', callback=self.recording_count_value_change)
        self.recording_timeout_value = tk.StringVar(master=self, value=str(settings.recording_timeout))
        self.recording_timeout_value.trace_add(mode='write', callback=self.recording_timeout_value_change)

        self.vent_time_value = tk.StringVar(master=self, value=str(settings.vent_time))
        self.vent_time_value.trace_add(mode='write', callback=self.vent_time_value_change)
        self.led1_time_value = tk.StringVar(master=self, value=str(settings.led1_time))
        self.led1_time_value.trace_add(mode='write', callback=self.led1_time_value_change)
        self.led2_time_value = tk.StringVar(master=self, value=str(settings.led2_time))
        self.led2_time_value.trace_add(mode='write', callback=self.led2_time_value_change)
        self.frame_count_value = tk.StringVar(master=self, value=str(settings.frame_count))
        self.frame_count_value.trace_add(mode='write', callback=self.frame_count_value_change)
        fps = get_feature(self.cam, 'AcquisitionFrameRateAbs')
        self.fps_value = tk.StringVar(master=self, value=str(fps))
        self.fps_value.trace_add(mode='write', callback=self.fps_value_change)

        self.vent_value = tk.StringVar(master=self, value=str(settings.vent))
        self.led1_value = tk.StringVar(master=self, value=str(settings.led1))
        self.led2_value = tk.StringVar(master=self, value=str(settings.led2))

        self.vent_on = False
        self.led1_on = False
        self.led2_on = False

        with self.ctrl as s:
            s.write(self.ctrl.set_all_off())

        self.settings = settings

        self._build_settings_ui()
        self._update_recording_time_label()
    
    def destroy(self):
        self.settings.save('settings.txt')
        with self.ctrl as s:
            s.write(self.ctrl.set_all_off())
        return super().destroy()
    
    def _update_recording_time_label(self):
        if not hasattr(self, 'recording_time_label'):
            return
        self.recording_time_label.configure(text='Recording time [s] = {:.2f}'.format(self.settings.frame_count / float(self.settings.fps)))

    def _build_settings_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill='both', expand='true', padx=(10, 10), pady=(10, 10))
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false', pady=(0, 5))
        label = tk.Label(frame, text='Test Run', font=('Noto Sans', 12, 'bold'), anchor='w')
        label.pack(side='left', fill='y', expand='false')
        button = tk.Button(frame, text='Help', command=self.show_help_view)
        button.pack(side='right', fill='x', expand='false')

        test_run_settings = [
            (f'Number of Recordings [{RECORDING_COUNT_RANGE[0]}, {RECORDING_COUNT_RANGE[1]}]', self.recording_count_value, RECORDING_COUNT_RANGE),
            (f'Time between Recordings [min] [{RECORDING_TIMEOUT_RANGE[0]}, {RECORDING_TIMEOUT_RANGE[1]}]', self.recording_timeout_value, RECORDING_TIMEOUT_RANGE),
        ]

        for setting in test_run_settings:
            frame = tk.Frame(self.frame)
            frame.pack(side='top', fill='x', expand='false')
            label = tk.Label(frame, text=setting[0], anchor='w', width=32)
            label.pack(side='left', fill='both', expand='false')
            input = tk.Spinbox(frame, textvariable=setting[1], from_=setting[2][0], to=setting[2][1])
            input.pack(side='left', fill='both', expand='true')


        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='Recording', font=('Noto Sans', 12, 'bold'), anchor='w')
        label.pack(side='left', fill='y', expand='false', pady=(10, 5))

        recording_settings = [
            (f'Ventilation duration [s] [{DURATION_RANGE[0]}, {DURATION_RANGE[1]}]', self.vent_time_value, DURATION_RANGE),
            (f'LED 1 duration [s] [{DURATION_RANGE[0]}, {DURATION_RANGE[1]}]', self.led1_time_value, DURATION_RANGE),
            (f'LED 2 duration [s] [{DURATION_RANGE[0]}, {DURATION_RANGE[1]}]', self.led2_time_value, DURATION_RANGE),
            (f'Number of Frames [{FRAME_COUNT_RANGE[0]}, {FRAME_COUNT_RANGE[1]}]', self.frame_count_value, FRAME_COUNT_RANGE),
            (f'FPS (Frames per second) [{FPS_RANGE[0]}, {FPS_RANGE[1]}]', self.fps_value, FPS_RANGE),
        ]

        for setting in recording_settings:
            frame = tk.Frame(self.frame)
            frame.pack(side='top', fill='x', expand='false')
            label = tk.Label(frame, text=setting[0], anchor='w', width=32)
            label.pack(side='left', fill='both', expand='false')
            input = tk.Spinbox(frame, textvariable=setting[1], from_=setting[2][0], to=setting[2][1])
            input.pack(side='left', fill='both', expand='true')

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='', anchor='w', width=32)
        label.pack(side='left', fill='both', expand='false')
        self.recording_time_label = tk.Label(frame, text='Recording time [s] = 0.0', anchor='w')
        self.recording_time_label.pack(side='left', fill='both', expand='true')

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text='Fan & LEDs', font=('Noto Sans', 12, 'bold'), anchor='w')
        label.pack(side='left', fill='y', expand='false', pady=(10, 5))

        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, wraplength=400, justify='left', anchor='w',
                         text='Set the intensity of the Fan and LEDs for the test ' \
                         'run using the following sliders. With the On/Off button ' \
                         'you can turn each of them on/off to check your settings.')
        label.pack(side='left', fill='x', expand='false', pady=(0, 5))

        self.vent_button = self._create_led_vent_setting_ui(
            'Fan', 'On/Off', self.toggle_vent, self.vent_value_change, self.vent_value, self.vent_on)
        self.led1_button = self._create_led_vent_setting_ui(
            'Led 1', 'On/Off', self.toggle_led1, self.led1_value_change, self.led1_value, self.led1_on)
        self.led2_button = self._create_led_vent_setting_ui(
            'Led 2', 'On/Off', self.toggle_led2, self.led2_value_change, self.led2_value, self.led2_on)

    def _create_led_vent_setting_ui(self, *setting):
        frame = tk.Frame(self.frame)
        frame.pack(side='top', fill='x', expand='false')
        label = tk.Label(frame, text=setting[0], anchor='w', width=12)
        label.pack(side='left', fill='x', expand='false')
        scale = tk.Scale(frame, variable=setting[4], to=255, orient='horizontal', command=setting[3], length=250, sliderlength=20)
        scale.pack(side='left', fill='x', expand='false')
        button = tk.Button(frame, text=setting[1], command=setting[2], bg=self._get_button_color(setting[5]))
        button.pack(side='right', fill='x', expand='false')
        return button

    def show_help_view(self):
        SettingsHelpView().start()

    def recording_count_value_change(self, value, index, mode):
        recording_count = self.recording_count_value.get()
        if (recording_count and recording_count.isdigit() and
                RECORDING_COUNT_RANGE[0] <= int(recording_count) <= RECORDING_COUNT_RANGE[1]):
            self.settings.recording_count = int(recording_count)

    def recording_timeout_value_change(self, value, index, mode):
        recording_timeout = self.recording_timeout_value.get()
        if (recording_timeout and recording_timeout.isdigit() and
                RECORDING_TIMEOUT_RANGE[0] <= int(recording_timeout) <= RECORDING_TIMEOUT_RANGE[1]):
            self.settings.recording_timeout = int(recording_timeout)

    def vent_time_value_change(self, value, index, mode):
        vent_time = self.vent_time_value.get()
        if (vent_time and vent_time.isdigit() and
                DURATION_RANGE[0] <= int(vent_time) <= DURATION_RANGE[1]):
            self.settings.vent_time = int(vent_time)

    def led1_time_value_change(self, value, index, mode):
        led1_time = self.led1_time_value.get()
        if (led1_time and led1_time.isdigit() and
                DURATION_RANGE[0] <= int(led1_time) <= DURATION_RANGE[1]):
            self.settings.led1_time = int(led1_time)

    def led2_time_value_change(self, value, index, mode):
        led2_time = self.led2_time_value.get()
        if (led2_time and led2_time.isdigit() and
                DURATION_RANGE[0] <= int(led2_time) <= DURATION_RANGE[1]):
            self.settings.led2_time = int(led2_time)

    def frame_count_value_change(self, value, index, mode):
        frame_count = self.frame_count_value.get()
        if (frame_count and frame_count.isdigit() and
                FRAME_COUNT_RANGE[0] <= int(frame_count) <= FRAME_COUNT_RANGE[1]):
            self.settings.frame_count = int(frame_count)
            self._update_recording_time_label()

    def fps_value_change(self, value, index, mode):
        fps = self.fps_value.get()
        if (fps and fps.isdigit() and
                FPS_RANGE[0] <= int(fps) <= FPS_RANGE[1]):
            set_feature(self.cam, 'AcquisitionFrameRateAbs', fps)
            self.settings.fps = int(fps)
            self._update_recording_time_label()
    
    def vent_value_change(self, value):
        if (value and value.isdigit() and
                SLIDER_RANGE[0] <= int(value) <= SLIDER_RANGE[1]):
            self.settings.vent = int(value)
            with self.ctrl as s:
                s.write(self.ctrl.set_vent(int(value)))

    def led1_value_change(self, value):
        if (value and value.isdigit() and
                SLIDER_RANGE[0] <= int(value) <= SLIDER_RANGE[1]):
            self.settings.led1 = int(value)
            with self.ctrl as s:
                s.write(self.ctrl.set_led1(int(value)))

    def led2_value_change(self, value):
        if (value and value.isdigit() and
                SLIDER_RANGE[0] <= int(value) <= SLIDER_RANGE[1]):
            self.settings.led2 = int(value)
            with self.ctrl as s:
                s.write(self.ctrl.set_led2(int(value)))

    def toggle_vent(self):
        with self.ctrl as s:
            self.vent_on = not self.vent_on
            s.write(self.ctrl.set_vent_on(self.vent_on))
            s.write(self.ctrl.set_vent(self.settings.vent))
        self.vent_button.configure(bg=self._get_button_color(self.vent_on))

    def toggle_led1(self):
        with self.ctrl as s:
            self.led1_on = not self.led1_on
            s.write(self.ctrl.set_led1_on(self.led1_on))
            s.write(self.ctrl.set_led1(self.settings.led1))
        self.led1_button.configure(bg=self._get_button_color(self.led1_on))

    def toggle_led2(self):
        with self.ctrl as s:
            self.led2_on = not self.led2_on
            s.write(self.ctrl.set_led2_on(self.led2_on))
            s.write(self.ctrl.set_led2(self.settings.led2))
        self.led2_button.configure(bg=self._get_button_color(self.led2_on))

    def _get_button_color(self, on: bool):
        return "#94db89" if on else "#dd9888"
