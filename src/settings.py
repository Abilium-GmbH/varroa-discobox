

class Settings():

    def __init__(self, **kwargs):
        self.frame_count = kwargs.get('frame_count', 100)
        self.fps = kwargs.get('fps', 10)
        self.led1_on = kwargs.get('led1_on', False)
        self.led1 = kwargs.get('led1', 255)
        self.led2_on = kwargs.get('led2_on', False)
        self.led2 = kwargs.get('led2', 255)
        self.vent_on = kwargs.get('vent_on', False)
        self.vent = kwargs.get('vent', 255)
