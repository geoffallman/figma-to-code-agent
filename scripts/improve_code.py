#!/usr/bin/env python3
"""
Code Improvement Agent
Uses Claude Sonnet 4.5 to apply feedback and improve HTML/Tailwind code
to better match the Figma design.
"""

import os
import sys
import json
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


def improve_code(original_code: str, feedback: list[dict], figma_context: str = None) -> dict:
    """
    Use Claude Sonnet to apply feedback and improve code.

    Args:
        original_code: Current HTML/CSS code
        feedback: List of improvement suggestions from evaluator
        figma_context: Optional context about the Figma design

    Returns:
        dict with keys:
            - improved_code: The improved HTML/CSS code
            - changes_applied: List of changes made
            - raw_response: Full LLM response
    """

    # Initialize Anthropic client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    client = anthropic.Anthropic(api_key=api_key)

    # Get model config
    improvement_config = config['models']['improvement']
    model = improvement_config['model']
    max_tokens = improvement_config['max_tokens']

    # Build improvement prompt
    improvement_prompt = f"""You are a front-end developer improving HTML/Tailwind CSS code to match a Figma design more accurately.

## Current Code
```html
{original_code}
```

## Evaluation Feedback
You received the following feedback from a visual fidelity evaluation:

"""

    # Add each feedback item
    if feedback:
        for i, item in enumerate(feedback, 1):
            priority = item.get('priority', 'medium').upper()
            category = item.get('category', 'general').title()
            issue = item.get('issue', 'N/A')
            fix = item.get('fix', 'N/A')

            improvement_prompt += f"""### {i}. [{priority}] {category}
**Issue:** {issue}
**Fix:** {fix}

"""
    else:
        improvement_prompt += "No specific feedback provided. Review the code for potential improvements.\n\n"

    if figma_context:
        improvement_prompt += f"""## Figma Design Context
{figma_context}

"""

    improvement_prompt += """## Your Task

Apply ALL feedback items to improve the code. For each fix:
1. Make the exact change suggested
2. Ensure the change doesn't break other parts of the layout
3. Maintain valid HTML structure
4. Use Tailwind CSS utility classes (not custom CSS)
5. Preserve all existing content and functionality

Return ONLY the improved HTML code, no explanations or markdown formatting.
The code should be complete and ready to save as an .html file.
"""

    print(f"\nCalling {model} to improve code...")
    print(f"Applying {len(feedback)} feedback items...")

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.0,  # Deterministic for consistent improvements
            messages=[
                {
                    "role": "user",
                    "content": improvement_prompt
                }
            ],
        )

        # Extract response
        response_text = message.content[0].text

        # Clean up response (remove markdown code blocks if present)
        improved_code = response_text
        if '```html' in improved_code:
            # Extract code from markdown block
            start = improved_code.find('```html') + 7
            end = improved_code.rfind('```')
            improved_code = improved_code[start:end].strip()
        elif '```' in improved_code:
            # Generic code block
            start = improved_code.find('```') + 3
            end = improved_code.rfind('```')
            improved_code = improved_code[start:end].strip()

        print("\n" + "="*60)
        print("CODE IMPROVEMENT COMPLETE")
        print("="*60)
        print(f"Original code length: {len(original_code)} chars")
        print(f"Improved code length: {len(improved_code)} chars")
        print("="*60 + "\n")

        return {
            'improved_code': improved_code,
            'changes_applied': feedback,
            'raw_response': response_text,
            'model_used': model
        }

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return {
            'improved_code': original_code,  # Return original on error
            'changes_applied': [],
            'error': str(e)
        }


def main():
    """Test the code improvement agent"""

    # Check for command line arguments
    if len(sys.argv) < 3:
        print("Usage: python improve_code.py <original_code_file> <feedback_json_file>")
        print("\nExample:")
        print("  python improve_code.py ../output/code/frame1-baseline.html ../output/evaluations/latest_evaluation.json")
        sys.exit(1)

    code_path = sys.argv[1]
    feedback_path = sys.argv[2]

    # Load original code
    if not os.path.exists(code_path):
        print(f"Error: Code file not found: {code_path}")
        sys.exit(1)

    with open(code_path, 'r') as f:
        original_code = f.read()

    # Load feedback
    if not os.path.exists(feedback_path):
        print(f"Error: Feedback file not found: {feedback_path}")
        sys.exit(1)

    with open(feedback_path, 'r') as f:
        evaluation_data = json.load(f)
        feedback = evaluation_data.get('feedback', [])

    print(f"\nLoaded original code: {len(original_code)} chars")
    print(f"Loaded {len(feedback)} feedback items")

    # Run improvement
    result = improve_code(original_code, feedback)

    # Display results
    print("\n" + "="*60)
    print("IMPROVEMENT RESULTS")
    print("="*60)
    print(f"Model used: {result.get('model_used', 'N/A')}")
    print(f"Changes applied: {len(result.get('changes_applied', []))}")

    if result.get('error'):
        print(f"\n⚠️  Error: {result['error']}")
        return

    # Save improved code
    output_dir = Path(__file__).parent.parent / "output" / "code"
    output_dir.mkdir(exist_ok=True, parents=True)

    # Generate version number
    base_name = Path(code_path).stem
    version = 2  # Start with v2 (baseline is v1)
    output_file = output_dir / f"{base_name}-v{version}.html"

    # Find next available version number
    while output_file.exists():
        version += 1
        output_file = output_dir / f"{base_name}-v{version}.html"

    with open(output_file, 'w') as f:
        f.write(result['improved_code'])

    print(f"\n✅ Improved code saved to: {output_file}")

    # Also save the improvement metadata
    metadata_file = output_dir / f"{base_name}-v{version}-metadata.json"
    metadata = {
        'original_file': str(code_path),
        'improved_file': str(output_file),
        'feedback_applied': result.get('changes_applied', []),
        'model_used': result.get('model_used', 'N/A'),
        'version': version
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"📋 Metadata saved to: {metadata_file}")
    print("\n" + "="*60)

    return result


if __name__ == "__main__":
    main()
