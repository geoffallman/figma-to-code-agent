# API Research Summary

**Date:** October 14, 2025
**Purpose:** Understanding key Python APIs before Day 2 implementation

---

## Anthropic Python SDK - Vision API

### Installation
```bash
pip install anthropic
```

### Sending Images (Base64)

**Complete Working Example:**
```python
import base64
from anthropic import Anthropic

# 1. Encode image to base64
with open('image_path.jpg', 'rb') as image_file:
    image_data = base64.b64encode(image_file.read()).decode('utf-8')

# 2. Initialize client
client = Anthropic(api_key="your_api_key")

# 3. Send image + text prompt
message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",  # or "image/jpeg"
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Describe this image."
                }
            ],
        }
    ],
)

# 4. Extract response
response_text = message.content[0].text
```

### Sending Multiple Images

```python
message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": figma_image_data,
                    },
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": rendered_image_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Compare these two screenshots and identify differences."
                }
            ],
        }
    ],
)
```

### Key Points
- ✅ Images placed **before** text prompts work best
- ✅ Supported formats: PNG, JPEG, WebP, GIF (non-animated)
- ✅ Max image size: 5MB per image
- ✅ Base64 encoding: `base64.b64encode(file.read()).decode('utf-8')`
- ✅ Response structure: `message.content[0].text`

---

## Playwright Python API

### Installation
```bash
pip install playwright
playwright install chromium
```

### Taking Screenshots

**Basic Example:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")
    page.screenshot(path="screenshot.png")
    browser.close()
```

**With Custom Viewport (Mobile):**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()

    # Set viewport size (e.g., iPhone 12)
    page = browser.new_page(viewport={'width': 390, 'height': 844})

    # Load local HTML file
    page.goto('file:///absolute/path/to/file.html')

    # Take screenshot
    page.screenshot(path="output.png")

    browser.close()
```

**Screenshot to Memory (No Disk):**
```python
# Returns bytes instead of saving to file
screenshot_bytes = page.screenshot()

# Can then encode to base64 directly
import base64
screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
```

**Full Page Screenshot:**
```python
page.screenshot(path="fullpage.png", full_page=True)
```

### Key Points
- ✅ Default browser: Chromium (consistent rendering)
- ✅ Viewport: Set with `browser.new_page(viewport={...})`
- ✅ Local files: Use `file:///absolute/path` protocol
- ✅ Screenshot formats: PNG (default), JPEG
- ✅ Full page: Use `full_page=True` parameter
- ✅ No disk write: Call `page.screenshot()` without `path` parameter

---

## Our Use Cases

### Day 3: Render HTML to Screenshot
```python
from playwright.sync_api import sync_playwright
from pathlib import Path

def render_html_to_screenshot(html_path: str, output_path: str):
    """Render HTML in headless browser and capture screenshot"""
    html_absolute = Path(html_path).resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.goto(f'file://{html_absolute}')
        page.screenshot(path=output_path)
        browser.close()
```

### Day 6: Vision LLM Evaluation
```python
import base64
from anthropic import Anthropic
from pathlib import Path

def evaluate_visual_fidelity(figma_screenshot: str, rendered_screenshot: str) -> dict:
    """Use Claude vision to compare two screenshots"""

    # Load and encode both images
    with open(figma_screenshot, 'rb') as f:
        figma_data = base64.b64encode(f.read()).decode('utf-8')

    with open(rendered_screenshot, 'rb') as f:
        rendered_data = base64.b64encode(f.read()).decode('utf-8')

    # Call Claude with both images
    client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": figma_data,
                        },
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": rendered_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Compare these screenshots:
                        1. First image: Figma design (ground truth)
                        2. Second image: Rendered HTML (candidate)

                        Identify visual differences and provide actionable feedback.
                        Return as JSON."""
                    }
                ],
            }
        ],
    )

    # Parse response
    feedback = json.loads(message.content[0].text)
    return feedback
```

---

## Confidence Level

After research:
- ✅ **Playwright Python:** 95% confident - API is straightforward
- ✅ **Anthropic Vision:** 95% confident - Clear examples, well documented
- ✅ **Base64 encoding:** 100% confident - Standard Python
- ✅ **File I/O:** 100% confident - Basic Python

**Ready to proceed with Day 2+** without additional research needed.
