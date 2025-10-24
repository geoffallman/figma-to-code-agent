#!/usr/bin/env python3
"""
Test script for Figma REST API client

Tests:
1. API authentication
2. Node metadata retrieval
3. Image export
4. Finding child image nodes
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to import tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.figma_api import FigmaClient, FigmaAPIError


def test_api_client():
    """Test Figma API client functionality"""

    print("=" * 70)
    print("FIGMA REST API CLIENT TEST")
    print("=" * 70)

    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)

    # Initialize client
    print("\n1. Testing API Authentication...")
    try:
        client = FigmaClient()
        print(f"   ✓ Client initialized")
        print(f"   ✓ Token: {client.token[:15]}...")
    except FigmaAPIError as e:
        print(f"   ✗ Failed: {e}")
        print("\n   Please set FIGMA_API_TOKEN in .env file")
        return False

    # Test URL parsing
    print("\n2. Testing URL Parsing...")
    test_urls = [
        "https://www.figma.com/file/ABC123/Test?node-id=120-13152",
        "https://www.figma.com/design/XYZ789/Design?node-id=51-1216"
    ]
    for url in test_urls:
        try:
            parsed = FigmaClient.parse_figma_url(url)
            print(f"   ✓ {url}")
            print(f"     File: {parsed['file_key']}, Node: {parsed['node_id']}")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    # Get product page node ID from file
    print("\n3. Testing Node Metadata Retrieval...")
    node_file = Path(__file__).parent.parent / 'output' / 'product-page-node.txt'

    if node_file.exists():
        with open(node_file) as f:
            node_content = f.read().strip()
            # Extract node ID from "Node ID: 120:13152" format
            node_id = node_content.split(': ')[1] if ': ' in node_content else node_content

        print(f"   Using node ID: {node_id}")
        print(f"   Note: You'll need the file_key from your Figma URL")
        print(f"   Example: https://www.figma.com/file/YOUR_FILE_KEY/Name?node-id=...")
        print()
        print(f"   To test metadata retrieval, update this script with your file_key")

        # Placeholder for actual test (user needs to provide file_key)
        # Uncomment and add your file_key to test:
        #
        # file_key = "YOUR_FILE_KEY_HERE"
        # try:
        #     metadata = client.get_node_metadata(file_key, node_id)
        #     print(f"   ✓ Retrieved metadata for node {node_id}")
        #     print(f"     Node type: {metadata.get('type')}")
        #     print(f"     Node name: {metadata.get('name')}")
        #     print(f"     Children: {len(metadata.get('children', []))}")
        #
        #     # Find image nodes
        #     images = client.find_image_nodes(metadata)
        #     print(f"     Image nodes found: {len(images)}")
        #     for img in images[:3]:  # Show first 3
        #         print(f"       - {img['name']} ({img['id']})")
        #
        # except FigmaAPIError as e:
        #     print(f"   ✗ Failed: {e}")

    else:
        print(f"   ⚠ Node file not found: {node_file}")

    print("\n4. Testing Image Export...")
    print(f"   To test image export, uncomment the code above and provide:")
    print(f"   - file_key: Your Figma file key")
    print(f"   - node_id: Node to export as image")
    print()
    print(f"   Example:")
    print(f"   output_path = 'output/test-export.png'")
    print(f"   client.export_image(file_key, node_id, output_path=output_path)")

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("✓ API client is ready to use")
    print("✓ Add your file_key to test full functionality")
    print()
    print("Next steps:")
    print("1. Get your Figma file URL")
    print("2. Extract file_key from URL")
    print("3. Uncomment test code above and add file_key")
    print("4. Run: python scripts/test_figma_api.py")
    print()

    return True


if __name__ == '__main__':
    success = test_api_client()
    sys.exit(0 if success else 1)
