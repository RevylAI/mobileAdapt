# device/device_factory.py
# from .device import Device
from device.android_device import AndroidDevice
from device.ios_device import IOSDevice
from loguru import logger


class DeviceFactory:
    @staticmethod
    def create_device(platform: str, app_url: str,
                      state_representation='aria', download_directory='default', session_id=None):
        if platform == 'android':
            return AndroidDevice(app_package=app_url, download_directory=download_directory, session_id=session_id)
        elif platform == 'ios':
            return IOSDevice(app_url)

        elif platform == 'web':
            raise NotImplementedError("Web device is not implemented in open source version check out https://revyl.ai")
        else:
            raise ValueError(
                "Invalid type. Expected one of: 'android', 'web'.")
