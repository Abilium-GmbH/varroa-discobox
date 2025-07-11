import tkinter as tk
from PIL import Image, ImageTk
from vmbpy import *
import logging

_logger = logging.getLogger(__name__)


class SettingsHelpView(tk.Toplevel):

    def __init__(self):
        super().__init__()

        self.title('Help')
        self.resizable(width=False, height=False)

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
        label = tk.Label(
            frame, wraplength=920, justify='left',
            text='A test run consists of one or more recording cycles.'
                 'The following diagram shows a timeline of one recording '
                 'cycle with all the avalaible settings.\n'
                 'The fan, led 1, and led 2 will be turned on such that they '
                 'run for their configured duration and end at the same '
                 'time as the recording '
                 '(to ensure all frames are captured with the same light, '
                 'they stay on for an additional second).')
        label.pack(side='left', fill='none', expand='false', pady=(0, 10))

        self.panel = tk.Label(self.frame)
        self.panel.pack(side='top', fill='both', expand='true')
        
        img = Image.open('recording_diagram.png')

        ratio = float(img.width) / img.height
        image_size = (920, int(920.0 / ratio))
        img = img.resize(image_size)
        img = ImageTk.PhotoImage(img)

        self.panel.configure(image=img)
        self.panel.image = img
