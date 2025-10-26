#!/usr/bin/env python3

"""
Enhanced Evaluation with DOM Measurements (Phase 1)

Combines pixel-diff evaluation with DOM-based dimensional analysis
to provide specific, actionable feedback for the improvement agent.
"""

import json
import subprocess
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tools.compare_measurements import compare_measurements, format_feedback_for_agent


def run_dom_measurement(html_path: str) -> dict:
    """
    Run DOM measurement script and return JSON results

    Args:
        html_path: Path to HTML file to measure

    Returns:
        Dictionary of measurements for each element
    """
    script_path = Path(__file__).parent.parent / 'tools' / 'measure_dom_simple.js'

    result = subprocess.run(
        ['node', str(script_path), html_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"DOM measurement failed: {result.stderr}")

    return json.loads(result.stdout)


def evaluate_with_measurements(html_path: str, output_dir: str = None) -> dict:
    """
    Run complete evaluation with DOM measurements

    Args:
        html_path: Path to HTML file
        output_dir: Optional directory to save results

    Returns:
        Dictionary with measurements, feedback, and summary
    """
    print(f"📏 Running DOM measurements on: {html_path}")

    # 1. Run DOM measurement
    measurements = run_dom_measurement(html_path)

    found_count = sum(1 for m in measurements.values() if m.get('found'))
    total_count = len(measurements)
    print(f"   Found {found_count}/{total_count} elements")

    # 2. Compare to Figma expected values
    print(f"\n🔍 Comparing to Figma design...")
    feedback = compare_measurements(measurements)

    # 3. Generate summary
    high_priority = len([f for f in feedback if f['priority'] == 'high'])
    medium_priority = len([f for f in feedback if f['priority'] == 'medium'])
    low_priority = len([f for f in feedback if f['priority'] == 'low'])

    summary = {
        'total_issues': len(feedback),
        'high_priority': high_priority,
        'medium_priority': medium_priority,
        'low_priority': low_priority,
        'measurements': measurements,
        'feedback': feedback,
        'formatted_feedback': format_feedback_for_agent(feedback)
    }

    # 4. Print summary
    print(f"\n📊 Results:")
    print(f"   Total issues: {summary['total_issues']}")
    print(f"   🔴 High: {high_priority}")
    print(f"   🟡 Medium: {medium_priority}")
    print(f"   🟢 Low: {low_priority}")

    # 5. Print formatted feedback
    print(f"\n{summary['formatted_feedback']}")

    # 6. Save results if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

        measurements_file = os.path.join(output_dir, 'dom_measurements.json')
        with open(measurements_file, 'w') as f:
            json.dump(measurements, f, indent=2)
        print(f"\n💾 Saved measurements to: {measurements_file}")

        feedback_file = os.path.join(output_dir, 'measurement_feedback.json')
        with open(feedback_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"💾 Saved feedback to: {feedback_file}")

    return summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python evaluate_with_measurements.py <html_file> [output_dir]")
        print("\nExample:")
        print("  python evaluate_with_measurements.py output/code/pdp.html")
        print("  python evaluate_with_measurements.py output/code/pdp.html output/evaluations/")
        sys.exit(1)

    html_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(html_path):
        print(f"❌ Error: File not found: {html_path}")
        sys.exit(1)

    try:
        summary = evaluate_with_measurements(html_path, output_dir)

        # Exit with code based on severity
        if summary['high_priority'] > 0:
            print("\n⚠️  High priority issues found - improvement needed")
            sys.exit(1)
        elif summary['medium_priority'] > 0:
            print("\n✅ No critical issues, but some improvements possible")
            sys.exit(0)
        else:
            print("\n🎉 All measurements match Figma design!")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
