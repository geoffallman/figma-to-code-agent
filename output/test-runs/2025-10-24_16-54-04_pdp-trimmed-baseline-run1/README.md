# Test Run: PDP Trimmed Baseline - Run 1

**Created:** 2025-10-24 16:54:04
**Status:** Completed - Archived

## Summary

First baseline code generation from the new trimmed Figma frame (157-738).

### Results

| Metric | Score | Assessment |
|--------|-------|------------|
| **Pixel-Diff** | **47.56%** | 🔴 Half the pixels match |
| Vision LLM | 98.5% | Overly optimistic |
| **Combined** | **67.94%** | 🔴 POOR - Major differences |

### Key Findings

1. **Layout is much closer** than previous attempts
   - No breadcrumb nav (correct - wasn't in trimmed design)
   - Product details layout matches design structure
   - Color swatches, pricing, buttons in correct positions

2. **Missing Images** (Major Issue)
   - Code references placeholder image paths:
     - `../images/model-close-up.png`
     - `../images/model-full-body.png`
     - `../images/cardigan-detail.png`
   - These files don't exist
   - Images failing to load significantly impacts pixel-diff score
   - Broken images show as gray boxes with alt text

3. **Vision LLM Still Too Optimistic**
   - Says "pixel-perfect" when 52% of pixels differ
   - Weighted scoring (60% pixel / 40% vision) correctly classifies as POOR

## Files

```
code/
  └── pdp-trimmed-baseline.html (8,650 chars)

screenshots/
  └── pdp-trimmed-baseline-rendered.png

diffs/
  └── pdp-trimmed-baseline-diff.png

evaluations/
  └── latest_combined_evaluation.json
```

## Next Steps

1. **Extract actual images from Figma** (node IDs from metadata)
2. **Update image paths** in HTML to point to real images
3. **Re-render and re-evaluate** with images loaded
4. **Expected improvement:** Pixel-diff should jump significantly (maybe 47% → 70%+)

## Technical Notes

- **Viewport Matching:** ✅ Working perfectly (1440×1170 → 2880×2340 at 2×)
- **Code Generation Model:** claude-sonnet-4-20250514
- **Evaluation Model:** claude-3-5-haiku-20241022
- **Fresh Context:** ✅ No contamination from previous tests
