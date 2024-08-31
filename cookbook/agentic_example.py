import asyncio
import base64
from mobileadapt import mobileadapt
from datetime import datetime
from PIL import Image
import io
import os
from loguru import logger


async def main():

    android_device = mobileadapt(platform="android")
    # Start device
    await android_device.start_device()

    encoded_ui, screenshot, ui = await android_device.get_state()

    # Generate set of mark
    set_of_mark: bytes = android_device.generate_set_of_mark(ui, screenshot, position='top-left')

    # Save image

    with open("set_of_mark.png", "wb") as image_file:
        image_file.write(set_of_mark)
        



    logger.info(f"Current state: {encoded_ui}")

    await android_device.tap(100, 100)

    await android_device.stop_device()
    await android_device.start_device()

if __name__ == "__main__":
    asyncio.run(main())