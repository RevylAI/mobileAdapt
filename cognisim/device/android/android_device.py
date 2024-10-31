import base64
from datetime import datetime
from cognisim.device.device import Device
from appium import webdriver
from appium.options.android import UiAutomator2Options
from cognisim.device.android.android_view_hierarchy import ViewHierarchy
import cv2
from loguru import logger
import numpy as np
import os
# Android Emulator Config
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 1920
SCREEN_CHANNEL = 4
SCREEN_TOP_HEAD = 63
SCREEN_BOTTOM_HEAD = 126
# screen config
ADJACENT_BOUNDING_BOX_THRESHOLD = 3
NORM_VERTICAL_NEIGHBOR_MARGIN = 0.01
NORM_HORIZONTAL_NEIGHBOR_MARGIN = 0.01
INPUT_ACTION_UPSAMPLE_RATIO = 1
# XML screen config
XML_SCREEN_WIDTH = 1440
XML_SCREEN_HEIGHT = 2960
# Get state implementation


def sortchildrenby_viewhierarchy(view, attr="bounds"):
    if attr == 'bounds':
        bounds = [(ele.uiobject.bounding_box.x1, ele.uiobject.bounding_box.y1,
                   ele.uiobject.bounding_box.x2, ele.uiobject.bounding_box.y2)
                  for ele in view]
        sorted_bound_index = [
            bounds.index(i) for i in sorted(
                bounds, key=lambda x: (
                    x[1], x[0]))]

        sort_children = [view[i] for i in sorted_bound_index]
        view[:] = sort_children


CLASS_MAPPING = {
    'TEXTVIEW': 'p',
    'BUTTON': 'button',
    'IMAGEBUTTON': 'button',
    'IMAGEVIEW': 'img',
    'EDITTEXT': 'input',
    'CHECKBOX': 'input',
    'CHECKEDTEXTVIEW': 'input',
    'TOGGLEBUTTON': 'button',
    'RADIOBUTTON': 'input',
    'SPINNER': 'select',
    'SWITCH': 'input',
    'SLIDINGDRAWER': 'input',
    'TABWIDGET': 'div',
    'VIDEOVIEW': 'video',
    'SEARCHVIEW': 'div'
}


class UI():
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.elements = {}

    def encoding(self):
        logger.info('reading hierarchy tree from {} ...'.format(
            self.xml_file.split('/')[-1]))
        with open(self.xml_file, 'r', encoding='utf-8') as f:
            vh_data = f.read().encode()

        vh = ViewHierarchy(
            screen_width=XML_SCREEN_WIDTH,
            screen_height=XML_SCREEN_HEIGHT)
        vh.load_xml(vh_data)
        view_hierarchy_leaf_nodes = vh.get_leaf_nodes()
        sortchildrenby_viewhierarchy(view_hierarchy_leaf_nodes, 'bounds')

        logger.debug('encoding the ui elements in hierarchy tree...')
        codes = ''
        # logger.info(view_hierarchy_leaf_nodes)
        for _id, ele in enumerate(view_hierarchy_leaf_nodes):
            obj_type = ele.uiobject.obj_type.name
            text = ele.uiobject.text
            text = text.replace('\n', ' ')
            resource_id = ele.uiobject.resource_id if ele.uiobject.resource_id is not None else ''
            content_desc = ele.uiobject.content_desc
            html_code = self.element_encoding(
                _id, obj_type, text, content_desc, resource_id)
            codes += html_code
            self.elements[_id] = ele.uiobject
        codes = "<html>\n" + codes + "</html>"
        return codes

    def element_encoding(
            self,
            _id,
            _obj_type,
            _text,
            _content_desc,
            _resource_id):

        _class = _resource_id.split('id/')[-1].strip()
        _text = _text.strip()
        assert _obj_type in CLASS_MAPPING.keys(), print(_obj_type)
        tag = CLASS_MAPPING[_obj_type]

        if _obj_type in ['CHECKBOX', 'CHECKEDTEXTVIEW', 'SWITCH']:
            code = f'  <input id={_id} type="checkbox" name="{_class}">\n'
            code += f'  <label for={_id}>{_text}</label>\n'
        elif _obj_type == 'RADIOBUTTON':
            code = f'  <input id={_id} type="radio" name="{_class}">\n'
            code += f'  <label for={_id}>{_text}</label>\n'
        elif _obj_type == 'SPINNER':
            code = f'  <label for={_id}>{_text}</label>\n'
            code += f'  <select id={_id} name="{_class}"></select>\n'
        elif _obj_type == 'IMAGEVIEW':
            if _class == "":
                code = f'  <img id={_id} alt="{_content_desc}" />\n'
            else:
                code = f'  <img id={_id} class="{_class}" alt="{_content_desc}" />\n'
        else:
            if _class == "":
                _text = _content_desc if _text == "" else _text
                code = f'  <{tag} id={_id}">{_text}</{tag}>\n'
            else:
                _text = _content_desc if _text == "" else _text
                code = f'  <{tag} id={_id} class="{_class}">{_text}</{tag}>\n'
        return code


class AndroidDevice(Device):
    def __init__(self, app_package, download_directory='default', session_id=None):
        super().__init__(app_package)
        self.download_directory = download_directory
        self.session_id = session_id
        self.desired_caps = {
            'deviceName': 'Android Device',
            'automationName': 'UiAutomator2',
            'autoGrantPermission': True,
            'newCommandTimeout': 600,
            'mjpegScreenshotUrl': 'http://localhost:4723/stream.mjpeg',

        }
        self.options = UiAutomator2Options().load_capabilities(self.desired_caps)

    async def get_state(self):
        raw_appium_state = self.driver.page_source

        file_path = os.path.join(os.path.dirname(__file__), 'android_view_hierarchy.xml')
        xml_file = open(file_path, 'w')
        xml_file.write(raw_appium_state)
        xml_file.close()

        ui = UI(file_path)
        encoded_ui: str = ui.encoding()
        logger.info(f"Encoded UI: {encoded_ui}")
        # Take screenshot and encode as base64
        screenshot: bytes = self.driver.get_screenshot_as_png()

        # Return encoded UI and screenshot
        return encoded_ui, screenshot, ui

    async def navigate(self, package_name):
        """
        Opens the specified package using Appium with UiAutomator2.

        :param package_name: The package name of the app to open
        """
        try:
            self.driver.activate_app(package_name)
            logger.info(f"Successfully opened package: {package_name}")
        except Exception as e:
            logger.error(f"Failed to open package {package_name}. Error: {str(e)}")
            raise

    async def tap(self, x, y):
        self.driver.tap([(x, y)], 1)

    async def input(self, x, y, text):
        await self.tap(x, y)
        self.driver.execute_script('mobile: type', {'text': text})

    async def drag(self, startX, startY, endX, endY):
        self.driver.swipe(startX, startY, endX, endY, duration=1000)

    async def scroll(self, direction):
        direction_map = {
            'up': 'UP',
            'down': 'DOWN',
            'left': 'LEFT',
            'right': 'RIGHT'
        }
        self.driver.execute_script('mobile: scroll', {'direction': direction_map[direction]})

    async def swipe(self, direction):
        left = self.window_size["width"] * 0.2
        top = self.window_size["height"] * 0.2
        width = self.window_size["width"] * 0.6
        height = self.window_size["height"] * 0.6
        self.driver.execute_script("mobile: swipeGesture", {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "direction": direction,
            "percent": 1.0
        })

    async def start_recording(self):
        """
        Starts screen recording on the Android device.

        Returns:
            None
        """
        try:
            self.driver.start_recording_screen()
            logger.info("Screen recording started successfully")
        except Exception as e:
            logger.error(f"Failed to start screen recording. Error: {str(e)}")
            raise

    async def stop_recording(self, save_path=None):
        """
        Stops screen recording on the Android device and saves the video.

        Args:
            save_path (str, optional): Path to save the video file. If not provided, a default path will be used.

        Returns:
            str: Path to the saved video file
        """
        video_base64 = self.driver.stop_recording_screen()

        if save_path is None:
            # Create a unique filename using timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_recording_{timestamp}.mp4"

            # Define the default save path
            save_dir = os.path.join(os.getcwd(), "recordings")
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)

        # Decode and save the video
        with open(save_path, "wb") as video_file:
            video_file.write(base64.b64decode(video_base64))

        logger.info(f"Screen recording saved to: {save_path}")
        return save_path

    async def stop_device(self):
        '''
        Stops a test
        '''
        pass
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
    
    def generate_set_of_mark(self,
                             ui,
                             image: bytes,
                             position='top-left') -> bytes:
        '''
        Code to generate a set of mark for a given image and UI state
        ui: UI object
        image: bytes of the image
        step_i: step number
        position: position of the annotation, defaults to 'top-lefts', can also be 'center'
        '''
        # Convert image bytes to numpy array
        nparr = np.frombuffer(image, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width, _ = img.shape

        # Define the minimum area
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

            # Only label elements with an area over k
            if area > k:
                # Draw a rectangle around the element
                cv2.rectangle(
                    img, (int(bounds[0]), int(bounds[1])),
                    (int(bounds[2]), int(bounds[3])), (0, 0, 255), 5)

                text = str(element_id)
                text_size = 2  # Fixed text size
                font = cv2.FONT_HERSHEY_SIMPLEX

                # Calculate the width and height of the text
                text_width, text_height = cv2.getTextSize(
                    text, font, text_size, 2)[0]

                # Calculate the position of the text
                if position == 'top-left':
                    text_x = int(bounds[0])
                    text_y = int(bounds[1]) + text_height
                else:  # Default to center
                    text_x = (int(bounds[0]) + int(bounds[2])) // 2 - text_width // 2
                    text_y = (int(bounds[1]) + int(bounds[3])) // 2 + text_height // 2

                # Draw a black rectangle behind the text
                cv2.rectangle(img, (text_x, text_y - text_height),
                              (text_x + text_width, text_y), (0, 0, 0), thickness=cv2.FILLED)

                # Draw the text in white
                cv2.putText(img, text, (text_x, text_y), font,
                            text_size, (255, 255, 255), 4)

        # Convert the image to bytes
        _, img_encoded = cv2.imencode('.png', img)
        img_bytes = img_encoded.tobytes()

        return img_bytes


    async def start_device(self):
        '''
        Start the Android device and connect to the appium server
        '''
        try:
            self.driver = webdriver.Remote('http://localhost:4723', options=self.options)
        except BaseException:
            self.desired_caps.pop('mjpegScreenshotUrl')
            self.options = UiAutomator2Options().load_capabilities(self.desired_caps)
            self.driver = webdriver.Remote('http://localhost:4723', options=self.options)

        # self.driver.start_recording_screen()
        self.driver.update_settings({'waitForIdleTimeout': 0, 'shouldWaitForQuiescence': False, 'maxTypingFrequency': 60})
        # self.driver.get_screenshot_as_base64()
#         self.driver.execute_script('mobile: startScreenStreaming', {
#             'width': 1080,
#             'height': 1920,
#             'considerRotation': True,
#             'quality': 45,
#             'bitRate': 500000,
# })


if __name__ == "__main__":
    ui = UI(os.path.join(os.path.dirname(__file__), 'android_view_hierarchy.xml'))
    encoded_ui = ui.encoding()
    logger.info(f"Encoded UI: {encoded_ui}")
