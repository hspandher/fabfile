import os
import sys
import importlib

ENVIRONMENT_VARIABLE = 'PROJECT_CONFIGURATION_MODULE'

PROJECT_BASE_PATH = os.path.dirname(__file__)
if PROJECT_BASE_PATH not in sys.path:
    sys.path.insert(0, PROJECT_BASE_PATH)

class ImproperlyConfigured(Exception):
    """ Project is not property configured """
    pass


class Config:

    def __init__(self, environment_variable):
        self.environment_variable = environment_variable
        self._config_module = None

    def __getattr__(self, name):
        try:
            if not self._config_module:
                self._config_module = self.instantiate_config()

            return getattr(self._config_module, name)
        except AttributeError as exp:
            raise AttributeError(str(self.__class__.__name__) + ' object has no attribute ' + str(name))

    def instantiate_config(self):
        config_module_path = os.environ.get(self.environment_variable)

        if not config_module_path:
            raise ImproperlyConfigured("{0} environment variable is either not defined or is invalid. This environment should contains the path of the the project configuration module".format(self.environment_variable))

        try:
            config_module = importlib.import_module(config_module_path)
        except ImportError as exp:
            raise ImportError("Could not import config {0} (Is it on sys.path? Is there an import error in config file. Error details - {1}".format(config_module_path, repr(exp)))

        return config_module

config = Config(ENVIRONMENT_VARIABLE)

