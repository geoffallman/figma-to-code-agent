#!/usr/bin/env python3
"""
Vision LLM Evaluation Script
Uses Claude's vision capabilities to compare Figma design vs rendered HTML
and generate actionable feedback for improvement.
"""

import os
import sys
import json
import base64
import yaml
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

# Load configuration
def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64 string"""
    with open(image_path, 'rb') as image_file:
        return base64.standard_b64encode(image_file.read()).decode('utf-8')

def evaluate_visual_fidelity(figma_screenshot_path: str, rendered_screenshot_path: str, code: str = None) -> dict:
    """
    Use Claude vision to evaluate visual fidelity between Figma design and rendered HTML.

    Args:
        figma_screenshot_path: Path to Figma screenshot (ground truth)
        rendered_screenshot_path: Path to rendered HTML screenshot (candidate)
        code: Optional HTML/CSS code for context

    Returns:
        dict with keys:
            - semantic_score: 0-100 score from vision LLM
            - feedback: List of specific improvement suggestions
            - raw_response: Full LLM response
    """

    # Initialize Anthropic client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Anthropic(api_key=api_key)

    # Encode both images
    print(f"Loading Figma screenshot: {figma_screenshot_path}")
    figma_b64 = encode_image_to_base64(figma_screenshot_path)

    print(f"Loading rendered screenshot: {rendered_screenshot_path}")
    rendered_b64 = encode_image_to_base64(rendered_screenshot_path)

    # Construct evaluation prompt
    evaluation_prompt = """You are evaluating visual fidelity between a Figma design and rendered HTML output.

Compare these two screenshots:
1. IMAGE 1: Original Figma design (ground truth)
2. IMAGE 2: Rendered HTML output (candidate)

Evaluate visual fidelity across these dimensions:
- **Layout & Spacing**: Margins, padding, gaps, alignment, component positioning
- **Typography**: Font family, size, weight, line-height, letter-spacing, text case
- **Colors**: Exact color matches (background, text, borders)
- **Visual Elements**: Icons, borders, dividers, shadows, backgrounds
- **Component Sizing**: Width, height, aspect ratios

For each discrepancy you find:
1. Identify the specific issue with precise measurements
2. Categorize it (spacing/typography/colors/layout/elements)
3. Provide exact code fix suggestion
4. Assign priority (high/medium/low)

Return your evaluation in this JSON format:
```json
{
  "semantic_score": 75.0,
  "overall_assessment": "Brief summary of how well the rendered output matches the design",
  "feedback": [
    {
      "category": "spacing",
      "issue": "Gap between menu sections is 24px, should be 18px",
      "measurement": "6px difference",
      "fix": "Change gap-6 to gap-[18px] on the nav element",
      "priority": "high"
    },
    {
      "category": "typography",
      "issue": "Font weight appears too bold",
      "measurement": "Using font-normal (400) instead of font-light (300)",
      "fix": "Change font-normal to font-light (300)",
      "priority": "medium"
    }
  ],
  "strengths": [
    "All content is present and in correct order",
    "Overall structure matches the design"
  ]
}
```

Be specific and actionable. Provide measurements where possible. Focus on visual differences that impact fidelity."""

    if code:
        evaluation_prompt += f"\n\nFor context, here is the current HTML/CSS code:\n```html\n{code[:2000]}...\n```"

    # Get model config
    eval_config = config['models']['evaluation']
    model = eval_config['model']
    max_tokens = eval_config['max_tokens']

    print(f"\nCalling {model} with vision...")

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": figma_b64,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": rendered_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": evaluation_prompt
                        }
                    ],
                }
            ],
        )

        # Extract response
        response_text = message.content[0].text
        print("\n" + "="*60)
        print("CLAUDE VISION EVALUATION")
        print("="*60)
        print(response_text)
        print("="*60 + "\n")

        # Parse JSON from response
        # Look for JSON block in response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            # If no JSON found, create a structured response from the text
            return {
                'semantic_score': 0,
                'feedback': [],
                'raw_response': response_text,
                'error': 'Could not parse JSON from response'
            }

        json_str = response_text[json_start:json_end]
        evaluation_data = json.loads(json_str)

        # Add raw response
        evaluation_data['raw_response'] = response_text

        return evaluation_data

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return {
            'semantic_score': 0,
            'feedback': [],
            'error': str(e)
        }


def main():
    """Test the vision evaluation"""

    # Check for command line arguments
    if len(sys.argv) < 3:
        print("Usage: python evaluate_visual.py <figma_screenshot> <rendered_screenshot> [code_file]")
        print("\nExample:")
        print("  python evaluate_visual.py ../output/screenshots/figma.png ../output/screenshots/rendered.png")
        sys.exit(1)

    figma_path = sys.argv[1]
    rendered_path = sys.argv[2]
    code = None

    # Load code file if provided
    if len(sys.argv) > 3:
        code_path = sys.argv[3]
        with open(code_path, 'r') as f:
            code = f.read()

    # Validate paths
    if not os.path.exists(figma_path):
        print(f"Error: Figma screenshot not found: {figma_path}")
        sys.exit(1)

    if not os.path.exists(rendered_path):
        print(f"Error: Rendered screenshot not found: {rendered_path}")
        sys.exit(1)

    # Run evaluation
    result = evaluate_visual_fidelity(figma_path, rendered_path, code)

    # Display results
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Semantic Score: {result.get('semantic_score', 'N/A')}/100")
    print(f"\nOverall Assessment:")
    print(f"  {result.get('overall_assessment', 'N/A')}")

    feedback = result.get('feedback', [])
    if feedback:
        print(f"\nFeedback ({len(feedback)} issues):")
        for i, item in enumerate(feedback, 1):
            print(f"\n  {i}. [{item.get('priority', '?').upper()}] {item.get('category', '?').title()}")
            print(f"     Issue: {item.get('issue', 'N/A')}")
            print(f"     Fix: {item.get('fix', 'N/A')}")

    strengths = result.get('strengths', [])
    if strengths:
        print(f"\nStrengths:")
        for strength in strengths:
            print(f"  ✓ {strength}")

    print("\n" + "="*60)

    # Save results to JSON file
    output_dir = Path(__file__).parent.parent / "output" / "evaluations"
    output_dir.mkdir(exist_ok=True, parents=True)

    output_file = output_dir / "latest_evaluation.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return result


if __name__ == "__main__":
    main()
