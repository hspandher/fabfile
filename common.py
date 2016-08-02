from fabric.api import local, run, lcd, cd

from . import config


class Executor(object):

    def __init__(self, remote):
        self.remote = remote

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


executor = Executor(remote = config.REMOTE_DEPLOYMENT)
