#!/usr/bin/env python3

"""
Improvement Loop with DOM Measurements

Runs complete iteration:
1. Measure current HTML dimensions
2. Generate specific dimensional feedback
3. Apply improvements with Sonnet 4.5
4. Re-measure improved version
5. Compare before/after
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from tools.compare_measurements import compare_measurements, format_feedback_for_agent
from scripts.improve_code import improve_code
from scripts import render_html


def copy_images_if_exist(html_path: str, output_dir: str) -> bool:
    """
    Copy images from input HTML's directory to output directory

    Args:
        html_path: Path to input HTML file
        output_dir: Output directory where images should be copied

    Returns:
        True if images were copied, False if no images found
    """
    # Find input HTML's parent directory
    html_file = Path(html_path).resolve()
    html_dir = html_file.parent

    # Look for images directory next to the HTML file's parent
    # Example: .../run3/code/file.html -> .../run3/images/
    input_images_dir = html_dir.parent / 'images'

    if not input_images_dir.exists():
        # Try looking in same directory as HTML (for flat structures)
        input_images_dir = html_dir / 'images'

    if not input_images_dir.exists():
        print(f"   ⚠️  No images directory found near input HTML")
        return False

    # Copy images to output directory
    output_images_dir = Path(output_dir) / 'images'

    if output_images_dir.exists():
        print(f"   ℹ️  Images already exist in output directory")
        return True

    try:
        shutil.copytree(input_images_dir, output_images_dir)
        image_count = len(list(output_images_dir.glob('*.*')))
        print(f"   ✅ Copied {image_count} images from {input_images_dir}")
        return True
    except Exception as e:
        print(f"   ⚠️  Failed to copy images: {e}")
        return False


def run_dom_measurement(html_path: str) -> dict:
    """Run DOM measurement script and return JSON results"""
    script_path = Path(__file__).parent.parent / 'tools' / 'measure_dom_simple.js'

    result = subprocess.run(
        ['node', str(script_path), html_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"DOM measurement failed: {result.stderr}")

    return json.loads(result.stdout)


def calculate_accuracy_score(feedback: list) -> float:
    """
    Calculate accuracy score based on dimensional deviations

    Score formula:
    - Start at 100%
    - Subtract penalty for each issue:
      - High priority: -5% per issue
      - Medium priority: -2% per issue
      - Low priority: -1% per issue
    """
    score = 100.0

    for item in feedback:
        priority = item.get('priority', 'low')
        if priority == 'high':
            score -= 5.0
        elif priority == 'medium':
            score -= 2.0
        elif priority == 'low':
            score -= 1.0

    return max(0.0, score)


def run_improvement_loop(html_path: str, output_dir: str, version_name: str = None):
    """
    Run complete improvement loop with DOM measurements

    Args:
        html_path: Path to current HTML file
        output_dir: Directory to save results
        version_name: Optional version name (e.g., "v4", "improved")
    """

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Auto-generate version name if not provided
    if not version_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_name = f"improved_{timestamp}"

    print("=" * 70)
    print(f"🚀 Starting Improvement Loop")
    print(f"   Input: {html_path}")
    print(f"   Output: {output_dir}")
    print(f"   Version: {version_name}")
    print("=" * 70)

    # Copy images from input directory if they exist
    print(f"\n📦 Step 0: Copying images from input directory...")
    copy_images_if_exist(html_path, output_dir)

    # Step 1: Measure BEFORE
    print(f"\n📏 Step 1: Measuring current HTML...")
    measurements_before = run_dom_measurement(html_path)

    found_count = sum(1 for m in measurements_before.values() if m.get('found'))
    total_count = len(measurements_before)
    print(f"   Found {found_count}/{total_count} elements")

    # Step 2: Compare to Figma and generate feedback
    print(f"\n🔍 Step 2: Comparing to Figma design...")
    feedback = compare_measurements(measurements_before)

    high_priority = len([f for f in feedback if f['priority'] == 'high'])
    medium_priority = len([f for f in feedback if f['priority'] == 'medium'])
    low_priority = len([f for f in feedback if f['priority'] == 'low'])

    accuracy_before = calculate_accuracy_score(feedback)

    print(f"   Total issues: {len(feedback)}")
    print(f"   🔴 High: {high_priority}")
    print(f"   🟡 Medium: {medium_priority}")
    print(f"   🟢 Low: {low_priority}")
    print(f"   Accuracy score: {accuracy_before:.1f}%")

    if len(feedback) == 0:
        print(f"\n✅ No issues found! Code already matches Figma design.")
        return

    # Print formatted feedback
    formatted_feedback = format_feedback_for_agent(feedback)
    print(f"\n{formatted_feedback}")

    # Save BEFORE measurements
    before_file = os.path.join(output_dir, f'{version_name}_before_measurements.json')
    with open(before_file, 'w') as f:
        json.dump({
            'measurements': measurements_before,
            'feedback': feedback,
            'accuracy_score': accuracy_before,
            'total_issues': len(feedback),
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority
        }, f, indent=2)
    print(f"\n💾 Saved BEFORE measurements to: {before_file}")

    # Step 3: Read original code
    print(f"\n📖 Step 3: Reading original code...")
    with open(html_path, 'r') as f:
        original_code = f.read()
    print(f"   Code length: {len(original_code)} characters")

    # Step 4: Apply improvements with Sonnet 4.5
    print(f"\n🤖 Step 4: Applying improvements with Claude Sonnet 4.5...")
    print(f"   Feeding {len(feedback)} feedback items to improvement agent...")

    improvement_result = improve_code(
        original_code=original_code,
        feedback=feedback,
        figma_context="Product detail page for J.Crew cashmere cardigan"
    )

    improved_code = improvement_result['improved_code']
    changes_applied = improvement_result.get('changes_applied', [])

    print(f"   ✅ Improvements applied!")
    print(f"   Changes made: {len(changes_applied)}")

    # Save improved code (in code/ subdirectory to match structure)
    code_dir = os.path.join(output_dir, 'code')
    os.makedirs(code_dir, exist_ok=True)
    improved_html_path = os.path.join(code_dir, f'{version_name}.html')
    with open(improved_html_path, 'w') as f:
        f.write(improved_code)
    print(f"\n💾 Saved improved code to: {improved_html_path}")

    # Step 5: Render improved version
    print(f"\n🎨 Step 5: Rendering improved version...")
    screenshot_path = os.path.join(output_dir, f'{version_name}_rendered.png')

    render_success = render_html.render_html_to_screenshot(
        html_path=improved_html_path,
        output_path=screenshot_path,
        viewport_width=1440,
        viewport_height=1170
    )

    if render_success:
        print(f"   ✅ Rendered to: {screenshot_path}")
    else:
        print(f"   ⚠️  Rendering failed (continuing anyway)")

    # Step 6: Measure AFTER
    print(f"\n📏 Step 6: Measuring improved HTML...")
    measurements_after = run_dom_measurement(improved_html_path)

    found_count_after = sum(1 for m in measurements_after.values() if m.get('found'))
    print(f"   Found {found_count_after}/{total_count} elements")

    # Step 7: Compare AFTER to Figma
    print(f"\n🔍 Step 7: Comparing improved version to Figma...")
    feedback_after = compare_measurements(measurements_after)

    high_priority_after = len([f for f in feedback_after if f['priority'] == 'high'])
    medium_priority_after = len([f for f in feedback_after if f['priority'] == 'medium'])
    low_priority_after = len([f for f in feedback_after if f['priority'] == 'low'])

    accuracy_after = calculate_accuracy_score(feedback_after)

    print(f"   Total issues: {len(feedback_after)}")
    print(f"   🔴 High: {high_priority_after}")
    print(f"   🟡 Medium: {medium_priority_after}")
    print(f"   🟢 Low: {low_priority_after}")
    print(f"   Accuracy score: {accuracy_after:.1f}%")

    # Save AFTER measurements
    after_file = os.path.join(output_dir, f'{version_name}_after_measurements.json')
    with open(after_file, 'w') as f:
        json.dump({
            'measurements': measurements_after,
            'feedback': feedback_after,
            'accuracy_score': accuracy_after,
            'total_issues': len(feedback_after),
            'high_priority': high_priority_after,
            'medium_priority': medium_priority_after,
            'low_priority': low_priority_after
        }, f, indent=2)
    print(f"\n💾 Saved AFTER measurements to: {after_file}")

    # Step 8: Calculate delta
    print(f"\n📊 Step 8: Calculating improvement delta...")

    issues_fixed = len(feedback) - len(feedback_after)
    accuracy_delta = accuracy_after - accuracy_before

    print(f"\n{'=' * 70}")
    print(f"📈 RESULTS SUMMARY")
    print(f"{'=' * 70}")
    print(f"\n🔴 High Priority Issues:")
    print(f"   BEFORE: {high_priority}")
    print(f"   AFTER:  {high_priority_after}")
    print(f"   Delta:  {high_priority - high_priority_after:+d}")

    print(f"\n🟡 Medium Priority Issues:")
    print(f"   BEFORE: {medium_priority}")
    print(f"   AFTER:  {medium_priority_after}")
    print(f"   Delta:  {medium_priority - medium_priority_after:+d}")

    print(f"\n📊 Total Issues:")
    print(f"   BEFORE: {len(feedback)}")
    print(f"   AFTER:  {len(feedback_after)}")
    print(f"   Fixed:  {issues_fixed} ({issues_fixed / len(feedback) * 100:.1f}%)")

    print(f"\n🎯 Accuracy Score:")
    print(f"   BEFORE: {accuracy_before:.1f}%")
    print(f"   AFTER:  {accuracy_after:.1f}%")
    print(f"   Delta:  {accuracy_delta:+.1f}%")

    print(f"\n{'=' * 70}")

    if accuracy_delta > 0:
        print(f"✅ SUCCESS! Improved by {accuracy_delta:.1f}%")
    elif accuracy_delta == 0:
        print(f"➡️  No change in accuracy score")
    else:
        print(f"⚠️  Accuracy decreased by {abs(accuracy_delta):.1f}%")

    print(f"{'=' * 70}\n")

    # Save summary
    summary_file = os.path.join(output_dir, f'{version_name}_summary.json')
    with open(summary_file, 'w') as f:
        json.dump({
            'version_name': version_name,
            'input_file': html_path,
            'output_file': improved_html_path,
            'before': {
                'accuracy_score': accuracy_before,
                'total_issues': len(feedback),
                'high_priority': high_priority,
                'medium_priority': medium_priority,
                'low_priority': low_priority
            },
            'after': {
                'accuracy_score': accuracy_after,
                'total_issues': len(feedback_after),
                'high_priority': high_priority_after,
                'medium_priority': medium_priority_after,
                'low_priority': low_priority_after
            },
            'delta': {
                'accuracy_score': accuracy_delta,
                'issues_fixed': issues_fixed,
                'high_priority': high_priority - high_priority_after,
                'medium_priority': medium_priority - medium_priority_after,
                'low_priority': low_priority - low_priority_after
            },
            'changes_applied': changes_applied
        }, f, indent=2)
    print(f"💾 Saved summary to: {summary_file}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_improvement_loop_with_measurements.py <html_file> [output_dir] [version_name]")
        print("\nExample:")
        print("  python run_improvement_loop_with_measurements.py output/code/pdp.html")
        print("  python run_improvement_loop_with_measurements.py output/code/pdp.html output/test-run4 v4")
        sys.exit(1)

    html_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'output/improvement-loop'
    version_name = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.exists(html_path):
        print(f"❌ Error: File not found: {html_path}")
        sys.exit(1)

    try:
        run_improvement_loop(html_path, output_dir, version_name)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
