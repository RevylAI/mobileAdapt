from abc import ABC, abstractmethod


class Device(ABC):
    def __init__(self, app_package):
        self.app_package = app_package

    @abstractmethod
    def start_device(self):
        '''
        Function to start device
        '''
        pass

    @abstractmethod
    def stop_device(self):
        '''
        Function to stop device
        '''
        pass

    @abstractmethod
    def get_state(self):
        pass

    @abstractmethod
    def tap(self, x, y):
        pass

    @abstractmethod
    def input(self, x, y, text):
        pass

    @abstractmethod
    def swipe(self, x, y, direction):
        pass
