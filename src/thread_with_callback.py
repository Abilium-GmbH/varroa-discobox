import threading


class ThreadWithCallback(threading.Thread):

    def __init__(self, callback=None, *args, **kwargs):
        self.callback = callback
        self.target_method = kwargs.pop('target')
        super().__init__(target=self.target_with_callback, *args, **kwargs)

    def target_with_callback(self, *args):
        try:
            self.target_method(*args)
        except Exception:
            pass
        if self.callback is not None:
            self.callback()
