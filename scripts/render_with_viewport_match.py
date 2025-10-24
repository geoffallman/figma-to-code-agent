#!/usr/bin/env python3
"""
Metadata-Aware HTML Rendering

Renders HTML with viewport dimensions matched to Figma artboard.
This ensures apples-to-apples comparison for pixel-diff evaluation.
"""

import sys
import json
from pathlib import Path

# Add parent scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from render_html import render_html_to_screenshot


def render_with_figma_viewport(
    html_path: str,
    metadata_path: str,
    output_path: str,
    device_scale_factor: float = 2.0
) -> bool:
    """
    Render HTML with viewport matching Figma artboard dimensions.

    Args:
        html_path: Path to HTML file to render
        metadata_path: Path to Figma metadata JSON with absoluteBoundingBox
        output_path: Where to save the screenshot
        device_scale_factor: Device pixel ratio (default 2.0 for retina)

    Returns:
        True if successful, False otherwise
    """

    print("=" * 70)
    print("VIEWPORT-MATCHED RENDERING")
    print("=" * 70)
    print()

    # Load Figma metadata
    print("[1/4] Loading Figma metadata...")
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        if 'absoluteBoundingBox' not in metadata:
            print(f"  ✗ Error: No absoluteBoundingBox found in metadata")
            return False

        bounds = metadata['absoluteBoundingBox']
        viewport_width = int(bounds['width'])
        viewport_height = int(bounds['height'])

        print(f"  ✓ Figma artboard: {viewport_width} x {viewport_height}")
        print(f"  ✓ Device scale: {device_scale_factor}x")
        print(f"  ✓ Output size: {viewport_width * device_scale_factor:.0f} x {viewport_height * device_scale_factor:.0f}")
        print()

    except FileNotFoundError:
        print(f"  ✗ Error: Metadata file not found: {metadata_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"  ✗ Error: Invalid JSON in metadata: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error loading metadata: {e}")
        return False

    # Use Playwright to render with matching viewport
    print("[2/4] Launching browser with matched viewport...")

    html_absolute = Path(html_path).resolve()
    if not html_absolute.exists():
        print(f"  ✗ Error: HTML file not found: {html_absolute}")
        return False

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)

            # Create context with matched viewport and device scale
            context = browser.new_context(
                viewport={'width': viewport_width, 'height': viewport_height},
                device_scale_factor=device_scale_factor
            )

            page = context.new_page()

            print(f"  ✓ Browser launched")
            print(f"  ✓ Viewport: {viewport_width}x{viewport_height}")
            print()

            # Load HTML
            print("[3/4] Loading HTML file...")
            page.goto(f'file://{html_absolute}')
            page.wait_for_load_state('networkidle')
            print(f"  ✓ Loaded: {html_absolute.name}")
            print()

            # Capture screenshot
            print("[4/4] Capturing screenshot...")
            page.screenshot(path=output_path)

            browser.close()

            # Verify output
            output_file = Path(output_path)
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                print(f"  ✓ Screenshot saved: {output_file.name}")
                print(f"  ✓ File size: {file_size:.1f} KB")
                print()
                print("=" * 70)
                print("✓ SUCCESS - Viewport-matched rendering complete")
                print("=" * 70)
                return True
            else:
                print(f"  ✗ Error: Screenshot file not created")
                return False

    except ImportError:
        print(f"  ✗ Error: Playwright not installed")
        print(f"  Run: pip install playwright && playwright install chromium")
        return False
    except Exception as e:
        print(f"  ✗ Error during rendering: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI interface for viewport-matched rendering"""

    if len(sys.argv) < 4:
        print("Usage: python render_with_viewport_match.py <html_file> <metadata_json> <output_screenshot> [scale]")
        print()
        print("Example:")
        print("  python render_with_viewport_match.py \\")
        print("    output/code/product-page.html \\")
        print("    output/pdp-trimmed-metadata.json \\")
        print("    output/screenshots/pdp-rendered-matched.png \\")
        print("    2.0")
        print()
        print("Arguments:")
        print("  html_file         - HTML file to render")
        print("  metadata_json     - Figma metadata with absoluteBoundingBox")
        print("  output_screenshot - Where to save screenshot")
        print("  scale             - Device scale factor (default: 2.0 for retina)")
        sys.exit(1)

    html_path = sys.argv[1]
    metadata_path = sys.argv[2]
    output_path = sys.argv[3]
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0

    success = render_with_figma_viewport(
        html_path,
        metadata_path,
        output_path,
        device_scale_factor=scale
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
