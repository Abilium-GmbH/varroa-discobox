import tkinter as tk
from vmbpy import *
import logging

_logger = logging.getLogger(__name__)


class SettingsView(tk.Toplevel):

    def __init__(self, cam: Camera, master=None):
        super().__init__(master=master)
        self.title('Camera Settings')
        self.geometry("720x480")
        self.resizable(width=True, height=True)
        self.cam = cam
        self._build_settings_ui()

    def _build_settings_ui(self):
        self.frame = tk.Frame(self)
        self.frame.grid()

        self.controls_panel = tk.Frame(self.frame, padx=10, pady=10)
        self.controls_panel.grid(column=0, row=0, sticky='NW')

        self.exposure_auto_label = tk.Label(self.controls_panel, text='Exposure Auto', width=15, anchor='nw', justify='left')
        self.exposure_auto_label.grid(column=0, row=0)

        exposure_feature = self.cam.ExposureAuto
        self.exposure_auto_value = tk.StringVar(value=exposure_feature.get())
        self.exposure_auto_select = tk.OptionMenu(self.controls_panel, self.exposure_auto_value, *exposure_feature.get_all_entries(), command=self.set_exposure_auto_value)
        self.exposure_auto_select.grid(column=1, row=0)

        self.exposure_time_label = tk.Label(self.controls_panel, text='Exposure Time [µs]', width=15, anchor='nw', justify='left')
        self.exposure_time_label.grid(column=0, row=1)

        exposure_time_feature = self.cam.ExposureTimeAbs
        self.exposure_time_value = tk.StringVar(value=exposure_time_feature.get())
        self.exposure_time_input = tk.Scale(self.controls_panel, from_=48, to=90_000_000, orient='horizontal', command=self.set_exposure_time_value, width=30)
        self.exposure_time_input.grid(column=1, row=1)
    
    def set_exposure_auto_value(self, value):
        self._set_feature('ExposureAuto', value)

    def set_exposure_time_value(self, value):
        self._set_feature('ExposureTimeAbs', value)

    def _set_feature(self, feat_name, value):
        if not hasattr(self.cam, feat_name):
            _logger.warning(f'Feature does not exist: {feat_name}')
            return
        _logger.info(f'Set feature {feat_name} to {value}')
        getattr(self.cam, feat_name).set(value)

