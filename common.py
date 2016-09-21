from fabric.api import local, run, lcd, cd

from .configuration import config


class Executor:

    def __init__(self, is_remote_func):
        self.is_remote_func = is_remote_func

    @property
    def remote(self):
        return self.is_remote_func()

    def run(self, *args, **kwargs):
        if self.remote:
            command = run
            kwargs.pop('capture', None)
        else:
            command = local

        return command(*args, **kwargs)

    def cd(self, *args, **kwargs):
        command = cd if self.remote else lcd

        return command(*args, **kwargs)


executor = Executor(is_remote_func = lambda : config.REMOTE_DEPLOYMENT)
