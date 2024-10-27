from cognisim.device.device import Device
from appium.options.ios import XCUITestOptions
from appium import webdriver
from cognisim.device.ios.ios_view_hierarchy import UI
from loguru import logger
import os
import cv2
import numpy as np

SCREEN_WITH = 430
SCREEN_HEIGHT = 932

SCREEN_CHANNEL = 4


class IOSDevice(Device):
    def __init__(self, app_package=None, download_directory='default', session_id=None):
        super().__init__(app_package)
        self.download_directory = download_directory
        self.app_package = app_package
        self.session_id = session_id
        self.desired_caps = {
            'deviceName': 'iPhone 15 Pro Max',
            'automationName': 'XCUITest',
            'autoGrantPermission': True,
            'newCommandTimeout': 600,
            'mjpegScreenshotUrl': 'http://localhost:4723/stream.mjpeg',
        }

        self.options = XCUITestOptions().load_capabilities(self.desired_caps)
        
    async def start_device(self):
        '''
        Start the IOS device and connect to the appium server
        '''
        try:
            self.driver = webdriver.Remote('http://localhost:4723', options=self.options)
        except BaseException:
            self.desired_caps.pop('mjpegScreenshotUrl')
            self.options = XCUITestOptions().load_capabilities(self.desired_caps)
            self.driver = webdriver.Remote('http://localhost:4723', options=self.options)
        
        self.driver.update_settings({'waitForIdleTimeout': 0, 'shouldWaitForQuiescence': False, 'maxTypingFrequency': 60})
        

    def get_state(self):
        raw_appium_state = self.driver.page_source

        file_path = os.path.join(os.path.dirname(__file__), 'ios_view_hierarchy.xml')
        xml_file = open(file_path, 'w')
        xml_file.write(raw_appium_state)
        xml_file.close()

        ui = UI(file_path)
        self.ui = ui
        encoded_ui: str = ui.encoding()
        logger.info(f"Encoded UI: {encoded_ui}")
        screenshot:bytes = self.driver.get_screenshot_as_png()
        return encoded_ui, screenshot, ui

    def generate_set_of_mark(self,
                             ui,
                             image:bytes,
                             position='top-left') -> bytes:
        '''
        Code to generate a set of mark for a given image and UI state
        ui: UI object 
        image: bytes of the image
        step_i: step number
        position: position of the annotation, defaults to 'top-lefts, can also be 'center
        '''
        nparr = np.frombuffer(image,np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width, _ = img.shape
        k = 3000

        for element_id in ui.elements:
            bounds = [
                ui.elements[element_id].bounding_box.x1,
                ui.elements[element_id].bounding_box.y1,
                ui.elements[element_id].bounding_box.x2,
                ui.elements[element_id].bounding_box.y2
            ]
            # Calculate the area of the bounding box
            area = (bounds[2]-bounds[0])*(bounds[3]-bounds[1])

            # Only label elements with area over k 
            if area > k:
                # Draw a rectangle around the element
                cv2.rectangle(
                    img, (int(bounds[0]), int(bounds[1])),
                    (int(bounds[2]), int(bounds[3])), (0, 0, 255), 5)
                
                text = str(element_id)
                text_size = 2 # Fixed text size
                font = cv2.FONT_HERSHEY_SIMPLEX
                
                # Calculate the width and height of the text
                text_width, text_height = cv2.getTextSize(text, font, text_size, 2)[0]

                if position == 'top-left':
                    text_x = int(bounds[0])
                    text_y = int(bounds[1]) + text_height
                else:
                    text_x = (int(bounds[0]) + int(bounds[2])) // 2 - text_width // 2
                    text_y = (int(bounds[1]) + int(bounds[3])) // 2 + text_height // 2

                  # Draw a black rectangle behind the text
                cv2.rectangle(img, (text_x, text_y - text_height),
                              (text_x + text_width, text_y), (0, 0, 0), thickness=cv2.FILLED)

                # Draw the text in white
                cv2.putText(img, text, (text_x, text_y), font,
                            text_size, (255, 255, 255), 4)
                
        _, img_encoded = cv2.imencode('.png', img)
        img_bytes = img_encoded.tobytes()

        return img_bytes

    async def tap(self, x, y):
        await self.driver.execute_script('mobile: tap', {'x': x, 'y': y})

    async def input(self, direction):
        # TODO: Implement input for iOS device
        await self.driver.execute_script('mobile: tap', {'x': x, 'y': y})
        await self.driver.execute_script('mobile: type', {'text': text})

    async def swipe(self, x, y, direction):
        # TODO: Implement swipe for iOS device
        await self.driver.execute_script('mobile: swipe', {'x': x, 'y': y, 'direction': direction})

    async def scroll(self, direction):
        direction_map = {
            'up': 'UP',
            'down': 'DOWN',
            'left': 'LEFT',
            'right': 'RIGHT'
        }
        await self.driver.execute_script('mobile: scroll', {'direction': direction_map[direction]})

    async def get_screenshot(self) -> bytes:
        '''
        Get Screenshot as bytes
        '''
        screenshot:bytes = self.driver.get_screenshot_as_png()
        return screenshot
    
    async def stop_device(self):
        '''
        Stops the device
        '''
        pass

if __name__ == "__main__":
    ui = UI(os.path.join(os.path.dirname(__file__), 'ios_view_hierarchy.xml'))
    encoded_ui = ui.encoding()
    logger.info(f"Encoded UI: {encoded_ui}")

