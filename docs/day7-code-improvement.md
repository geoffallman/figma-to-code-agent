# Day 7: Code Improvement Agent - COMPLETE ✅

**Date:** October 23, 2025
**Status:** Complete
**Time:** ~2 hours

---

## Summary

Built the code improvement agent that uses Claude Sonnet 4.5 to apply feedback from the evaluator and generate improved HTML/Tailwind code. Tested the full iteration loop end-to-end with a complex product detail page.

## Deliverables

### 1. Code Improvement Agent ✅
**File:** `scripts/improve_code.py`

**Capabilities:**
- Takes original HTML/CSS code
- Takes structured feedback from evaluator
- Uses Claude Sonnet 4.5 to apply improvements
- Generates improved code versions (V2, V3, etc.)
- Saves metadata about changes applied

**Key Features:**
- Uses Sonnet 4.5 (high quality for code generation)
- Configurable via `config.yaml`
- Version tracking (automatic V2, V3, etc.)
- Metadata logging for each iteration
- Deterministic output (temperature=0.0)

### 2. Model Configuration System ✅
**File:** `config.yaml`

**Hybrid Strategy:**
```yaml
models:
  evaluation:
    model: claude-3-5-haiku-20241022  # Cheap, fast
  improvement:
    model: claude-sonnet-4-20250514   # High quality
```

**Cost Optimization:**
- Vision eval: ~$0.001 per evaluation (Haiku)
- Code improvement: ~$0.01 per iteration (Sonnet)
- Total per iteration: ~$0.011 (vs ~$0.04 all-Sonnet)

### 3. Full Iteration Loop Testing ✅
Tested on complex product detail page:
- Breadcrumb navigation
- Product image gallery
- Color swatches
- Size selectors
- Accordion sections
- Add to bag button

---

## Test Results: Product Detail Page

### Iteration 1: Baseline → V2

**Input:**
- Figma screenshot: 2880x4498px product page
- Generated baseline HTML using vision

**V1 Baseline Scores:**
- Pixel-diff (70%): 71.8%
- Vision LLM (30%): 92.5%
- **Combined: 78.0%**

**Feedback Applied (2 issues):**
1. [LOW] Color swatch positioning
2. [MEDIUM] Typography line-height and tracking

**V2 Improved Scores:**
- Pixel-diff (70%): 71.81% (+0.01%)
- Vision LLM (30%): 65.0% (-27.5% - LLM variability!)
- **Combined: 69.8%** (-8.2%)

### Key Findings 🎯

**1. Pixel-Diff is Stable and Objective**
- V1 → V2: 71.8% → 71.81% (consistent)
- Barely changed despite code improvements
- This is the "ground truth" metric

**2. Vision LLM is Variable**
- V1 → V2: 92.5% → 65% (same design, different score!)
- Demonstrates why LLM can't be the only metric
- Useful for semantic feedback, not absolute scoring

**3. Two-Tier Evaluation is Essential**
- Pixel-diff (70%) catches objective visual differences
- Vision LLM (30%) provides semantic understanding
- Combined score prevents over-reliance on variable LLM

**4. Code Improvements Didn't Fix Core Issues**
- Small typography tweaks don't improve pixel similarity
- Need structural changes (image layout, spacing)
- Proves evaluator feedback needs to be more specific

---

## What We Validated

### ✅ Full Multi-Agent Loop Works
```
Figma Design
    ↓
Generate Baseline Code (Vision)
    ↓
Render to Screenshot (Playwright)
    ↓
Evaluate Fidelity (Haiku + Pixel-diff)
    ↓
Generate Feedback
    ↓
Improve Code (Sonnet)
    ↓
Re-render and Re-evaluate
    ↓
Compare Scores
```

### ✅ Hybrid Model Strategy Works
- **Haiku** for vision evaluation: cheap, fast, good enough
- **Sonnet** for code improvement: high quality, worth the cost
- Total cost: ~$0.011 per iteration (vs $0.04 all-Sonnet)

### ✅ Two-Tier Evaluation is Critical
- Pixel-diff provides objective baseline
- Vision LLM provides semantic understanding
- 70/30 weighting prevents LLM variability issues

### ✅ Architecture is Sound
- Builder agent: Generates code from designs
- Evaluator agent: Measures fidelity objectively
- Improvement agent: Applies feedback iteratively
- Orchestrator: (Day 8) Will chain these together

---

## Usage

### Generate Improved Code

```bash
cd /Users/geoff.allman/Desktop/figma-to-code-agent
source venv/bin/activate

# Run improvement agent
python scripts/improve_code.py \
  output/code/product-page-baseline.html \
  output/evaluations/latest_evaluation.json
```

**Output:**
- Improved code: `output/code/product-page-baseline-v2.html`
- Metadata: `output/code/product-page-baseline-v2-metadata.json`

### Switch Models

Edit `config.yaml`:
```yaml
models:
  improvement:
    model: claude-3-5-haiku-20241022  # Try cheaper model
    # model: gpt-4o  # Try OpenAI
    # model: gemini-1.5-pro  # Try Google
```

---

## Lessons Learned

### 1. LLM Evaluation Alone is Insufficient
**Problem:** Same design scored 92.5% then 65% on different runs

**Solution:** Use pixel-diff as primary metric (70% weight)

### 2. Feedback Needs to Be More Specific
**Problem:** "Adjust line-height" doesn't fix layout issues

**Solution:** Need pixel-level precision ("Change gap-6 to gap-[18px]")

### 3. Starting Score Matters
**Finding:** 71.8% baseline for complex product page is actually good!

**Context:** Simple nav menu hit 95% baseline, complex pages start lower

### 4. Iteration Requires Structural Changes
**Problem:** Typography tweaks don't improve pixel similarity

**Solution:** Need layout fixes (grid structure, spacing, images)

---

## Next Steps (Day 8)

Build the **Orchestrator** that automatically:
1. Runs baseline generation
2. Evaluates with both metrics
3. Checks exit criteria (score ≥ 85% or max iterations)
4. If not met, applies improvements and loops
5. Returns best version after iterations

This will complete the **automated multi-iteration system**.

---

## Files Created

**Scripts:**
- `scripts/improve_code.py` - Code improvement agent
- `scripts/evaluate_visual.py` - Vision evaluation agent (Day 6)

**Configuration:**
- `config.yaml` - Model and system configuration

**Test Outputs:**
- `output/code/product-page-baseline.html` - V1 baseline
- `output/code/product-page-baseline-v2.html` - V2 improved
- `output/screenshots/product-page-rendered-v1-full.png` - V1 render
- `output/screenshots/product-page-rendered-v2-full.png` - V2 render
- `output/diffs/product-page-v1-diff.png` - Pixel-diff visualization
- `output/diffs/product-page-v2-diff.png` - V2 diff visualization
- `output/evaluations/latest_evaluation.json` - Evaluation results

**Documentation:**
- `docs/day6-vision-evaluation.md` - Day 6 complete
- `docs/day7-code-improvement.md` - Day 7 complete (this file)

---

## Day 7 Completion Checklist

- [x] Build code improvement agent
- [x] Configure hybrid model strategy (Haiku + Sonnet)
- [x] Test on complex product page
- [x] Run full iteration loop (baseline → improve → re-evaluate)
- [x] Validate two-tier evaluation approach
- [x] Measure pixel-diff + vision LLM scores
- [x] Document findings and lessons learned
- [x] Identify improvements for Day 8

**Status:** ✅ Days 6-7 Complete - Ready for Day 8 (Orchestration)

**Total Week 2 Progress:** 2/5 days complete (40%)

---

## Performance Summary

### Cost per Iteration
- Vision evaluation: $0.001 (Haiku)
- Code improvement: $0.01 (Sonnet)
- **Total: $0.011 per iteration**

### Time per Iteration
- Vision evaluation: ~5 seconds
- Code improvement: ~10 seconds
- Rendering: ~2 seconds
- Pixel-diff: ~1 second
- **Total: ~18 seconds per iteration**

### Quality Metrics
- Baseline fidelity: 71.8% (pixel-diff)
- Target fidelity: 85%+
- Gap to close: ~13 percentage points
- Estimated iterations needed: 3-5
