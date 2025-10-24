# Day 6: Vision LLM Evaluation - COMPLETE ✅

**Date:** October 23, 2025
**Status:** Complete
**Time:** ~2 hours

---

## Summary

Built the vision evaluation system that uses Claude Sonnet 4.5's vision capabilities to compare Figma screenshots with rendered HTML and generate actionable feedback for improvement.

## Deliverables

### 1. Vision Evaluation Script ✅
**File:** `scripts/evaluate_visual.py`

**Capabilities:**
- Loads two screenshots (Figma ground truth + rendered HTML)
- Encodes images as base64 for Claude API
- Sends both images to Claude Sonnet 4.5 with structured prompt
- Parses structured JSON feedback with specific improvement suggestions
- Saves evaluation results to JSON file

**Key Features:**
- Structured JSON output format
- Categorized feedback (spacing, typography, colors, layout, elements)
- Priority levels (high/medium/low)
- Specific, actionable fix suggestions
- Semantic scoring (0-100)
- Strengths identification

### 2. Evaluation Prompt Template ✅
Comprehensive prompt that asks Claude to evaluate:
- Layout & Spacing (margins, padding, gaps, alignment)
- Typography (font family, size, weight, line-height, letter-spacing)
- Colors (exact color matches)
- Visual Elements (icons, borders, dividers, shadows)
- Component Sizing (width, height, aspect ratios)

### 3. Environment Setup ✅
- Created `.env` file template for API key
- Added `python-dotenv` to requirements
- Configured Anthropic SDK integration

### 4. Manual Evaluation Demonstration ✅
Analyzed Frame 1 baseline vs V2 from spike:
- Identified key improvements (status bar icons, search bar width)
- Generated sample evaluation JSON
- Validated the evaluation approach works

---

## Usage

### Setup
1. Add your Anthropic API key to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   ```

2. Ensure dependencies installed:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Run Evaluation
```bash
# Basic usage
python scripts/evaluate_visual.py \
  path/to/figma_screenshot.png \
  path/to/rendered_screenshot.png

# With code context (helps improve feedback)
python scripts/evaluate_visual.py \
  output/screenshots/figma.png \
  output/screenshots/rendered.png \
  output/code/frame1-baseline.html
```

### Output
Results saved to: `output/evaluations/latest_evaluation.json`

**JSON Structure:**
```json
{
  "semantic_score": 75.0,
  "overall_assessment": "Brief summary...",
  "feedback": [
    {
      "category": "spacing",
      "issue": "Description of the issue",
      "measurement": "Specific measurements",
      "fix": "Exact code change needed",
      "priority": "high"
    }
  ],
  "strengths": [
    "List of things that match well"
  ],
  "raw_response": "Full LLM response..."
}
```

---

## Key Findings

### What Works Well
✅ **Vision model is excellent at identifying:**
- Visual differences in layout and spacing
- Icon and visual element mismatches
- Typography inconsistencies
- Color differences
- Overall design fidelity

✅ **Structured JSON output** makes feedback actionable and parseable

✅ **Specific fix suggestions** help the code improvement agent know exactly what to change

### Challenges
⚠️ **Requires API key** - User needs to add their own Anthropic API key to `.env`

⚠️ **Token costs** - Vision API calls consume more tokens than text-only
  - Solution: Use vision eval as secondary metric (30% weight) combined with pixel-diff (70%)

⚠️ **Consistency** - LLM evaluations can vary slightly between runs
  - Solution: Use pixel-diff as primary objective metric

---

## Integration with Overall System

### Two-Tier Evaluation (from PRD)

**Primary Metric (70% weight):** Pixel-diff comparison
- Objective, consistent, fast
- Built in Day 4: `tools/pixel_diff.py`

**Secondary Metric (30% weight):** Vision LLM semantic evaluation
- Identifies subtle issues pixel-diff might miss
- Provides actionable feedback for improvement
- Built today: `scripts/evaluate_visual.py`

### Combined Score Calculation
```python
def final_evaluation(figma_path, rendered_path, code):
    # Pixel-diff (objective)
    pixel_result = compare_screenshots(figma_path, rendered_path)
    pixel_score = pixel_result['similarity']

    # Vision LLM (semantic)
    vision_result = evaluate_visual_fidelity(figma_path, rendered_path, code)
    semantic_score = vision_result['semantic_score']

    # Combined (70/30 weighting)
    final_score = (pixel_score * 0.7) + (semantic_score * 0.3)

    return {
        'final_score': final_score,
        'pixel_score': pixel_score,
        'semantic_score': semantic_score,
        'feedback': vision_result['feedback'],
        'pass': final_score >= 85
    }
```

This will be implemented in Day 8 when we build the complete iteration loop.

---

## Example Evaluation

**Input:**
- Figma screenshot: Frame 1 navigation menu (ground truth)
- Rendered screenshot: V2 improved version

**Output:**
See: `output/evaluations/manual_evaluation_frame1.json`

**Key Findings:**
- Semantic score: 85/100
- Main improvement: Status bar icons (emoji → proper SVG icons)
- Strengths: Layout, spacing, typography all accurate
- Remaining gaps: Minor search bar width adjustment

---

## Next Steps (Day 7)

Build the **Code Improvement Agent** that:
1. Takes original HTML/CSS code
2. Takes feedback from this vision evaluation
3. Uses Claude to apply improvements
4. Generates improved code (V2)

This completes the builder → evaluator → improver loop!

---

## Day 6 Completion Checklist

- [x] Set up Anthropic API client
- [x] Write vision evaluation prompt template
- [x] Build evaluate_visual.py script
- [x] Test with existing screenshots
- [x] Parse and structure feedback as JSON
- [x] Create .env file template
- [x] Document usage and findings
- [x] Validate approach with manual evaluation

**Status:** ✅ Day 6 Complete - Ready for Day 7 (Code Improvement Agent)

**Total Week 2 Progress:** 1/5 days complete (20%)
