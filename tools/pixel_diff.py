#!/usr/bin/env python3
"""
Day 4: Python wrapper for pixel_compare.js

This module provides a Python interface to the Node.js pixel comparison tool.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional


def compare_screenshots(
    figma_screenshot: str,
    rendered_screenshot: str,
    diff_output: Optional[str] = None
) -> Dict:
    """
    Compare two screenshots using pixelmatch.

    Args:
        figma_screenshot: Path to Figma screenshot (ground truth)
        rendered_screenshot: Path to rendered HTML screenshot
        diff_output: Optional path to save diff visualization

    Returns:
        Dictionary with comparison results:
        {
            'success': bool,
            'similarity': float,  # 0-100%
            'diffPixels': int,
            'totalPixels': int,
            'width': int,
            'height': int,
            'diffImagePath': str or None
        }
    """
    # Get absolute path to pixel_compare.js
    tools_dir = Path(__file__).parent
    script_path = tools_dir / "pixel_compare.js"

    if not script_path.exists():
        return {
            'success': False,
            'error': f'pixel_compare.js not found at {script_path}'
        }

    # Verify input files exist
    figma_path = Path(figma_screenshot)
    rendered_path = Path(rendered_screenshot)

    if not figma_path.exists():
        return {
            'success': False,
            'error': f'Figma screenshot not found: {figma_screenshot}'
        }

    if not rendered_path.exists():
        return {
            'success': False,
            'error': f'Rendered screenshot not found: {rendered_screenshot}'
        }

    # Build command
    cmd = ['node', str(script_path), str(figma_path), str(rendered_path)]

    if diff_output:
        cmd.append(str(diff_output))

    try:
        # Run Node.js script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        # Parse JSON output
        output = json.loads(result.stdout)
        return output

    except subprocess.CalledProcessError as e:
        # Node script failed
        try:
            error_data = json.loads(e.stdout)
            return error_data
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': f'Script failed: {e.stderr}'
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Comparison timed out after 30 seconds'
        }

    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Failed to parse output: {e}'
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'{type(e).__name__}: {e}'
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pixel_diff.py <image1> <image2> [diff-output]")
        print("Example: python pixel_diff.py img1.png img2.png diff.png")
        sys.exit(1)

    img1 = sys.argv[1]
    img2 = sys.argv[2]
    diff_out = sys.argv[3] if len(sys.argv) > 3 else None

    result = compare_screenshots(img1, img2, diff_out)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get('success') else 1)
