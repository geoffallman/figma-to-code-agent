#!/usr/bin/env python3
"""
Metadata-Enhanced Evaluation

Provides vision LLM with exact Figma dimensions to verify against rendered output.
This should produce more accurate, measurement-based feedback.
"""

import os
import sys
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import yaml

load_dotenv()


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, 'rb') as f:
        return base64.standard_b64encode(f.read()).decode('utf-8')


def extract_key_elements_from_metadata(metadata: dict) -> list:
    """Extract important elements with dimensions from Figma metadata"""

    elements = []

    def traverse(node, parent_name=""):
        if not isinstance(node, dict):
            return

        node_type = node.get('type', '')
        node_name = node.get('name', 'Unnamed')
        bounds = node.get('absoluteBoundingBox')

        # Extract key elements
        if bounds and node_type in ['FRAME', 'RECTANGLE', 'TEXT', 'INSTANCE']:
            elements.append({
                'name': f"{parent_name}/{node_name}" if parent_name else node_name,
                'type': node_type,
                'bounds': bounds,
                'width': bounds.get('width'),
                'height': bounds.get('height'),
                'x': bounds.get('x'),
                'y': bounds.get('y')
            })

        # Recurse
        for child in node.get('children', []):
            traverse(child, node_name)

    traverse(metadata)
    return elements


def evaluate_with_metadata(
    figma_screenshot_path: str,
    rendered_screenshot_path: str,
    metadata_path: str
) -> dict:
    """
    Evaluate using vision LLM WITH Figma metadata for precise measurements
    """

    print("=" * 70)
    print("METADATA-ENHANCED EVALUATION")
    print("=" * 70)
    print()

    # Load metadata
    print("[1/4] Loading Figma metadata...")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    elements = extract_key_elements_from_metadata(metadata)
    print(f"  ✓ Extracted {len(elements)} elements with dimensions")
    print()

    # Load screenshots
    print("[2/4] Loading screenshots...")
    figma_b64 = encode_image_to_base64(figma_screenshot_path)
    rendered_b64 = encode_image_to_base64(rendered_screenshot_path)
    print(f"  ✓ Figma: {Path(figma_screenshot_path).name}")
    print(f"  ✓ Rendered: {Path(rendered_screenshot_path).name}")
    print()

    # Build element specifications
    specs = []
    for elem in elements[:15]:  # Top 15 most important elements
        spec = f"""
Element: {elem['name']}
- Type: {elem['type']}
- Expected Width: {elem['width']:.0f}px
- Expected Height: {elem['height']:.0f}px
- Expected Position: ({elem['x']:.0f}px, {elem['y']:.0f}px)
- Aspect Ratio: {(elem['width']/elem['height']):.2f}
"""
        specs.append(spec)

    specifications_text = "\n".join(specs)

    # Build enhanced prompt
    prompt = f"""You are evaluating pixel-perfect visual fidelity between a Figma design and rendered HTML.

**CRITICAL: You have access to EXACT MEASUREMENTS from the Figma design.**

## FIGMA DESIGN SPECIFICATIONS (Ground Truth)

{specifications_text}

## YOUR TASK

Compare the two screenshots:
1. IMAGE 1 (FIRST): Original Figma design (ground truth)
2. IMAGE 2 (SECOND): Rendered HTML output (candidate)

For each element listed above:
1. **MEASURE the dimensions** in the rendered screenshot
2. **CALCULATE the deviation** from expected dimensions
3. **REPORT specific measurements** (e.g., "Image is 400px wide, should be 576px - 31% too narrow")

## SCORING GUIDELINES

- **Dimension deviation > 20%**: HIGH priority issue, score impact: -10 points
- **Dimension deviation 10-20%**: MEDIUM priority, score impact: -5 points
- **Dimension deviation 5-10%**: LOW priority, score impact: -2 points
- **Dimension deviation < 5%**: Acceptable tolerance

Your score MUST reflect dimensional accuracy. If elements are 20%+ wrong, score should be ≤ 80.

Return JSON:
```json
{{
  "semantic_score": 75.0,
  "overall_assessment": "Focus on MEASUREMENTS and DEVIATIONS, not just presence of elements",
  "feedback": [
    {{
      "category": "sizing",
      "element": "Left Product Image",
      "issue": "Image is 400px wide, should be 576px",
      "measurement": "176px too narrow (31% deviation)",
      "expected": "576px × 720px",
      "actual": "400px × 500px",
      "fix": "Adjust image container width from w-1/3 to w-[576px]",
      "priority": "high"
    }}
  ],
  "strengths": ["Typography dimensions match", "Color swatches are correct size"]
}}
```

**IMPORTANT**: Measure dimensions precisely. Report deviations as percentages. Be critical - if it's not within 5%, flag it.
"""

    # Call vision LLM
    print("[3/4] Calling vision LLM with metadata context...")

    config = load_config()
    model = config['models']['evaluation']['model']

    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0.0,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": figma_b64}},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": rendered_b64}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        response_text = message.content[0].text
        print("  ✓ Vision LLM response received")
        print()
        print("=" * 70)
        print("RAW RESPONSE:")
        print("=" * 70)
        print(response_text[:500])
        print("=" * 70)
        print()

        # Extract JSON
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.rfind('```')
            json_text = response_text[start:end].strip()
        elif '```' in response_text:
            start = response_text.find('```') + 3
            end = response_text.rfind('```')
            json_text = response_text[start:end].strip()
        else:
            json_text = response_text

        result = json.loads(json_text)

        print("[4/4] Evaluation complete")
        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"\nScore: {result.get('semantic_score')}/100")
        print(f"Assessment: {result.get('overall_assessment')}")
        print(f"\nFeedback items: {len(result.get('feedback', []))}")

        for item in result.get('feedback', []):
            print(f"\n[{item.get('priority', 'unknown').upper()}] {item.get('element', 'Unknown')}")
            print(f"  Issue: {item.get('issue')}")
            print(f"  Expected: {item.get('expected', 'N/A')}")
            print(f"  Actual: {item.get('actual', 'N/A')}")
            print(f"  Deviation: {item.get('measurement')}")

        print()
        return {
            'success': True,
            'score': result.get('semantic_score'),
            'feedback': result.get('feedback', []),
            'assessment': result.get('overall_assessment'),
            'raw_response': response_text
        }

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {'success': False, 'error': str(e)}


def main():
    if len(sys.argv) < 4:
        print("Usage: python evaluate_with_metadata.py <figma_screenshot> <rendered_screenshot> <metadata_json>")
        print()
        print("Example:")
        print("  python scripts/evaluate_with_metadata.py \\")
        print("    output/screenshots/pdp-trimmed-figma.png \\")
        print("    output/test-runs/.../screenshots/rendered.png \\")
        print("    output/pdp-trimmed-metadata.json")
        sys.exit(1)

    figma_path = sys.argv[1]
    rendered_path = sys.argv[2]
    metadata_path = sys.argv[3]

    result = evaluate_with_metadata(figma_path, rendered_path, metadata_path)

    if not result.get('success'):
        print(f"\n✗ Evaluation failed: {result.get('error')}")
        sys.exit(1)

    # Save result
    output_dir = Path("output/evaluations")
    output_dir.mkdir(exist_ok=True, parents=True)
    output_file = output_dir / "metadata_enhanced_evaluation.json"

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Results saved: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
