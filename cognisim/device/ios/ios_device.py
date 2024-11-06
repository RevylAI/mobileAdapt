import base64
from datetime import datetime
from appium.webdriver.common.appiumby import AppiumBy
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
            'deviceName': 'iPhone 14',
            'automationName': 'XCUITest',
            'autoGrantPermission': True,
            'newCommandTimeout': 600,
            'mjpegScreenshotUrl': 'http://localhost:4723/stream.mjpeg',
            'platformVersion': '16.4',
            'snapshotMaxDepth': 30,
            'customSnapshotTimeout': 250,
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

    async def mobile_get_source(self, format='json'):
        return self.driver.execute_script('mobile: source', {'format': format, 'excludedAttributes': 'visible'})

    async def start_recording(self):
        '''
        Start recording screen on the IOS device
        returns: None
        '''
        try:
            self.driver.start_recording_screen()
        except Exception as e:
            logger.error(f"Failed to start screen recording. Error: {str(e)}")
            raise

    async def stop_recording(self, save_path=None):
        '''
        Stops screen recording on the IOS device and saves the video

        Args:
            save_path (str, optional): Path to save the video file. If not provided, a default path will be used.

        Returns:
            str: Path to the saved video file

        '''
        video_base64 = self.driver.stop_recording_screen()
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_recording_{timestamp}.mp4"
            save_dir = os.path.join(os.getcwd(), "recordings")
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

        with open(save_path, "wb") as video_file:
            video_file.write(base64.b64decode(video_base64))

        logger.info(f"Screen recording saved to: {save_path}")
        return save_path

    async def get_state(self):
        try:
            raw_appium_state = await self.mobile_get_source()
            logger.info(f"Raw Appium State: {raw_appium_state}")
        except Exception as e:
            logger.info(f"Error getting page source: {e}")
            raw_appium_state = ""

        file_path = os.path.join(os.path.dirname(__file__), 'ios_view_hierarchy.xml')
        xml_file = open(file_path, 'w')
        xml_file.write(raw_appium_state)
        xml_file.close()

        ui = UI(file_path)
        self.ui = ui
        encoded_ui: str = ui.encoding()
        logger.info(f"Encoded UI: {encoded_ui}")
        screenshot: bytes = self.driver.get_screenshot_as_png()
        return encoded_ui, screenshot, ui

    def generate_set_of_mark(self,
                             ui,
                             image: bytes,
                             position='top-left') -> bytes:
        '''
        Code to generate a set of mark for a given image and UI state
        ui: UI object
        image: bytes of the image
        step_i: step number
        position: position of the annotation, defaults to 'top-lefts, can also be 'center
        '''
        nparr = np.frombuffer(image, np.uint8)
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
            area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])

            # Only label elements with area over k
            if area > k:
                # Draw a rectangle around the element
                cv2.rectangle(
                    img, (int(bounds[0]), int(bounds[1])),
                    (int(bounds[2]), int(bounds[3])), (0, 0, 255), 5)

                text = str(element_id)
                text_size = 2  # Fixed text size
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
        self.driver.execute_script('mobile: tap', {'x': x, 'y': y})

    async def input(self, x, y, text):
        self.driver.execute_script('mobile: tap', {'x': x, 'y': y})
        self.driver.find_element(AppiumBy.IOS_PREDICATE, "type == 'XCUIElementTypeApplication'").send_keys(text)
        # self.driver.execute_script('mobile: type', {'text': text})

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
        screenshot: bytes = self.driver.get_screenshot_as_png()
        return screenshot

    async def capture_screenshot_with_bounding_box(self, bounds: dict, image_state: bytes = None) -> bytes:
        """
        Capture a screenshot with a bounding box drawn around a specified element.

        Args:
            bounds (dict): A dictionary containing the bounding box coordinates.
                           Expected keys are x1, y1, x2, y2, all of which are integers.
            image_state (bytes, optional): The current screenshot if available.

        Returns:
            bytes: The screenshot image with bounding box as bytes.
        """
        logger.info("Creating tagged image")
        screenshot = image_state if image_state is not None else await self.device.screenshot()
        if screenshot is None:
            logger.info("Screenshot failed")
            return None

        # Convert the screenshot to a NumPy array
        image_np = np.frombuffer(screenshot, dtype=np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        # Extract bounding box coordinates
        x1 = int(bounds[0])
        y1 = int(bounds[1])
        x2 = int(bounds[2])
        y2 = int(bounds[3])

        # Calculate width and height
        #  width = x2 - x1
        # height = y2 - y1

        bright_color = (128, 0, 128)  # Pink color
        # Draw the bounding box on the image
        cv2.rectangle(image, (x1, y1), (x2, y2), bright_color, 5)

        # Convert the image back to bytes
        _, encoded_image = cv2.imencode('.png', image)
        screenshot_with_bounding_box = encoded_image.tobytes()

        return screenshot_with_bounding_box

    async def navigate(self, package_name: str):
        self.driver.activate_app(package_name)

    async def stop_device(self):
        '''
        Stops the device
        '''
        pass


if __name__ == "__main__":
    ui = UI(os.path.join(os.path.dirname(__file__), 'ios_view_hierarchy.xml'))
    encoded_ui = ui.encoding()
    logger.info(f"Encoded UI: {encoded_ui}")
