#!/usr/bin/env python3
"""
Day 1 Test: Can we fetch and save Figma screenshots from Python?

This script tests the critical assumption that we can:
1. Call the Figma MCP server from Python
2. Receive image data back
3. Save it to disk as a PNG file

If this works, the rest of the pipeline is straightforward.
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from datetime import datetime


def fetch_figma_screenshot(node_id: str, output_path: str) -> bool:
    """
    Test fetching a Figma screenshot via MCP server.

    Args:
        node_id: Figma node ID (e.g., "51:1216")
        output_path: Where to save the PNG

    Returns:
        True if successful, False otherwise
    """
    mcp_url = os.getenv('FIGMA_MCP_URL', 'http://localhost:3845/mcp')

    print(f"[1/4] Calling Figma MCP server at {mcp_url}")
    print(f"      Node ID: {node_id}")

    # Construct MCP JSON-RPC request
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_screenshot",
            "arguments": {
                "node_id": node_id,  # Note: underscore, not camelCase
                "clientLanguages": "python",
                "clientFrameworks": "langchain"
            }
        },
        "id": int(datetime.now().timestamp() * 1000)
    }

    try:
        # Call MCP server
        response = requests.post(
            mcp_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"[2/4] Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"      Error: HTTP {response.status_code}")
            print(f"      Body: {response.text[:200]}")
            return False

        result = response.json()

        # Debug: Show response structure
        print(f"[3/4] Parsing response...")
        if 'error' in result:
            print(f"      MCP Error: {result['error']}")
            return False

        if 'result' not in result:
            print(f"      Error: No 'result' in response")
            print(f"      Response keys: {list(result.keys())}")
            return False

        # Look for image data in the response
        result_data = result['result']

        # MCP responses typically have a 'content' array with image blocks
        if 'content' in result_data:
            for item in result_data['content']:
                if item.get('type') == 'image':
                    print(f"      Found image in response")

                    # Handle base64 data
                    if 'data' in item:
                        # Extract base64 data (may have data URL prefix)
                        image_data = item['data']
                        if image_data.startswith('data:image'):
                            # Remove data URL prefix
                            image_data = image_data.split(',')[1]

                        # Decode and save
                        image_bytes = base64.b64decode(image_data)

                        print(f"[4/4] Saving screenshot to {output_path}")
                        with open(output_path, 'wb') as f:
                            f.write(image_bytes)

                        file_size = len(image_bytes) / 1024  # KB
                        print(f"      ✓ Success! Saved {file_size:.1f} KB")
                        return True

                    # Handle URL (less common)
                    elif 'url' in item:
                        image_url = item['url']
                        print(f"      Image URL: {image_url}")

                        # Fetch image from URL
                        img_response = requests.get(image_url, timeout=30)
                        if img_response.status_code == 200:
                            with open(output_path, 'wb') as f:
                                f.write(img_response.content)

                            file_size = len(img_response.content) / 1024
                            print(f"[4/4] ✓ Success! Saved {file_size:.1f} KB")
                            return True

        # If we got here, we didn't find an image
        print(f"      Error: No image found in response")
        print(f"      Result structure: {json.dumps(result_data, indent=2)[:500]}")
        return False

    except requests.exceptions.ConnectionError:
        print(f"      Error: Could not connect to MCP server at {mcp_url}")
        print(f"      Is Figma MCP running? Check localhost:3845")
        return False
    except requests.exceptions.Timeout:
        print(f"      Error: Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"      Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the Day 1 test"""
    print("=" * 60)
    print("Day 1 Test: Figma MCP Screenshot Fetching")
    print("=" * 60)
    print()

    # Test node ID from spike (Frame 1)
    node_id = "51:1216"  # J.Crew mobile nav - Frame 1
    output_dir = Path(__file__).parent.parent / "output" / "screenshots"
    output_path = output_dir / "test-figma-frame1.png"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Test Configuration:")
    print(f"  Node ID: {node_id}")
    print(f"  Output: {output_path}")
    print()

    # Run test
    success = fetch_figma_screenshot(node_id, str(output_path))

    print()
    print("=" * 60)
    if success:
        print("✓ TEST PASSED")
        print()
        print("Next steps:")
        print("  1. Check the screenshot: open", output_path)
        print("  2. Verify it looks correct")
        print("  3. Proceed to Day 2 (baseline code generation)")
        return 0
    else:
        print("✗ TEST FAILED")
        print()
        print("Troubleshooting:")
        print("  1. Is Figma desktop app running?")
        print("  2. Is the MCP server accessible at localhost:3845?")
        print("  3. Try: curl http://localhost:3845/mcp")
        print("  4. Check that the node ID is valid in your Figma file")
        return 1


if __name__ == "__main__":
    sys.exit(main())
