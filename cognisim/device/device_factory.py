# device/device_factory.py
# from .device import Device
from cognisim.device.android.android_device import AndroidDevice
from cognisim.device.ios.ios_device import IOSDevice
from loguru import logger


class DeviceFactory:
    @staticmethod
    def create_device(
        platform: str,
        app_url: str,
        state_representation='aria',
        download_directory='default',
        session_id=None,
        tracing=False,
        tracingconfig=None
    ):
        if platform == 'android':
            return AndroidDevice(
                app_package=app_url,
                download_directory=download_directory,
                session_id=session_id
            )
        elif platform == 'ios':
            return IOSDevice(app_url)

        elif platform == 'web':
            logger.info("Creating web device")
            raise NotImplementedError("Web support is not yet implemented")
        else:
            raise ValueError(
                "Invalid type. Expected one of: 'android', 'web'.")
