"""title: Venice Image Generation Button.

author: Simon
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.1.0
required_open_webui_version: 0.3.17
"""

import logging
import random
import re
import time
from collections.abc import Generator
from typing import Any, Literal

import requests
from pydantic import BaseModel, Field


class Action:
    """Main class for Venice AI ImageGen integration with Open-WebUI.

    Handles image generation using Venice AI's API with configurable parameters.
    """

    class Valves(BaseModel):
        """Options that are configurable for all buttons."""

        VENICE_API_BASE_URL: str = "https://api.venice.ai/api/v1"
        VENICE_API_KEY: str = ""
        IMAGE_WIDTH: int = 720
        IMAGE_HEIGHT: int = 1080
        HIDE_WATERMARK: bool = True
        RETURN_BINARY: bool = False
        SEED: int | None = 123
        MODEL_ID: str = "fluently-xl"
        CFG_SCALE: int = Field(default=7, le=20)
        STEPS: int = Field(default=80, le=100)
        STYLE_PRESET: str = "Photographic"
        NEGATIVE_PROMPT: str = ""
        TIMEOUT: int = Field(default=10, description="Timeout in seconds")

    def __init__(self) -> None:
        """Venice AI ImageGen action."""
        self.valves = self.Valves()
        self.keep_alive_active = False

    async def action(
        self,
        body: dict,
        __user__: Any | None = None,
        __event_emitter__: Any | None = None,
        __event_call__: Any | None = None,
    ) -> None:
        """Generate an image using Venice AI's API.

        Args:
            body: Dictionary containing the request body with user messages
            __user__: Optional user information object
            __event_emitter__: Event emitter for sending messages back to the UI
            __event_call__: Optional event call object

        Returns:
            None: Sends generated images through the event emitter

        """
        logging.info(f"action:{__name__}")

        if not __event_emitter__ or not self.valves.VENICE_API_KEY:
            return

        # Show generating status
        await __event_emitter__(
            {
                "type": "status",
                "data": {"description": "Generating image...", "done": False},
            }
        )

        try:
            # Get the last user message content, using empty string as fallback
            prompt = body.get("messages", [{}])[-1].get("content", "")

            prompt, overrides = self.parse_prompt_overrides(prompt)

            # Make API request
            url = f"{self.valves.VENICE_API_BASE_URL}/image/generate"
            payload = {
                "model": self.valves.MODEL_ID,
                "prompt": prompt,
                "width": overrides.get("width", self.valves.IMAGE_WIDTH),
                "height": overrides.get("height", self.valves.IMAGE_HEIGHT),
                "steps": overrides.get("steps", self.valves.STEPS),
                "hide_watermark": self.valves.HIDE_WATERMARK,
                "return_binary": self.valves.RETURN_BINARY,
                "cfg_scale": overrides.get("cfg_scale", self.valves.CFG_SCALE),
                "seed": overrides.get("seed", random.randint(0, 999999)),
                "negative_prompt": overrides.get(
                    "negative_prompt",
                    self.valves.NEGATIVE_PROMPT,
                ),
                "style_preset": self.valves.STYLE_PRESET,
            }
            headers = {
                "Authorization": f"Bearer {self.valves.VENICE_API_KEY}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                url, headers=headers, json=payload, timeout=self.valves.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if "images" in data and data["images"]:
                for image_data in data["images"]:
                    if image_data.startswith("http"):
                        image_markdown = f"![image]({image_data})"
                    else:
                        image_markdown = self._process_base64_image(image_data)

                    await __event_emitter__(
                        {
                            "type": "message",
                            "data": {"content": image_markdown, "role": "assistant"},
                        }
                    )

            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "Image generated!", "done": True},
                }
            )

        except Exception as e:
            logging.error(f"Error generating image: {str(e)}")
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": f"Error: {str(e)}", "done": True},
                }
            )

    def keep_alive_generator(self) -> Generator[Literal[" "], Any, None]:
        """Generate keep-alive messages to maintain connection.

        Yields:
            Literal[" "]: A space character sent periodically to keep connection alive

        """
        while self.keep_alive_active:
            yield " "
            time.sleep(1)

    def parse_prompt_overrides(self, prompt: str) -> tuple[str, dict]:
        """Parse prompt for parameter overrides and return cleaned prompt and overrides.

        Args:
            prompt: Input prompt string that may contain override parameters in format "key: value"

        Returns:
            tuple[str, dict]: A tuple containing:
                - str: The cleaned prompt with override parameters removed
                - dict: Dictionary of parsed override parameters with their values

        """
        override_pattern = r"(\w+):\s*([^\n]+)"
        overrides = {}
        cleaned_prompt = prompt

        # Find all override patterns
        matches = re.findall(override_pattern, prompt)
        for key, value in matches:
            key = key.lower()
            if key in [
                "width",
                "height",
                "steps",
                "seed",
                "cfg_scale",
                "style_preset",
                "negative_prompt",
            ]:
                # Remove the override from the prompt
                cleaned_prompt = cleaned_prompt.replace(f"{key}: {value}", "").strip()
                # Convert numeric values
                if key in ["width", "height", "steps", "seed", "cfg_scale"]:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                overrides[key] = value

        return cleaned_prompt, overrides

    def _process_base64_image(self, image_data: str) -> str:
        """Convert base64 encoded image data into a markdown image string.

        Args:
            image_data: Base64 encoded image data string

        Returns:
            str: Markdown formatted image string or error message if processing fails

        """
        try:
            logging.info("Processing base64 image")
            # Create data URL format
            data_url = f"data:image/png;base64,{image_data}"
            return f"![image]({data_url})"
        except Exception as e:
            logging.info(f"Error processing image: {str(e)}")
            return f"Error processing image: {str(e)}"
