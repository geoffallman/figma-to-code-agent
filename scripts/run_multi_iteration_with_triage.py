#!/usr/bin/env python3

"""
Multi-Iteration Improvement Loop with Triage

Runs up to 2 automatic improvement iterations.
If plateau detected (no improvement), triggers designer triage.

Workflow:
1. Loop 1: Auto-fix easy issues (widths, fonts)
2. Loop 2: Validate & attempt remaining issues
3. If plateau: Generate designer questions
4. Designer reviews & provides input
5. Loop 3+: Apply designer guidance
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
from tools.triage_issues import triage_issues, format_triage_report_for_display, save_triage_report
from scripts.improve_code import improve_code
from scripts import render_html


# Configuration
MAX_AUTO_ITERATIONS = 2
PLATEAU_THRESHOLD = 0  # No improvement = plateau
MIN_ACCURACY_TARGET = 85.0  # Stop if we hit target


def copy_images_if_exist(html_path: str, output_dir: str) -> bool:
    """Copy images from input HTML's directory to output directory"""
    html_file = Path(html_path).resolve()
    html_dir = html_file.parent

    input_images_dir = html_dir.parent / 'images'
    if not input_images_dir.exists():
        input_images_dir = html_dir / 'images'

    if not input_images_dir.exists():
        return False

    output_images_dir = Path(output_dir) / 'images'
    if output_images_dir.exists():
        return True

    try:
        shutil.copytree(input_images_dir, output_images_dir)
        return True
    except Exception:
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
    """Calculate accuracy score based on dimensional deviations"""
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


def run_multi_iteration_with_triage(
    html_path: str,
    output_dir: str,
    base_name: str = "improved"
):
    """
    Run multi-iteration improvement with automatic triage

    Args:
        html_path: Path to initial HTML file
        output_dir: Directory to save all results
        base_name: Base name for output files
    """

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print(f"🚀 Multi-Iteration Improvement with Triage")
    print(f"   Input: {html_path}")
    print(f"   Output: {output_dir}")
    print(f"   Max auto iterations: {MAX_AUTO_ITERATIONS}")
    print(f"   Target accuracy: {MIN_ACCURACY_TARGET}%")
    print("=" * 70)

    # Copy images once at the start
    print(f"\n📦 Copying images from input directory...")
    copy_images_if_exist(html_path, output_dir)

    # Track iteration history
    iteration_history = []
    previous_accuracy = 0
    current_html_path = html_path

    # Run automatic iterations
    for iteration in range(1, MAX_AUTO_ITERATIONS + 1):
        print(f"\n{'=' * 70}")
        print(f"📍 ITERATION {iteration}/{MAX_AUTO_ITERATIONS}")
        print(f"{'=' * 70}")

        # Step 1: Measure current state
        print(f"\n📏 Measuring current HTML...")
        measurements = run_dom_measurement(current_html_path)

        found_count = sum(1 for m in measurements.values() if m.get('found'))
        total_count = len(measurements)
        print(f"   Found {found_count}/{total_count} elements")

        # Step 2: Compare to Figma
        print(f"\n🔍 Comparing to Figma design...")
        feedback = compare_measurements(measurements)

        high_priority = len([f for f in feedback if f['priority'] == 'high'])
        medium_priority = len([f for f in feedback if f['priority'] == 'medium'])
        low_priority = len([f for f in feedback if f['priority'] == 'low'])

        current_accuracy = calculate_accuracy_score(feedback)

        print(f"   Total issues: {len(feedback)}")
        print(f"   🔴 High: {high_priority}")
        print(f"   🟡 Medium: {medium_priority}")
        print(f"   🟢 Low: {low_priority}")
        print(f"   Accuracy: {current_accuracy:.1f}%")

        # Save iteration state
        iteration_state = {
            'iteration': iteration,
            'accuracy': current_accuracy,
            'total_issues': len(feedback),
            'feedback': feedback,
            'measurements': measurements
        }
        iteration_history.append(iteration_state)

        # Check for completion
        if len(feedback) == 0:
            print(f"\n✅ SUCCESS! All issues resolved in {iteration} iteration(s)")
            print(f"   Final accuracy: {current_accuracy:.1f}%")
            break

        # Check if we hit target
        if current_accuracy >= MIN_ACCURACY_TARGET:
            print(f"\n✅ TARGET REACHED! Accuracy: {current_accuracy:.1f}%")
            break

        # After completing MAX_AUTO_ITERATIONS, triage any remaining issues
        if iteration >= MAX_AUTO_ITERATIONS and len(feedback) > 0:
            # Calculate improvement (for diagnostic info)
            improvement = current_accuracy - previous_accuracy if iteration > 1 else 0
            plateau_detected = improvement <= PLATEAU_THRESHOLD

            # Report on progress
            if iteration > 1:
                if plateau_detected:
                    print(f"\n⚠️  PLATEAU DETECTED")
                    print(f"   Iteration {iteration - 1}: {previous_accuracy:.1f}%")
                    print(f"   Iteration {iteration}: {current_accuracy:.1f}%")
                    print(f"   Improvement: +{improvement:.1f}%")
                else:
                    print(f"\n✅ PROGRESS MADE")
                    print(f"   Iteration {iteration - 1}: {previous_accuracy:.1f}%")
                    print(f"   Iteration {iteration}: {current_accuracy:.1f}%")
                    print(f"   Improvement: +{improvement:.1f}%")

            print(f"\n   Remaining issues: {len(feedback)}")
            print(f"   Completed {MAX_AUTO_ITERATIONS} automatic iterations")
            print(f"   Triggering designer triage for remaining issues")

            # ALWAYS TRIGGER TRIAGE after 2 loops if issues remain
            print(f"\n{'=' * 70}")
            print(f"🔍 RUNNING ISSUE TRIAGE")
            print(f"{'=' * 70}")

            triage_report = triage_issues(
                feedback,
                iteration_count=iteration,
                iteration_history=iteration_history
            )

            # Display triage report
            print(format_triage_report_for_display(triage_report))

            # Save triage report
            triage_file = os.path.join(output_dir, 'designer_questions.json')
            save_triage_report(triage_report, triage_file)
            print(f"\n💾 Saved designer questions to: {triage_file}")

            # Save formatted report
            formatted_report_file = os.path.join(output_dir, 'designer_questions.txt')
            with open(formatted_report_file, 'w') as f:
                f.write(format_triage_report_for_display(triage_report))
            print(f"💾 Saved formatted report to: {formatted_report_file}")

            print(f"\n{'=' * 70}")
            print(f"⏸️  PAUSED FOR DESIGNER INPUT")
            print(f"{'=' * 70}")
            print(f"\nNext steps:")
            print(f"1. Review designer questions: {formatted_report_file}")
            print(f"2. Provide answers in: {output_dir}/designer_responses.json")
            print(f"3. Run: python scripts/apply_designer_input.py {output_dir}")
            print(f"\nThis will resume improvement with designer guidance.")
            print(f"{'=' * 70}\n")

            # Stop automatic iterations
            break

        # Step 3: Read current code
        print(f"\n📖 Reading code for improvement...")
        with open(current_html_path, 'r') as f:
            original_code = f.read()

        # Step 4: Apply improvements
        print(f"\n🤖 Applying improvements with Claude Sonnet 4.5...")
        print(f"   Feeding {len(feedback)} feedback items...")

        improvement_result = improve_code(
            original_code=original_code,
            feedback=feedback,
            figma_context="Product detail page for J.Crew cashmere cardigan"
        )

        improved_code = improvement_result['improved_code']
        changes_applied = improvement_result.get('changes_applied', [])

        print(f"   ✅ Improvements applied!")
        print(f"   Changes made: {len(changes_applied)}")

        # Step 5: Save improved version
        code_dir = os.path.join(output_dir, 'code')
        os.makedirs(code_dir, exist_ok=True)

        version_name = f"{base_name}_v{iteration}"
        improved_html_path = os.path.join(code_dir, f'{version_name}.html')

        with open(improved_html_path, 'w') as f:
            f.write(improved_code)
        print(f"\n💾 Saved improved code to: {improved_html_path}")

        # Step 6: Render improved version
        print(f"\n🎨 Rendering improved version...")
        screenshot_path = os.path.join(output_dir, f'{version_name}_rendered.png')

        render_html.render_html_to_screenshot(
            html_path=improved_html_path,
            output_path=screenshot_path,
            viewport_width=1440,
            viewport_height=1170
        )

        print(f"   ✅ Rendered to: {screenshot_path}")

        # Prepare for next iteration
        current_html_path = improved_html_path
        previous_accuracy = current_accuracy

    # Save final summary
    summary_file = os.path.join(output_dir, 'iteration_summary.json')
    with open(summary_file, 'w') as f:
        json.dump({
            'iterations_run': len(iteration_history),
            'max_iterations': MAX_AUTO_ITERATIONS,
            'final_accuracy': current_accuracy if iteration_history else 0,
            'target_accuracy': MIN_ACCURACY_TARGET,
            'plateau_detected': len(iteration_history) > 1 and current_accuracy - previous_accuracy <= PLATEAU_THRESHOLD,
            'iteration_history': iteration_history
        }, f, indent=2)

    print(f"\n💾 Saved iteration summary to: {summary_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_multi_iteration_with_triage.py <html_file> [output_dir] [base_name]")
        print("\nExample:")
        print("  python run_multi_iteration_with_triage.py output/code/pdp.html")
        print("  python run_multi_iteration_with_triage.py output/code/pdp.html output/multi-run improved")
        sys.exit(1)

    html_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'output/multi-iteration-run'
    base_name = sys.argv[3] if len(sys.argv) > 3 else 'improved'

    if not os.path.exists(html_path):
        print(f"❌ Error: File not found: {html_path}")
        sys.exit(1)

    try:
        run_multi_iteration_with_triage(html_path, output_dir, base_name)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
