from PIL import Image, ImageTk
from datetime import datetime
from vmbpy import *
import tkinter as tk
from tkinter import ttk, messagebox
import ui_states
import logging
import sys
import os
import queue
import threading
import time

logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', datefmt='%Y-%m-%d %I:%M:%S', level=logging.INFO)

_logger = logging.getLogger(__name__)

from src.select_camera_view import SelectCameraView
from src.settings_view import SettingsView
from src.camera_utils import setup_camera, list_cameras, get_camera, set_feature, get_feature, exec_command
from src.processing import process_images
from src.thread_with_callback import ThreadWithCallback
from src.controller import DiscoboxController
from src.settings import Settings
from src.start_test_run_view import StartTestRunView

class UserInterface:

    def __init__(self, ctrl: DiscoboxController, cam: Camera = None):
        self.cam = cam

        self.window_width = 0
        self.window_height = 0

        self.is_test_run = None
        self.test_run_paused = False
        self.recording = None
        self.recording_count = 0
        self.recording_count_total = 0
        self.recording_timeout = 0
        self.vent_time = 0
        self.vent_timeout = 0
        self.frame_count = 0
        self.frame_count_total = 0

        self.test_run_event = threading.Event()
        self.test_run_unpause_event = threading.Event()

        self.loaded_test_run = None
        self.loaded_test_run_image = 0
        self.loaded_recording = None
        self.show_result_images = False

        self.frame_queue = queue.Queue()
        
        self.resize_debounce = None

        self.state = ui_states.IDLE

        self.root = tk.Tk()
        self.root.title('Discobox')
        self.root.geometry('1440x960+100+100')
        self.root.resizable(width=True, height=True)
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        self._build_root_ui()

        self.change_state(ui_states.IDLE)

        self.settings = Settings.from_file('settings.txt')
        set_feature(self.cam, 'AcquisitionFrameRateAbs', self.settings.fps)
        
        self.ctrl = ctrl
        self.ctrl.start()
        with self.ctrl as s:
            s.write(self.ctrl.set_led1(self.settings.led1))
            s.write(self.ctrl.set_led2(self.settings.led2))
            s.write(self.ctrl.set_vent(255))
            s.write(self.ctrl.set_all_off())

    def start(self):
        self.root.mainloop()
        if self.cam and self.cam.is_streaming():
            self.cam.stop_streaming()
        with self.ctrl as s:
            s.write(self.ctrl.set_all_off())
        self.ctrl.stop()
    
    def close_window(self):
        if self.is_test_run:
            if not messagebox.askokcancel(
                title="Test Run", message="There is currently a test run in progress. Are you sure you want to close the appliaction?"):
                return
        self.root.destroy()

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

            self.settings_button.configure(state=tk.NORMAL if self.cam else tk.DISABLED)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.DISABLED)
            self.test_runs_list.configure(state=tk.NORMAL)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.NORMAL if self.test_runs_list.curselection() else tk.DISABLED)
            self.recordings_list.configure(state=tk.DISABLED)
            self.load_exit_recording_button.configure(state=tk.DISABLED)
            self.view_controls_parent.grid_forget()
            self.title.configure(text=f'{self.cam.get_model()} {self.cam.get_id()}' if self.cam else 'No camera selected')

        elif self.state == ui_states.TEST_RUN:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.settings_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Stop Test Run', state=tk.NORMAL)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.NORMAL)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.DISABLED)
            self.recordings_list.configure(state=tk.DISABLED)
            self.load_exit_recording_button.configure(state=tk.DISABLED)
            self.view_controls_parent.grid_forget()
            self.title.configure(text=f'{self.cam.get_model()} {self.cam.get_id()}' if self.cam else 'No camera selected')

        elif self.state == ui_states.TEST_RUN_PAUSED:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.settings_button.configure(state=tk.DISABLED)
            self.start_stop_button.configure(text='Stop Test Run', state=tk.NORMAL)
            self.pause_resume_button.configure(text='Resume Test Run', state=tk.NORMAL)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Load Test Run', state=tk.DISABLED)
            self.recordings_list.configure(state=tk.DISABLED)
            self.load_exit_recording_button.configure(state=tk.DISABLED)
            self.view_controls_parent.grid_forget()
            self.title.configure(text=f'{self.cam.get_model()} {self.cam.get_id()}' if self.cam else 'No camera selected')

        elif self.state == ui_states.VIEW:
            self.show_hide_cam_button.configure(state=tk.DISABLED)
            self.settings_button.configure(state=tk.NORMAL)
            self.start_stop_button.configure(text='Start Test Run', state=tk.DISABLED)
            self.pause_resume_button.configure(text='Pause Test Run', state=tk.DISABLED)
            self.test_runs_list.configure(state=tk.DISABLED)
            self.load_exit_test_run_button.configure(text='Close Test Run', state=tk.NORMAL)
            self.recordings_list.configure(state=tk.DISABLED)
            self.load_exit_recording_button.configure(state=tk.DISABLED)
            self.view_controls_parent.grid(column=1, row=2, sticky='ew')
            self.title.configure(text=f'Test Run: {self.loaded_test_run} - {self.loaded_recording if self.loaded_recording else "Results"}')
        

    def show_hide_cam(self):
        if self.cam.is_streaming():
            self.cam.stop_streaming()
            self.clear_panel()
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
            thread = threading.Thread(target=self.frame_processor, daemon=True)
            thread.start()
        self.change_state(ui_states.IDLE)

    def start_stop_test_run(self, ask=True):
        if self.is_test_run is None:
            StartTestRunView(self.start_test_run).start()
        elif (
            not ask or
            messagebox.askokcancel(
                title='Stop Test Run',
                message='Are you sure you want to stop the current test run?')
        ):
            self.is_test_run = None
            self.test_run_paused = False
            self.test_run_frame.grid_forget()
            self.update_test_runs_list()
            self.change_state(ui_states.IDLE)
            self.test_run_event.set()
            self.test_run_unpause_event.set()
            # self.test_run_thread.join()
    
    def start_test_run(self, name):
        if not name:
            return

        self.is_test_run = name
        self._update_test_run_label()
        self.test_run_paused = False
        self.recording = None
        self.recording_count = 0
        self.recording_count_total = self.settings.recording_count
        self._update_recording_label()
        self.recording_timeout = self.settings.recording_timeout * 60
        self.vent_time = self.settings.vent_time
        self.vent_timeout = self.settings.vent_timeout
        self.frame_count = 0
        self.frame_count_total = self.settings.frame_count
        self._update_frame_label()
        self._update_ventilation_label(False)

        self.test_run_frame.grid(column=1, row=1, sticky='ne')
        self.test_run_frame.lift(self.panel)
        os.makedirs(f'output/{self.is_test_run}', exist_ok=True)
        self.change_state(ui_states.TEST_RUN)

        self.test_run_event.clear()
        self.test_run_unpause_event.clear()
        self.test_run_thread = threading.Thread(target=self.test_run, daemon=True)
        self.test_run_thread.start()

    def pause_resume_test_run(self):
        if self.is_test_run is None:
            return
        if self.test_run_paused:
            self.test_run_unpause_event.set()
            self.test_run_paused = False
            self.change_state(ui_states.TEST_RUN)
        else:
            self.test_run_unpause_event.clear()
            self.test_run_paused = True
            self.change_state(ui_states.TEST_RUN_PAUSED)

    # ----------------------------------------------------------------------- #
    # Displaying Previous Test Runs                                           #

    def update_test_runs_list(self):
        os.makedirs(f'output', exist_ok=True)
        self.test_runs.set(sorted([dir.name for dir in os.scandir('output')], reverse=True))
    
    def update_recordings_list(self):
        if not self.loaded_test_run:
            self.recordings.set([])
            return
        
        recordings = [
            file for file in os.listdir(f'output/{self.loaded_test_run}')
            if file != 'results' and os.path.isdir(f'output/{self.loaded_test_run}/{file}')]
        self.recordings.set(sorted(recordings, reverse=False))
    
    def on_select_test_run(self, val):
        if self.test_runs_list['state'] == 'disabled':
            return
        selected = self._get_selected_from_list(self.test_runs_list)
        if len(selected) != 1 or self.state != ui_states.IDLE:
            self.load_exit_test_run_button.configure(state=tk.DISABLED)
        else:
            self.load_exit_test_run_button.configure(state=tk.NORMAL)
    
    def load_close_test_run(self):
        if self.loaded_test_run is None:
            if self.cam and self.cam.is_streaming():
                self.cam.stop_streaming()
                self.clear_panel()

            selected = self._get_selected_from_list(self.test_runs_list)
            if len(selected) != 1:
                return

            self.loaded_test_run = selected[0]
            self.loaded_recording = None
            self.update_recordings_list()
            if not self.show_result_images:
                self.show_hide_results()
            self.update_has_results()
            self.change_state(ui_states.VIEW)
            self.recordings_list.configure(state=tk.NORMAL)
            self.show_first_image()
        else:
            self.loaded_test_run = None
            self.loaded_recording = None
            self.update_recordings_list()
            self.update_has_results()
            self.change_state(ui_states.IDLE)
            self.recordings_list.configure(state=tk.DISABLED)
            self.clear_panel()
    
    def on_select_recording(self, val):
        if self.recordings_list['state'] == 'disabled':
            return
        selected = self._get_selected_from_list(self.recordings_list)
        if len(selected) != 1 or self.state != ui_states.VIEW:
            self.load_exit_recording_button.configure(state=tk.DISABLED)
        else:
            self.load_exit_recording_button.configure(state=tk.NORMAL)
    
    def load_close_recording(self):
        if self.loaded_recording is None:
            selected = self._get_selected_from_list(self.recordings_list)
            if len(selected) != 1:
                return
            self.loaded_recording = selected[0]
            if self.show_result_images:
                self.show_hide_results()
            self.show_first_image()
            self.load_exit_recording_button.configure(text='Close Recording')
        else:
            self.loaded_recording = None
            if not self.show_result_images:
                self.show_hide_results()
            self.show_first_image()
            self.load_exit_recording_button.configure(text='Load Recording')
        self.title.configure(text=f'Test Run: {self.loaded_test_run} - {self.loaded_recording if self.loaded_recording else "Results"}')
    
    def _get_selected_from_list(self, selection_list):
        return [selection_list.get(i) for i in selection_list.curselection()]
    
    def show_settings_window(self):
        self.settings_view = SettingsView(self.root, self.cam, self.settings, self.ctrl)

    def analyze_testrun(self):
        thread = ThreadWithCallback(target=process_images, args=(f'output/{self.loaded_test_run}',), callback=self.testrun_analyze_finished, daemon=True)
        self.view_controls_parent.grid_forget()
        self.analyze_progressbar_parent.grid(column=1, row=2, sticky='ew')
        self.analyze_progressbar.start()
        self.load_exit_test_run_button.configure(state=tk.DISABLED)
        self.load_exit_recording_button.configure(state=tk.DISABLED)
        thread.start()

    def testrun_analyze_finished(self):
        self.view_controls_parent.grid(column=1, row=2, sticky='ew')
        self.analyze_progressbar_parent.grid_forget()
        self.analyze_progressbar.stop()
        self.load_exit_test_run_button.configure(state=tk.NORMAL)
        self.load_exit_recording_button.configure(state=tk.NORMAL)
        self.update_has_results()

    def show_hide_results(self):
        self.show_result_images = not self.show_result_images
        self.update_has_results()
        self.show_first_image()

    def update_has_results(self):
        path = f'output/{self.loaded_test_run}/results'
        if self.loaded_test_run and self.show_result_images and (not os.path.exists(path) or len(os.listdir(path)) == 0):
            self.test_results_label.grid(column=1, row=1)
            self.test_results_label.lift(self.panel)
        else:
            self.test_results_label.grid_forget()

    def show_first_image(self):
        self.show_image(0)
    
    def show_prev_image(self):
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

    def show_image(self, index):
        if self.loaded_test_run is None:
            return
        
        path = f'output/{self.loaded_test_run}/results' if self.show_result_images else f'output/{self.loaded_test_run}/{self.loaded_recording}'
        images = (sorted([file for file in os.listdir(path) if file.endswith(('.bmp', '.jpg', '.png', '.jpeg'))])
                  if os.path.isdir(path) else [])

        frame_size = (
            self.root.winfo_width() - self.controls_panel.winfo_width(),
            self.root.winfo_height() - self.view_controls_parent.winfo_height() - self.camera_label.winfo_height())
        
        if len(images) == 0:
            img = Image.new('RGB', frame_size, color='#ffffff')
            img = ImageTk.PhotoImage(img)
            self.panel.configure(image=img, text='Test')
            return

        while index < 0:
            index = len(images) + index
        while index >= len(images):
            index = index - len(images)
        
        self.loaded_test_run_image = index
        img = Image.open(f'{path}/{images[index]}')

        self.view_image_label.configure(text=images[index])
        self.view_page.set(index+1)
        self.view_image_pager.configure(text=f'/{len(images)}')

        self.first_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == 0 else tk.NORMAL)
        self.prev_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == 0 else tk.NORMAL)
        self.next_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == len(images) - 1 else tk.NORMAL)
        self.last_image_button.configure(state=tk.DISABLED if self.loaded_test_run_image == len(images) - 1 else tk.NORMAL)

        image_size = self._compute_image_size(frame_size, img.width, img.height)
        img = img.resize(image_size)
        img = ImageTk.PhotoImage(img)

        self.panel.configure(image=img)
        self.panel.image = img

    # ----------------------------------------------------------------------- #
    
    def clear_panel(self):
        self.panel.configure(image=None)
        self.panel.image = None

    def on_window_resize(self, event):
        if (event.widget == self.root and (event.width != self.window_width or event.height != self.window_height)) or event.widget == self.view_controls_parent:
            if self.resize_debounce is not None:
                self.resize_debounce.cancel()
            self.resize_debounce = threading.Timer(0.2, self.resize, (event,))
            self.resize_debounce.start()
    
    def resize(self, event):
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

                    img = Image.fromarray(frame.as_numpy_ndarray()[:, :, 0], mode='L')
                    fps = round(self.stream.get_feature_by_name("FrameRate").get(), 1)
                    self.fps_label.configure(text=f'FPS: {fps}')
                    
                    if self.is_test_run is not None and self.recording is not None:
                        self.frame_count += 1
                        self._update_frame_label()
                        img.save(f'output/{self.is_test_run}/{self.recording}/{self.recording}_{frame.get_id():06}.bmp')
                        if self.frame_count >= self.frame_count_total:
                            self._stop_recording()

                    frame_size = (self.root.winfo_width() - self.controls_panel.winfo_width(), self.root.winfo_height() - self.camera_label.winfo_height())
                    image_size = self._compute_image_size(frame_size, frame.get_width(), frame.get_height())
                    img = img.resize(image_size)
                    img = ImageTk.PhotoImage(img)

                    if self.cam.is_streaming():
                        self.panel.configure(image=img)
                        self.panel.image = img

                self.cam.queue_frame(frame)
            except queue.Empty:
                continue
            except ValueError as e:
                _logger.error(e)
                continue
            except RuntimeError:
                break
        
        try:
            self.show_first_image()
        except:
            pass
    
    def _compute_image_size(self, frame_size, width, height):
        ratio = width / height
        if frame_size[0] / ratio > frame_size[1]:
            return (int(frame_size[1] * ratio), frame_size[1])
        else:
            return (frame_size[0], int(frame_size[0] / ratio))
    
    # ----------------------------------------------------------------------- #
    # Test Run Thread                                                         #

    def test_run(self):
        test_run_start_time = time.time() + 0.5

        while (self.recording_count < self.recording_count_total
               and not self.test_run_event.is_set()):

            cycle_time = test_run_start_time + (self.recording_timeout * self.recording_count)
            stop_vent_time = cycle_time + self.vent_time
            start_recording_time = cycle_time + self.vent_time + self.vent_timeout

            self._wait_until(cycle_time)
            self.recording_count += 1
            self._update_recording_label()
            self.frame_count = 0
            self._update_frame_label()

            # Paused
            if self.test_run_paused:
                pause_start_time = time.time()
                _logger.debug('test run paused')
                self.test_run_unpause_event.wait()
                test_run_start_time += (time.time() - pause_start_time)
                cycle_time = test_run_start_time + (self.recording_timeout * (self.recording_count - 1))
                stop_vent_time = cycle_time + self.vent_time
                start_recording_time = cycle_time + self.vent_time + self.vent_timeout
                _logger.debug('test run continue')

            with self.ctrl as s:
                # Start Ventilation
                s.write(self.ctrl.set_vent_on(True))
                self._update_ventilation_label(True)
                _logger.debug('start ventilation')

                self._wait_until(stop_vent_time)

                # Stop Ventilation
                s.write(self.ctrl.set_vent_on(False))
                self._update_ventilation_label(False)
                _logger.debug('stop ventilation')
            
            self._wait_until(start_recording_time)

            # Start Recording
            recording_name = f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_fps-{self.settings.fps}'
            recording_path = f'output/{self.is_test_run}/{recording_name}'
            os.makedirs(recording_path, exist_ok=True)
            self.recording = recording_name
            _logger.debug('start recording')
        
        _logger.debug('test run finished')

    def _update_test_run_label(self):
        self.test_run_label.configure(text=f'Test Run: {self.is_test_run}')
    
    def _update_recording_label(self):
        self.recording_label.configure(text=f'Recording: {self.recording_count}/{self.recording_count_total}')
    
    def _update_ventilation_label(self, vent: bool):
        self.ventilation_label.configure(text=f'Ventilation: {"ON" if vent else "OFF"}')
    
    def _update_frame_label(self):
        self.frame_label.configure(text=f'Frame: {self.frame_count}/{self.frame_count_total}')

    def _wait_until(self, target_time):
        now = time.time()
        if now < target_time:
            self.test_run_event.wait(target_time - now)
    
    def _stop_recording(self):
        _logger.debug('stop recording')
        recording_name = self.recording
        self.recording = None
        self._analyze_recording(f'output/{self.is_test_run}', recording_name)
        if self.recording_count >= self.recording_count_total:
            self.start_stop_test_run(False)

    def _analyze_recording(self, test_run_path, recording_name):
        _logger.debug('analyze recording')
        thread = threading.Thread(target=process_images, args=(test_run_path, recording_name,))
        thread.start()

    # ----------------------------------------------------------------------- #
    

    def _build_root_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.grid()

        self.camera_label = tk.Label(self.frame, text='Camera', font=('Noto Sans', 12, 'bold'), padx=10, pady=5)
        self.camera_label.grid(column=0, row=0, sticky='nw')
        self.title = tk.Label(self.frame, text='No camera selected', font=('Noto Sans', 12), padx=10, pady=5)
        self.title.grid(column=1, row=0, sticky='nw')
        self.fps_label = tk.Label(self.frame, text='FPS: 0.0', font=('Noto Sans', 12), padx=10, pady=5)
        self.fps_label.grid(column=1, row=0, sticky='ne')

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

        self.test_runs_label = tk.Label(self.controls_panel, text='Previous Test Runs', font=('Noto Sans', 12, 'bold'))
        self.test_runs_label.grid(column=0, row=7, pady=(20, 0), sticky='nw')

        self.test_runs = tk.Variable(value=[])
        self.test_runs_list = tk.Listbox(self.controls_panel, listvariable=self.test_runs, selectmode='single')
        self.test_runs_list.grid(column=0, row=8, sticky='ew')
        self.test_runs_list.bind('<<ListboxSelect>>', self.on_select_test_run)
        self.update_test_runs_list()

        self.load_exit_test_run_button = tk.Button(self.controls_panel, text='Load Test Run', command=self.load_close_test_run, state=tk.DISABLED)
        self.load_exit_test_run_button.grid(column=0, row=9, sticky='ew')

        self.recordings = tk.Variable(value=[])
        self.recordings_list = tk.Listbox(self.controls_panel, listvariable=self.recordings, selectmode='single')
        self.recordings_list.grid(column=0, row=10, sticky='ew', pady=(5, 0))
        self.recordings_list.bind('<<ListboxSelect>>', self.on_select_recording)
        self.update_recordings_list()

        self.load_exit_recording_button = tk.Button(self.controls_panel, text='Load Recording', command=self.load_close_recording, state=tk.DISABLED)
        self.load_exit_recording_button.grid(column=0, row=11, sticky='ew')

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

        self.test_results_label = tk.Label(self.frame, text='No Test Results', anchor='center')
        self.test_run_frame = tk.Frame(self.frame, padx=2, pady=2)

        self.test_run_label = tk.Label(self.test_run_frame, text='Test', anchor='ne', justify='right')
        self.test_run_label.grid(column=0, row=0, sticky='ne')
        self.recording_label = tk.Label(self.test_run_frame, text='TestREcodring', anchor='ne', justify='right')
        self.recording_label.grid(column=0, row=1, sticky='ne')
        self.ventilation_label = tk.Label(self.test_run_frame, text='Vent', anchor='ne', justify='right')
        self.ventilation_label.grid(column=0, row=2, sticky='ne')
        self.frame_label = tk.Label(self.test_run_frame, text='Frame:', anchor='ne', justify='right')
        self.frame_label.grid(column=0, row=3, sticky='ne')

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
        ctrl = DiscoboxController()
        ui = UserInterface(ctrl, cam)
        ui.start()

def start_without_cam():
    ctrl = DiscoboxController(True)
    ui = UserInterface(ctrl)
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
