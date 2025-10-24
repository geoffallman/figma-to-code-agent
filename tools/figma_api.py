#!/usr/bin/env python3
"""
Figma REST API Client
Provides reliable access to Figma files, node metadata, and image exports.
Replaces unreliable MCP connection with direct API calls.
"""

import os
import requests
from typing import Dict, List, Optional
from pathlib import Path
import json


class FigmaAPIError(Exception):
    """Custom exception for Figma API errors"""
    pass


class FigmaClient:
    """
    Client for Figma REST API

    Provides methods to:
    - Get node metadata (structure, children, types)
    - Export images (screenshots of any node)
    - Batch operations for efficiency

    Docs: https://www.figma.com/developers/api
    """

    def __init__(self, api_token: str = None):
        """
        Initialize Figma API client

        Args:
            api_token: Figma personal access token
                      If not provided, reads from FIGMA_API_TOKEN env var
        """
        self.token = api_token or os.getenv('FIGMA_API_TOKEN')
        if not self.token:
            raise FigmaAPIError(
                "Figma API token required. "
                "Pass as argument or set FIGMA_API_TOKEN environment variable."
            )

        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            'X-Figma-Token': self.token,
            'Content-Type': 'application/json'
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request to Figma API with error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON data

        Raises:
            FigmaAPIError: On API errors or network issues
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"Figma API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_msg += f" - {error_data.get('err', error_data.get('message', ''))}"
            except:
                pass
            raise FigmaAPIError(error_msg) from e

        except requests.exceptions.RequestException as e:
            raise FigmaAPIError(f"Network error: {str(e)}") from e

    def get_file_metadata(self, file_key: str) -> Dict:
        """
        Get basic file information

        Args:
            file_key: Figma file key (from URL)

        Returns:
            File metadata including name, last modified, etc.
        """
        return self._make_request('GET', f'files/{file_key}')

    def get_node_metadata(self, file_key: str, node_id: str, depth: int = 3) -> Dict:
        """
        Get detailed metadata for a specific node and its children

        Returns structure including:
        - Node type (FRAME, IMAGE, TEXT, etc.)
        - Children nodes (recursive)
        - Bounding boxes and positions
        - Layer names

        This replaces mcp__figma__get_metadata

        Args:
            file_key: Figma file key
            node_id: Node ID to fetch
            depth: How many levels of children to fetch (default 3)

        Returns:
            Node metadata with children
        """
        params = {
            'ids': node_id,
            'depth': depth
        }

        response = self._make_request('GET', f'files/{file_key}/nodes', params=params)

        # API returns: {"nodes": {"node-id": {...}}}
        nodes = response.get('nodes', {})
        node_data = nodes.get(node_id)

        if not node_data:
            raise FigmaAPIError(f"Node {node_id} not found in file {file_key}")

        return node_data.get('document', {})

    def export_image(
        self,
        file_key: str,
        node_id: str,
        format: str = 'png',
        scale: float = 2.0,
        output_path: Optional[str] = None
    ) -> str:
        """
        Export a node as an image

        This replaces mcp__figma__get_screenshot

        Args:
            file_key: Figma file key
            node_id: Node ID to export
            format: Image format (png, jpg, svg, pdf)
            scale: Export scale (1.0 = 1x, 2.0 = 2x for retina)
            output_path: Where to save image (optional)

        Returns:
            Path to saved image or image URL if output_path not provided
        """
        # Step 1: Request image export
        params = {
            'ids': node_id,
            'format': format,
            'scale': scale
        }

        export_response = self._make_request(
            'GET',
            f'images/{file_key}',
            params=params
        )

        # Get image URL from response
        images = export_response.get('images', {})
        image_url = images.get(node_id)

        if not image_url:
            raise FigmaAPIError(f"Failed to export node {node_id}")

        # Step 2: Download image if output path provided
        if output_path:
            image_response = requests.get(image_url)
            image_response.raise_for_status()

            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Save image
            with open(output_path, 'wb') as f:
                f.write(image_response.content)

            return output_path

        return image_url

    def batch_export_images(
        self,
        file_key: str,
        node_ids: List[str],
        format: str = 'png',
        scale: float = 2.0,
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Export multiple nodes as images in a single API call

        More efficient than calling export_image multiple times

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to export
            format: Image format
            scale: Export scale
            output_dir: Directory to save images (optional)

        Returns:
            Dict mapping node_id -> image_path or image_url
        """
        # Request all exports at once
        params = {
            'ids': ','.join(node_ids),
            'format': format,
            'scale': scale
        }

        export_response = self._make_request(
            'GET',
            f'images/{file_key}',
            params=params
        )

        images = export_response.get('images', {})
        results = {}

        # Download each image if output_dir provided
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            for node_id, image_url in images.items():
                # Generate filename from node_id
                filename = f"{node_id.replace(':', '-')}.{format}"
                output_path = os.path.join(output_dir, filename)

                # Download image
                image_response = requests.get(image_url)
                image_response.raise_for_status()

                with open(output_path, 'wb') as f:
                    f.write(image_response.content)

                results[node_id] = output_path
        else:
            results = images

        return results

    def find_image_nodes(self, node_data: Dict) -> List[Dict]:
        """
        Recursively find all nodes with image fills in a node tree

        Finds:
        - RECTANGLE nodes with IMAGE fills
        - FRAME nodes with IMAGE fills (common for product photos)
        - IMAGE nodes (standalone images)

        Args:
            node_data: Node metadata from get_node_metadata()

        Returns:
            List of dicts with image node info:
            [
                {
                    'id': 'node-id',
                    'name': 'Product Photo',
                    'bounds': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    'type': 'FRAME' or 'RECTANGLE' or 'IMAGE',
                    'image_ref': 'hash'
                }
            ]
        """
        images = []

        # Check for nodes with IMAGE fills (RECTANGLE or FRAME)
        node_type = node_data.get('type')
        if node_type in ['RECTANGLE', 'FRAME'] and node_data.get('fills'):
            # Check if it has image fill
            for fill in node_data.get('fills', []):
                if fill.get('type') == 'IMAGE':
                    images.append({
                        'id': node_data['id'],
                        'name': node_data.get('name', 'Unnamed'),
                        'bounds': node_data.get('absoluteBoundingBox', {}),
                        'type': node_type,
                        'image_ref': fill.get('imageRef')
                    })
                    break

        # Also check for standalone IMAGE type nodes
        if node_type == 'IMAGE':
            images.append({
                'id': node_data['id'],
                'name': node_data.get('name', 'Unnamed'),
                'bounds': node_data.get('absoluteBoundingBox', {}),
                'type': 'IMAGE'
            })

        # Recursively check children
        for child in node_data.get('children', []):
            images.extend(self.find_image_nodes(child))

        return images

    @staticmethod
    def parse_figma_url(url: str) -> Dict[str, str]:
        """
        Parse Figma URL to extract file_key and node_id

        Args:
            url: Figma URL like:
                https://www.figma.com/file/ABC123/Name?node-id=123-456
                or
                https://www.figma.com/design/ABC123/Name?node-id=123-456

        Returns:
            {'file_key': 'ABC123', 'node_id': '123:456'}
        """
        import re

        # Extract file key
        file_match = re.search(r'/(?:file|design)/([a-zA-Z0-9]+)', url)
        if not file_match:
            raise ValueError(f"Could not extract file key from URL: {url}")

        file_key = file_match.group(1)

        # Extract node ID (convert dash format to colon format)
        node_match = re.search(r'node-id=([0-9]+-[0-9]+)', url)
        if not node_match:
            return {'file_key': file_key, 'node_id': None}

        node_id = node_match.group(1).replace('-', ':')

        return {
            'file_key': file_key,
            'node_id': node_id
        }


# Convenience function for quick access
def create_client(api_token: str = None) -> FigmaClient:
    """Create a FigmaClient instance"""
    return FigmaClient(api_token)


if __name__ == '__main__':
    # Quick test
    print("Figma REST API Client")
    print("=" * 50)

    try:
        client = create_client()
        print("✓ Client initialized")
        print(f"  Token: {client.token[:10]}...")

        # Test URL parsing
        test_url = "https://www.figma.com/file/ABC123/Test?node-id=120-13152"
        parsed = FigmaClient.parse_figma_url(test_url)
        print(f"\n✓ URL parsing works")
        print(f"  File key: {parsed['file_key']}")
        print(f"  Node ID: {parsed['node_id']}")

    except FigmaAPIError as e:
        print(f"✗ Error: {e}")
        print("\nMake sure FIGMA_API_TOKEN environment variable is set")
