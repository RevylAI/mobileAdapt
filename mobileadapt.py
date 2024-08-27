from device.device_factory import DeviceFactory

'''
This file defines the MobileAdapt class, which provides a high-level interface
for interacting with mobile devices, and includes a factory function for creating instances.
'''
class MobileAdapt:
    def __init__(self, platform: str, app_url: str):
        """
        Initialize the MobileAdapt instance.
        
        Args:
            platform (str): The mobile platform (e.g., 'android' or 'ios').
            app_url (str): The URL or path to the mobile application.
        """
        self.device = DeviceFactory.create_device(platform, app_url)

    async def initialize(self):
        """
        Initialize the device by starting it.
        
        This method should be called before performing any other operations.
        """
        await self.device.start_device()

    async def get_state(self):
        """
        Retrieve the current state of the device.
        
        Returns:
            The current state representation of the device UI.
        """
        return await self.device.get_state()

    async def tap(self, x: int, y: int):
        """
        Perform a tap action on the device screen.
        
        Args:
            x (int): The x-coordinate of the tap location.
            y (int): The y-coordinate of the tap location.
        """
        await self.device.tap(x, y)

    async def input(self, x: int, y: int, text: str):
        """
        Input text at a specific location on the device screen.
        
        Args:
            x (int): The x-coordinate of the input location.
            y (int): The y-coordinate of the input location.
            text (str): The text to be input.
        """
        await self.device.input(x, y, text)

    async def swipe(self, direction: str):
        """
        Perform a swipe action on the device screen.
        
        Args:
            direction (str): The direction of the swipe (e.g., 'up', 'down', 'left', 'right').
        """
        await self.device.swipe(direction)

def mobildevice(platform: str, app_url: str = None):
    """
    Create and return a MobileAdapt instance.
    
    Args:
        platform (str): The mobile platform (e.g., 'android' or 'ios').
        app_url (str, optional): The URL or path to the mobile application.
    
    Returns:
        MobileAdapt: An instance of the MobileAdapt class.
    """
    return MobileAdapt(platform, app_url)