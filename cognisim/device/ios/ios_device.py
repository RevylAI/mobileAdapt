from cognisim.device.device import Device
from appium.options.ios import XCUITestOptions
from appium import webdriver
from cognisim.device.ios.ios_view_hierarchy import UI
from loguru import logger
import os
SCREEN_WITH = 430
SCREEN_HEIGHT = 932

SCREEN_CHANNEL = 4


class IOSDevice(Device):
    def __init__(self, app_package, download_directory='default', session_id=None):
        super().__init__(app_package)
        self.download_directory = download_directory
        self.session_id = session_id
        self.desired_caps = {
            'deviceName': 'iPhone 15 Pro Max',
            'automationName': 'XCUITest',
            'autoGrantPermission': True,
            'newCommandTimeout': 600,
            'mjpegScreenshotUrl': 'http://localhost:4723/stream.mjpeg',
        }

        self.options = XCUITestOptions().load_capabilities(self.desired_caps)
        



    def get_state(self):
        raw_appium_state = self.driver.page_source

        file_path = os.path.join(os.path.dirname(__file__), 'ios_view_hierarchy.xml')
        xml_file = open(file_path, 'w')
        xml_file.write(raw_appium_state)
        xml_file.close()

        ui = UI(file_path)
        encoded_ui: str = ui.encoding()
        logger.info(f"Encoded UI: {encoded_ui}")

    def tap_(self, x, y):
        # TODO: Implement tap for iOS device
        self.driver.execute_script('mobile: tap', {'x': x, 'y': y})

    def input(self, direction):
        # TODO: Implement input for iOS device
        self.driver.execute_script('mobile: swipe', {'direction': direction})

    def swipe(self, x, y, direction):
        # TODO: Implement swipe for iOS device
        pass
