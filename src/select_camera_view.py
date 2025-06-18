import tkinter as tk
from vmbpy import *
import logging

from .camera_utils import get_all_cameras

_logger = logging.getLogger(__name__)


class SelectCameraView(tk.Tk):

    def __init__(self, start_with_cam, start_without_cam):
        super().__init__()
        self.start_with_cam = start_with_cam
        self.start_without_cam = start_without_cam

        self.title('Select Camera')
        self.resizable(width=False, height=False)
        self.cams = get_all_cameras()
        self._build_settings_ui()

    def start(self):
        self.mainloop()

    def _build_settings_ui(self):
        self.frame = tk.Frame(self)
        self.frame.pack(side='top', fill="both", expand="true", padx=(10, 10), pady=(10, 10))
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.cameras = tk.Variable(value=[])
        self.cameras.set(sorted([f'{cam.get_model()} {cam.get_id()}' for cam in self.cams]))
        self.cameras_list = tk.Listbox(self.frame, listvariable=self.cameras, selectmode='single', height=5, width=0)
        self.cameras_list.pack(side='top', fill="x", expand="false", pady=10)
        if len(self.cams) > 0:
            self.cameras_list.selection_set(0)

        self.select_camera_button = tk.Button(self.frame, text='Select Camera', command=self.select_camera, width=15)
        self.select_camera_button.pack(side='top', fill="x", expand="false")

        self.no_camera_button = tk.Button(self.frame, text='Start without Camera', command=self.no_camera, width=15)
        self.no_camera_button.pack(side='top', fill="x", expand="false")

    def select_camera(self):
        selected = [self.cameras_list.get(i) for i in self.cameras_list.curselection()]
        if len(selected) == 1:
            cam_id = selected[0].split(' ')[-1]
            self.destroy()
            self.start_with_cam(cam_id)
    
    def no_camera(self):
        self.destroy()
        self.start_without_cam()
