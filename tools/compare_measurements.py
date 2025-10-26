#!/usr/bin/env python3

"""
Simple Measurement Comparison Tool (Phase 1 - Manual Mapping)

Compares Figma metadata to DOM measurements and generates
specific, actionable feedback for the improvement agent.
"""

import json
import sys
from typing import Dict, List, Any


# Manual mapping: Figma node IDs to DOM measurement keys
ELEMENT_MAPPING = {
    'main_product_image': {
        'figma_id': '157:745',
        'figma_name': 'Image1',
        'expected_width': 576.0,
        'expected_height': 720.0,
        'type': 'image'
    },
    'product_title': {
        'figma_id': '157:800',
        'figma_name': 'Brushed cashmere short-sleeve cardigan',
        'expected_width': 500.0,
        'expected_height': 24.0,
        'expected_font_size': 24.0,
        'expected_font_family': 'Big Caslon',
        'type': 'text'
    },
    'product_description': {
        'figma_id': '157:814',
        'figma_name': 'romance copy',
        'expected_width': 500.0,
        'expected_height': 108.0,
        'expected_font_size': 18.0,
        'expected_font_family': 'Soleil',
        'type': 'text'
    },
    'selection_bar': {
        'figma_id': '157:817',
        'figma_name': 'floating-selection-bar',
        'expected_width': 1162.0,
        'expected_height': 112.0,
        'type': 'container'
    },
    'left_column': {
        'figma_id': '157:798',
        'figma_name': 'left column',
        'expected_width': 500.0,
        'expected_height': 224.0,
        'type': 'container'
    }
}


def calculate_deviation(actual: float, expected: float) -> float:
    """Calculate percentage deviation"""
    if expected == 0:
        return 0.0
    return ((actual - expected) / expected) * 100


def parse_font_size(font_size_str: str) -> float:
    """Extract numeric font size from CSS string like '24px'"""
    if not font_size_str:
        return 0.0
    try:
        return float(font_size_str.replace('px', '').strip())
    except ValueError:
        return 0.0


def compare_measurements(dom_measurements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compare DOM measurements to expected Figma values

    Returns:
        List of feedback items with specific dimensional issues
    """
    feedback = []

    for element_key, expected in ELEMENT_MAPPING.items():
        dom_elem = dom_measurements.get(element_key)

        # Check if element was found
        if not dom_elem or not dom_elem.get('found'):
            feedback.append({
                'priority': 'high',
                'category': 'missing_element',
                'element': expected['figma_name'],
                'figma_id': expected['figma_id'],
                'issue': f"Element not found in DOM",
                'fix': f"Add {expected['type']} element matching Figma node {expected['figma_id']}"
            })
            continue

        # Get actual dimensions
        dims = dom_elem.get('dimensions', {})
        actual_width = dims.get('width', 0)
        actual_height = dims.get('height', 0)

        # Compare width
        width_deviation = calculate_deviation(actual_width, expected['expected_width'])
        if abs(width_deviation) > 10:  # More than 10% off
            direction = 'wide' if width_deviation > 0 else 'narrow'
            feedback.append({
                'priority': 'high' if abs(width_deviation) > 20 else 'medium',
                'category': 'dimension',
                'element': expected['figma_name'],
                'figma_id': expected['figma_id'],
                'issue': f"Width is {actual_width}px, should be {expected['expected_width']}px",
                'deviation': f"{abs(width_deviation):.1f}% too {direction}",
                'fix': f"Set width to {expected['expected_width']}px"
            })

        # Compare height
        height_deviation = calculate_deviation(actual_height, expected['expected_height'])
        if abs(height_deviation) > 10:  # More than 10% off
            direction = 'tall' if height_deviation > 0 else 'short'
            feedback.append({
                'priority': 'high' if abs(height_deviation) > 20 else 'medium',
                'category': 'dimension',
                'element': expected['figma_name'],
                'figma_id': expected['figma_id'],
                'issue': f"Height is {actual_height}px, should be {expected['expected_height']}px",
                'deviation': f"{abs(height_deviation):.1f}% too {direction}",
                'fix': f"Set height to {expected['expected_height']}px"
            })

        # Compare font size (if text element)
        if expected['type'] == 'text' and 'expected_font_size' in expected:
            actual_font_size = parse_font_size(dom_elem.get('styles', {}).get('fontSize', ''))
            font_size_deviation = calculate_deviation(actual_font_size, expected['expected_font_size'])

            if abs(font_size_deviation) > 10:
                direction = 'large' if font_size_deviation > 0 else 'small'
                feedback.append({
                    'priority': 'medium',
                    'category': 'typography',
                    'element': expected['figma_name'],
                    'figma_id': expected['figma_id'],
                    'issue': f"Font size is {actual_font_size}px, should be {expected['expected_font_size']}px",
                    'deviation': f"{abs(font_size_deviation):.1f}% too {direction}",
                    'fix': f"Set font-size to {expected['expected_font_size']}px"
                })

    return feedback


def format_feedback_for_agent(feedback: List[Dict[str, Any]]) -> str:
    """
    Format feedback as readable text for improvement agent
    """
    if not feedback:
        return "✅ All measurements match Figma design!"

    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    feedback.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['element']))

    output = []
    output.append(f"Found {len(feedback)} dimensional issues:\n")

    for i, item in enumerate(feedback, 1):
        priority_emoji = '🔴' if item['priority'] == 'high' else '🟡' if item['priority'] == 'medium' else '🟢'
        output.append(f"{i}. {priority_emoji} [{item['priority'].upper()}] {item['element']}")
        output.append(f"   Issue: {item['issue']}")
        if 'deviation' in item:
            output.append(f"   Deviation: {item['deviation']}")
        output.append(f"   Fix: {item['fix']}")
        output.append("")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_measurements.py <dom_measurements.json>", file=sys.stderr)
        print("Example: python compare_measurements.py measurements.json", file=sys.stderr)
        sys.exit(1)

    measurements_file = sys.argv[1]

    try:
        # Load DOM measurements
        with open(measurements_file, 'r') as f:
            dom_measurements = json.load(f)

        # Compare to Figma expected values
        feedback = compare_measurements(dom_measurements)

        # Output structured JSON
        output = {
            'total_issues': len(feedback),
            'high_priority': len([f for f in feedback if f['priority'] == 'high']),
            'medium_priority': len([f for f in feedback if f['priority'] == 'medium']),
            'low_priority': len([f for f in feedback if f['priority'] == 'low']),
            'feedback': feedback,
            'formatted_feedback': format_feedback_for_agent(feedback)
        }

        print(json.dumps(output, indent=2))

        # Print summary to stderr
        print(f"\n✅ Comparison complete!", file=sys.stderr)
        print(f"Total issues: {output['total_issues']}", file=sys.stderr)
        print(f"  🔴 High: {output['high_priority']}", file=sys.stderr)
        print(f"  🟡 Medium: {output['medium_priority']}", file=sys.stderr)
        print(f"  🟢 Low: {output['low_priority']}", file=sys.stderr)

    except FileNotFoundError:
        print(f"❌ Error: File not found: {measurements_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
