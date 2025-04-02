from PIL import Image, ImageTk
from datetime import datetime
from typing import Optional
from vmbpy import *
import tkinter as tk
import ui_states
import sys
import os


class UserInterface:

    def __init__(self, cam):
        self.cam = cam

        self.root = tk.Tk()
        self.root.title('Discobox')
        self.root.geometry("720x480+300+150")
        self.root.resizable(width=True, height=True)
        # self.root.bind('<Configure>', self.on_window_resize)

        self.frame = tk.Frame(self.root)
        self.frame.grid()

        self.panel = tk.Label(self.frame)
        self.panel.grid(column=1, row=0)

        self.controls_panel = tk.Frame(self.frame, padx=10, pady=10)
        self.controls_panel.grid(column=0, row=0, sticky='NW')

        self.show_hide_cam_button = tk.Button(self.controls_panel, text='Show Camera', command=self.show_hide_cam, width=15)
        self.show_hide_cam_button.grid(column=0, row=0, pady=(0, 10))

        self.start_stop_button = tk.Button(self.controls_panel, text='Start', command=self.start_stop_test_run, width=15, state=tk.DISABLED)
        self.start_stop_button.grid(column=0, row=1)
            
        self.pause_resume_button = tk.Button(self.controls_panel, text='Pause', command=self.pause_resume_test_run, width=15, state=tk.DISABLED)
        self.pause_resume_button.grid(column=0, row=2)

        self.test_run_label = tk.Label(self.controls_panel, text='', width=15, anchor='nw', justify='left', wraplength=100)
        self.test_run_label.grid(column=0, row=3)

        self.test_runs = tk.Variable(value=[])
        self.test_runs_list = tk.Listbox(self.controls_panel, listvariable=self.test_runs, selectmode='single')
        self.test_runs_list.grid(column=0, row=4, pady=(10, 0))
        self.test_runs_list.bind('<<ListboxSelect>>', self.on_select_test_run)
        self.update_test_runs_list()

        self.load_exit_test_run_button = tk.Button(self.controls_panel, text='Load Test Run', command=self.load_close_test_run, width=15, state=tk.DISABLED)
        self.load_exit_test_run_button.grid(column=0, row=5)

        self.view_controls = tk.Frame(self.frame, padx=10, pady=10)
        self.view_controls.grid(column=1, row=1, sticky='NE')

        self.view_image_label = tk.Label(self.view_controls, text='')
        self.view_image_label.grid(column=0, row=0, padx=(0, 10))
        self.first_image_button = tk.Button(self.view_controls, text='<<<', command=self.show_first_image, border=0)
        self.first_image_button.grid(column=1, row=0)
        self.prev_image_button = tk.Button(self.view_controls, text='<', command=self.show_prev_image, border=0)
        self.prev_image_button.grid(column=2, row=0)
        self.view_page = tk.StringVar()
        self.view_page_input = tk.Entry(self.view_controls, textvariable=self.view_page, width=2)
        self.view_page_input.grid(column=3, row=0, padx=(8, 0))
        self.view_page_input.bind('<Return>', self.go_to_image)
        self.view_image_pager = tk.Label(self.view_controls, text='')
        self.view_image_pager.grid(column=4, row=0, padx=(0, 8))
        self.next_image_button = tk.Button(self.view_controls, text='>', command=self.show_next_image, border=0)
        self.next_image_button.grid(column=5, row=0)
        self.last_image_button = tk.Button(self.view_controls, text='>>>', command=self.show_last_image, border=0)
        self.last_image_button.grid(column=6, row=0)

        # self.root.bind('<Escape>', lambda e: self.root.quit())

        self.is_test_run = None
        self.test_run_paused = False

        self.loaded_test_run = None
        self.loaded_test_run_image = 0

        self.change_state(ui_states.IDLE)

    def start(self):
        self.root.mainloop()

    def change_state(self, state):
        self.state = state
        if self.state == ui_states.IDLE:
            if self.cam.is_streaming():
                self.show_hide_cam_button.configure(text='Close Camera', state=tk.NORMAL)
                self.start_stop_button.configure(text='Start Test Run', state=tk.NORMAL)
            else:
                self.show_hide_cam_button.configure(text='Show Camera', state=tk.NORMAL)
                self.start_stop_button.configure(text='Start Test Run', state=tk.DISABLED)

            self.pause_resume_button.configure(text='Pause Test Run', state=tk.DISABLED)
            self.test_runs_list.configure(state=tk.NORMAL)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.NORMAL if self.test_runs_list.curselection() else tk.DISABLED)
            self.view_controls.grid_forget()

        elif self.state == ui_states.TEST_RUN:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Stop Test Run', state=tk.NORMAL)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.NORMAL)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.DISABLED)
            self.view_controls.grid_forget()

        elif self.state == ui_states.TEST_RUN_PAUSED:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Stop Test Run', state=tk.NORMAL)
            self.pause_resume_button.configure(text='Resume Test Run', state=tk.NORMAL)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.DISABLED)
            self.view_controls.grid_forget()

        elif self.state == ui_states.VIEW:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Start Test Run', state=tk.DISABLED)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.DISABLED)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Close Test Run', state=tk.NORMAL)
            self.view_controls.grid(column=1, row=1, sticky='NE')

    def show_hide_cam(self):
        if self.cam.is_streaming():
            self.cam.stop_streaming()
            self.clear_panel()
        else:
            # Start Streaming with a custom a buffer of 10 Frames (defaults to 5)
            self.cam.start_streaming(
                handler=self,
                buffer_count=10,
                allocation_mode=AllocationMode.AnnounceFrame)
        self.change_state(ui_states.IDLE)

    def start_stop_test_run(self):
        if self.is_test_run is None:
            self.is_test_run = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            self.test_run_paused = False
            self.test_run_label.configure(text=f'Test Run:\n{self.is_test_run}')
            os.makedirs(f'output/{self.is_test_run}', exist_ok=True)
            self.change_state(ui_states.TEST_RUN)
        else:
            self.is_test_run = None
            self.test_run_paused = False
            self.test_run_label.configure(text='')
            self.update_test_runs_list()
            self.change_state(ui_states.IDLE)

    def pause_resume_test_run(self):
        if self.is_test_run is None:
            return
        
        self.test_run_paused = not self.test_run_paused
        self.change_state(ui_states.TEST_RUN_PAUSED if self.test_run_paused else ui_states.TEST_RUN)

    def update_test_runs_list(self):
        os.makedirs(f'output', exist_ok=True)
        self.test_runs.set(sorted([dir.name for dir in os.scandir('output')], reverse=True))
    
    def on_select_test_run(self, val):
        selected = [self.test_runs_list.get(i) for i in self.test_runs_list.curselection()]
        if len(selected) != 1 or self.state != ui_states.IDLE:
            self.load_exit_test_run_button.configure(state=tk.DISABLED)
        else:
            self.load_exit_test_run_button.configure(state=tk.NORMAL)
    
    def load_close_test_run(self):
        if self.loaded_test_run is None:
            if self.cam.is_streaming():
                self.cam.stop_streaming()
                self.clear_panel()

            selected = [self.test_runs_list.get(i) for i in self.test_runs_list.curselection()]
            if len(selected) != 1:
                self.load_exit_test_run_button.configure(state=tk.DISABLED)
                return
            self.loaded_test_run = selected[0]
            self.change_state(ui_states.VIEW)
            self.show_image()
        else:
            self.loaded_test_run = None
            self.clear_panel()
            self.change_state(ui_states.IDLE)

    def show_first_image(self):
        self.show_image(0)
    
    def show_prev_image(self):
        if self.loaded_test_run_image == 0:
            return
        self.show_image(self.loaded_test_run_image - 1)

    def show_next_image(self):
        self.show_image(self.loaded_test_run_image + 1)
    
    def show_last_image(self):
        self.show_image(-1)

    def go_to_image(self, value):
        try:
            self.show_image(int(self.view_page.get()) - 1)
        except:
            pass

    def show_image(self, index=0):
        if self.loaded_test_run is None:
            return
        
        images = sorted([dir.name for dir in os.scandir(f'output/{self.loaded_test_run}')])

        if index < -1 or index >= len(images):
            return
        if index == -1:
            index = len(images) - 1
        
        self.loaded_test_run_image = index
        img = Image.open(f'output/{self.loaded_test_run}/{images[index]}')

        self.view_image_label.configure(text=images[index])
        self.view_page.set(index+1)
        self.view_image_pager.configure(text=f'/{len(images)}')

        self.first_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == 0 else tk.NORMAL)
        self.prev_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == 0 else tk.NORMAL)
        self.next_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == len(images) - 1 else tk.NORMAL)
        self.last_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == len(images) - 1 else tk.NORMAL)

        frame_size = (self.root.winfo_width() - self.controls_panel.winfo_width(), self.root.winfo_height() - self.view_controls.winfo_height())
        image_size = (0, 0)
        ratio = img.width / img.height

        if frame_size[0] / ratio > frame_size[1]:
            image_size = (int(frame_size[1] * ratio), frame_size[1])
        else:
            image_size = (frame_size[0], int(frame_size[0] / ratio))

        img = img.resize(image_size)
        img = ImageTk.PhotoImage(img)

        self.panel.configure(image=img)
        self.panel.image = img
    
    def clear_panel(self):
        self.panel.configure(image=None)
        self.panel.image = None

    # def on_window_resize(self, event):
    #     print(f'on_window_resize {event}')
    #     self.show_image(self.loaded_test_run_image)

    def __call__(self, cam: Camera, stream: Stream, frame: Frame):
        # print('{} acquired {}'.format(cam, frame), flush=True)

        if frame.get_status() == FrameStatus.Complete:
            frame_size = (self.root.winfo_width() - self.controls_panel.winfo_width(), self.root.winfo_height())
            image_size = (0, 0)
            ratio = frame.get_width() / frame.get_height()

            if frame_size[0] / ratio > frame_size[1]:
                image_size = (int(frame_size[1] * ratio), frame_size[1])
            else:
                image_size = (frame_size[0], int(frame_size[0] / ratio))

            img = Image.fromarray(frame.convert_pixel_format(PixelFormat.Rgb8).as_numpy_ndarray())
            
            if self.is_test_run is not None and not self.test_run_paused:
                img.save(f'output/{self.is_test_run}/{self.is_test_run}-{frame.get_id():06}.png')

            img = img.resize(image_size)
            img = ImageTk.PhotoImage(img)

            self.panel.configure(image=img)
            self.panel.image = img

        cam.queue_frame(frame)



def abort(reason: str, return_code: int = 1):
    """ Prints `reason` to the console and exits the program with `return_code`.
    """
    _logger.info(reason + '\n')
    sys.exit(return_code)


def get_camera(camera_id: Optional[str]) -> Camera:
    """ Loads the camera specified by `camera_id` from the Vimba API.
    If `camera_id` is not provided, loads the first available camera.

    :param camera_id: (optional) ID of the camera to load
    """
    with VmbSystem.get_instance() as vmb:
        if camera_id:
            try:
                return vmb.get_camera_by_id(camera_id)
            except VmbCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))
        else:
            cams = vmb.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')
            return cams[0]


def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            stream = cam.get_streams()[0]
            stream.GVSPAdjustPacketSize.run()
            while not stream.GVSPAdjustPacketSize.is_done():
                pass
        except (AttributeError, VmbFeatureError):
            pass


def print_camera(cam: Camera):
    """ Prints all relevant information about a camera to the console.
    """
    print('/// Camera Name   : {}'.format(cam.get_name()))
    print('/// Model Name    : {}'.format(cam.get_model()))
    print('/// Camera ID     : {}'.format(cam.get_id()))
    print('/// Serial Number : {}'.format(cam.get_serial()))
    print('/// Interface ID  : {}\n'.format(cam.get_interface_id()))


def list_cameras():
    """ Lists all available cameras
    """
    with VmbSystem.get_instance() as vmb:
        cams = vmb.get_all_cameras()
        print('Cameras found: {}'.format(len(cams)))
        for cam in cams:
            print_camera(cam)


def print_help():
    """ Prints help information about this script to the console.
    """
    print(
        'Opens a camera viewer for the Discobox.\n'
        '\n'
        'Usage:\n'
        '  $ python3 discobox.py [opt] [arg]\n'
        '\n'
        'Options:\n'
        '  -h, --help: print help information and exit\n'
        '  -l, --list: list all available cameras and exit\n'
        '\n'
        'Arguments:\n'
        '  camera_id: (optional) ID of the camera to open in the viewer\n'
        '             defaults to the first available camera\n'
    )


def main():
    args = sys.argv[1:]

    if len(args) > 0 and args[0] in ('-h', '--help'):
        print_help()
        return

    if len(args) > 0 and args[0] in ('-l', '--list'):
        list_cameras()
        return

    cam_id = args[0] if len(args) > 0 else None

    with VmbSystem.get_instance():
        with get_camera(cam_id) as cam:
            _logger.info(f'Selected camera with ID {cam.get_id()}')
            setup_camera(cam)
            ui = UserInterface(cam)
            ui.start()


if __name__ == '__main__':
    main()
