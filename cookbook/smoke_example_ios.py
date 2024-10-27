import asyncio

import base64
import io
import os

from datetime import datetime

from PIL import Image
from loguru import logger
from cognisim import mobileadapt


async def main():

    ios_device = mobileadapt(platform="ios")

    await ios_device.start_device()


    encoded_ui, screenshot, ui = await ios_device.get_state()
    logger.info(f"Current state: {encoded_ui}")

if __name__ == "__main__":
    asyncio.run(main())
