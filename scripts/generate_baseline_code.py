#!/usr/bin/env python3
"""
Baseline Code Generation Agent

Generates HTML/Tailwind code from Figma design using Claude with vision.
This creates a fresh implementation from scratch with no prior context.

Usage:
    python scripts/generate_baseline_code.py <figma_screenshot> <metadata_json> <output_name>
"""

import os
import sys
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import yaml

# Load environment variables
load_dotenv()


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 string"""
    with open(image_path, 'rb') as image_file:
        return base64.standard_b64encode(image_file.read()).decode('utf-8')


def generate_code_from_figma(screenshot_path: str, metadata_path: str) -> dict:
    """
    Generate HTML/Tailwind code from Figma screenshot using Claude vision.

    Args:
        screenshot_path: Path to Figma screenshot
        metadata_path: Path to Figma metadata JSON

    Returns:
        dict with keys:
            - html_code: Generated HTML/Tailwind code
            - reasoning: LLM's reasoning about the design
            - raw_response: Full LLM response
    """

    print("=" * 70)
    print("BASELINE CODE GENERATION (FRESH START)")
    print("=" * 70)
    print()

    # Load metadata
    print("[1/4] Loading Figma metadata...")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    bounds = metadata.get('absoluteBoundingBox', {})
    width = bounds.get('width', 'unknown')
    height = bounds.get('height', 'unknown')
    frame_name = metadata.get('name', 'Unknown Frame')

    print(f"  Frame: {frame_name}")
    print(f"  Dimensions: {width} x {height}")
    print()

    # Encode screenshot
    print("[2/4] Loading Figma screenshot...")
    screenshot_b64 = encode_image_to_base64(screenshot_path)
    print(f"  ✓ Loaded: {Path(screenshot_path).name}")
    print()

    # Initialize Claude client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Anthropic(api_key=api_key)

    # Load config
    config = load_config()
    model = config['models']['code_generation']['model']
    max_tokens = config['models']['code_generation']['max_tokens']

    print(f"[3/4] Generating code with {model}...")
    print()

    # Build prompt
    generation_prompt = f"""You are an expert front-end developer converting Figma designs to production-ready HTML/Tailwind CSS code.

## Design Information
- Frame name: {frame_name}
- Dimensions: {width}px × {height}px
- This is a FRESH implementation - ignore any prior context

## Your Task

Analyze the Figma screenshot and generate pixel-perfect HTML/Tailwind CSS code that matches the design exactly.

### Requirements:

1. **Use Tailwind CSS** (via CDN) for all styling - NO custom CSS
2. **Semantic HTML** - use appropriate HTML5 elements
3. **Responsive** - code should work at the design's breakpoint
4. **Complete** - include <!DOCTYPE html>, proper head, all necessary structure
5. **Pixel-perfect** - match spacing, typography, colors, layout exactly
6. **Clean code** - well-formatted, readable, with comments for major sections

### Important Notes:

- For images: Use placeholder `<img>` tags with relative paths like `../images/placeholder.png`
- For interactive elements (buttons, dropdowns): Use proper semantic HTML even if not functional
- Match colors exactly from the design
- Pay close attention to spacing, font sizes, and alignment
- Use Tailwind's utility classes for everything (text-gray-700, px-4, rounded-lg, etc.)

### Output Format:

Return ONLY the complete HTML code, ready to save as a .html file.
NO markdown code blocks, NO explanations - just the raw HTML.

The code should start with `<!DOCTYPE html>` and be complete and valid.
"""

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.2,  # Low temp for more consistent output
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": generation_prompt
                        }
                    ],
                }
            ],
        )

        # Extract response
        response_text = message.content[0].text

        print("  ✓ Code generated")
        print()

        # Clean up response (remove markdown if present)
        html_code = response_text
        if '```html' in html_code:
            start = html_code.find('```html') + 7
            end = html_code.rfind('```')
            html_code = html_code[start:end].strip()
        elif '```' in html_code:
            start = html_code.find('```') + 3
            end = html_code.rfind('```')
            html_code = html_code[start:end].strip()

        # Verify it's valid HTML
        if not html_code.strip().startswith('<!DOCTYPE') and not html_code.strip().startswith('<html'):
            print("  ⚠️  Warning: Generated code doesn't start with <!DOCTYPE> or <html>")
            print("  Attempting to use as-is...")

        print("[4/4] Code generation complete")
        print(f"  Generated: {len(html_code)} characters")
        print()

        return {
            'html_code': html_code,
            'raw_response': response_text,
            'model_used': model,
            'metadata': {
                'frame_name': frame_name,
                'dimensions': f"{width}x{height}",
                'source_screenshot': str(screenshot_path)
            }
        }

    except Exception as e:
        print(f"  ✗ Error generating code: {e}")
        return {
            'html_code': None,
            'error': str(e)
        }


def main():
    """Generate baseline code from command line"""

    if len(sys.argv) < 4:
        print("Usage: python generate_baseline_code.py <figma_screenshot> <metadata_json> <output_name>")
        print()
        print("Example:")
        print("  python scripts/generate_baseline_code.py \\")
        print("    output/screenshots/pdp-trimmed-figma.png \\")
        print("    output/pdp-trimmed-metadata.json \\")
        print("    pdp-trimmed-baseline")
        print()
        sys.exit(1)

    screenshot_path = sys.argv[1]
    metadata_path = sys.argv[2]
    output_name = sys.argv[3]

    # Validate inputs
    if not os.path.exists(screenshot_path):
        print(f"Error: Screenshot not found: {screenshot_path}")
        sys.exit(1)

    if not os.path.exists(metadata_path):
        print(f"Error: Metadata not found: {metadata_path}")
        sys.exit(1)

    # Generate code
    result = generate_code_from_figma(screenshot_path, metadata_path)

    if result.get('error'):
        print(f"✗ Code generation failed: {result['error']}")
        sys.exit(1)

    # Save code
    output_dir = Path(__file__).parent.parent / "output" / "code"
    output_dir.mkdir(exist_ok=True, parents=True)

    output_file = output_dir / f"{output_name}.html"

    with open(output_file, 'w') as f:
        f.write(result['html_code'])

    print("=" * 70)
    print("✓ BASELINE CODE GENERATED")
    print("=" * 70)
    print(f"\nOutput: {output_file}")
    print(f"Size: {len(result['html_code'])} characters")
    print(f"Model: {result['model_used']}")
    print()
    print("Next steps:")
    print(f"  1. Render: python scripts/render_with_viewport_match.py \\")
    print(f"       {output_file} \\")
    print(f"       {metadata_path} \\")
    print(f"       output/screenshots/{output_name}-rendered.png")
    print()
    print(f"  2. Evaluate: python scripts/evaluate_combined.py \\")
    print(f"       {screenshot_path} \\")
    print(f"       output/screenshots/{output_name}-rendered.png \\")
    print(f"       output/diffs/{output_name}-diff.png")
    print()
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
