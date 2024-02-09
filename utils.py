import json
import logging
import logging.handlers


class Config:
    def __init__(self):
        with open('config.json', "r") as config_file:
            self._config = json.load(config_file)

    def get(self, parameter):
        return self._config.get(parameter)


class Logger:
    def __init__(self):
        handler = logging.handlers.WatchedFileHandler('abonoteatro.log')
        handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s",
                                               datefmt="%d/%b/%Y %H:%M:%S"))
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
