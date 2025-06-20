from PIL import Image, ImageTk
from datetime import datetime
from vmbpy import *
import tkinter as tk
from tkinter import ttk
import ui_states
import logging
import sys
import os
import queue
import threading

logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', datefmt='%Y-%m-%d %I:%M:%S', level=logging.DEBUG)

_logger = logging.getLogger(__name__)

from src.select_camera_view import SelectCameraView
from src.settings_view import SettingsView
from src.camera_utils import setup_camera, list_cameras, get_camera, set_feature, get_feature, exec_command
from src.processing import process_images
from src.thread_with_callback import ThreadWithCallback
from src.controller import DiscoboxController
from src.settings import Settings

class UserInterface:

    def __init__(self, cam: Camera = None):
        self.cam = cam

        self.window_width = 0
        self.window_height = 0

        self.is_test_run = None
        self.test_run_paused = False

        self.loaded_test_run = None
        self.loaded_test_run_image = 0
        self.show_result_images = False

        self.frame_queue = queue.Queue()
        self.frame_count = 0

        self.state = ui_states.IDLE

        self.root = tk.Tk()
        self.root.title('Discobox')
        self.root.geometry('1440x960+100+100')
        self.root.resizable(width=True, height=True)
        self.root.bind('<Configure>', self.on_window_resize)

        self._build_root_ui()

        self.change_state(ui_states.IDLE)
        
        fps = get_feature(self.cam, 'AcquisitionFrameRateAbs')
        self.settings = Settings(
            frame_count=100, fps=fps,
            led1_on=False, led2_on=False, vent_on=False)
        ctrl = DiscoboxController()
        with ctrl as s:
            s.write(ctrl.set_led1(self.settings.led1))
            s.write(ctrl.set_led2(self.settings.led2))
            s.write(ctrl.set_vent(self.settings.vent))
            s.write(ctrl.set_all_off())

    def start(self):
        self.root.mainloop()
        if self.cam and self.cam.is_streaming():
            self.cam.stop_streaming()
        ctrl = DiscoboxController()
        with ctrl as s:
            s.write(ctrl.set_all_off())

    def change_state(self, state):
        self.state = state
        if self.state == ui_states.IDLE:
            if self.cam and self.cam.is_streaming():
                self.show_hide_cam_button.configure(text='Close Camera', state=tk.NORMAL)
                self.start_stop_button.configure(text='Start Test Run', state=tk.NORMAL)
                self.fps_label.grid(column=0, columnspan=2, row=0, sticky='ne')
            else:
                self.show_hide_cam_button.configure(text='Show Camera', state=tk.NORMAL if self.cam else tk.DISABLED)
                self.start_stop_button.configure(text='Start Test Run', state=tk.DISABLED)
                self.fps_label.grid_forget()

            self.pause_resume_button.configure(text='Pause Test Run', state=tk.DISABLED)
            self.test_runs_list.configure(state=tk.NORMAL)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.NORMAL if self.test_runs_list.curselection() else tk.DISABLED)
            self.view_controls_parent.grid_forget()

        elif self.state == ui_states.TEST_RUN:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Stop Test Run', state=tk.NORMAL)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.NORMAL)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.DISABLED)
            self.view_controls_parent.grid_forget()

        elif self.state == ui_states.TEST_RUN_PAUSED:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Stop Test Run', state=tk.NORMAL)
            self.pause_resume_button.configure(text='Resume Test Run', state=tk.NORMAL)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.DISABLED)
            self.view_controls_parent.grid_forget()

        elif self.state == ui_states.VIEW:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Start Test Run', state=tk.DISABLED)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.DISABLED)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Close Test Run', state=tk.NORMAL)
            self.view_controls_parent.grid(column=1, row=2, sticky='ew')
        
        self.settings_button.configure(state=tk.NORMAL if self.cam else tk.DISABLED)
        self.title.configure(text=f'Camera: {self.cam.get_model()} {self.cam.get_id()}' if self.cam else 'No camera selected')

    def show_hide_cam(self):
        if self.cam.is_streaming():
            self.cam.stop_streaming()
        else:
            self.cam.UserSetSelector.set('Default')
            set_feature(self.cam, 'ExposureAuto', 'Continuous')
            set_feature(self.cam, 'AcquisitionMode', 'Continuous')
            set_feature(self.cam, 'AcquisitionFrameCount', 65535)
            set_feature(self.cam, 'TriggerSelector', 'FrameStart')
            set_feature(self.cam, 'TriggerMode', 'On')
            set_feature(self.cam, 'TriggerSource', 'FixedRate')
            # Start Streaming with a custom a buffer of 10 Frames (defaults to 5)
            self.cam.start_streaming(
                handler=self,
                buffer_count=10,
                allocation_mode=AllocationMode.AnnounceFrame)
            thread = threading.Thread(target=self.frame_processor)
            thread.start()
        self.change_state(ui_states.IDLE)

    def start_stop_test_run(self):
        if self.is_test_run is None:
            self.is_test_run = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + f'_fps-{self.settings.fps}'
            self.test_run_paused = False
            self.frame_count = 0
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
        if self.test_runs_list['state'] == 'disabled':
            return
        selected = [self.test_runs_list.get(i) for i in self.test_runs_list.curselection()]
        if len(selected) != 1 or self.state != ui_states.IDLE:
            self.load_exit_test_run_button.configure(state=tk.DISABLED)
        else:
            self.load_exit_test_run_button.configure(state=tk.NORMAL)
    
    def load_close_test_run(self):
        if self.loaded_test_run is None:
            if self.cam and self.cam.is_streaming():
                self.cam.stop_streaming()
                self.clear_panel()

            selected = [self.test_runs_list.get(i) for i in self.test_runs_list.curselection()]
            if len(selected) != 1:
                self.load_exit_test_run_button.configure(state=tk.DISABLED)
                return
            self.loaded_test_run = selected[0]
            self.change_state(ui_states.VIEW)
            self.show_image()
            self.update_has_results()
        else:
            self.loaded_test_run = None
            self.clear_panel()
            self.change_state(ui_states.IDLE)
            self.update_has_results()
    
    def show_settings_window(self):
        self.settings_view = SettingsView(self.root, self.cam, self.settings)

    def analyze_testrun(self):
        thread = ThreadWithCallback(target=process_images, args=(f'output/{self.loaded_test_run}',), callback=self.testrun_analyze_finished)
        self.view_controls_parent.grid_forget()
        self.analyze_progressbar_parent.grid(column=1, row=2, sticky='ew')
        self.analyze_progressbar.start()
        self.load_exit_test_run_button.configure(state=tk.DISABLED)
        thread.start()

    def testrun_analyze_finished(self):
        self.view_controls_parent.grid(column=1, row=2, sticky='ew')
        self.analyze_progressbar_parent.grid_forget()
        self.analyze_progressbar.stop()
        self.load_exit_test_run_button.configure(state=tk.NORMAL)
        self.update_has_results()

    def show_hide_results(self):
        self.show_result_images = not self.show_result_images
        self.show_hide_results_button.configure(text='Show testrun images' if self.show_result_images else 'Show results')
        if self.show_result_images:
            self.analyze_button.grid_forget()
        else:
            self.analyze_button.grid(column=1, row=0, padx=(0, 20))
        self.show_first_image()

    def update_has_results(self):
        if not self.loaded_test_run:
            return

        path = f'output/{self.loaded_test_run}/results'
        if not self.show_result_images and not os.path.exists(path):
            self.show_hide_results_button.configure(state=tk.DISABLED)

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

    def go_to_image(self, value, index, mode):
        try:
            self.show_image(int(self.view_page.get()) - 1)
        except:
            pass

    def show_image(self, index=0):
        if self.loaded_test_run is None:
            return
        
        path = f'output/{self.loaded_test_run}/results' if self.show_result_images else f'output/{self.loaded_test_run}'
        if self.show_result_images and not os.path.exists(path):
            self.show_hide_results()
            return

        images = sorted([dir.name for dir in os.scandir(path) if dir.name.endswith(('.bmp', '.jpg', '.png', '.jpeg'))])

        if index < -1 or index >= len(images) or len(images) == 0:
            return
        if index == -1:
            index = len(images) - 1
        
        self.loaded_test_run_image = index
        img = Image.open(f'{path}/{images[index]}')

        self.view_image_label.configure(text=images[index])
        self.view_page.set(index+1)
        self.view_image_pager.configure(text=f'/{len(images)}')

        self.first_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == 0 else tk.NORMAL)
        self.prev_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == 0 else tk.NORMAL)
        self.next_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == len(images) - 1 else tk.NORMAL)
        self.last_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == len(images) - 1 else tk.NORMAL)

        frame_size = (self.root.winfo_width() - self.controls_panel.winfo_width(), self.root.winfo_height() - self.view_controls_parent.winfo_height() - self.title.winfo_height())
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

    def on_window_resize(self, event):
        if (event.widget == self.root and (event.width != self.window_width or event.height != self.window_height)) or event.widget == self.view_controls_parent:
            self.window_width = event.width
            self.window_height = event.height
            self.show_image(self.loaded_test_run_image)

    def __call__(self, cam: Camera, stream: Stream, frame: Frame):
        self.stream = stream
        self.frame_queue.put(frame)
    
    def frame_processor(self):
        while self.cam.is_streaming():
            try:
                frame = self.frame_queue.get(timeout=0.1)

                if frame.get_status() == FrameStatus.Complete:
                    frame_size = (self.root.winfo_width() - self.controls_panel.winfo_width(), self.root.winfo_height() - self.title.winfo_height())
                    image_size = (0, 0)
                    ratio = frame.get_width() / frame.get_height()

                    if frame_size[0] / ratio > frame_size[1]:
                        image_size = (int(frame_size[1] * ratio), frame_size[1])
                    else:
                        image_size = (frame_size[0], int(frame_size[0] / ratio))

                    img = Image.fromarray(frame.as_numpy_ndarray()[:, :, 0], mode='L')
                    fps = round(self.stream.get_feature_by_name("FrameRate").get(), 1)
                    
                    if self.is_test_run is not None and not self.test_run_paused:
                        self.frame_count += 1
                        self.fps_label.configure(text=f'FPS {fps}    Frame {self.frame_count}/{self.settings.frame_count}')
                        img.save(f'output/{self.is_test_run}/{self.is_test_run}_{frame.get_id():06}.bmp')
                        if self.frame_count >= self.settings.frame_count:
                            self.start_stop_test_run()
                    else:
                        self.fps_label.configure(text=f'FPS: {fps}')

                    img = img.resize(image_size)
                    img = ImageTk.PhotoImage(img)

                    self.panel.configure(image=img)
                    self.panel.image = img

                self.cam.queue_frame(frame)
            except queue.Empty:
                continue
            except RuntimeError:
                break
        
        try:
            self.clear_panel()
        except:
            pass
    
    def _build_root_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.grid()

        self.title = tk.Label(self.frame, text='No camera selected', font=('Noto Sans', 12, 'bold'), padx=10, pady=5)
        self.title.grid(column=0, columnspan=2, row=0, sticky='nw')
        self.fps_label = tk.Label(self.frame, text='FPS: 0.0', font=('Noto Sans', 12), padx=10, pady=5)
        self.fps_label.grid(column=0, columnspan=2, row=0, sticky='ne')

        self.panel = tk.Label(self.frame)
        self.panel.grid(column=1, row=1)

        self.controls_panel = tk.Frame(self.frame, padx=10)
        self.controls_panel.grid(column=0, row=1, sticky='NW')

        self.show_hide_cam_button = tk.Button(self.controls_panel, width=22, text='Show Camera', command=self.show_hide_cam)
        self.show_hide_cam_button.grid(column=0, row=1, sticky='ew')

        self.settings_button = tk.Button(self.controls_panel, text='Settings', command=self.show_settings_window)
        self.settings_button.grid(column=0, row=2, pady=(0, 10), sticky='ew')

        self.start_stop_button = tk.Button(self.controls_panel, text='Start', command=self.start_stop_test_run, state=tk.DISABLED)
        self.start_stop_button.grid(column=0, row=4, sticky='ew')
            
        self.pause_resume_button = tk.Button(self.controls_panel, text='Pause', command=self.pause_resume_test_run, state=tk.DISABLED)
        self.pause_resume_button.grid(column=0, row=5, sticky='ew')

        self.test_run_label = tk.Label(self.controls_panel, text='', anchor='nw', justify='left', wraplength=200)
        self.test_run_label.grid(column=0, row=6, sticky='ew')

        self.test_runs = tk.Variable(value=[])
        self.test_runs_list = tk.Listbox(self.controls_panel, listvariable=self.test_runs, selectmode='single')
        self.test_runs_list.grid(column=0, row=7, pady=(10, 0), sticky='ew')
        self.test_runs_list.bind('<<ListboxSelect>>', self.on_select_test_run)
        self.update_test_runs_list()

        self.load_exit_test_run_button = tk.Button(self.controls_panel, text='Load Test Run', command=self.load_close_test_run, state=tk.DISABLED)
        self.load_exit_test_run_button.grid(column=0, row=8, sticky='ew')

        self.view_controls_parent = tk.Frame(self.frame, padx=10, pady=10)
        self.view_controls_parent.grid(column=1, row=2, sticky='ew')
        self.view_controls_parent.grid_rowconfigure(0, weight=1)
        self.view_controls_parent.grid_columnconfigure(0, weight=1)

        self.analyze_progressbar_parent = tk.Frame(self.frame, padx=10, pady=10)
        self.analyze_progressbar_parent.grid_rowconfigure(0, weight=1)
        self.analyze_progressbar_parent.grid_columnconfigure(1, weight=1)

        self.analyze_progressbar_label = tk.Label(self.analyze_progressbar_parent, text='analyzing ...')
        self.analyze_progressbar_label.grid(column=0, row=0, padx=(0, 40))
        
        self.analyze_progressbar = ttk.Progressbar(self.analyze_progressbar_parent, orient='horizontal', mode='indeterminate', length=100)
        self.analyze_progressbar.grid(column=1, row=0, sticky='ew')
        self.analyze_progressbar.step(40)

        self.view_controls = tk.Frame(self.view_controls_parent)
        self.view_controls.grid(column=0, row=0, sticky='ew')
        self.view_controls.grid_rowconfigure(0, weight=1)
        self.view_controls.grid_columnconfigure(2, weight=1)

        self.show_hide_results_button = tk.Button(self.view_controls, text='Show results', command=self.show_hide_results)
        self.show_hide_results_button.grid(column=0, row=0, padx=(0, 5))

        self.analyze_button = tk.Button(self.view_controls, text='Analyze Testrun', command=self.analyze_testrun)
        self.analyze_button.grid(column=1, row=0, padx=(0, 20))

        self.spacer = tk.Frame(self.view_controls)
        self.spacer.grid(column=2, row=0)

        self.view_image_label = tk.Label(self.view_controls, text='')
        self.view_image_label.grid(column=3, row=0, padx=(0, 10))
        self.first_image_button = tk.Button(self.view_controls, text='<<<', command=self.show_first_image, border=0)
        self.first_image_button.grid(column=4, row=0)
        self.prev_image_button = tk.Button(self.view_controls, text='<', command=self.show_prev_image, border=0)
        self.prev_image_button.grid(column=5, row=0)
        self.view_page = tk.StringVar()
        self.view_page_input = tk.Entry(self.view_controls, textvariable=self.view_page, width=4)
        self.view_page_input.grid(column=6, row=0, padx=(8, 0))
        self.view_page.trace_add(mode='write', callback=self.go_to_image)
        self.view_image_pager = tk.Label(self.view_controls, text='')
        self.view_image_pager.grid(column=7, row=0, padx=(0, 8))
        self.next_image_button = tk.Button(self.view_controls, text='>', command=self.show_next_image, border=0)
        self.next_image_button.grid(column=8, row=0)
        self.last_image_button = tk.Button(self.view_controls, text='>>>', command=self.show_last_image, border=0)
        self.last_image_button.grid(column=9, row=0)

        # self.root.bind('<Escape>', lambda e: self.root.quit())


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
    )


def start_with_cam(cam_id):
    with get_camera(cam_id) as cam:
        _logger.info(f'Selected camera with ID {cam.get_id()}')
        setup_camera(cam)
        ui = UserInterface(cam)
        ui.start()

def start_without_cam():
    ui = UserInterface()
    ui.start()

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
        if cam_id:
            start_with_cam(cam_id)
        else:
            select_camera = SelectCameraView(start_with_cam, start_without_cam)
            select_camera.start()


if __name__ == '__main__':
    main()
