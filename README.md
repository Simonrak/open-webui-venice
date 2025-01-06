
# Open-WebUI Venice Image Generation Button

This script adds an image generation button to the Open-WebUI interface, leveraging the Venice AI API. It allows users to generate images directly from the chat interface using simple text prompts.

## Features

- Configurable image generation parameters
- Real-time status updates during generation
- Support for both URL and base64 encoded images
- Keep-alive functionality for long-running requests

### Prompt Overrides

The script supports overriding default image generation parameters directly within the prompt. This is achieved using a simple `key: value` syntax. The following parameters can be overridden:

- `width`: The width of the generated image (e.g., `width: 512`)
- `height`: The height of the generated image (e.g., `height: 768`)
- `steps`: The number of diffusion steps (e.g., `steps: 50`)
- `seed`: The random seed for image generation (e.g., `seed: 12345`)
- `cfg_scale`: The classifier-free guidance scale (e.g., `cfg_scale: 7`)
- `negative_prompt`: Undesired elements in the generated image (e.g., `negative_prompt: blurry, text`)
- `style_preset`: The style preset to use (e.g., `style_preset: Photographic`)

The override pattern uses a regular expression (`(\w+):\s*([^\n]+)`) to extract key-value pairs from the prompt. These overrides are then used to customize the image generation request sent to the Venice AI API.

### Example Usage

```text
A beautiful landscape with mountains and a lake

width: 1024
height: 768
steps: 60
style_preset: Digital Art
```

This would generate a 1024x768 digital art style landscape image using 60 diffusion steps.
