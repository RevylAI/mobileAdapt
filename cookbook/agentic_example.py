import asyncio
import base64
import io
import json
import os
from datetime import datetime
from typing import Any, Dict

import openai
from loguru import logger
from openai import OpenAI
from PIL import Image

from mobileadapt import mobileadapt

openai.api_key = "<your_openai_api_key>"


def llm_call(html_state: str, image: bytes, nlp_task: str):
    client = OpenAI()

    function_call_instruction_guided_replay = {
        "name": "run_step",
        "description": "Based on the current step and the current state, return the next action to take",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "The reasoning for the action to be performed in the current step",
                },
                "action_type": {
                    "type": "string",
                    "description": "The type of action to be performed",
                    "enum": ["tap", "input", "swipe", "validate" "scroll"],
                },
                "action_id": {
                    "type": "integer",
                    "description": "The id of the action to be performed in the current step based on the current state",
                },
                "value": {
                    "type": "string",
                    "description": "The value to be inputted if action_type is input or the text to be validated if action_type is validate",
                },
                "direction": {
                    "type": "string",
                    "description": "The direction to be swiped if action_type is swipe",
                    "enum": ["up", "down", "left", "right"],
                },
            },
            "required": ["action_type", "action_id", "reasoning"],
        },
    }

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant that helps with mobile app testing.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Given the following task: {nlp_task}\n\nAnd the current state of the app:\n\nHTML: {html_state}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64.b64encode(image).decode('utf-8')}"
                        },
                    },
                ],
            },
        ],
        functions=[function_call_instruction_guided_replay],
        function_call={"name": "run_step"},
    )

    return json.loads(response.choices[0].message.function_call.arguments)


async def main():

    android_device = mobileadapt(platform="android")
    # Start device
    await android_device.start_device()

    encoded_ui, screenshot, ui = await android_device.get_state()

    # Open the app (Flexify - https://f-droid.org/en/packages/com.presley.flexify/)
    await android_device.navigate("com.presley.flexify")

    # Press the button with the text 'Add a new task'

    encoded_ui, screenshot, ui = await android_device.get_state()

    # Create set of mark screenshot
    set_of_mark: bytes = android_device.generate_set_of_mark(ui, screenshot)

    action_grounded: Dict[str, Any] = llm_call(
        html_state=encoded_ui,
        image=set_of_mark,
        nlp_task="Press the buttom with the text 'Add a new task'",
    )

    await android_device.perform_action(action_grounded)

    encoded_ui, screenshot, ui = await android_device.get_state()

    # save set of mark screens

    await android_device.stop_device()
    await android_device.start_device()


if __name__ == "__main__":
    asyncio.run(main())
