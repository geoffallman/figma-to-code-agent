#!/usr/bin/env python3
"""
Extract images from Figma design for a specific test run
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from figma_api import FigmaClient

load_dotenv()


def extract_images_for_design(file_key: str, image_node_ids: list, output_dir: str):
    """
    Extract specific images from Figma

    Args:
        file_key: Figma file key
        image_node_ids: List of image node IDs to extract
        output_dir: Directory to save images
    """

    print("=" * 70)
    print("EXTRACTING IMAGES FROM FIGMA")
    print("=" * 70)
    print()

    client = FigmaClient()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"File: {file_key}")
    print(f"Images to extract: {len(image_node_ids)}")
    print(f"Output: {output_dir}")
    print()

    extracted = []

    for i, node_id in enumerate(image_node_ids, 1):
        clean_id = node_id.replace(':', '-')
        filename = f"image-{i}-{clean_id}.png"
        output_file = output_path / filename

        print(f"[{i}/{len(image_node_ids)}] Extracting {node_id}...")

        try:
            success = client.export_image(
                file_key=file_key,
                node_id=node_id,
                format='png',
                scale=2.0,
                output_path=str(output_file)
            )

            if success:
                file_size = output_file.stat().st_size / 1024  # KB
                print(f"  ✓ Saved: {filename} ({file_size:.1f} KB)")
                extracted.append({
                    'node_id': node_id,
                    'filename': filename,
                    'path': str(output_file)
                })
            else:
                print(f"  ✗ Failed to export {node_id}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print()
    print("=" * 70)
    print(f"✓ EXTRACTED {len(extracted)}/{len(image_node_ids)} IMAGES")
    print("=" * 70)

    return extracted


def main():
    if len(sys.argv) < 4:
        print("Usage: python extract_images.py <file_key> <node_ids_comma_separated> <output_dir>")
        print()
        print("Example:")
        print("  python scripts/extract_images.py \\")
        print("    jqrMDcomcoBE6Rvy8nJZ7p \\")
        print("    '157:745,157:746,157:747' \\")
        print("    output/images")
        sys.exit(1)

    file_key = sys.argv[1]
    node_ids = sys.argv[2].split(',')
    output_dir = sys.argv[3]

    extracted = extract_images_for_design(file_key, node_ids, output_dir)

    # Save manifest
    manifest_path = Path(output_dir) / 'images_manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(extracted, f, indent=2)

    print(f"\nManifest saved: {manifest_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
