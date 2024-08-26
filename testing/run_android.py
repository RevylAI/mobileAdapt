import logging
import asyncio
from device.android_device import AndroidDevice

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_android_device():
    logger.info("Starting Android device test")
    
    # Initialize AndroidDevice
    logger.info("Initializing AndroidDevice")
    android_device = AndroidDevice(app_package="com.android.settings")

    try:
        # Start the device
        logger.info("Starting the device")
        await android_device.start_device()

        # Navigate to the Settings app
        logger.info("Navigating to the Settings app")
        await android_device.navigate("com.android.settings")

        # Get the current state
        logger.info("Getting current UI state")
        encoded_ui, screenshot, ui = await android_device.get_state()

        logger.info("Current UI state:")
        logger.info(encoded_ui)

        # Perform some actions
        logger.info("Performing tap action at (100, 100)")
        await android_device.tap(100, 100)
        
        logger.info("Performing input action at (200, 200) with text 'Test input'")
        await android_device.input(200, 200, "Test input")
        
        logger.info("Performing swipe action (up)")
        await android_device.swipe("up")

        # Get the state again after actions
        logger.info("Getting UI state after actions")
        encoded_ui, screenshot, ui = await android_device.get_state()
        
        logger.info("UI state after actions:")
        logger.info(encoded_ui)

        logger.info("Test completed successfully")
    except Exception as e:
        logger.error(f"An error occurred during the test: {str(e)}")
    finally:
        # Stop the device
        logger.info("Stopping the device")
        await android_device.stop_device()

if __name__ == "__main__":
    asyncio.run(test_android_device())