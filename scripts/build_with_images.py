#!/usr/bin/env python3
"""
Enhanced Builder: Generate code from Figma with image asset extraction

This script:
1. Fetches Figma node metadata
2. Discovers and exports all image nodes
3. Generates HTML with correct image paths
4. Renders and evaluates the result

Usage:
    python scripts/build_with_images.py <figma_url> [--output-name custom-name]
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.figma_api import FigmaClient, FigmaAPIError
from tools import pixel_diff
import subprocess


def build_with_images(figma_url: str, output_name: str = None):
    """
    Complete build workflow with image extraction

    Args:
        figma_url: Full Figma URL with node-id
        output_name: Optional custom name for output files
    """
    print("=" * 80)
    print("FIGMA-TO-CODE BUILDER WITH IMAGE EXTRACTION")
    print("=" * 80)

    # Initialize client
    load_dotenv(Path(__file__).parent.parent / '.env')
    client = FigmaClient()

    # Parse URL
    print("\n1. Parsing Figma URL...")
    parsed = FigmaClient.parse_figma_url(figma_url)
    file_key = parsed['file_key']
    node_id = parsed['node_id']

    print(f"   File: {file_key}")
    print(f"   Node: {node_id}")

    # Generate output name if not provided
    if not output_name:
        output_name = f"frame-{node_id.replace(':', '-')}"

    # Create output directories
    output_dir = Path('output')
    code_dir = output_dir / 'code'
    images_dir = output_dir / 'images'
    screenshots_dir = output_dir / 'screenshots'

    for dir in [code_dir, images_dir, screenshots_dir]:
        dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Get node metadata
    print("\n2. Fetching node metadata from Figma...")
    try:
        metadata = client.get_node_metadata(file_key, node_id, depth=10)
        print(f"   ✓ Retrieved {metadata.get('name')}")
        print(f"   Type: {metadata.get('type')}")
        print(f"   Children: {len(metadata.get('children', []))}")

        # Save metadata for reference
        metadata_path = output_dir / f"{output_name}-metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"   ✓ Saved metadata: {metadata_path}")

    except FigmaAPIError as e:
        print(f"   ✗ Error fetching metadata: {e}")
        return False

    # Step 2: Find image nodes
    print("\n3. Finding image nodes...")
    images = client.find_image_nodes(metadata)
    print(f"   ✓ Found {len(images)} image nodes")

    if images:
        for i, img in enumerate(images[:5], 1):
            print(f"      {i}. {img['name']} ({img['type']})")
        if len(images) > 5:
            print(f"      ... and {len(images) - 5} more")

    # Step 3: Export images
    image_files = {}
    if images:
        print("\n4. Exporting images from Figma...")

        for i, img in enumerate(images, 1):
            node_id_clean = img['id'].replace(':', '-')
            filename = f"{output_name}-image-{i}-{node_id_clean}.png"
            output_path = images_dir / filename

            try:
                print(f"   Exporting {i}/{len(images)}: {img['name']}")
                client.export_image(
                    file_key=file_key,
                    node_id=img['id'],
                    format='png',
                    scale=2.0,
                    output_path=str(output_path)
                )

                # Store mapping of node ID to file path
                image_files[img['id']] = {
                    'filename': filename,
                    'path': str(output_path),
                    'relative_path': f"../images/{filename}",
                    'name': img['name'],
                    'bounds': img.get('bounds', {})
                }
                print(f"      ✓ Saved: {filename}")

            except Exception as e:
                print(f"      ✗ Failed: {e}")
    else:
        print("\n4. No images to export (skipping)")

    # Save image manifest
    if image_files:
        manifest_path = output_dir / f"{output_name}-images.json"
        with open(manifest_path, 'w') as f:
            json.dump(image_files, f, indent=2)
        print(f"   ✓ Image manifest: {manifest_path}")

    # Step 4: Generate HTML (placeholder for now)
    print("\n5. Generating HTML...")
    print("   Note: Full HTML generation coming in next step")
    print("   For now, showing how images would be included:")
    print()

    if image_files:
        print("   HTML Image Tags:")
        for node_id, img_info in list(image_files.items())[:3]:
            bounds = img_info.get('bounds', {})
            width = bounds.get('width', 0)
            height = bounds.get('height', 0)
            print(f"   <img src=\"{img_info['relative_path']}\" ")
            print(f"        alt=\"{img_info['name']}\" ")
            if width and height:
                print(f"        width=\"{width:.0f}\" height=\"{height:.0f}\" />")
            else:
                print(f"        />")
            print()

    # Step 5: Export Figma screenshot for comparison
    print("\n6. Exporting Figma screenshot (ground truth)...")
    figma_screenshot_path = screenshots_dir / f"{output_name}-figma.png"

    try:
        client.export_image(
            file_key=file_key,
            node_id=parsed['node_id'],
            format='png',
            scale=2.0,
            output_path=str(figma_screenshot_path)
        )
        print(f"   ✓ Saved: {figma_screenshot_path}")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        figma_screenshot_path = None

    # Summary
    print("\n" + "=" * 80)
    print("BUILD COMPLETE!")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  Metadata: {metadata_path}")
    if image_files:
        print(f"  Images: {len(image_files)} files in {images_dir}/")
        print(f"  Manifest: {manifest_path}")
    if figma_screenshot_path:
        print(f"  Figma screenshot: {figma_screenshot_path}")

    print(f"\nNext steps:")
    print(f"  1. Generate HTML with image tags")
    print(f"  2. Render HTML to screenshot")
    print(f"  3. Compare with Figma screenshot")
    print(f"  4. Iterate to improve")

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scripts/build_with_images.py <figma_url> [--output-name name]")
        print()
        print("Example:")
        print("  python scripts/build_with_images.py \\")
        print("    'https://www.figma.com/design/jqrMDcomcoBE6Rvy8nJZ7p/JC-Ideas?node-id=120-13152'")
        sys.exit(1)

    figma_url = sys.argv[1]

    # Parse optional output name
    output_name = None
    if '--output-name' in sys.argv:
        idx = sys.argv.index('--output-name')
        if idx + 1 < len(sys.argv):
            output_name = sys.argv[idx + 1]

    success = build_with_images(figma_url, output_name)
    sys.exit(0 if success else 1)
