#!/usr/bin/env python3
"""
Fetch the new trimmed PDP frame from Figma (157-738)
Dimensions: 1440 x 1170
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from figma_api import FigmaClient

def main():
    """Fetch new PDP frame metadata and screenshot"""

    print("=" * 70)
    print("Fetching New Trimmed PDP Frame")
    print("=" * 70)
    print()

    # Configuration
    file_key = "jqrMDcomcoBE6Rvy8nJZ7p"
    node_id = "157:738"  # Converted from URL format 157-738

    print(f"File Key: {file_key}")
    print(f"Node ID: {node_id}")
    print(f"Expected Dimensions: 1440 x 1170")
    print()

    # Initialize client
    client = FigmaClient()

    # Output paths
    output_dir = Path(__file__).parent.parent / "output"
    metadata_path = output_dir / "pdp-trimmed-metadata.json"
    screenshot_path = output_dir / "screenshots" / "pdp-trimmed-figma.png"

    # Ensure output directories exist
    output_dir.mkdir(exist_ok=True)
    screenshot_path.parent.mkdir(exist_ok=True, parents=True)

    # Step 1: Fetch metadata
    print("[1/2] Fetching node metadata...")
    try:
        metadata = client.get_node_metadata(file_key, node_id)

        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"  ✓ Metadata saved: {metadata_path.name}")

        # Display dimensions
        if 'absoluteBoundingBox' in metadata:
            bounds = metadata['absoluteBoundingBox']
            width = bounds.get('width', 'N/A')
            height = bounds.get('height', 'N/A')
            print(f"  ✓ Frame dimensions: {width} x {height}")

        print()

    except Exception as e:
        print(f"  ✗ Error fetching metadata: {e}")
        return 1

    # Step 2: Fetch screenshot
    print("[2/2] Fetching screenshot...")
    try:
        success = client.export_image(
            file_key,
            node_id,
            output_path=str(screenshot_path),
            scale=2  # 2x for retina
        )

        if success:
            # Check file size
            file_size = screenshot_path.stat().st_size / 1024  # KB
            print(f"  ✓ Screenshot saved: {screenshot_path.name}")
            print(f"  ✓ File size: {file_size:.1f} KB")
        else:
            print(f"  ✗ Failed to export screenshot")
            return 1

    except Exception as e:
        print(f"  ✗ Error exporting screenshot: {e}")
        return 1

    print()
    print("=" * 70)
    print("✓ SUCCESS - New trimmed frame fetched")
    print()
    print("Next steps:")
    print(f"  1. View screenshot: open {screenshot_path}")
    print(f"  2. Check metadata: cat {metadata_path}")
    print(f"  3. Render HTML with matching viewport")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
