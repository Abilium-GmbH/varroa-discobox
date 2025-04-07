import tkinter as tk
from vmbpy import *
import logging

_logger = logging.getLogger(__name__)

from .camera_utils import get_all_cameras


class SelectCameraView(tk.Tk):

    def __init__(self, start_with_cam, start_without_cam):
        super().__init__()
        self.start_with_cam = start_with_cam
        self.start_without_cam = start_without_cam

        self.title('Select Camera')
        self.geometry("480x480")
        self.resizable(width=True, height=True)
        self.cams = get_all_cameras()
        self._build_settings_ui()

    def start(self):
        self.mainloop()

    def _build_settings_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill="both", expand="true")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.controls_panel = tk.Frame(self.frame, padx=10, pady=10)
        self.controls_panel.pack(side='top', fill="both", expand="true")
        self.controls_panel.grid_rowconfigure(0, weight=1)
        self.controls_panel.grid_columnconfigure(0, weight=1)

        self.cameras = tk.Variable(value=[])
        self.cameras.set(sorted([f'{cam.get_model()} {cam.get_id()}' for cam in self.cams]))
        self.cameras_list = tk.Listbox(self.controls_panel, listvariable=self.cameras, selectmode='single')
        self.cameras_list.pack(side='top', fill="both", expand="true", pady=10)

        self.select_camera_button = tk.Button(self.controls_panel, text='Select Camera', command=self.select_camera, width=15)
        self.select_camera_button.pack(side='top', fill="both", expand="false")

        self.no_camera_button = tk.Button(self.controls_panel, text='Start with no Camera', command=self.no_camera, width=15)
        self.no_camera_button.pack(side='top', fill="both", expand="false")

    def select_camera(self):
        selected = [self.cameras_list.get(i) for i in self.cameras_list.curselection()]
        if len(selected) == 1:
            cam_id = selected[0].split(' ')[-1]
            self.destroy()
            self.start_with_cam(cam_id)
    
    def no_camera(self):
        self.destroy()
        self.start_without_cam()
