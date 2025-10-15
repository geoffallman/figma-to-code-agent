#!/usr/bin/env python3
"""
Day 3: Render HTML to Screenshot using Playwright

This script uses Playwright to render HTML files in a headless browser
and capture screenshots with a mobile viewport.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def render_html_to_screenshot(html_path: str, output_path: str, viewport_width: int = 390, viewport_height: int = 844) -> bool:
    """
    Render HTML in headless Chrome and capture screenshot.

    Args:
        html_path: Path to HTML file to render
        output_path: Where to save the screenshot
        viewport_width: Browser viewport width (default: 390px - iPhone)
        viewport_height: Browser viewport height (default: 844px - iPhone)

    Returns:
        True if successful, False otherwise
    """
    html_absolute = Path(html_path).resolve()

    if not html_absolute.exists():
        print(f"Error: HTML file not found: {html_absolute}")
        return False

    print(f"[1/3] Launching browser...")
    print(f"      Viewport: {viewport_width}x{viewport_height}px")

    try:
        with sync_playwright() as p:
            # Launch Chromium in headless mode
            browser = p.chromium.launch(headless=True)

            # Create page with mobile viewport
            page = browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})

            print(f"[2/3] Loading HTML file...")
            print(f"      File: {html_absolute}")

            # Load local HTML file
            page.goto(f'file://{html_absolute}')

            # Wait for page to fully load
            page.wait_for_load_state('networkidle')

            print(f"[3/3] Capturing screenshot...")
            print(f"      Output: {output_path}")

            # Capture screenshot
            page.screenshot(path=output_path)

            browser.close()

            # Verify screenshot was created
            output_file = Path(output_path)
            if output_file.exists():
                file_size = output_file.stat().st_size / 1024  # KB
                print(f"      ✓ Success! Saved {file_size:.1f} KB")
                return True
            else:
                print(f"      ✗ Error: Screenshot file not created")
                return False

    except Exception as e:
        print(f"      ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the Day 3 test"""
    print("=" * 60)
    print("Day 3: Render HTML to Screenshot")
    print("=" * 60)
    print()

    # Default paths
    project_root = Path(__file__).parent.parent
    html_file = project_root / "output" / "code" / "frame1-baseline.html"
    output_file = project_root / "output" / "screenshots" / "frame1-baseline-rendered.png"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Configuration:")
    print(f"  HTML File: {html_file}")
    print(f"  Output: {output_file}")
    print()

    # Render
    success = render_html_to_screenshot(str(html_file), str(output_file))

    print()
    print("=" * 60)
    if success:
        print("✓ TEST PASSED")
        print()
        print("Next steps:")
        print(f"  1. View screenshot: open {output_file}")
        print("  2. Verify it matches the HTML in browser")
        print("  3. Proceed to Day 4 (pixel-diff comparison)")
        return 0
    else:
        print("✗ TEST FAILED")
        print()
        print("Troubleshooting:")
        print("  1. Check that the HTML file exists")
        print("  2. Verify Playwright is installed: pip list | grep playwright")
        print("  3. Check Chromium is installed: playwright install chromium")
        return 1


if __name__ == "__main__":
    sys.exit(main())
