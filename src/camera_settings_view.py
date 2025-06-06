import tkinter as tk
from vmbpy import *
import logging

from .camera_utils import set_feature, exec_command

_logger = logging.getLogger(__name__)


class CameraSettingsView(tk.Toplevel):
    """
    AcquisitionFrameCount
    AcquisitionFrameRateAbs
    AcquisitionMode MultiFrame
    
    FrameStart Trigger Off
    
    """

    def __init__(self, cam: Camera, master=None):
        super().__init__(master=master)
        self.title('Camera Settings')
        self.geometry("720x480")
        self.resizable(width=True, height=True)
        self.cam = cam
        self._build_settings_ui()

    def _build_settings_ui(self):
        # self.frame = tk.Frame(self)
        # self.frame.pack(side='top', fill='both', expand='true', padx=(10, 10), pady=(10, 10))
        # self.frame.grid_rowconfigure(0, weight=1)
        # self.frame.grid_columnconfigure(0, weight=1)
        
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

        self.set_def_button = tk.Button(self.controls_panel, text='Set Default', command=self.set_def)
        self.set_def_button.grid(column=0, row=2)
        self.record_button = tk.Button(self.controls_panel, text='Record', command=self.record)
        self.record_button.grid(column=0, row=3)
    
    def set_exposure_auto_value(self, value):
        set_feature(self.cam, 'ExposureAuto', value)

    def set_exposure_time_value(self, value):
        set_feature(self.cam, 'ExposureTimeAbs', value)


    def set_def(self):
        set_feature(self.cam, 'AcquisitionFrameCount', 50)
        set_feature(self.cam, 'AcquisitionFrameRateAbs', 20)
        set_feature(self.cam, 'AcquisitionMode', 'Continuous')
        set_feature(self.cam, 'TriggerSelector', 'FrameStart')
        set_feature(self.cam, 'TriggerMode', 'On')
        set_feature(self.cam, 'TriggerSource', 'FixedRate')
        exec_command(self.cam, 'AcquisitionStart')
    
    def record(self):
        set_feature(self.cam, 'AcquisitionMode', 'MultiFrame')
        exec_command(self.cam, 'AcquisitionStart')

        # attrib = getattr(self.cam, 'AcquisitionEnd')
        # object_methods = [method_name for method_name in dir(attrib)
        #           if callable(getattr(attrib, method_name))]
        # for method in object_methods:
        #     print(method)

        print(f'{self.cam.get_all_features()}')
        # self.cam.save_settings()
        # self.cam.load_settings()
