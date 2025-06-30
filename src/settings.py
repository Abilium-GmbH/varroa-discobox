import os


class Settings():

    @classmethod
    def from_file(cls, file_path):
        if not os.path.exists(file_path):
            return Settings()
        
        kwargs = {}
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.strip(' \n').split('=')
                if value in ('True', 'False'):
                    value = bool(value)
                else:
                    value = int(value)
                kwargs[key] = value
        return Settings(**kwargs)

    @classmethod
    def copy(cls, settings):
        return Settings(
            recording_count=settings.recording_count,
            recording_timeout=settings.recording_timeout,
            vent_time=settings.vent_time,
            led1_time=settings.led1_time,
            led2_time=settings.led2_time,
            frame_count=settings.frame_count,
            fps=settings.fps,
            vent=settings.vent,
            led1=settings.led1,
            led2=settings.led2,
        )
            

    def __init__(self, **kwargs):
        self.recording_count: int = kwargs.get('recording_count', 10)
        self.recording_timeout: int = kwargs.get('recording_timeout', 1)
        self.vent_time: int = kwargs.get('vent_time', 10)
        self.led1_time: int = kwargs.get('led1_time', 10)
        self.led2_time: int = kwargs.get('led2_time', 10)
        self.frame_count: int = kwargs.get('frame_count', 10)
        self.fps: int = kwargs.get('fps', 10)
        self.vent: int = kwargs.get('vent', 255)
        self.led1: int = kwargs.get('led1', 255)
        self.led2: int = kwargs.get('led2', 255)
    
    def save(self, file_path):
        with open(file_path, 'w') as file:
            file.write(str(self))
    
    def __str__(self):
        return (
            f'recording_count={self.recording_count}\n'
            f'recording_timeout={self.recording_timeout}\n'
            f'vent_time={self.vent_time}\n'
            f'led1_time={self.led1_time}\n'
            f'led2_time={self.led2_time}\n'
            f'frame_count={self.frame_count}\n'
            f'fps={self.fps}\n'
            f'vent={self.vent}\n'
            f'led1={self.led1}\n'
            f'led2={self.led2}\n'
        )


