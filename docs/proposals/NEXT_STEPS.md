# Next Steps: DOM Measurement Tool

**Priority:** HIGH → ✅ **PHASE 1 COMPLETE!**
**Impact:** Should significantly improve evaluation accuracy (79% → 85%+ possible)
**Status:** Phase 1 (Manual Mapping) complete in 2.5 hours
**Date:** October 24, 2025

---

## ✅ Phase 1 Complete - Results

**Time:** 2.5 hours (on target: estimated 2-3 hours)

**Deliverables:**
- ✅ `tools/measure_dom_simple.js` - DOM measurement via Playwright
- ✅ `tools/compare_measurements.py` - Comparison + feedback generation
- ✅ `scripts/evaluate_with_measurements.py` - Integrated evaluation

**Test Results:**
- Found **11 specific dimensional issues** with exact pixel values
- 4 high priority (50%-89% deviations)
- 7 medium priority (12%-25% deviations)
- Feedback quality: **Excellent** - specific, actionable, measurable

**Sample Feedback:**
```
🔴 [HIGH] Product title
   Issue: Height is 36px, should be 24.0px
   Deviation: 50.0% too tall
   Fix: Set height to 24.0px

🟡 [MEDIUM] Main image
   Issue: Width is 480px, should be 576.0px
   Deviation: 16.7% too narrow
   Fix: Set width to 576.0px
```

**Next Step:** Integrate into improvement agent and test if this unlocks 79.86% → 85%+ improvement!

See `DOM_MEASUREMENT_SUMMARY.md` for complete details.

---

## The Problem

**Vision LLM evaluation is unreliable for dimensional accuracy:**
- Says "pixel-perfect" when 33% of pixels differ
- Can't accurately measure element dimensions from screenshots
- Evaluates semantic similarity ("are images present?") not precision ("are they 576px?")

**Current bottleneck:** 79.86% score with 33.57% pixel difference remaining

---

## The Solution: DOM Measurement Tool

### Concept

Instead of asking vision LLM to measure from screenshots, **extract actual DOM measurements** and compare to Figma metadata programmatically.

### Approach

1. **Extract Figma Ground Truth** (we already have this!)
   - Parse `pdp-trimmed-metadata.json`
   - Get exact dimensions for every element:
     ```json
     {
       "id": "157:745",
       "name": "Image1",
       "absoluteBoundingBox": {
         "width": 576.0,
         "height": 720.0,
         "x": 2992.0,
         "y": 2435.0
       }
     }
     ```

2. **Extract Rendered DOM Measurements**
   - Use Playwright to inject measurement script
   - Get computed styles and bounding boxes:
     ```javascript
     const elements = document.querySelectorAll('img, div, button, p, h1');
     elements.forEach(el => {
       const rect = el.getBoundingClientRect();
       measurements.push({
         selector: getSelector(el),
         width: rect.width,
         height: rect.height,
         x: rect.x,
         y: rect.y
       });
     });
     ```

3. **Intelligent Element Mapping**
   - Match Figma elements to DOM elements by:
     - Position (similar x, y coordinates)
     - Dimensions (similar width, height)
     - Type (image → `<img>`, text → `<p>/<h1>`, etc.)
     - Order in layout

4. **Calculate Deviations**
   ```python
   for figma_elem, dom_elem in matched_pairs:
       width_deviation = abs(figma_elem.width - dom_elem.width) / figma_elem.width
       height_deviation = abs(figma_elem.height - dom_elem.height) / figma_elem.height

       if width_deviation > 0.20:  # 20% off
           feedback.append({
               'priority': 'high',
               'element': figma_elem.name,
               'issue': f"Width is {dom_elem.width}px, should be {figma_elem.width}px",
               'deviation': f"{width_deviation*100:.1f}% too {'narrow' if dom_elem.width < figma_elem.width else 'wide'}",
               'fix': f"Adjust width to {figma_elem.width}px"
           })
   ```

5. **Generate Actionable Feedback**
   - Specific measurements (not vague descriptions)
   - Exact deviations (% off)
   - Concrete fixes (exact pixel values or CSS changes)

---

## Implementation Tasks

### Task 1: DOM Measurement Script
**File:** `tools/measure_dom.js`

Create Playwright script that:
- Injects measurement code into rendered page
- Extracts bounding boxes for all elements
- Returns structured JSON with measurements

**Deliverable:** JSON file with all DOM element measurements

---

### Task 2: Element Matching Algorithm
**File:** `tools/match_elements.py`

Create algorithm that:
- Loads Figma metadata
- Loads DOM measurements
- Matches corresponding elements using heuristics
- Returns paired elements (Figma ↔ DOM)

**Deliverable:** Matched pairs JSON

---

### Task 3: Deviation Calculator
**File:** `tools/calculate_deviations.py`

Create calculator that:
- Takes matched pairs
- Calculates dimensional deviations
- Categorizes by severity (high/medium/low)
- Generates specific feedback

**Deliverable:** Feedback JSON in improvement agent format

---

### Task 4: Integrated Evaluation Script
**File:** `scripts/evaluate_with_dom_measurements.py`

Combine all pieces:
1. Render HTML with Playwright
2. Extract DOM measurements
3. Load Figma metadata
4. Match elements
5. Calculate deviations
6. Generate feedback
7. Run improvement agent with feedback
8. Re-evaluate

**Deliverable:** End-to-end evaluation with DOM-based feedback

---

### Task 5: Test & Validate
- Run on current test (run3)
- Validate feedback is specific and actionable
- Compare scores before/after improvement
- Target: 79.86% → 85%+

---

## Expected Benefits

### Better Feedback Quality
**Before (Vision LLM):**
- "Color selector strip has slight tonal variation" (vague, low priority)

**After (DOM Measurements):**
- "Left product image is 400px wide, should be 576px (31% too narrow)" (specific, high priority)
- "Product title is 24px font-size, should be 32px (25% too small)" (actionable)
- "Color swatches are 24px diameter, should be 32px (25% too small)" (measurable)

### Objective Scoring
- No more "pixel-perfect" when 33% of pixels differ
- Scores reflect actual dimensional accuracy
- Clear path to improvement (fix specific measurements)

### Faster Iteration
- Precise feedback → targeted fixes
- No guessing what needs to change
- Measurable progress each iteration

---

## Questions to Resolve

1. **Element Matching Complexity**
   - How to handle elements that moved significantly?
   - What if DOM has different structure (fewer/more elements)?
   - Fallback strategy for unmatched elements?

2. **Coordinate System Translation**
   - Figma uses absolute coordinates (2992, 2435)
   - DOM uses relative coordinates (0, 0 = viewport)
   - Need to normalize for comparison

3. **Layout Differences**
   - Figma: Fixed artboard
   - HTML: Responsive (elements may reflow)
   - How to handle acceptable vs. unacceptable layout shifts?

4. **Performance**
   - DOM extraction adds overhead
   - Element matching is O(n²) worst case
   - Need efficient algorithm for 100+ elements

---

## Success Criteria

✅ **Generate 10+ specific dimensional feedback items** (vs. 1 vague item currently)

✅ **Improvement agent produces measurable progress** (79.86% → 85%+)

✅ **Feedback includes exact pixel values** (not subjective descriptions)

✅ **Process is automated** (no manual measurement needed)

✅ **Works on different designs** (not hardcoded for PDP)

---

## Estimated Effort

- Task 1 (DOM measurement): 2-3 hours
- Task 2 (Element matching): 4-6 hours (most complex)
- Task 3 (Deviation calc): 1-2 hours
- Task 4 (Integration): 2-3 hours
- Task 5 (Testing): 2-3 hours

**Total: 11-17 hours of development**

**Timeline:** Could complete in 2-3 focused work sessions

---

## Alternative: Hybrid Approach

Start simpler, iterate:

**Phase 1: Manual Mapping (Quick Win)**
- Manually specify key elements to measure
- Extract just those measurements
- Generate feedback for top 5-10 elements
- **Effort:** 2-3 hours

**Phase 2: Auto-Matching (Full Solution)**
- Build full element matching algorithm
- Handle all elements automatically
- **Effort:** 8-12 hours

Recommend starting with Phase 1 to validate approach!
