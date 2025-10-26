# Evaluation System Improvements

## Problem Identified

The original evaluation system had a critical disconnect between scores and actual visual fidelity:

### Product Page v2 - Original Scoring:
- **Vision LLM**: 95.0% - "Extremely high fidelity... virtually identical"
- **Pixel-Diff**: 71.81% - (28% of pixels different!)
- **User Observation**: Layout is "strikingly different"

The vision LLM was evaluating **semantic similarity** (are elements present?) rather than **pixel-perfect accuracy** (do they match exactly?).

---

## Solutions Implemented

### 1. Improved Vision Evaluation Prompt ✓

**Changes:**
- Explicit instruction to score based on PIXEL-LEVEL accuracy, not semantic similarity
- Added scoring guidelines with specific thresholds
- Emphasized that spacing differences even 5-10px should impact score significantly
- Required EXACT measurements in pixels for all feedback
- Added priority levels based on visual impact (high: >20px differences)

**Location:** `scripts/evaluate_visual.py` lines 65-131

### 2. Weighted Scoring System ✓

**Implementation:**
- Created `scripts/evaluate_combined.py` - new evaluation script
- Combines pixel-diff (60%) + vision LLM (40%)
- Uses pixel-diff as PRIMARY ground truth metric
- Vision LLM provides explanatory feedback on WHY pixels differ

**Weighting:**
```python
final_score = (pixel_similarity * 0.6) + (vision_score * 0.4)
```

### 3. Pixel-Diff as Primary Metric ✓

**Architecture:**
1. **Phase 1**: Run pixel-diff first (ground truth)
2. **Phase 2**: Run vision LLM (explanatory)
3. **Phase 3**: Combine with weighted score
4. **Output**: Clear severity classification

**Severity Levels:**
- 95-100: EXCELLENT - Nearly pixel-perfect 🟢
- 85-94: GOOD - Minor differences 🟡
- 70-84: NEEDS WORK - Noticeable differences 🟠
- <70: POOR - Major differences 🔴

---

## Results Comparison

### Frame1 (Mobile Menu)
| Metric | Score | Notes |
|--------|-------|-------|
| Pixel-Diff | 99.25% | 2,471 / 329,160 pixels different |
| Vision LLM | 100% | "No visible differences" |
| **Final Score** | **99.55%** | EXCELLENT ✓ |

### Product Page v2
| Metric | Old System | New System | Delta |
|--------|-----------|------------|-------|
| Pixel-Diff | N/A (dimension mismatch) | 71.81% | - |
| Vision LLM | 95.0% | 98.5% | +3.5% |
| **Final Score** | **95.0%** | **82.49%** | **-12.51%** |
| Severity | N/A | NEEDS WORK 🟠 | ✓ Accurate! |

**Key Finding:** The new system correctly identifies the product page needs significant work, while the old system gave false confidence with a 95% score.

---

## Usage

### Old Evaluation (Vision LLM only):
```bash
python scripts/evaluate_visual.py \
  output/screenshots/figma.png \
  output/screenshots/rendered.png
```

### New Combined Evaluation (Recommended):
```bash
python scripts/evaluate_combined.py \
  output/screenshots/figma.png \
  output/screenshots/rendered.png \
  output/diffs/diff.png \
  output/code/page.html
```

---

## Next Steps

**Item #4: Fix Dimension Mismatches**

Current issue identified:
- Figma screenshots: 2880x4498 pixels
- Rendered screenshots: 1440x900 pixels (some)
- Rendered screenshots (full): 2880x4498 pixels (some)

Need to ensure rendered screenshots always match Figma dimensions.

**Pending user discussion for implementation approach.**

---

## Files Modified

1. `scripts/evaluate_visual.py` - Enhanced prompt for pixel-perfect evaluation
2. `scripts/evaluate_combined.py` - NEW: Combined weighted evaluation system
3. `EVALUATION_IMPROVEMENTS.md` - THIS FILE: Documentation

## Files Created

- `output/diffs/product-page-v2-combined-diff.png` - Visual diff with pixel-diff overlay
- `output/evaluations/latest_combined_evaluation.json` - Combined evaluation results
