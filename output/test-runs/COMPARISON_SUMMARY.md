# Test Runs Comparison Summary

**Design:** PDP Trimmed (1440×1170)
**Date:** 2025-10-24
**Baseline Model:** claude-sonnet-4-20250514
**Evaluation Model:** claude-3-5-haiku-20241022

---

## Score Progression

| Run | Description | Pixel-Diff | Vision LLM | **Final Score** | Improvement |
|-----|-------------|-----------|-----------|----------------|-------------|
| **Run 1** | Baseline (no images) | 47.56% | 98.5% | **67.94%** | - |
| **Run 2** | With images loaded | 66.43% | 98.5% | **79.26%** | **+11.32** 🎯 |
| **Run 3** | After improvement | 66.43% | 100% | **79.86%** | **+0.60** |

---

## Key Insights

### Run 1 → Run 2: Images Make Huge Difference (+11.32 pts)

**The Problem:** Run 1 had broken image links
- Placeholder paths: `../images/model-close-up.png`, etc.
- Images showed as gray boxes with alt text
- ~60% of viewport was placeholder instead of actual photos

**The Fix:** Extracted real images from Figma (nodes 157:745, 157:746, 157:747)

**Impact:**
- Pixel-Diff: **47.56% → 66.43%** (+18.87 pts!)
- Final Score: **67.94% → 79.26%** (+11.32 pts)
- Status: POOR → NEEDS WORK (approaching GOOD threshold of 85%)

### Run 2 → Run 3: Minimal Improvement (+0.60 pts)

**The Problem:** Vision LLM only flagged 1 low-priority issue:
- "Color selector strip has slight tonal variation"

**The Fix:** Improvement agent applied 1 change (code: 8651 → 8768 chars)

**Impact:**
- Pixel-Diff: **66.43% → 66.43%** (unchanged!)
- Vision LLM: **98.5% → 100%** (+1.5 pts)
- Final Score: **79.26% → 79.86%** (+0.60 pts)

**Analysis:** The improvement was cosmetic and didn't address the real 33.57% pixel difference. Vision LLM now says "pixel-perfect" despite 1/3 of pixels being different.

---

## Vision LLM Reliability Issue

### The Problem:
Vision LLM consistently over-estimates quality:

| Run | Pixel-Diff | Vision Says | Reality |
|-----|-----------|-------------|---------|
| Run 1 | 47.56% | "98.5% - extremely high fidelity" | Half the pixels wrong! |
| Run 2 | 66.43% | "98.5% - extremely high fidelity" | 1/3 pixels wrong |
| Run 3 | 66.43% | "100% - pixel-perfect" | 1/3 pixels wrong |

### Why Weighted Scoring Matters:
- Pure vision score: Would give 100% ❌
- Pure pixel-diff: Would give 66.43% ✓
- **Weighted (60/40):** Gives 79.86% - **realistic assessment** ✓

The weighted system correctly identifies this as "NEEDS WORK" not "EXCELLENT".

---

## Current Status

**Score:** 79.86% / 100
**Status:** 🟠 NEEDS WORK - Noticeable differences
**Gap to GOOD (85%):** 5.14 points
**Gap to EXCELLENT (95%):** 15.14 points

### What's Actually Different? (33.57% pixel diff)

Based on pixel-diff, likely issues:
1. **Image proportions** - Layout may be using equal-width grid vs. varied sizes
2. **Spacing/padding** - Gaps between elements not matching exactly
3. **Typography** - Font sizes, weights, or line-heights slightly off
4. **Colors** - Subtle color differences in backgrounds, text, or swatches
5. **Layout structure** - Overall proportions not matching design exactly

---

## Test Run Archiving System

All test runs preserved in timestamped directories:

```
output/test-runs/
├── 2025-10-24_16-54-04_pdp-trimmed-baseline-run1/
│   ├── code/
│   ├── screenshots/
│   ├── diffs/
│   ├── evaluations/
│   └── README.md
├── 2025-10-24_16-56-20_pdp-trimmed-with-images-run2/
│   ├── code/
│   ├── screenshots/
│   ├── diffs/
│   ├── evaluations/
│   └── images/ (3 extracted Figma images)
└── 2025-10-24_17-11-06_pdp-trimmed-improved-run3/
    ├── code/
    ├── screenshots/
    ├── diffs/
    ├── evaluations/
    └── images/
```

**Benefits:**
- No overwriting of previous results ✓
- Easy to compare iterations ✓
- Full audit trail ✓
- Can roll back if needed ✓

---

## Recommendations

### To Reach 85% (GOOD):
1. **Analyze the diff images** to identify specific layout/styling issues
2. **Provide more specific feedback** to the improvement agent
3. **Consider manual tweaks** for layout proportions
4. **Extract exact spacing/sizing** from Figma metadata

### To Improve the Process:
1. **Vision LLM feedback is insufficient** - it's too optimistic
2. **Need better feedback loop** - analyze pixel-diff to generate specific fixes
3. **Consider multi-iteration improvement** - run 3-5 iterations with targeted feedback

### System Improvements:
1. ✅ Viewport matching - Working perfectly
2. ✅ Test run archiving - Solid system in place
3. ⚠️ Improvement agent - Needs better feedback to work with
4. ⚠️ Vision LLM evaluation - Too optimistic, needs recalibration

---

**Last Updated:** 2025-10-24 17:11
