from .device.device_factory import DeviceFactory

def mobileadapt(platform: str, app_url: str = None, state_representation='aria', download_directory='default', session_id=None):
    return DeviceFactory.create_device(platform, app_url, state_representation, download_directory, session_id)

__all__ = ['mobileadapt']