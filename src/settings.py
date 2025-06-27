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
            

    def __init__(self, **kwargs):
        self.recording_count: int = kwargs.get('recording_count', 10)
        self.recording_timeout: int = kwargs.get('recording_timeout', 1)
        self.vent_time: int = kwargs.get('vent_time', 10)
        self.vent_timeout: int = kwargs.get('vent_timeout', 5)
        self.frame_count: int = kwargs.get('frame_count', 10)
        self.fps: int = kwargs.get('fps', 20)
        self.led1_on: bool = kwargs.get('led1_on', False)
        self.led1: int = kwargs.get('led1', 255)
        self.led2_on: bool = kwargs.get('led2_on', False)
        self.led2: int = kwargs.get('led2', 255)
    
    def save(self, file_path):
        with open(file_path, 'w') as file:
            file.write(str(self))
    
    def __str__(self):
        return (
            f'recording_count={self.recording_count}\n'
            f'recording_timeout={self.recording_timeout}\n'
            f'vent_time={self.vent_time}\n'
            f'vent_timeout={self.vent_timeout}\n'
            f'frame_count={self.frame_count}\n'
            f'fps={self.fps}\n'
        )


