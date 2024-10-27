import asyncio
import io
import os
from datetime import datetime

from PIL import Image

from cognisim import mobileadapt


async def save_screenshot(screenshot_data, filename):
    image = Image.open(io.BytesIO(screenshot_data))
    image.save(filename)


async def perform_actions(device):
    # Tap actions
    await device.tap(200, 300)
    print("Tapped at (200, 300)")
    await device.tap(100, 400)
    print("Tapped at (100, 400)")

    # Swipe actions
    await device.swipe("up")
    print("Swiped up")
    await device.swipe("down")
    print("Swiped down")
    await device.swipe("left")
    print("Swiped left")
    await device.swipe("right")
    print("Swiped right")

    # Input text
    await device.input(150, 500, "Hello, MobileAdapt!")
    print("Input text at (150, 500)")


async def main():
    android_device = mobileadapt(platform="android")
    await android_device.start_device()

    # Perform initial state capture
    encoded_ui, screenshot, ui = await android_device.get_state()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(
        os.path.dirname(__file__), f"screenshot_initial_{timestamp}.png"
    )
    await save_screenshot(screenshot, filename)
    print(f"Initial screenshot saved as {filename}")
    print("Initial UI state:", encoded_ui)

    # Perform a series of actions and capture states
    for i in range(3):
        print(f"\nPerforming action set {i+1}")
        await perform_actions(android_device)

        encoded_ui, screenshot, ui = await android_device.get_state()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            os.path.dirname(__file__), f"screenshot_action{i+1}_{timestamp}.png"
        )
        await save_screenshot(screenshot, filename)
        print(f"Screenshot after action set {i+1} saved as {filename}")
        print(f"UI state after action set {i+1}:", encoded_ui)

    # Additional complex interaction
    print("\nPerforming additional complex interaction")
    await android_device.tap(300, 300)
    await android_device.swipe("up")
    await android_device.input(200, 600, "Complex interaction")
    await android_device.swipe("left")
    await android_device.tap(150, 450)

    # Capture final state
    encoded_ui, screenshot, ui = await android_device.get_state()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(
        os.path.dirname(__file__), f"screenshot_final_{timestamp}.png"
    )
    await save_screenshot(screenshot, filename)
    print(f"Final screenshot saved as {filename}")
    print("Final UI state:", encoded_ui)


if __name__ == "__main__":
    asyncio.run(main())
