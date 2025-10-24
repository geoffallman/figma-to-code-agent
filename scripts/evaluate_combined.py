#!/usr/bin/env python3
"""
Enhanced Evaluation Script - Combines Pixel-Diff + Vision LLM

This script uses a two-phase approach:
1. Pixel-Diff (PRIMARY): Ground truth similarity score
2. Vision LLM (SECONDARY): Explains WHY pixels differ and provides actionable feedback

Final score is weighted: pixel_diff (60%) + vision_llm (40%)
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
sys.path.insert(0, str(Path(__file__).parent))

from pixel_diff import compare_screenshots
from evaluate_visual import evaluate_visual_fidelity

# Load environment variables
load_dotenv()


def evaluate_with_combined_metrics(
    figma_screenshot_path: str,
    rendered_screenshot_path: str,
    diff_output_path: str = None,
    code_path: str = None,
    pixel_weight: float = 0.6,
    vision_weight: float = 0.4
) -> dict:
    """
    Run combined evaluation using pixel-diff + vision LLM.

    Args:
        figma_screenshot_path: Path to Figma screenshot (ground truth)
        rendered_screenshot_path: Path to rendered HTML screenshot
        diff_output_path: Optional path to save diff visualization
        code_path: Optional path to HTML/CSS code for context
        pixel_weight: Weight for pixel-diff score (default 0.6)
        vision_weight: Weight for vision LLM score (default 0.4)

    Returns:
        dict with combined evaluation results
    """

    print("\n" + "=" * 70)
    print("ENHANCED EVALUATION: Pixel-Diff + Vision LLM")
    print("=" * 70)
    print()

    # Phase 1: Pixel-Diff (Ground Truth)
    print("[1/2] Running Pixel-Diff Analysis...")
    print("-" * 70)

    pixel_result = compare_screenshots(
        figma_screenshot_path,
        rendered_screenshot_path,
        diff_output_path
    )

    if not pixel_result.get('success'):
        print(f"✗ Pixel-diff failed: {pixel_result.get('error')}")
        return {
            'success': False,
            'error': f"Pixel-diff failed: {pixel_result.get('error')}"
        }

    pixel_similarity = pixel_result['similarity']
    diff_pixels = pixel_result['diffPixels']
    total_pixels = pixel_result['totalPixels']

    print(f"  Similarity: {pixel_similarity}%")
    print(f"  Different pixels: {diff_pixels:,} / {total_pixels:,}")
    print(f"  Image size: {pixel_result['width']}x{pixel_result['height']}")
    if diff_output_path:
        print(f"  Diff saved to: {Path(diff_output_path).name}")
    print()

    # Phase 2: Vision LLM (Explanatory)
    print("[2/2] Running Vision LLM Analysis...")
    print("-" * 70)

    # Load code if provided
    code = None
    if code_path and Path(code_path).exists():
        with open(code_path, 'r') as f:
            code = f.read()

    vision_result = evaluate_visual_fidelity(
        figma_screenshot_path,
        rendered_screenshot_path,
        code
    )

    if vision_result.get('error'):
        print(f"✗ Vision LLM failed: {vision_result.get('error')}")
        # Continue with pixel-diff only
        vision_score = pixel_similarity  # Fallback to pixel score
        vision_feedback = []
    else:
        vision_score = vision_result.get('semantic_score', 0)
        vision_feedback = vision_result.get('feedback', [])
        print(f"  Vision Score: {vision_score}/100")
        print(f"  Feedback items: {len(vision_feedback)}")
        print()

    # Phase 3: Combine Scores
    print("=" * 70)
    print("COMBINED RESULTS")
    print("=" * 70)
    print()

    # Weighted final score
    final_score = (pixel_similarity * pixel_weight) + (vision_score * vision_weight)

    print(f"Pixel-Diff Score:    {pixel_similarity:.2f}/100  (weight: {pixel_weight*100:.0f}%)")
    print(f"Vision LLM Score:    {vision_score:.2f}/100  (weight: {vision_weight*100:.0f}%)")
    print(f"─" * 70)
    print(f"FINAL SCORE:         {final_score:.2f}/100")
    print()

    # Determine severity based on final score
    if final_score >= 95:
        severity = "EXCELLENT - Nearly pixel-perfect"
        color = "🟢"
    elif final_score >= 85:
        severity = "GOOD - Minor differences"
        color = "🟡"
    elif final_score >= 70:
        severity = "NEEDS WORK - Noticeable differences"
        color = "🟠"
    else:
        severity = "POOR - Major differences"
        color = "🔴"

    print(f"{color} {severity}")
    print()

    # Display feedback from vision LLM
    if vision_feedback:
        print("Feedback from Vision LLM:")
        print("-" * 70)
        for i, item in enumerate(vision_feedback, 1):
            priority = item.get('priority', 'unknown').upper()
            category = item.get('category', 'unknown').title()
            issue = item.get('issue', 'N/A')
            measurement = item.get('measurement', 'N/A')
            fix = item.get('fix', 'N/A')

            print(f"\n{i}. [{priority}] {category}")
            print(f"   Issue: {issue}")
            print(f"   Measurement: {measurement}")
            print(f"   Fix: {fix}")
        print()

    # Build comprehensive result
    result = {
        'success': True,
        'final_score': round(final_score, 2),
        'pixel_diff': {
            'similarity': pixel_similarity,
            'diff_pixels': diff_pixels,
            'total_pixels': total_pixels,
            'weight': pixel_weight,
            'diff_image': diff_output_path
        },
        'vision_llm': {
            'score': vision_score,
            'weight': vision_weight,
            'feedback': vision_feedback,
            'overall_assessment': vision_result.get('overall_assessment', ''),
            'strengths': vision_result.get('strengths', [])
        },
        'severity': severity,
        'methodology': 'combined_weighted',
        'weights': {
            'pixel_diff': pixel_weight,
            'vision_llm': vision_weight
        }
    }

    return result


def main():
    """Run combined evaluation from command line"""

    if len(sys.argv) < 3:
        print("Usage: python evaluate_combined.py <figma_screenshot> <rendered_screenshot> [diff_output] [code_file]")
        print("\nExample:")
        print("  python evaluate_combined.py \\")
        print("    output/screenshots/figma.png \\")
        print("    output/screenshots/rendered.png \\")
        print("    output/diffs/diff.png \\")
        print("    output/code/page.html")
        sys.exit(1)

    figma_path = sys.argv[1]
    rendered_path = sys.argv[2]
    diff_output = sys.argv[3] if len(sys.argv) > 3 else None
    code_path = sys.argv[4] if len(sys.argv) > 4 else None

    # Validate paths
    if not os.path.exists(figma_path):
        print(f"Error: Figma screenshot not found: {figma_path}")
        sys.exit(1)

    if not os.path.exists(rendered_path):
        print(f"Error: Rendered screenshot not found: {rendered_path}")
        sys.exit(1)

    # Run combined evaluation
    result = evaluate_with_combined_metrics(
        figma_path,
        rendered_path,
        diff_output,
        code_path
    )

    if not result.get('success'):
        print(f"\n✗ Evaluation failed: {result.get('error')}")
        sys.exit(1)

    # Save results to JSON
    output_dir = Path(__file__).parent.parent / "output" / "evaluations"
    output_dir.mkdir(exist_ok=True, parents=True)

    output_file = output_dir / "latest_combined_evaluation.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print("=" * 70)
    print(f"Results saved to: {output_file}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
