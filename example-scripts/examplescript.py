import asyncio
import base64
from mobileadapt import mobildevice
from datetime import datetime
from PIL import Image
import io
import os

''' From the root directory use the following command to start the script:
   python example-scripts/examplescript.py
'''

async def save_screenshot(screenshot_data, filename):
    # Open the screenshot data as an image and save it
    image = Image.open(io.BytesIO(screenshot_data))
    image.save(filename)

async def main():
    # Create an Android device instance
    android_device = mobildevice(platform="android")
    
    # Initialize the device (starts the Appium session)
    await android_device.initialize()
    
    # Get the current state of the device
    encoded_ui, screenshot, ui = await android_device.get_state()
    print("Current state:", encoded_ui)
    
    # Save the first screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename1 = os.path.join(os.path.dirname(__file__), f"screenshot_before_{timestamp}.png")
    await save_screenshot(screenshot, filename1)
    print(f"Screenshot saved as {filename1}")
    
    # Perform a tap action at coordinates (100, 100)
    await android_device.tap(100, 100)
    
    # Get the state again after the tap action
    new_encoded_ui, new_screenshot, new_ui = await android_device.get_state()
    print("New state after tap:", new_encoded_ui)
    
    # Save the second screenshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename2 = os.path.join(os.path.dirname(__file__), f"screenshot_after_{timestamp}.png")
    await save_screenshot(new_screenshot, filename2)
    print(f"Screenshot saved as {filename2}")

if __name__ == "__main__":
    # Run the main function asynchronously
    asyncio.run(main())